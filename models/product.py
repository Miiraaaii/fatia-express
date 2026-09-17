"""
Modelos de domínio para Produtos, Categorias, Tamanhos e Bordas.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    id: int
    name: str
    icon: str


@dataclass
class PizzaSize:
    id: int
    name: str
    slices: int
    price_multiplier: float


@dataclass
class CrustOption:
    id: int
    name: str
    price: float


@dataclass
class Product:
    id: int
    category_id: int
    name: str
    description: str
    price_base: float
    image_emoji: str = "🍕"
    is_pizza: bool = True
    available: bool = True
    category_name: Optional[str] = None

    def calculate_price(self, size: Optional[PizzaSize] = None, crust: Optional[CrustOption] = None) -> float:
        """Calcula o valor final da pizza com base no tamanho e borda recheada."""
        if not self.is_pizza or size is None:
            return round(self.price_base, 2)

        base_adjusted = self.price_base * size.price_multiplier
        crust_price = crust.price if crust else 0.0
        return round(base_adjusted + crust_price, 2)
