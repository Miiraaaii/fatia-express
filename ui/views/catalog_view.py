"""
Tela de Cardápio e Novo Pedido.
"""

from typing import Optional, List
import flet as ft
from models.product import Product, Category, PizzaSize, CrustOption
from services.catalog_service import CatalogService
from services.order_service import OrderService
from ui.components.product_card import ProductCard
from ui.components.product_dialog import ProductDialog
from ui.components.cart_view import CartView
from ui.theme import AppColors


class CatalogView(ft.Container):
    def __init__(
        self,
        catalog_service: CatalogService,
        order_service: OrderService,
        on_order_created_callback,
    ):
        self.catalog_service = catalog_service
        self.order_service = order_service
        self.on_order_created_callback = on_order_created_callback

        self.categories: List[Category] = self.catalog_service.get_categories()
        self.pizza_sizes: List[PizzaSize] = self.catalog_service.get_pizza_sizes()
        self.crust_options: List[CrustOption] = self.catalog_service.get_crust_options()

        self.selected_category_id: Optional[int] = None
        self.search_query: str = ""

        # Controles
        self.products_wrap = ft.Row(
            wrap=True,
            spacing=14,
            run_spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.txt_search = ft.TextField(
            hint_text="Buscar pizza ou bebida...",
            prefix_icon=ft.Icons.SEARCH,
            border_color=AppColors.BORDER,
            focused_border_color=AppColors.SECONDARY,
            expand=True,
            on_change=self._on_search_change,
        )

        self.category_chips_row = ft.Row(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        # Painel do Carrinho
        self.cart_view = CartView(
            order_service=self.order_service,
            on_order_created=self._handle_order_created,
            on_cart_updated=self._handle_cart_updated,
        )

        # Montar Chips de Categoria
        self._build_category_chips()
        self._load_products()

        super().__init__(
            content=ft.Row(
                spacing=16,
                expand=True,
                cross_axis_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    # Área de Produtos (Cardápio)
                    ft.Column(
                        expand=True,
                        spacing=14,
                        controls=[
                            # Barra Superior de Pesquisa e Filtros
                            ft.Row(
                                spacing=12,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    self.txt_search,
                                ],
                            ),
                            self.category_chips_row,
                            # Grid de Produtos
                            ft.Container(
                                content=self.products_wrap,
                                expand=True,
                            ),
                        ],
                    ),

                    # Painel do Carrinho Lateral
                    self.cart_view,
                ],
            ),
            expand=True,
            padding=16,
        )

    def _build_category_chips(self):
        self.category_chips_row.controls.clear()

        # Botão "Todas"
        is_all_selected = self.selected_category_id is None
        self.category_chips_row.controls.append(
            ft.FilledButton(
                text="Todos os Itens",
                icon=ft.Icons.RESTAURANT_MENU,
                style=ft.ButtonStyle(
                    bgcolor=AppColors.PRIMARY if is_all_selected else AppColors.SURFACE_VARIANT,
                    color=AppColors.TEXT_PRIMARY,
                    shape=ft.RoundedRectangleBorder(radius=20),
                ),
                on_click=lambda _: self._select_category(None),
            )
        )

        for cat in self.categories:
            is_sel = self.selected_category_id == cat.id
            self.category_chips_row.controls.append(
                ft.FilledButton(
                    text=cat.name,
                    style=ft.ButtonStyle(
                        bgcolor=AppColors.PRIMARY if is_sel else AppColors.SURFACE_VARIANT,
                        color=AppColors.TEXT_PRIMARY,
                        shape=ft.RoundedRectangleBorder(radius=20),
                    ),
                    on_click=lambda _, cid=cat.id: self._select_category(cid),
                )
            )

    def _select_category(self, category_id: Optional[int]):
        self.selected_category_id = category_id
        self._build_category_chips()
        self._load_products()
        if self.page:
            self.page.update()

    def _on_search_change(self, e):
        self.search_query = e.control.value.strip()
        self._load_products()
        if self.page:
            self.page.update()

    def _load_products(self):
        self.products_wrap.controls.clear()
        products = self.catalog_service.get_products(
            category_id=self.selected_category_id,
            search=self.search_query if self.search_query else None,
        )

        if not products:
            self.products_wrap.controls.append(
                ft.Container(
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.SEARCH_OFF, size=48, color=AppColors.TEXT_SECONDARY),
                            ft.Text("Nenhum produto encontrado com este filtro.", size=14, color=AppColors.TEXT_SECONDARY),
                        ],
                    ),
                    expand=True,
                    alignment=ft.alignment.center,
                    height=300,
                )
            )
            return

        for prod in products:
            self.products_wrap.controls.append(
                ProductCard(product=prod, on_select=self._open_product_modal)
            )

    def _open_product_modal(self, product: Product):
        dialog = ProductDialog(
            page=self.page,
            product=product,
            sizes=self.pizza_sizes,
            crusts=self.crust_options,
            on_add=self._handle_add_to_cart,
        )
        self.page.show_dialog(dialog)
        self.page.update()

    def _handle_add_to_cart(
        self,
        product: Product,
        size: Optional[PizzaSize],
        crust: Optional[CrustOption],
        quantity: int,
        notes: Optional[str],
        unit_price: float,
    ):
        self.order_service.add_to_cart(
            product_id=product.id,
            product_name=product.name,
            unit_price=unit_price,
            quantity=quantity,
            size_name=size.name if size else None,
            crust_name=crust.name if crust else None,
            notes=notes,
        )
        self.cart_view.refresh_cart_display()
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(f"🍕 {quantity}x {product.name} adicionado(s) ao pedido!"),
                bgcolor=AppColors.PRIMARY,
            )
        )
        self.page.update()

    def _handle_cart_updated(self):
        if self.page:
            self.page.update()

    def _handle_order_created(self, order_id: int):
        self.on_order_created_callback(order_id)
