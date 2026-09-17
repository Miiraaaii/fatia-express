"""
Serviço de Negócio para Gestão de Pedidos, Carrinho e Cozinha.
"""

from typing import List, Optional, Dict, Any, Tuple
from models.order import Order, OrderItem, OrderStatus, PaymentMethod, DeliveryType
from repositories.order_repo import OrderRepository


class OrderService:
    DEFAULT_DELIVERY_FEE = 7.00

    def __init__(self, order_repo: Optional[OrderRepository] = None):
        self.repo = order_repo or OrderRepository()
        self.cart: List[OrderItem] = []

    # ==========================
    # Gestão do Carrinho
    # ==========================

    def add_to_cart(
        self,
        product_id: int,
        product_name: str,
        unit_price: float,
        quantity: int,
        size_name: Optional[str] = None,
        crust_name: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> OrderItem:
        """Adiciona um item ao carrinho atual."""
        subtotal = round(unit_price * quantity, 2)
        item = OrderItem(
            id=None,
            product_id=product_id,
            product_name=product_name,
            size_name=size_name,
            crust_name=crust_name,
            unit_price=unit_price,
            quantity=quantity,
            subtotal=subtotal,
            notes=notes,
        )
        self.cart.append(item)
        return item

    def remove_from_cart(self, index: int) -> bool:
        """Remove um item do carrinho pelo índice."""
        if 0 <= index < len(self.cart):
            self.cart.pop(index)
            return True
        return False

    def clear_cart(self) -> None:
        """Limpa todos os itens do carrinho."""
        self.cart.clear()

    def get_cart_subtotal(self) -> float:
        """Calcula o subtotal dos produtos no carrinho."""
        return round(sum(item.subtotal for item in self.cart), 2)

    def calculate_total(self, delivery_type: DeliveryType) -> Tuple[float, float, float]:
        """
        Calcula (subtotal, taxa_entrega, total) com base no tipo de entrega.
        """
        subtotal = self.get_cart_subtotal()
        delivery_fee = self.DEFAULT_DELIVERY_FEE if delivery_type == DeliveryType.ENTREGA else 0.0
        total = round(subtotal + delivery_fee, 2)
        return subtotal, delivery_fee, total

    # ==========================
    # Criação e Validação do Pedido
    # ==========================

    def checkout(
        self,
        customer_name: str,
        customer_phone: str,
        delivery_type: DeliveryType,
        payment_method: PaymentMethod,
        address: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Valida e efetua o fechamento do pedido a partir do carrinho.
        Retorna (sucesso: bool, mensagem: str, order_id: Optional[int]).
        """
        if not self.cart:
            return False, "O carrinho está vazio. Adicione itens antes de finalizar.", None

        if not customer_name or len(customer_name.strip()) < 2:
            return False, "Por favor, informe o nome do cliente.", None

        if not customer_phone or len(customer_phone.strip()) < 8:
            return False, "Por favor, informe um telefone de contato válido.", None

        if delivery_type == DeliveryType.ENTREGA and (not address or len(address.strip()) < 5):
            return False, "Para entregas em domicílio, informe o endereço completo.", None

        subtotal, delivery_fee, total = self.calculate_total(delivery_type)

        new_order = Order(
            customer_name=customer_name.strip(),
            customer_phone=customer_phone.strip(),
            delivery_type=delivery_type,
            address=address.strip() if address else None,
            payment_method=payment_method,
            status=OrderStatus.RECEBIDO,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
            notes=notes.strip() if notes else None,
            items=list(self.cart),
        )

        try:
            order_id = self.repo.create_order(new_order)
            self.clear_cart()
            return True, f"Pedido #{order_id} realizado com sucesso!", order_id
        except Exception as e:
            return False, f"Erro ao salvar pedido: {str(e)}", None

    # ==========================
    # Operações de Cozinha / Gestão
    # ==========================

    def advance_status(self, order_id: int, current_status: OrderStatus) -> Tuple[bool, Optional[OrderStatus]]:
        """Avança o pedido para o próximo estágio operacional."""
        next_st = current_status.next_status
        if not next_st:
            return False, None

        success = self.repo.update_order_status(order_id, next_st)
        return success, next_st if success else None

    def cancel_order(self, order_id: int) -> bool:
        """Cancela um pedido."""
        return self.repo.update_order_status(order_id, OrderStatus.CANCELADO)

    def get_orders(self, status: Optional[OrderStatus] = None) -> List[Order]:
        """Obtém pedidos filtrados por status ou todos."""
        return self.repo.get_orders(status=status)

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Obtém métricas consolidadas para a tela de relatórios."""
        return self.repo.get_metrics()
