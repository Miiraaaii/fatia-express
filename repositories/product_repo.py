"""
Repositório de dados para Produtos, Categorias, Tamanhos e Bordas.
"""

from typing import List, Optional
from database.connection import get_connection
from models.product import Category, PizzaSize, CrustOption, Product


class ProductRepository:
    def get_all_categories(self) -> List[Category]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, icon FROM categories ORDER BY id ASC;")
            rows = cursor.fetchall()
            return [Category(id=r["id"], name=r["name"], icon=r["icon"]) for r in rows]

    def get_pizza_sizes(self) -> List[PizzaSize]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, slices, price_multiplier FROM pizza_sizes ORDER BY id ASC;")
            rows = cursor.fetchall()
            return [
                PizzaSize(
                    id=r["id"],
                    name=r["name"],
                    slices=r["slices"],
                    price_multiplier=r["price_multiplier"],
                )
                for r in rows
            ]

    def get_crust_options(self) -> List[CrustOption]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, price FROM crust_options ORDER BY id ASC;")
            rows = cursor.fetchall()
            return [
                CrustOption(id=r["id"], name=r["name"], price=r["price"])
                for r in rows
            ]

    def get_products(
        self, category_id: Optional[int] = None, search: Optional[str] = None
    ) -> List[Product]:
        query = """
        SELECT p.id, p.category_id, p.name, p.description, p.price_base, 
               p.image_emoji, p.is_pizza, p.available, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.available = 1
        """
        params = []

        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)

        if search:
            query += " AND (p.name LIKE ? OR p.description LIKE ?)"
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        query += " ORDER BY p.is_pizza DESC, p.name ASC;"

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                Product(
                    id=r["id"],
                    category_id=r["category_id"],
                    name=r["name"],
                    description=r["description"] or "",
                    price_base=r["price_base"],
                    image_emoji=r["image_emoji"],
                    is_pizza=bool(r["is_pizza"]),
                    available=bool(r["available"]),
                    category_name=r["category_name"],
                )
                for r in rows
            ]

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        query = """
        SELECT p.id, p.category_id, p.name, p.description, p.price_base, 
               p.image_emoji, p.is_pizza, p.available, c.name as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id = ?;
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (product_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Product(
                id=row["id"],
                category_id=row["category_id"],
                name=row["name"],
                description=row["description"] or "",
                price_base=row["price_base"],
                image_emoji=row["image_emoji"],
                is_pizza=bool(row["is_pizza"]),
                available=bool(row["available"]),
                category_name=row["category_name"],
            )
