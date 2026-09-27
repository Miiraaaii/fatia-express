"""Checkout HTTP: validação, preços oficiais e acesso privado aos pedidos.

Mantém os pedidos nas mesmas tabelas usadas pelo aplicativo Flet. Nenhum valor
monetário enviado pelo navegador é utilizado para calcular o pedido.
"""

from contextlib import closing
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import hmac
import json
import re
import secrets
from uuid import UUID

from database.connection import get_connection
from models.order import DeliveryType, PaymentMethod


class CheckoutError(ValueError):
    def __init__(self, message, field=None, status=400):
        super().__init__(message)
        self.field = field
        self.status = status


class WebOrderService:
    DELIVERY_FEE = Decimal("7.00")
    VALID_DDDS = {
        11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28,
        31, 32, 33, 34, 35, 37, 38, 41, 42, 43, 44, 45, 46, 47, 48, 49,
        51, 53, 54, 55, 61, 62, 63, 64, 65, 66, 67, 68, 69,
        71, 73, 74, 75, 77, 79, 81, 82, 83, 84, 85, 86, 87, 88, 89,
        91, 92, 93, 94, 95, 96, 97, 98, 99,
    }

    def __init__(self, db_path):
        self.db_path = db_path
        with closing(get_connection(db_path)) as conn, conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS web_settings (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS web_order_access (
                    order_id INTEGER PRIMARY KEY REFERENCES orders(id) ON DELETE CASCADE,
                    request_id_hash TEXT NOT NULL UNIQUE,
                    payload_hash TEXT NOT NULL,
                    token_hash TEXT NOT NULL
                )
            """)
            conn.execute(
                "INSERT OR IGNORE INTO web_settings(key, value) VALUES ('token_secret', ?)",
                (secrets.token_hex(32),),
            )
            self._token_secret = bytes.fromhex(conn.execute(
                "SELECT value FROM web_settings WHERE key = 'token_secret'"
            ).fetchone()["value"])

    def catalog(self):
        with closing(get_connection(self.db_path)) as conn:
            products = [dict(row) for row in conn.execute("""
                SELECT p.*, c.name AS category_name FROM products p
                JOIN categories c ON c.id = p.category_id
                WHERE p.available = 1 ORDER BY p.id
            """)]
            for product in products:
                product["is_pizza"] = bool(product["is_pizza"])
                product["available"] = bool(product["available"])
                product["description"] = product["description"] or ""
            return {
                "products": products,
                "categories": [dict(row) for row in conn.execute("SELECT * FROM categories ORDER BY id")],
                "sizes": [dict(row) for row in conn.execute("SELECT * FROM pizza_sizes ORDER BY id")],
                "crusts": [dict(row) for row in conn.execute("SELECT * FROM crust_options ORDER BY id")],
                "delivery_fee": float(self.DELIVERY_FEE),
            }

    @staticmethod
    def _text(value, field, label, limit, minimum=0):
        if value is None and minimum == 0:
            return None
        if not isinstance(value, str):
            raise CheckoutError(f"Informe {label} válido.", field)
        # Reject control characters while allowing line breaks in free text.
        if any(ord(character) < 32 and character not in "\t\n\r" for character in value):
            raise CheckoutError(f"Revise {label}.", field)
        if len(value) > limit:
            raise CheckoutError(f"{label.capitalize()} deve ter até {limit} caracteres.", field)
        value = " ".join(value.split())
        if len(value) < minimum:
            raise CheckoutError(f"Informe {label} com pelo menos {minimum} caracteres.", field)
        return value or None

    @staticmethod
    def _id(value, field, optional=False):
        if optional and value is None:
            return None
        if type(value) is not int or value < 1 or value > 2_147_483_647:
            raise CheckoutError("Selecione uma opção válida.", field)
        return value

    def _normalize(self, data):
        if not isinstance(data, dict):
            raise CheckoutError("Envie os dados do pedido em um objeto JSON.")
        request_id = data.get("request_id")
        try:
            if not isinstance(request_id, str) or len(request_id) > 36:
                raise ValueError
            parsed_id = UUID(request_id)
            if parsed_id.version != 4:
                raise ValueError
            request_id = str(parsed_id)
        except (ValueError, AttributeError):
            raise CheckoutError("Identificador do pedido inválido. Atualize e tente novamente.", "request_id") from None
        name = self._text(data.get("customer_name"), "customer_name", "seu nome", 80, 2)
        if sum(character.isalpha() for character in name) < 2:
            raise CheckoutError("Informe seu nome.", "customer_name")
        phone = self._text(data.get("customer_phone"), "customer_phone", "um telefone com DDD", 25, 10)
        if not re.fullmatch(r"[0-9+().\s-]+", phone):
            raise CheckoutError("Informe um telefone brasileiro válido com DDD.", "customer_phone")
        phone = re.sub(r"\D", "", phone)
        if len(phone) in (12, 13) and phone.startswith("55"):
            phone = phone[2:]
        if (len(phone) not in (10, 11) or int(phone[:2]) not in self.VALID_DDDS
                or (len(phone) == 11 and phone[2] != "9")
                or (len(phone) == 10 and phone[2] not in "2345")):
            raise CheckoutError("Informe um telefone brasileiro válido com DDD.", "customer_phone")
        delivery = data.get("delivery_type")
        payment = data.get("payment_method")
        if not isinstance(delivery, str) or delivery not in {item.value for item in DeliveryType}:
            raise CheckoutError("Escolha entrega ou retirada no balcão.", "delivery_type")
        if not isinstance(payment, str) or payment not in {item.value for item in PaymentMethod}:
            raise CheckoutError("Escolha uma forma de pagamento válida.", "payment_method")
        address = self._text(data.get("address"), "address", "o endereço completo", 280,
                             8 if delivery == "ENTREGA" else 0)
        notes = self._text(data.get("notes"), "notes", "observações", 500)
        raw_items = data.get("items")
        if not isinstance(raw_items, list) or not 1 <= len(raw_items) <= 30:
            raise CheckoutError("O carrinho deve conter entre 1 e 30 itens.", "items")
        items = []
        for index, item in enumerate(raw_items):
            field = f"items.{index}"
            if not isinstance(item, dict):
                raise CheckoutError("Revise os itens do carrinho.", field)
            quantity = item.get("quantity")
            if type(quantity) is not int or not 1 <= quantity <= 20:
                raise CheckoutError("A quantidade de cada item deve ser de 1 a 20.", f"{field}.quantity")
            items.append({
                "product_id": self._id(item.get("product_id"), f"{field}.product_id"),
                "size_id": self._id(item.get("size_id"), f"{field}.size_id", optional=True),
                "crust_id": self._id(item.get("crust_id"), f"{field}.crust_id", optional=True),
                "quantity": quantity,
                "notes": self._text(item.get("notes"), f"{field}.notes", "observações do item", 250),
            })
        return request_id, {
            "customer_name": name, "customer_phone": phone, "delivery_type": delivery,
            "payment_method": payment, "address": address if delivery == "ENTREGA" else None,
            "notes": notes, "items": items,
        }

    @staticmethod
    def _digest(value):
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _token(self, request_id):
        # Stable after a restart, so a lost HTTP response can be retried safely.
        # The database stores only a digest of this per-order bearer credential.
        return hmac.new(self._token_secret, ("order:" + request_id).encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _money(value):
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def checkout(self, data):
        request_id, payload = self._normalize(data)
        request_hash = self._digest(request_id)
        payload_hash = self._digest(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
        token = self._token(request_id)
        with closing(get_connection(self.db_path)) as conn, conn:
            # One writer owns the idempotency check and the complete order insert.
            conn.execute("BEGIN IMMEDIATE")
            previous = conn.execute(
                "SELECT order_id, payload_hash FROM web_order_access WHERE request_id_hash = ?",
                (request_hash,),
            ).fetchone()
            if previous:
                if not hmac.compare_digest(previous["payload_hash"], payload_hash):
                    raise CheckoutError("Este envio já foi usado para outro pedido. Revise o carrinho e tente novamente.",
                                        "request_id", 409)
                return {"order": self._order(conn, previous["order_id"]), "tracking_token": token, "replayed": True}

            priced_items = []
            subtotal = Decimal("0.00")
            for index, item in enumerate(payload["items"]):
                field = f"items.{index}"
                product = conn.execute("SELECT * FROM products WHERE id = ? AND available = 1",
                                       (item["product_id"],)).fetchone()
                if not product:
                    raise CheckoutError("Um produto ficou indisponível. Atualize o cardápio.", f"{field}.product_id")
                unit = Decimal(str(product["price_base"]))
                size_name = crust_name = None
                if product["is_pizza"]:
                    size = conn.execute("SELECT * FROM pizza_sizes WHERE id = ?", (item["size_id"],)).fetchone()
                    if not size:
                        raise CheckoutError("Escolha um tamanho válido para a pizza.", f"{field}.size_id")
                    size_name = size["name"]
                    unit *= Decimal(str(size["price_multiplier"]))
                    if item["crust_id"] is not None:
                        crust = conn.execute("SELECT * FROM crust_options WHERE id = ?", (item["crust_id"],)).fetchone()
                        if not crust:
                            raise CheckoutError("Escolha uma borda válida.", f"{field}.crust_id")
                        crust_name = crust["name"]
                        unit += Decimal(str(crust["price"]))
                elif item["size_id"] is not None or item["crust_id"] is not None:
                    raise CheckoutError("Bebidas não têm tamanho de pizza ou borda.", field)
                unit = self._money(unit)
                line_total = unit * item["quantity"]
                subtotal += line_total
                priced_items.append((item["product_id"], size_name, crust_name, product["name"],
                                     float(unit), item["quantity"], float(line_total), item["notes"]))
            fee = self.DELIVERY_FEE if payload["delivery_type"] == "ENTREGA" else Decimal("0.00")
            cursor = conn.execute("""
                INSERT INTO orders (customer_name, customer_phone, delivery_type, address,
                    payment_method, status, subtotal, delivery_fee, total, notes)
                VALUES (?, ?, ?, ?, ?, 'RECEBIDO', ?, ?, ?, ?)
            """, (payload["customer_name"], payload["customer_phone"], payload["delivery_type"],
                  payload["address"], payload["payment_method"], float(subtotal), float(fee),
                  float(subtotal + fee), payload["notes"]))
            order_id = cursor.lastrowid
            conn.executemany("""
                INSERT INTO order_items (order_id, product_id, size_name, crust_name,
                    product_name, unit_price, quantity, subtotal, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(order_id, *item) for item in priced_items])
            conn.execute("""
                INSERT INTO web_order_access(order_id, request_id_hash, payload_hash, token_hash)
                VALUES (?, ?, ?, ?)
            """, (order_id, request_hash, payload_hash, self._digest(token)))
            return {"order": self._order(conn, order_id), "tracking_token": token, "replayed": False}

    @staticmethod
    def _order(conn, order_id):
        order = dict(conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone())
        for key in ("created_at", "updated_at"):
            if order[key]:
                order[key] = order[key].replace(" ", "T") + "Z"
        order["items"] = [dict(row) for row in conn.execute(
            "SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (order_id,))]
        return order

    def track(self, order_id, token):
        if (not 1 <= order_id <= 2_147_483_647 or not isinstance(token, str)
                or not re.fullmatch(r"[a-f0-9]{64}", token)):
            raise CheckoutError("Pedido não encontrado ou código de acompanhamento inválido.", status=404)
        with closing(get_connection(self.db_path)) as conn:
            access = conn.execute("SELECT token_hash FROM web_order_access WHERE order_id = ?", (order_id,)).fetchone()
            if not access or not hmac.compare_digest(access["token_hash"], self._digest(token)):
                raise CheckoutError("Pedido não encontrado ou código de acompanhamento inválido.", status=404)
            return {"order": self._order(conn, order_id)}
