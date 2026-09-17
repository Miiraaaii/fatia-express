"""
Modelos de domínio para Pedidos, Itens e Estados.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class OrderStatus(str, Enum):
    RECEBIDO = "RECEBIDO"
    EM_PREPARO = "EM_PREPARO"
    NO_FORNO = "NO_FORNO"
    SAIU_ENTREGA = "SAIU_ENTREGA"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"

    @property
    def label(self) -> str:
        labels = {
            OrderStatus.RECEBIDO: "Recebido",
            OrderStatus.EM_PREPARO: "Em Preparo",
            OrderStatus.NO_FORNO: "No Forno 🔥",
            OrderStatus.SAIU_ENTREGA: "Saiu para Entrega 🛵",
            OrderStatus.ENTREGUE: "Entregue / Concluído ✅",
            OrderStatus.CANCELADO: "Cancelado ❌",
        }
        return labels.get(self, self.value)

    @property
    def next_status(self) -> Optional["OrderStatus"]:
        flow = {
            OrderStatus.RECEBIDO: OrderStatus.EM_PREPARO,
            OrderStatus.EM_PREPARO: OrderStatus.NO_FORNO,
            OrderStatus.NO_FORNO: OrderStatus.SAIU_ENTREGA,
            OrderStatus.SAIU_ENTREGA: OrderStatus.ENTREGUE,
            OrderStatus.ENTREGUE: None,
            OrderStatus.CANCELADO: None,
        }
        return flow.get(self)


class PaymentMethod(str, Enum):
    PIX = "PIX"
    CARTAO_CREDITO = "CARTAO_CREDITO"
    CARTAO_DEBITO = "CARTAO_DEBITO"
    DINHEIRO = "DINHEIRO"

    @property
    def label(self) -> str:
        labels = {
            PaymentMethod.PIX: "Pix (Instantâneo)",
            PaymentMethod.CARTAO_CREDITO: "Cartão de Crédito",
            PaymentMethod.CARTAO_DEBITO: "Cartão de Débito",
            PaymentMethod.DINHEIRO: "Dinheiro",
        }
        return labels.get(self, self.value)


class DeliveryType(str, Enum):
    ENTREGA = "ENTREGA"
    BALCAO = "BALCAO"

    @property
    def label(self) -> str:
        return "Entrega em Domicílio" if self == DeliveryType.ENTREGA else "Retirada no Balcão"


@dataclass
class OrderItem:
    id: Optional[int]
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    subtotal: float
    size_name: Optional[str] = None
    crust_name: Optional[str] = None
    notes: Optional[str] = None
    order_id: Optional[int] = None

    @property
    def formatted_description(self) -> str:
        parts = [self.product_name]
        details = []
        if self.size_name:
            details.append(self.size_name)
        if self.crust_name and "Sem Borda" not in self.crust_name:
            details.append(f"Borda: {self.crust_name}")
        if details:
            parts.append(f"({', '.join(details)})")
        if self.notes:
            parts.append(f"Obs: {self.notes}")
        return " ".join(parts)


@dataclass
class Order:
    customer_name: str
    customer_phone: str
    delivery_type: DeliveryType
    payment_method: PaymentMethod
    subtotal: float
    total: float
    id: Optional[int] = None
    address: Optional[str] = None
    status: OrderStatus = OrderStatus.RECEBIDO
    delivery_fee: float = 0.0
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    items: List[OrderItem] = field(default_factory=list)
