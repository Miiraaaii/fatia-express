"""
Componente de exibição de produto no cardápio.
"""

from typing import Callable
import flet as ft
from models.product import Product
from ui.theme import AppColors, format_currency


class ProductCard(ft.Container):
    def __init__(self, product: Product, on_select: Callable[[Product], None]):
        self.product = product
        self.on_select = on_select

        price_display = (
            f"A partir de {format_currency(product.price_base)}"
            if product.is_pizza
            else format_currency(product.price_base)
        )

        super().__init__(
            content=ft.Column(
                spacing=8,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    # Cabeçalho do Card (Ícone e Categoria)
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Container(
                                content=ft.Text(product.image_emoji, size=28),
                                padding=8,
                                border_radius=12,
                                bgcolor=AppColors.SURFACE_VARIANT,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    product.category_name or "Geral",
                                    size=11,
                                    color=AppColors.SECONDARY,
                                    weight=ft.FontWeight.W_600,
                                ),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=8,
                                bgcolor=AppColors.PRIMARY_CONTAINER,
                            ),
                        ],
                    ),

                    # Nome e Descrição
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text(
                                product.name,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.TEXT_PRIMARY,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                product.description,
                                size=12,
                                color=AppColors.TEXT_SECONDARY,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                    ),

                    ft.Divider(color=AppColors.BORDER, height=1),

                    # Rodapé: Preço e Botão Adicionar
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                spacing=2,
                                controls=[
                                    ft.Text(
                                        "Valor",
                                        size=10,
                                        color=AppColors.TEXT_SECONDARY,
                                    ),
                                    ft.Text(
                                        price_display,
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.SECONDARY,
                                    ),
                                ],
                            ),
                            ft.FilledButton(
                                text="Pedir",
                                icon=ft.Icons.ADD_SHOPPING_CART_ROUNDED,
                                style=ft.ButtonStyle(
                                    bgcolor=AppColors.PRIMARY,
                                    color=AppColors.TEXT_PRIMARY,
                                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                ),
                                on_click=lambda _: self.on_select(self.product),
                            ),
                        ],
                    ),
                ],
            ),
            bgcolor=AppColors.SURFACE,
            border=ft.border.all(1, AppColors.BORDER),
            border_radius=14,
            padding=16,
            width=280,
            height=200,
        )
