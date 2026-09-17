"""
Definições visuais, paleta de cores e estilos do FatiaExpress.
"""

import flet as ft
from models.order import OrderStatus


class AppColors:
    # Cores Principais (Tema Pizzaria Moderna)
    PRIMARY = "#D90429"           # Vermelho pizzaria vibrante
    PRIMARY_CONTAINER = "#3B1015"
    SECONDARY = "#F77F00"         # Âmbar dourado
    BACKGROUND = "#121216"        # Fundo escuro elegante
    SURFACE = "#1C1C24"           # Cartões e painéis
    SURFACE_VARIANT = "#282834"   # Elementos interativos secundários
    TEXT_PRIMARY = "#FFFFFF"      # Texto principal
    TEXT_SECONDARY = "#A0A0B0"    # Texto secundário/apoio
    BORDER = "#323242"            # Bordas sutis
    SUCCESS = "#2EC4B6"           # Verde sucesso
    WARNING = "#FF9F1C"           # Alerta
    DANGER = "#E63946"            # Erro/Perigo


def get_status_color(status: OrderStatus) -> str:
    """Retorna a cor correspondente para cada status operacional."""
    colors = {
        OrderStatus.RECEBIDO: "#3A86FF",       # Azul
        OrderStatus.EM_PREPARO: "#FFBE0B",     # Amarelo/Laranja
        OrderStatus.NO_FORNO: "#FB5607",       # Laranja Forno
        OrderStatus.SAIU_ENTREGA: "#8338EC",   # Roxo Delivery
        OrderStatus.ENTREGUE: "#2EC4B6",       # Verde Concluído
        OrderStatus.CANCELADO: "#6C757D",      # Cinza
    }
    return colors.get(status, "#6C757D")


def format_currency(value: float) -> str:
    """Formata valor numérico para padrão monetário brasileiro (R$ 0,00)."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
