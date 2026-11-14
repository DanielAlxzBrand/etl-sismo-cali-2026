"""Formato de cifras del panel: coma decimal, punto de miles, signo menos «−» y redondeo half-up (igual que los documentos)."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MENOS = "−"
SIN_DATO = "—"


def _decimal(valor):
    """Decimal exacto de la representación en texto del número (evita el error binario: 99,8445 no es 99,84449999)."""
    if valor is None or isinstance(valor, bool):
        return None
    try:
        d = Decimal(repr(valor)) if isinstance(valor, float) else Decimal(str(valor))
    except InvalidOperation:
        return None
    return d if d.is_finite() else None


def _con_miles(texto_entero):
    partes = []
    while len(texto_entero) > 3:
        partes.insert(0, texto_entero[-3:])
        texto_entero = texto_entero[:-3]
    partes.insert(0, texto_entero)
    return ".".join(partes)


def numero(valor, decimales=0, signo=False):
    """Número con miles y decimales; `signo=True` antepone «+» a los positivos. None o no finito: «—»."""
    d = _decimal(valor)
    if d is None:
        return SIN_DATO
    cuant = Decimal(1).scaleb(-decimales)
    redondeado = d.quantize(cuant, rounding=ROUND_HALF_UP)
    negativo = redondeado < 0
    texto = f"{abs(redondeado):f}"
    entero, _, frac = texto.partition(".")
    cuerpo = _con_miles(entero) + ("," + frac if decimales > 0 else "")
    if negativo:
        return MENOS + cuerpo
    return ("+" + cuerpo) if signo and redondeado > 0 else cuerpo


def porcentaje(fraccion, decimales=2):
    """Fracción (0,0662) como porcentaje («6,62 %»); un cero queda «0,00 %» y 1 queda «100,00 %»."""
    d = _decimal(fraccion)
    if d is None:
        return SIN_DATO
    return numero(d * 100, decimales) + " %"


def puntos_porcentuales(diferencia, decimales=2, signo=True):
    """Diferencia de fracciones en puntos porcentuales («+0,49 pp», «−2,36 pp»)."""
    d = _decimal(diferencia)
    if d is None:
        return SIN_DATO
    return numero(d * 100, decimales, signo=signo) + " pp"


def intervalo(inferior, superior, como="porcentaje", decimales=2):
    """Intervalo: «[3,92 %; 8,61 %]» (`porcentaje`) o «[−2,36; +2,55] pp» (`pp`, con signo en los dos extremos); si falta un extremo, «—»."""
    if como == "porcentaje":
        a, b = porcentaje(inferior, decimales), porcentaje(superior, decimales)
        return SIN_DATO if SIN_DATO in (a, b) else f"[{a}; {b}]"
    da, db = _decimal(inferior), _decimal(superior)
    if da is None or db is None:
        return SIN_DATO
    return f"[{numero(da * 100, decimales, signo=True)}; {numero(db * 100, decimales, signo=True)}] pp"


def razon(valor, decimales=3):
    """Razón de tasas con coma decimal («1,084»)."""
    return numero(valor, decimales)
