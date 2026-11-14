"""Colores del panel (desde config.yaml) y relación de contraste WCAG 2.x entre dos colores."""
from src.panel.configuracion import cargar_panel


def colores():
    return dict(cargar_panel()["colores"])


def _canal(c):
    c = c / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _canal(r) + 0.7152 * _canal(g) + 0.0722 * _canal(b)


def contraste(color_a, color_b):
    """Relación de contraste (de 1 a 21) entre dos colores hexadecimales."""
    la, lb = sorted((luminancia(color_a), luminancia(color_b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)
