"""La cabecera de docs/DECISIONES.md y el índice de docs/README.md coinciden con la última decisión registrada."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DECISIONES = (RAIZ / "docs" / "DECISIONES.md").read_text(encoding="utf-8")
INDICE = (RAIZ / "docs" / "README.md").read_text(encoding="utf-8")


def _ultima(texto):
    return max(int(n) for n in re.findall(r"^\*\*D(\d+) ·", texto, re.M))


def test_la_cabecera_nombra_la_siguiente_decision_a_la_ultima_registrada():
    ultima = _ultima(DECISIONES)
    m = re.search(r"Las decisiones nuevas continúan desde D(\d+)", DECISIONES)
    assert m is not None
    assert int(m[1]) == ultima + 1


def test_el_indice_de_docs_nombra_el_mismo_rango_que_las_decisiones():
    ultima = _ultima(DECISIONES)
    m = re.search(r"\(D1 a D(\d+); las nuevas continúan desde D(\d+)\)", INDICE)
    assert m is not None
    assert (int(m[1]), int(m[2])) == (ultima, ultima + 1)


def test_los_identificadores_de_decision_no_se_repiten_ni_saltan_numeros():
    ids = [int(n) for n in re.findall(r"^\*\*D(\d+) ·", DECISIONES, re.M)]
    assert len(ids) == len(set(ids))
    assert set(range(11, max(ids) + 1)) <= set(ids)


def test_la_cabecera_detecta_un_desajuste():
    ultima = _ultima(DECISIONES)
    alterado = DECISIONES.replace(f"continúan desde D{ultima + 1}", f"continúan desde D{ultima}", 1)
    m = re.search(r"Las decisiones nuevas continúan desde D(\d+)", alterado)
    assert int(m[1]) != _ultima(alterado) + 1
