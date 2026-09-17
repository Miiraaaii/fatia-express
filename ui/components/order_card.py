"""
Componente de exibição de pedido no painel de gestão / cozinha.
"""

from typing import Callable
import flet as ft
from models.order import Order, OrderStatus
from ui.theme import AppColors, get_status_color, format_currency


class OrderCard(ft.Container):
    def __init__(
        self,
        order: Order,
        on_advance_status: Callable[[int, OrderStatus], None],
        on_cancel_order: Callable[[int], None],
    ):
        self.order = order
        self.on_advance_status = on_advance_status
        self.on_cancel_order = on_cancel_order

        status_color = get_status_color(order.status)
        is_active = order.status not in (OrderStatus.ENTREGUE, OrderStatus.CANCELADO)
        next_status = order.status.next_status

        # Lista formatada de itens
        items_controls = []
        for it in order.items:
            items_controls.append(
                ft.Row(
                    cross_axis_alignment=ft.CrossAxisAlignment.START,
                    controls=[
                        ft.Text(f"• {it.quantity}x", weight=ft.FontWeight.BOLD, color=AppColors.SECONDARY),
                        ft.Column(
                            spacing=1,
                            expand=True,
                            controls=[
                                ft.Text(it.product_name, size=13, weight=ft.FontWeight.W_600),
                                ft.Text(
                                    f"{it.size_name or ''} {(' | ' + it.crust_name) if it.crust_name and 'Sem Borda' not in it.crust_name else ''}",
                                    size=11,
                                    color=AppColors.TEXT_SECONDARY,
                                ) if it.size_name or it.crust_name else ft.Container(),
                                ft.Text(
                                    f"Obs: {it.notes}",
                                    size=11,
                                    color=AppColors.WARNING,
                                    italic=True,
                                ) if it.notes else ft.Container(),
                            ],
                        ),
                        ft.Text(format_currency(it.subtotal), size=12, color=AppColors.TEXT_SECONDARY),
                    ],
                )
            )

        # Botões de Ação
        action_buttons = []
        if is_active and next_status:
            btn_advance_label = {
                OrderStatus.RECEBIDO: "Iniciar Preparo 👨‍🍳",
                OrderStatus.EM_PREPARO: "Colocar no Forno 🔥",
                OrderStatus.NO_FORNO: "Despachar Entrega 🛵" if order.delivery_type.value == "ENTREGA" else "Pronto p/ Retirada 📦",
                OrderStatus.SAIU_ENTREGA: "Confirmar Entrega ✅",
            }.get(order.status, f"Avançar: {next_status.label}")

            action_buttons.append(
                ft.FilledButton(
                    text=btn_advance_label,
                    style=ft.ButtonStyle(
                        bgcolor=status_color,
                        color=AppColors.TEXT_PRIMARY,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: self.on_advance_status(self.order.id, self.order.status),
                )
            )

            action_buttons.append(
                ft.TextButton(
                    text="Cancelar",
                    style=ft.ButtonStyle(color=AppColors.DANGER),
                    on_click=lambda _: self.on_cancel_order(self.order.id),
                )
            )

        super().__init__(
            content=ft.Column(
                spacing=10,
                controls=[
                    # Cabeçalho: Número do Pedido + Tag de Status
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=6,
                                controls=[
                                    ft.Icon(ft.Icons.RECEIPT_LONG, size=18, color=AppColors.SECONDARY),
                                    ft.Text(f"Pedido #{order.id}", size=16, weight=ft.FontWeight.BOLD),
                                ],
                            ),
                            ft.Container(
                                content=ft.Text(
                                    order.status.label,
                                    size=12,
                                    color="#FFFFFF",
                                    weight=ft.FontWeight.BOLD,
                                ),
                                bgcolor=status_color,
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                border_radius=12,
                            ),
                        ],
                    ),

                    # Informações do Cliente e Entrega
                    ft.Container(
                        content=ft.Column(
                            spacing=3,
                            controls=[
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(ft.Icons.PERSON, size=14, color=AppColors.TEXT_SECONDARY),
                                        ft.Text(f"{order.customer_name} ({order.customer_phone})", size=12),
                                    ],
                                ),
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(
                                            ft.Icons.MOPED if order.delivery_type.value == "ENTREGA" else ft.Icons.STORE,
                                            size=14,
                                            color=AppColors.TEXT_SECONDARY,
                                        ),
                                        ft.Text(order.delivery_type.label, size=12, weight=ft.FontWeight.W_500),
                                    ],
                                ),
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(ft.Icons.LOCATION_ON, size=14, color=AppColors.TEXT_SECONDARY),
                                        ft.Text(f"Endereço: {order.address}", size=12, color=AppColors.TEXT_SECONDARY),
                                    ],
                                ) if order.address else ft.Container(),
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Icon(ft.Icons.PAYMENTS_OUTLINED, size=14, color=AppColors.TEXT_SECONDARY),
                                        ft.Text(f"Pagamento: {order.payment_method.label}", size=12, color=AppColors.TEXT_SECONDARY),
                                    ],
                                ),
                            ],
                        ),
                        padding=8,
                        bgcolor=AppColors.SURFACE_VARIANT,
                        border_radius=8,
                    ),

                    # Itens do Pedido
                    ft.Text("Itens do Pedido:", size=13, weight=ft.FontWeight.BOLD),
                    ft.Column(spacing=6, controls=items_controls),

                    # Observações Gerais (se houver)
                    ft.Container(
                        content=ft.Row(
                            spacing=6,
                            controls=[
                                ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=AppColors.WARNING),
                                ft.Text(f"Obs: {order.notes}", size=12, color=AppColors.WARNING, expand=True),
                            ],
                        ),
                        bgcolor="#2D2615",
                        padding=6,
                        border_radius=6,
                    ) if order.notes else ft.Container(),

                    ft.Divider(color=AppColors.BORDER, height=1),

                    # Rodapé: Total e Ações
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=1,
                                controls=[
                                    ft.Text(
                                        f"Horário: {order.created_at[11:16] if order.created_at else ''}",
                                        size=11,
                                        color=AppColors.TEXT_SECONDARY,
                                    ),
                                    ft.Text(
                                        f"Total: {format_currency(order.total)}",
                                        size=15,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.SECONDARY,
                                    ),
                                ],
                            ),
                            ft.Row(spacing=6, controls=action_buttons),
                        ],
                    ),
                ],
            ),
            bgcolor=AppColors.SURFACE,
            border=ft.border.all(1, status_color if is_active else AppColors.BORDER),
            border_radius=14,
            padding=14,
            width=360,
        )
