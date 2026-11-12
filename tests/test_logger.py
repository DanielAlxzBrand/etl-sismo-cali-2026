"""El registro enmascara secretos y escribe en el archivo diario."""
import logging

from src.logger import EnmascararSecretos, get_logger


def _mensaje(texto):
    r = logging.LogRecord("etl.prueba", logging.INFO, __file__, 1, texto, (), None)
    EnmascararSecretos().filter(r)
    return r.getMessage()


def test_enmascara_cabeceras_y_tokens():
    assert "abc123" not in _mensaje("X-App-Token: abc123")
    assert "abc123" not in _mensaje("token=abc123 y password=abc123")
    assert "xyz" not in _mensaje("Authorization: Bearer xyz")
    assert _mensaje("filas=5146") == "filas=5146"


def test_get_logger_devuelve_hijo_de_etl():
    assert get_logger("src.transform.integrate").name == "etl.integrate"
