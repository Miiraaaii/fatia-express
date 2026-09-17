"""
Modal de personalização e adição de produto ao carrinho.
"""

from typing import Callable, List, Optional
import flet as ft
from models.product import Product, PizzaSize, CrustOption
from ui.theme import AppColors, format_currency


class ProductDialog(ft.AlertDialog):
    def __init__(
        self,
        page: ft.Page,
        product: Product,
        sizes: List[PizzaSize],
        crusts: List[CrustOption],
        on_add: Callable[[Product, Optional[PizzaSize], Optional[CrustOption], int, Optional[str], float], None],
    ):
        self.main_page = page
        self.product = product
        self.sizes = sizes
        self.crusts = crusts
        self.on_add = on_add

        # Estado inicial
        self.selected_size: Optional[PizzaSize] = sizes[1] if sizes and product.is_pizza else None # Média por padrão
        self.selected_crust: Optional[CrustOption] = crusts[0] if crusts and product.is_pizza else None # Tradicional
        self.quantity: int = 1

        # Controles interativos
        self.txt_quantity = ft.Text(str(self.quantity), size=18, weight=ft.FontWeight.BOLD)
        self.txt_notes = ft.TextField(
            label="Observações / Instruções especiais",
            hint_text="Ex: Sem cebola, massa fina, bem assada...",
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.SECONDARY,
        )

        self.lbl_unit_price = ft.Text(size=14, color=AppColors.TEXT_SECONDARY)
        self.btn_confirm = ft.FilledButton(
            text="Adicionar ao Pedido",
            icon=ft.Icons.CHECK_CIRCLE_ROUNDED,
            style=ft.ButtonStyle(
                bgcolor=AppColors.PRIMARY,
                color=AppColors.TEXT_PRIMARY,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self._on_confirm_click,
        )

        # Montar opções de tamanho
        content_controls = []

        if product.is_pizza and sizes:
            self.dropdown_size = ft.Dropdown(
                label="Selecione o Tamanho",
                value=str(self.selected_size.id) if self.selected_size else None,
                options=[
                    ft.dropdown.Option(
                        key=str(s.id),
                        text=f"{s.name} - {format_currency(product.price_base * s.price_multiplier)}",
                    )
                    for s in sizes
                ],
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.SECONDARY,
                on_change=self._on_size_change,
            )
            content_controls.append(self.dropdown_size)

        if product.is_pizza and crusts:
            self.dropdown_crust = ft.Dropdown(
                label="Borda Recheada",
                value=str(self.selected_crust.id) if self.selected_crust else None,
                options=[
                    ft.dropdown.Option(
                        key=str(c.id),
                        text=f"{c.name} (+{format_currency(c.price)})" if c.price > 0 else c.name,
                    )
                    for c in crusts
                ],
                border_color=AppColors.BORDER,
                focused_border_color=AppColors.SECONDARY,
                on_change=self._on_crust_change,
            )
            content_controls.append(self.dropdown_crust)

        # Seletor de Quantidade
        content_controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Text("Quantidade:", size=14, weight=ft.FontWeight.W_500),
                    ft.Row(
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.REMOVE_CIRCLE_OUTLINE,
                                icon_color=AppColors.TEXT_SECONDARY,
                                on_click=self._decrease_qty,
                            ),
                            self.txt_quantity,
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                icon_color=AppColors.SECONDARY,
                                on_click=self._increase_qty,
                            ),
                        ],
                    ),
                ],
            )
        )

        content_controls.append(self.txt_notes)
        content_controls.append(self.lbl_unit_price)

        self._update_price_display()

        super().__init__(
            title=ft.Row(
                spacing=10,
                controls=[
                    ft.Text(product.image_emoji, size=24),
                    ft.Text(product.name, size=18, weight=ft.FontWeight.BOLD),
                ],
            ),
            content=ft.Container(
                content=ft.Column(
                    spacing=14,
                    controls=content_controls,
                    tight=True,
                ),
                width=420,
            ),
            actions=[
                ft.TextButton(
                    text="Cancelar",
                    on_click=lambda _: self.main_page.pop_dialog(),
                ),
                self.btn_confirm,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _get_current_unit_price(self) -> float:
        return self.product.calculate_price(self.selected_size, self.selected_crust)

    def _update_price_display(self) -> None:
        unit = self._get_current_unit_price()
        total = round(unit * self.quantity, 2)
        self.lbl_unit_price.value = f"Unitário: {format_currency(unit)} | Total: {format_currency(total)}"
        self.btn_confirm.text = f"Adicionar • {format_currency(total)}"

    def _on_size_change(self, e) -> None:
        size_id = int(e.control.value)
        self.selected_size = next((s for s in self.sizes if s.id == size_id), None)
        self._update_price_display()
        self.main_page.update()

    def _on_crust_change(self, e) -> None:
        crust_id = int(e.control.value)
        self.selected_crust = next((c for c in self.crusts if c.id == crust_id), None)
        self._update_price_display()
        self.main_page.update()

    def _increase_qty(self, _) -> None:
        self.quantity += 1
        self.txt_quantity.value = str(self.quantity)
        self._update_price_display()
        self.main_page.update()

    def _decrease_qty(self, _) -> None:
        if self.quantity > 1:
            self.quantity -= 1
            self.txt_quantity.value = str(self.quantity)
            self._update_price_display()
            self.main_page.update()

    def _on_confirm_click(self, _) -> None:
        unit = self._get_current_unit_price()
        notes = self.txt_notes.value.strip() if self.txt_notes.value else None
        self.main_page.pop_dialog()
        self.on_add(
            self.product,
            self.selected_size,
            self.selected_crust,
            self.quantity,
            notes,
            unit,
        )
