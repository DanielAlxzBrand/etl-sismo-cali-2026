"""Normalizacion de llaves de JOIN: codigo de barrio = int(COMUNA)*100 + int(BARRIO), como texto."""
import re
import unicodedata


def codigo_barrio(comuna, barrio):
    """Llave del JOIN construcciones <-> estrato (H5); None si COMUNA o BARRIO vienen vacíos o no numéricos."""
    c, b = str(comuna).strip(), str(barrio).strip()
    if not (c.isdigit() and b.isdigit()):
        return None
    return str(int(c) * 100 + int(b))


def codigo_csv(valor):
    """Código único del CSV de estrato (H5); None para filas resumen con '-' (H6)."""
    v = str(valor).strip()
    return str(int(v)) if v.isdigit() else None


def normalize_key(texto):
    """Mayúsculas, sin tildes ni puntuación, espacios colapsados (solo para comparar nombres, H18)."""
    if texto is None or (isinstance(texto, float) and texto != texto):
        return ""
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).upper()
    t = re.sub(r"[^A-Z0-9 ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()
