"""
Serviço de Cardápio e Catálogo de Produtos.
"""

from typing import List, Optional
from models.product import Category, PizzaSize, CrustOption, Product
from repositories.product_repo import ProductRepository


class CatalogService:
    def __init__(self, product_repo: Optional[ProductRepository] = None):
        self.repo = product_repo or ProductRepository()

    def get_categories(self) -> List[Category]:
        return self.repo.get_all_categories()

    def get_pizza_sizes(self) -> List[PizzaSize]:
        return self.repo.get_pizza_sizes()

    def get_crust_options(self) -> List[CrustOption]:
        return self.repo.get_crust_options()

    def get_products(
        self, category_id: Optional[int] = None, search: Optional[str] = None
    ) -> List[Product]:
        return self.repo.get_products(category_id=category_id, search=search)

    def get_product(self, product_id: int) -> Optional[Product]:
        return self.repo.get_product_by_id(product_id)
