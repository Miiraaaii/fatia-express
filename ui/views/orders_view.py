"""
Tela de Gestão de Pedidos (Cozinha e Delivery).
"""

from typing import Optional, List
import flet as ft
from models.order import Order, OrderStatus
from services.order_service import OrderService
from ui.components.order_card import OrderCard
from ui.theme import AppColors


class OrdersView(ft.Container):
    def __init__(self, order_service: OrderService):
        self.order_service = order_service
        self.selected_filter: str = "ATIVOS"
        self.search_query: str = ""

        self.orders_wrap = ft.Row(
            wrap=True,
            spacing=16,
            run_spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.txt_search = ft.TextField(
            hint_text="Buscar por cliente ou # pedido...",
            prefix_icon=ft.Icons.SEARCH,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.SECONDARY,
            expand=True,
            on_change=self._on_search_change,
        )

        self.filter_chips_row = ft.Row(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        self._build_filters()
        self.reload_orders()

        super().__init__(
            content=ft.Column(
                spacing=14,
                expand=True,
                controls=[
                    # Barra Superior
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            self.txt_search,
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                icon_color=AppColors.SECONDARY,
                                tooltip="Atualizar Pedidos",
                                on_click=lambda _: self.reload_orders(),
                            ),
                        ],
                    ),
                    self.filter_chips_row,
                    ft.Divider(color=AppColors.BORDER, height=1),
                    # Grid de Pedidos
                    ft.Container(
                        content=self.orders_wrap,
                        expand=True,
                    ),
                ],
            ),
            expand=True,
            padding=16,
        )

    def _build_filters(self):
        filters = [
            ("ATIVOS", "⚡ Em Andamento"),
            (OrderStatus.RECEBIDO.value, "Novos (Recebidos)"),
            (OrderStatus.EM_PREPARO.value, "Na Cozinha"),
            (OrderStatus.NO_FORNO.value, "No Forno 🔥"),
            (OrderStatus.SAIU_ENTREGA.value, "Em Entrega 🛵"),
            (OrderStatus.ENTREGUE.value, "Concluídos ✅"),
            ("TODOS", "Todos"),
        ]

        self.filter_chips_row.controls.clear()
        for f_key, f_label in filters:
            is_active = self.selected_filter == f_key
            self.filter_chips_row.controls.append(
                ft.FilledButton(
                    text=f_label,
                    style=ft.ButtonStyle(
                        bgcolor=AppColors.PRIMARY if is_active else AppColors.SURFACE_VARIANT,
                        color=AppColors.TEXT_PRIMARY,
                        shape=ft.RoundedRectangleBorder(radius=20),
                    ),
                    on_click=lambda _, k=f_key: self._select_filter(k),
                )
            )

    def _select_filter(self, filter_key: str):
        self.selected_filter = filter_key
        self._build_filters()
        self.reload_orders()
        if self.page:
            self.page.update()

    def _on_search_change(self, e):
        self.search_query = e.control.value.strip().lower()
        self.reload_orders()
        if self.page:
            self.page.update()

    def reload_orders(self):
        self.orders_wrap.controls.clear()

        # Buscar pedidos
        all_orders: List[Order] = self.order_service.get_orders()

        # Filtrar por status
        if self.selected_filter == "ATIVOS":
            filtered = [
                o for o in all_orders 
                if o.status in (OrderStatus.RECEBIDO, OrderStatus.EM_PREPARO, OrderStatus.NO_FORNO, OrderStatus.SAIU_ENTREGA)
            ]
        elif self.selected_filter != "TODOS":
            filtered = [o for o in all_orders if o.status.value == self.selected_filter]
        else:
            filtered = all_orders

        # Filtrar por busca (nome do cliente ou ID)
        if self.search_query:
            filtered = [
                o for o in filtered
                if (self.search_query in o.customer_name.lower() or 
                    self.search_query in str(o.id) or
                    self.search_query in o.customer_phone)
            ]

        if not filtered:
            self.orders_wrap.controls.append(
                ft.Container(
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=52, color=AppColors.TEXT_SECONDARY),
                            ft.Text("Nenhum pedido encontrado nesta seção.", size=14, color=AppColors.TEXT_SECONDARY),
                        ],
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                    height=300,
                )
            )
        else:
            for order in filtered:
                self.orders_wrap.controls.append(
                    OrderCard(
                        order=order,
                        on_advance_status=self._handle_advance_status,
                        on_cancel_order=self._handle_cancel_order,
                    )
                )

        if self.page:
            self.page.update()

    def _handle_advance_status(self, order_id: int, current_status: OrderStatus):
        success, next_st = self.order_service.advance_status(order_id, current_status)
        if success and next_st:
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Pedido #{order_id} avançado para: {next_st.label}"),
                    bgcolor=AppColors.SUCCESS,
                )
            )
            self.reload_orders()

    def _handle_cancel_order(self, order_id: int):
        success = self.order_service.cancel_order(order_id)
        if success:
            self.page.show_dialog(
                ft.SnackBar(
                    content=ft.Text(f"Pedido #{order_id} foi cancelado."),
                    bgcolor=AppColors.DANGER,
                )
            )
            self.reload_orders()
