"""
Painel / Gaveta de Carrinho de Compras e Checkout.
"""

from typing import Callable
import flet as ft
from models.order import DeliveryType, PaymentMethod
from services.order_service import OrderService
from ui.theme import AppColors, format_currency


class CartView(ft.Container):
    def __init__(
        self,
        order_service: OrderService,
        on_order_created: Callable[[int], None],
        on_cart_updated: Callable[[], None],
    ):
        self.order_service = order_service
        self.on_order_created = on_order_created
        self.on_cart_updated = on_cart_updated

        # Formulário do Cliente
        self.txt_customer_name = ft.TextField(
            label="Nome do Cliente *",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.SECONDARY,
        )
        self.txt_customer_phone = ft.TextField(
            label="Telefone / WhatsApp *",
            prefix_icon=ft.Icons.PHONE_OUTLINE,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.SECONDARY,
            keyboard_type=ft.KeyboardType.PHONE,
        )

        self.rg_delivery_type = ft.RadioGroup(
            content=ft.Row(
                spacing=10,
                controls=[
                    ft.Radio(value=DeliveryType.ENTREGA.value, label="🛵 Entrega"),
                    ft.Radio(value=DeliveryType.BALCAO.value, label="🏬 Balcão"),
                ],
            ),
            value=DeliveryType.ENTREGA.value,
            on_change=self._on_delivery_type_changed,
        )

        self.txt_address = ft.TextField(
            label="Endereço Completo (Rua, Número, Bairro) *",
            prefix_icon=ft.Icons.LOCATION_ON_OUTLINED,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.SECONDARY,
            multiline=True,
            min_lines=2,
            max_lines=3,
        )

        self.dd_payment = ft.Dropdown(
            label="Forma de Pagamento",
            value=PaymentMethod.PIX.value,
            options=[
                ft.dropdown.Option(PaymentMethod.PIX.value, "⚡ Pix"),
                ft.dropdown.Option(PaymentMethod.CARTAO_CREDITO.value, "💳 Cartão de Crédito"),
                ft.dropdown.Option(PaymentMethod.CARTAO_DEBITO.value, "💳 Cartão de Débito"),
                ft.dropdown.Option(PaymentMethod.DINHEIRO.value, "💵 Dinheiro"),
            ],
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.SECONDARY,
        )

        self.txt_order_notes = ft.TextField(
            label="Observações do Pedido (Opcional)",
            hint_text="Ex: Troco para R$ 100, campainha estragada...",
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.SECONDARY,
        )

        # Contêineres dinâmicos
        self.cart_items_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)
        self.lbl_subtotal = ft.Text("R$ 0,00", size=14, color=AppColors.TEXT_PRIMARY)
        self.lbl_delivery_fee = ft.Text("R$ 7,00", size=14, color=AppColors.TEXT_PRIMARY)
        self.lbl_total = ft.Text("R$ 0,00", size=18, weight=ft.FontWeight.BOLD, color=AppColors.SECONDARY)
        self.lbl_feedback = ft.Text("", size=12, color=AppColors.DANGER)

        self.btn_checkout = ft.FilledButton(
            text="Confirmar Pedido",
            icon=ft.Icons.CHECK_CIRCLE,
            style=ft.ButtonStyle(
                bgcolor=AppColors.PRIMARY,
                color=AppColors.TEXT_PRIMARY,
                padding=ft.padding.symmetric(vertical=14),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            width=360,
            on_click=self._handle_checkout,
        )

        super().__init__(
            content=ft.Column(
                spacing=12,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    # Cabeçalho do Carrinho
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Icon(ft.Icons.SHOPPING_BAG_ROUNDED, color=AppColors.SECONDARY),
                                    ft.Text("Meu Pedido", size=18, weight=ft.FontWeight.BOLD),
                                ],
                            ),
                            ft.TextButton(
                                text="Limpar",
                                icon=ft.Icons.DELETE_SWEEP_OUTLINED,
                                style=ft.ButtonStyle(color=AppColors.DANGER),
                                on_click=self._clear_cart,
                            ),
                        ],
                    ),
                    ft.Divider(color=AppColors.BORDER),

                    # Lista de Itens no Carrinho
                    ft.Container(
                        content=self.cart_items_column,
                        height=200,
                        border=ft.border.all(1, AppColors.BORDER),
                        border_radius=8,
                        padding=8,
                    ),

                    # Formulário de Entrega e Cliente
                    ft.Text("Dados para Entrega / Retirada", size=14, weight=ft.FontWeight.BOLD, color=AppColors.SECONDARY),
                    self.txt_customer_name,
                    self.txt_customer_phone,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Modalidade:", size=13),
                            self.rg_delivery_type,
                        ],
                    ),
                    self.txt_address,
                    self.dd_payment,
                    self.txt_order_notes,

                    ft.Divider(color=AppColors.BORDER),

                    # Resumo Financeiro
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[ft.Text("Subtotal:"), self.lbl_subtotal],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[ft.Text("Taxa de Entrega:"), self.lbl_delivery_fee],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Total a Pagar:", size=16, weight=ft.FontWeight.BOLD),
                            self.lbl_total,
                        ],
                    ),

                    self.lbl_feedback,
                    self.btn_checkout,
                ],
            ),
            width=380,
            bgcolor=AppColors.SURFACE,
            border_radius=16,
            border=ft.border.all(1, AppColors.BORDER),
            padding=16,
        )

        self.refresh_cart_display()

    def _on_delivery_type_changed(self, e):
        is_delivery = self.rg_delivery_type.value == DeliveryType.ENTREGA.value
        self.txt_address.visible = is_delivery
        self.refresh_cart_display()
        if self.page:
            self.page.update()

    def _remove_item(self, index: int):
        self.order_service.remove_from_cart(index)
        self.refresh_cart_display()
        self.on_cart_updated()
        if self.page:
            self.page.update()

    def _clear_cart(self, _):
        self.order_service.clear_cart()
        self.refresh_cart_display()
        self.on_cart_updated()
        if self.page:
            self.page.update()

    def refresh_cart_display(self):
        self.cart_items_column.controls.clear()
        cart = self.order_service.cart

        if not cart:
            self.cart_items_column.controls.append(
                ft.Container(
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.REMOVE_SHOPPING_CART_OUTLINED, size=40, color=AppColors.TEXT_SECONDARY),
                            ft.Text("Seu carrinho está vazio", size=13, color=AppColors.TEXT_SECONDARY),
                        ],
                    ),
                    alignment=ft.alignment.center,
                    height=180,
                )
            )
            self.btn_checkout.disabled = True
        else:
            self.btn_checkout.disabled = False
            for idx, item in enumerate(cart):
                self.cart_items_column.controls.append(
                    ft.Container(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Column(
                                    spacing=2,
                                    expand=True,
                                    controls=[
                                        ft.Text(
                                            f"{item.quantity}x {item.product_name}",
                                            size=13,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        ft.Text(
                                            f"{item.size_name or ''} {('- ' + item.crust_name) if item.crust_name and 'Sem Borda' not in item.crust_name else ''}",
                                            size=11,
                                            color=AppColors.TEXT_SECONDARY,
                                        ),
                                        ft.Text(
                                            format_currency(item.subtotal),
                                            size=12,
                                            color=AppColors.SECONDARY,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                    ],
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=AppColors.DANGER,
                                    icon_size=18,
                                    on_click=lambda _, i=idx: self._remove_item(i),
                                ),
                            ],
                        ),
                        bgcolor=AppColors.SURFACE_VARIANT,
                        border_radius=8,
                        padding=8,
                    )
                )

        del_type = DeliveryType(self.rg_delivery_type.value)
        subtotal, delivery_fee, total = self.order_service.calculate_total(del_type)

        self.lbl_subtotal.value = format_currency(subtotal)
        self.lbl_delivery_fee.value = format_currency(delivery_fee)
        self.lbl_total.value = format_currency(total)
        self.btn_checkout.text = f"Confirmar Pedido • {format_currency(total)}"

    def _handle_checkout(self, _):
        del_type = DeliveryType(self.rg_delivery_type.value)
        pay_method = PaymentMethod(self.dd_payment.value)

        success, message, order_id = self.order_service.checkout(
            customer_name=self.txt_customer_name.value or "",
            customer_phone=self.txt_customer_phone.value or "",
            delivery_type=del_type,
            payment_method=pay_method,
            address=self.txt_address.value or "",
            notes=self.txt_order_notes.value or "",
        )

        if not success:
            self.lbl_feedback.value = f"⚠️ {message}"
            self.lbl_feedback.color = AppColors.DANGER
            if self.page:
                self.page.update()
            return

        # Limpar formulário após sucesso
        self.lbl_feedback.value = f"✅ {message}"
        self.lbl_feedback.color = AppColors.SUCCESS
        self.txt_customer_name.value = ""
        self.txt_customer_phone.value = ""
        self.txt_address.value = ""
        self.txt_order_notes.value = ""

        self.refresh_cart_display()
        self.on_cart_updated()
        self.on_order_created(order_id)
        if self.page:
            self.page.update()
