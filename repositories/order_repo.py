"""
Repositório de dados para Pedidos e Itens de Pedido.
"""

from typing import List, Optional, Dict, Any
from database.connection import get_connection
from models.order import Order, OrderItem, OrderStatus, PaymentMethod, DeliveryType


class OrderRepository:
    def create_order(self, order: Order) -> int:
        """Cria um novo pedido com seus itens em uma transação atômica."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO orders (
                    customer_name, customer_phone, delivery_type, address,
                    payment_method, status, subtotal, delivery_fee, total, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    order.customer_name,
                    order.customer_phone,
                    order.delivery_type.value,
                    order.address,
                    order.payment_method.value,
                    order.status.value,
                    order.subtotal,
                    order.delivery_fee,
                    order.total,
                    order.notes,
                ),
            )
            order_id = cursor.lastrowid

            # Inserir itens
            for item in order.items:
                cursor.execute(
                    """
                    INSERT INTO order_items (
                        order_id, product_id, size_name, crust_name,
                        product_name, unit_price, quantity, subtotal, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        order_id,
                        item.product_id,
                        item.size_name,
                        item.crust_name,
                        item.product_name,
                        item.unit_price,
                        item.quantity,
                        item.subtotal,
                        item.notes,
                    ),
                )

            conn.commit()
            return order_id

    def update_order_status(self, order_id: int, new_status: OrderStatus) -> bool:
        """Atualiza o status de um pedido."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE orders 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
                """,
                (new_status.value, order_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_orders(self, status: Optional[OrderStatus] = None, limit: int = 100) -> List[Order]:
        """Recupera lista de pedidos ordenada pelo mais recente."""
        query = """
        SELECT id, customer_name, customer_phone, delivery_type, address,
               payment_method, status, subtotal, delivery_fee, total, notes,
               created_at, updated_at
        FROM orders
        """
        params = []
        if status:
            query += " WHERE status = ?"
            params.append(status.value)

        query += " ORDER BY id DESC LIMIT ?;"
        params.append(limit)

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            orders = []

            for r in rows:
                # Buscar itens do pedido
                cursor.execute(
                    """
                    SELECT id, order_id, product_id, size_name, crust_name,
                           product_name, unit_price, quantity, subtotal, notes
                    FROM order_items
                    WHERE order_id = ?
                    ORDER BY id ASC;
                    """,
                    (r["id"],),
                )
                item_rows = cursor.fetchall()
                items = [
                    OrderItem(
                        id=it["id"],
                        order_id=it["order_id"],
                        product_id=it["product_id"],
                        size_name=it["size_name"],
                        crust_name=it["crust_name"],
                        product_name=it["product_name"],
                        unit_price=it["unit_price"],
                        quantity=it["quantity"],
                        subtotal=it["subtotal"],
                        notes=it["notes"],
                    )
                    for it in item_rows
                ]

                orders.append(
                    Order(
                        id=r["id"],
                        customer_name=r["customer_name"],
                        customer_phone=r["customer_phone"],
                        delivery_type=DeliveryType(r["delivery_type"]),
                        address=r["address"],
                        payment_method=PaymentMethod(r["payment_method"]),
                        status=OrderStatus(r["status"]),
                        subtotal=r["subtotal"],
                        delivery_fee=r["delivery_fee"],
                        total=r["total"],
                        notes=r["notes"],
                        created_at=r["created_at"],
                        updated_at=r["updated_at"],
                        items=items,
                    )
                )

            return orders

    def get_metrics(self) -> Dict[str, Any]:
        """Calcula métricas financeiras e de operação para o dashboard."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Faturamento e Pedidos Totais (exceto cancelados)
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total), 0) as total_revenue
                FROM orders
                WHERE status != 'CANCELADO';
                """
            )
            totals = cursor.fetchone()

            # Faturamento e Pedidos de Hoje
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as today_orders,
                    COALESCE(SUM(total), 0) as today_revenue
                FROM orders
                WHERE status != 'CANCELADO' 
                  AND date(created_at, 'localtime') = date('now', 'localtime');
                """
            )
            today = cursor.fetchone()

            # Contagem por Status
            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM orders
                GROUP BY status;
                """
            )
            status_counts = {r["status"]: r["count"] for r in cursor.fetchall()}

            # Top 5 Produtos Mais Vendidos
            cursor.execute(
                """
                SELECT 
                    oi.product_name,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.subtotal) as total_amount
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                WHERE o.status != 'CANCELADO'
                GROUP BY oi.product_name
                ORDER BY total_quantity DESC
                LIMIT 5;
                """
            )
            top_products = [
                {
                    "name": r["product_name"],
                    "quantity": r["total_quantity"],
                    "amount": r["total_amount"],
                }
                for r in cursor.fetchall()
            ]

            return {
                "total_orders": totals["total_orders"] if totals else 0,
                "total_revenue": totals["total_revenue"] if totals else 0.0,
                "today_orders": today["today_orders"] if today else 0,
                "today_revenue": today["today_revenue"] if today else 0.0,
                "status_counts": status_counts,
                "top_products": top_products,
            }
