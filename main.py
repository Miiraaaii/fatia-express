"""
FatiaExpress - Sistema de Gestão e Pedidos de Pizzaria.
Aplicação Desktop & Mobile desenvolvida em Python com Flet e SQLite.
"""

import flet as ft
from database.connection import init_database, seed_data_if_empty
from services.catalog_service import CatalogService
from services.order_service import OrderService
from ui.theme import AppColors
from ui.views.catalog_view import CatalogView
from ui.views.orders_view import OrdersView
from ui.views.dashboard_view import DashboardView


def main(page: ft.Page):
    # Inicialização do Banco de Dados SQLite
    init_database()
    seed_data_if_empty()

    # Serviços da aplicação
    catalog_service = CatalogService()
    order_service = OrderService()

    # Configurações gerais da Janela e Página
    page.title = "FatiaExpress - Sistema de Gestão de Pizzaria"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.bgcolor = AppColors.BACKGROUND

    # Ajustes da Janela no Desktop
    try:
        page.window.width = 1200
        page.window.height = 840
        page.window.min_width = 850
        page.window.min_height = 650
    except Exception:
        pass

    # Callback quando um novo pedido é registrado com sucesso
    def on_order_created(order_id: int):
        page.show_dialog(
            ft.SnackBar(
                content=ft.Text(f"🎉 Pedido #{order_id} enviado para a cozinha com sucesso!"),
                bgcolor=AppColors.SUCCESS,
            )
        )
        orders_view.reload_orders()
        dashboard_view.refresh_dashboard()
        page.update()

    # Instâncias das Telas
    catalog_view = CatalogView(
        catalog_service=catalog_service,
        order_service=order_service,
        on_order_created_callback=on_order_created,
    )
    orders_view = OrdersView(order_service=order_service)
    dashboard_view = DashboardView(order_service=order_service)

    # Área dinâmica de conteúdo
    content_container = ft.Container(
        content=catalog_view,
        expand=True,
    )

    # Função de troca de abas
    current_tab = "catalog"

    def switch_tab(tab_name: str):
        nonlocal current_tab
        current_tab = tab_name

        btn_tab_catalog.style.bgcolor = AppColors.PRIMARY if tab_name == "catalog" else ft.Colors.TRANSPARENT
        btn_tab_orders.style.bgcolor = AppColors.PRIMARY if tab_name == "orders" else ft.Colors.TRANSPARENT
        btn_tab_dashboard.style.bgcolor = AppColors.PRIMARY if tab_name == "dashboard" else ft.Colors.TRANSPARENT

        if tab_name == "catalog":
            content_container.content = catalog_view
        elif tab_name == "orders":
            orders_view.reload_orders()
            content_container.content = orders_view
        elif tab_name == "dashboard":
            dashboard_view.refresh_dashboard()
            content_container.content = dashboard_view

        page.update()

    # Botões da Barra Superior
    btn_tab_catalog = ft.FilledButton(
        text="Cardápio & Pedidos",
        icon=ft.Icons.LOCAL_PIZZA,
        style=ft.ButtonStyle(
            bgcolor=AppColors.PRIMARY,
            color=AppColors.TEXT_PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        ),
        on_click=lambda _: switch_tab("catalog"),
    )

    btn_tab_orders = ft.FilledButton(
        text="Cozinha & Gestão",
        icon=ft.Icons.SOUP_KITCHEN,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.TRANSPARENT,
            color=AppColors.TEXT_PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        ),
        on_click=lambda _: switch_tab("orders"),
    )

    btn_tab_dashboard = ft.FilledButton(
        text="Relatórios & Métricas",
        icon=ft.Icons.ANALYTICS,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.TRANSPARENT,
            color=AppColors.TEXT_PRIMARY,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        ),
        on_click=lambda _: switch_tab("dashboard"),
    )

    # Barra Superior (Header / Navbar)
    header = ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Marca do App
                ft.Row(
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            content=ft.Text("🍕", size=24),
                            padding=6,
                            border_radius=10,
                            bgcolor=AppColors.PRIMARY_CONTAINER,
                        ),
                        ft.Column(
                            spacing=1,
                            controls=[
                                ft.Row(
                                    spacing=8,
                                    controls=[
                                        ft.Text("FatiaExpress", size=20, weight=ft.FontWeight.BOLD),
                                        ft.Container(
                                            content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color=AppColors.BACKGROUND),
                                            bgcolor=AppColors.SECONDARY,
                                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                            border_radius=6,
                                        ),
                                    ],
                                ),
                                ft.Text("Sistema Integrado de Pedidos & Cozinha", size=11, color=AppColors.TEXT_SECONDARY),
                            ],
                        ),
                    ],
                ),

                # Abas Centrais de Navegação
                ft.Row(
                    spacing=8,
                    controls=[
                        btn_tab_catalog,
                        btn_tab_orders,
                        btn_tab_dashboard,
                    ],
                ),

                # Status da Conexão / Informações
                ft.Container(
                    content=ft.Row(
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE, size=14, color=AppColors.SUCCESS),
                            ft.Text("SQLite Ativo", size=12, color=AppColors.SUCCESS, weight=ft.FontWeight.W_500),
                        ],
                    ),
                    bgcolor=AppColors.SURFACE_VARIANT,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    border_radius=20,
                ),
            ],
        ),
        bgcolor=AppColors.SURFACE,
        border=ft.border.only(bottom=ft.BorderSide(1, AppColors.BORDER)),
        padding=ft.padding.symmetric(horizontal=20, vertical=12),
    )

    # Montagem da Interface Geral
    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[
                header,
                content_container,
            ],
        )
    )


if __name__ == "__main__":
    ft.run(main)
