"""Testes de integração do checkout, usando um SQLite isolado por cenário."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from database.connection import get_connection, init_database, seed_data_if_empty
from repositories.order_repo import OrderRepository
from models.order import OrderStatus
from web_app import create_app


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.directory.name) / "test.db")
        self.app = create_app({"TESTING": True, "DATABASE": self.db_path})
        self.client = self.app.test_client()

    def tearDown(self):
        self.directory.cleanup()

    def payload(self, **changes):
        data = {
            "request_id": str(uuid4()),
            "customer_name": "Ana Silva",
            "customer_phone": "(11) 98765-4321",
            "delivery_type": "ENTREGA",
            "payment_method": "PIX",
            "address": "Rua das Flores, 100, Centro",
            "notes": "Interfone 10",
            "items": [{"product_id": 1, "size_id": 3, "crust_id": 2, "quantity": 2, "notes": "Sem cebola"}],
        }
        data.update(changes)
        return data

    def query(self, sql, params=()):
        with closing(get_connection(self.db_path)) as conn, conn:
            return conn.execute(sql, params).fetchall()

    def post(self, payload=None, **kwargs):
        return self.client.post("/api/orders", json=self.payload() if payload is None else payload, **kwargs)

    def test_catalog_contains_original_menu_and_no_demo_orders(self):
        response = self.client.get("/api/catalog")
        self.assertEqual(response.status_code, 200)
        catalog = response.get_json()
        self.assertEqual(len(catalog["products"]), 17)
        self.assertEqual(len(catalog["categories"]), 4)
        self.assertEqual(len(catalog["sizes"]), 4)
        self.assertEqual(len(catalog["crusts"]), 5)
        self.assertEqual(catalog["delivery_fee"], 7)
        self.assertIs(catalog["products"][0]["is_pizza"], True)
        self.assertEqual(self.query("SELECT COUNT(*) AS n FROM orders")[0]["n"], 0)

    def test_checkout_uses_official_price_instead_of_browser_totals(self):
        payload = self.payload(total=0.01, subtotal=0, delivery_fee=0)
        payload["items"][0].update(unit_price=0.01, subtotal=0.01, product_name="Produto falso")
        response = self.post(payload)
        self.assertEqual(response.status_code, 201)
        order = response.get_json()["order"]
        self.assertEqual(order["status"], "RECEBIDO")
        self.assertEqual(order["subtotal"], 129.4)  # (42 * 1.35 + 8) * 2
        self.assertEqual(order["delivery_fee"], 7)
        self.assertEqual(order["total"], 136.4)
        self.assertEqual(order["items"][0]["unit_price"], 64.7)
        self.assertEqual(order["items"][0]["product_name"], "Calabresa Especial")
        self.assertEqual(order["items"][0]["size_name"], "Grande (8 fatias)")
        self.assertEqual(order["items"][0]["notes"], "Sem cebola")
        self.assertEqual(order["customer_phone"], "11987654321")
        self.assertTrue(order["created_at"].endswith("Z"))

    def test_pickup_removes_delivery_fee_and_address(self):
        response = self.post(self.payload(delivery_type="BALCAO", address=""))
        order = response.get_json()["order"]
        self.assertEqual(response.status_code, 201)
        self.assertEqual(order["delivery_fee"], 0)
        self.assertEqual(order["total"], order["subtotal"])
        self.assertIsNone(order["address"])

    def test_drinks_and_pizzas_without_stuffed_crust(self):
        response = self.post(self.payload(items=[
            {"product_id": 1, "size_id": 1, "crust_id": None, "quantity": 1},
            {"product_id": 14, "size_id": None, "crust_id": None, "quantity": 3},
        ]))
        self.assertEqual(response.status_code, 201)
        order = response.get_json()["order"]
        self.assertEqual(order["subtotal"], 48.9)
        self.assertEqual(order["total"], 55.9)
        self.assertIsNone(order["items"][1]["size_name"])

    def test_prices_round_half_up_per_unit_to_centavos(self):
        self.query("UPDATE products SET price_base = 10.05 WHERE id = 1")
        payload = self.payload(delivery_type="BALCAO", items=[
            {"product_id": 1, "size_id": 1, "crust_id": None, "quantity": 3},
        ])
        order = self.post(payload).get_json()["order"]
        self.assertEqual(order["items"][0]["unit_price"], 7.04)
        self.assertEqual(order["total"], 21.12)

    def test_tracking_requires_the_matching_private_token(self):
        first = self.post().get_json()
        second = self.post().get_json()
        url = f'/api/orders/{first["order"]["id"]}'
        for headers in ({}, {"Authorization": "Bearer incorrect"},
                        {"Authorization": f'Bearer {second["tracking_token"]}'}):
            with self.subTest(headers=bool(headers)):
                response = self.client.get(url, headers=headers)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("customer_name", response.get_json())
        response = self.client.get(url, headers={"Authorization": f'Bearer {first["tracking_token"]}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["order"], first["order"])
        self.assertEqual(self.client.get("/api/orders").status_code, 405)

    def test_only_token_digest_is_stored_and_token_survives_restart(self):
        created = self.post().get_json()
        token = created["tracking_token"]
        stored = self.query("SELECT * FROM web_order_access")[0]
        self.assertEqual(stored["token_hash"], hashlib.sha256(token.encode()).hexdigest())
        self.assertNotIn(token, tuple(stored))
        restarted = create_app({"TESTING": True, "DATABASE": self.db_path}).test_client()
        response = restarted.get(f'/api/orders/{created["order"]["id"]}',
                                 headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(response.status_code, 200)

    def test_retry_returns_same_order_and_token_even_after_catalog_change_and_restart(self):
        payload = self.payload()
        first = self.post(payload).get_json()
        self.query("UPDATE products SET price_base = 99, available = 0 WHERE id = 1")
        restarted = create_app({"TESTING": True, "DATABASE": self.db_path}).test_client()
        response = restarted.post("/api/orders", json=payload)
        self.assertEqual(response.status_code, 201)
        replay = response.get_json()
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["order"], first["order"])
        self.assertEqual(replay["tracking_token"], first["tracking_token"])
        self.assertEqual(self.query("SELECT COUNT(*) AS n FROM orders")[0]["n"], 1)

    def test_same_request_id_with_different_payload_is_a_conflict(self):
        payload = self.payload()
        self.post(payload)
        payload["items"][0]["quantity"] = 3
        response = self.post(payload)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["field"], "request_id")
        self.assertEqual(self.query("SELECT COUNT(*) AS n FROM orders")[0]["n"], 1)

    def test_simultaneous_retries_create_exactly_one_order(self):
        payload = self.payload()
        def submit(_):
            with self.app.test_client() as client:
                response = client.post("/api/orders", json=payload)
                return response.status_code, response.get_json()
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(submit, range(4)))
        self.assertEqual([status for status, _ in results], [201] * 4)
        self.assertEqual(len({body["order"]["id"] for _, body in results}), 1)
        self.assertEqual(len({body["tracking_token"] for _, body in results}), 1)
        self.assertEqual(self.query("SELECT COUNT(*) AS n FROM orders")[0]["n"], 1)

    def test_invalid_customer_and_order_fields(self):
        invalid = {
            "customer_name": [None, "", "A", "123", "A" * 81, {}, "Ana\x00Silva"],
            "customer_phone": [None, "1234", "(20) 98765-4321", "(11) 88765-4321", "119ABCDEFGH"],
            "delivery_type": [None, "DELIVERY", [], {}],
            "payment_method": [None, "TRANSFERENCIA", [], {}],
            "address": [None, "", "Rua", "a" * 281],
            "notes": ["a" * 501, 123],
            "request_id": [None, "not-a-uuid", "00000000-0000-0000-0000-000000000000"],
            "items": [None, [], {}, [None], [{}] * 31],
        }
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=str(value)[:40]):
                    response = self.post(self.payload(**{field: value}))
                    self.assertEqual(response.status_code, 400, response.get_json())
        self.assertEqual(self.query("SELECT COUNT(*) AS n FROM orders")[0]["n"], 0)

    def test_formatted_brazilian_mobile_and_landline_numbers(self):
        for phone, expected in [("+55 (11) 98765-4321", "11987654321"), ("(21) 2345-6789", "2123456789")]:
            with self.subTest(phone=phone):
                response = self.post(self.payload(customer_phone=phone))
                self.assertEqual(response.status_code, 201)
                self.assertEqual(response.get_json()["order"]["customer_phone"], expected)

    def test_item_validation_and_atomicity(self):
        valid = self.payload()["items"][0]
        invalid_items = [
            {**valid, "product_id": 999}, {**valid, "product_id": True},
            {**valid, "product_id": "1"}, {**valid, "product_id": -1},
            {**valid, "size_id": None}, {**valid, "size_id": 999}, {**valid, "size_id": True},
            {**valid, "crust_id": 999}, {**valid, "crust_id": False},
            {**valid, "quantity": 0}, {**valid, "quantity": -1}, {**valid, "quantity": 21},
            {**valid, "quantity": 1.5}, {**valid, "quantity": True}, {**valid, "quantity": "1"},
            {**valid, "notes": "a" * 251}, {**valid, "product_id": 14},
        ]
        for item in invalid_items:
            with self.subTest(item=item):
                response = self.post(self.payload(items=[valid, item]))
                self.assertEqual(response.status_code, 400, response.get_json())
        self.assertEqual(self.query("SELECT COUNT(*) AS n FROM orders")[0]["n"], 0)
        self.assertEqual(self.query("SELECT COUNT(*) AS n FROM order_items")[0]["n"], 0)

    def test_unavailable_product_is_hidden_and_cannot_be_ordered(self):
        self.query("UPDATE products SET available = 0 WHERE id = 1")
        catalog = self.client.get("/api/catalog").get_json()
        self.assertNotIn(1, [product["id"] for product in catalog["products"]])
        self.assertEqual(self.post().status_code, 400)

    def test_malformed_json_wrong_content_type_and_body_limit(self):
        self.assertEqual(self.client.post("/api/orders", data="{", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/orders", json=[]).status_code, 400)
        self.assertEqual(self.client.post("/api/orders", data="null", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/orders", data="{}").status_code, 415)
        self.assertEqual(self.client.post("/api/orders", data=" " * 65537, content_type="application/json").status_code, 413)

    def test_cross_origin_browser_posts_are_rejected(self):
        for headers in [
            {"Origin": "https://malicious.example"}, {"Origin": "null"}, {"Origin": "http://["},
            {"Sec-Fetch-Site": "cross-site"}, {"Sec-Fetch-Site": "same-site"},
        ]:
            with self.subTest(headers=headers):
                self.assertEqual(self.post(headers=headers).status_code, 403)
        self.assertEqual(self.post(headers={"Origin": "http://localhost", "Sec-Fetch-Site": "same-origin"}).status_code, 201)

    def test_database_isolation_and_missing_order_lookup(self):
        first = self.post().get_json()
        isolated = create_app({"TESTING": True, "DATABASE": str(Path(self.directory.name) / "another.db")}).test_client()
        headers = {"Authorization": f'Bearer {first["tracking_token"]}'}
        self.assertEqual(isolated.get(f'/api/orders/{first["order"]["id"]}', headers=headers).status_code, 404)
        self.assertEqual(self.client.get(f'/api/orders/{10 ** 100}', headers=headers).status_code, 404)
        self.assertEqual(self.client.get("/api/orders/999", headers=headers).status_code, 404)

    def test_existing_desktop_kitchen_updates_appear_in_tracking(self):
        created = self.post().get_json()
        with patch.dict(os.environ, {"FATIA_DB_PATH": self.db_path}):
            self.assertTrue(OrderRepository().update_order_status(created["order"]["id"], OrderStatus.EM_PREPARO))
        response = self.client.get(f'/api/orders/{created["order"]["id"]}',
                                   headers={"Authorization": f'Bearer {created["tracking_token"]}'})
        self.assertEqual(response.get_json()["order"]["status"], "EM_PREPARO")
        # The legacy repository leaves a connection to GC; release it before Windows cleanup.
        import gc
        gc.collect()

    def test_default_desktop_seed_behavior_is_preserved(self):
        desktop_db = str(Path(self.directory.name) / "desktop.db")
        init_database(desktop_db)
        seed_data_if_empty(db_path=desktop_db)
        with closing(get_connection(desktop_db)) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 4)

    def test_health_and_response_headers(self):
        self.assertEqual(self.client.get("/health").get_json(), {"status": "ok"})
        response = self.client.get("/api/catalog")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)


if __name__ == "__main__":
    unittest.main()
