"""
Tela de Relatórios e Métricas de Vendas (Dashboard).
"""

from typing import Dict, Any
import flet as ft
from services.order_service import OrderService
from ui.theme import AppColors, format_currency


class DashboardView(ft.Container):
    def __init__(self, order_service: OrderService):
        self.order_service = order_service

        # KPI Containers
        self.kpi_today_revenue = self._create_kpi_card("Faturamento Hoje", "R$ 0,00", ft.Icons.ATTACH_MONEY, AppColors.SUCCESS)
        self.kpi_today_orders = self._create_kpi_card("Pedidos Hoje", "0", ft.Icons.TODAY, AppColors.SECONDARY)
        self.kpi_total_revenue = self._create_kpi_card("Faturamento Total", "R$ 0,00", ft.Icons.QUERY_STATS, AppColors.PRIMARY)
        self.kpi_total_orders = self._create_kpi_card("Total de Pedidos", "0", ft.Icons.RECEIPT, "#3A86FF")

        # Seção de Produtos Mais Vendidos
        self.top_products_column = ft.Column(spacing=8)

        # Seção de Status dos Pedidos
        self.status_summary_row = ft.Row(wrap=True, spacing=10)

        super().__init__(
            content=ft.Column(
                spacing=20,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                controls=[
                    # Cabeçalho
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text("Painel de Desempenho", size=22, weight=ft.FontWeight.BOLD),
                                    ft.Text("Métricas consolidadas de vendas e operação", size=13, color=AppColors.TEXT_SECONDARY),
                                ],
                            ),
                            ft.FilledButton(
                                text="Atualizar Métricas",
                                icon=ft.Icons.REFRESH,
                                style=ft.ButtonStyle(
                                    bgcolor=AppColors.SURFACE_VARIANT,
                                    color=AppColors.TEXT_PRIMARY,
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                                on_click=lambda _: self.refresh_dashboard(),
                            ),
                        ],
                    ),

                    # Linha de KPIs
                    ft.Row(
                        wrap=True,
                        spacing=16,
                        run_spacing=16,
                        controls=[
                            self.kpi_today_revenue,
                            self.kpi_today_orders,
                            self.kpi_total_revenue,
                            self.kpi_total_orders,
                        ],
                    ),

                    ft.Divider(color=AppColors.BORDER),

                    # Status dos Pedidos
                    ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Visão Geral da Operação", size=16, weight=ft.FontWeight.BOLD),
                            self.status_summary_row,
                        ],
                    ),

                    ft.Divider(color=AppColors.BORDER),

                    # Top 5 Sabores Mais Vendidos
                    ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("🏆 Pizzas & Bebidas Mais Vendidas", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=self.top_products_column,
                                bgcolor=AppColors.SURFACE,
                                border=ft.border.all(1, AppColors.BORDER),
                                border_radius=12,
                                padding=14,
                            ),
                        ],
                    ),
                ],
            ),
            expand=True,
            padding=16,
        )

        self.refresh_dashboard()

    def _create_kpi_card(self, title: str, value: str, icon: str, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(title, size=12, color=AppColors.TEXT_SECONDARY),
                            ft.Text(value, size=20, weight=ft.FontWeight.BOLD, color=AppColors.TEXT_PRIMARY),
                        ],
                    ),
                    ft.Container(
                        content=ft.Icon(icon, color=color, size=28),
                        bgcolor=AppColors.SURFACE_VARIANT,
                        padding=10,
                        border_radius=10,
                    ),
                ],
            ),
            bgcolor=AppColors.SURFACE,
            border=ft.border.all(1, AppColors.BORDER),
            border_radius=12,
            padding=16,
            width=260,
        )

    def refresh_dashboard(self):
        metrics: Dict[str, Any] = self.order_service.get_dashboard_metrics()

        # Atualizar KPIs
        self.kpi_today_revenue.content.controls[0].controls[1].value = format_currency(metrics.get("today_revenue", 0.0))
        self.kpi_today_orders.content.controls[0].controls[1].value = str(metrics.get("today_orders", 0))
        self.kpi_total_revenue.content.controls[0].controls[1].value = format_currency(metrics.get("total_revenue", 0.0))
        self.kpi_total_orders.content.controls[0].controls[1].value = str(metrics.get("total_orders", 0))

        # Atualizar Status da Operação
        self.status_summary_row.controls.clear()
        counts = metrics.get("status_counts", {})
        status_labels = [
            ("RECEBIDO", "Recebidos", "#3A86FF"),
            ("EM_PREPARO", "Em Preparo", "#FFBE0B"),
            ("NO_FORNO", "No Forno", "#FB5607"),
            ("SAIU_ENTREGA", "Em Entrega", "#8338EC"),
            ("ENTREGUE", "Entregues", "#2EC4B6"),
            ("CANCELADO", "Cancelados", "#6C757D"),
        ]

        for s_key, s_name, s_col in status_labels:
            qty = counts.get(s_key, 0)
            self.status_summary_row.controls.append(
                ft.Container(
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Container(width=10, height=10, border_radius=5, bgcolor=s_col),
                            ft.Text(f"{s_name}:", size=12, color=AppColors.TEXT_SECONDARY),
                            ft.Text(str(qty), size=13, weight=ft.FontWeight.BOLD),
                        ],
                    ),
                    bgcolor=AppColors.SURFACE,
                    border=ft.border.all(1, AppColors.BORDER),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                )
            )

        # Atualizar Top Produtos
        self.top_products_column.controls.clear()
        top_prods = metrics.get("top_products", [])
        if not top_prods:
            self.top_products_column.controls.append(
                ft.Text("Nenhum item vendido ainda.", size=13, color=AppColors.TEXT_SECONDARY)
            )
        else:
            for idx, p in enumerate(top_prods, 1):
                self.top_products_column.controls.append(
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                spacing=10,
                                controls=[
                                    ft.Text(f"#{idx}", size=14, weight=ft.FontWeight.BOLD, color=AppColors.SECONDARY),
                                    ft.Text(p["name"], size=14, weight=ft.FontWeight.W_500),
                                ],
                            ),
                            ft.Row(
                                spacing=16,
                                controls=[
                                    ft.Text(f"{p['quantity']} un. vendidas", size=13, color=AppColors.TEXT_SECONDARY),
                                    ft.Text(format_currency(p["amount"]), size=14, weight=ft.FontWeight.BOLD, color=AppColors.SECONDARY),
                                ],
                            ),
                        ],
                    )
                )

        if self.page:
            self.page.update()
