"""`preparar_airflow.py` no pisa una carpeta de Airflow que ya existe y no preparó este proyecto, salvo con `--forzar`.

Por qué existe: con el destino por defecto (`airflow-medallon`, hermana del proyecto) se podía escribir encima de la carpeta de otra instalación sin avisar.
Qué NO demuestra: el comportamiento de Docker (se usa uno simulado) ni que la carpeta de otra persona tenga nada en particular: solo que no se toca sin permiso.
"""
import pytest

from tests.test_nombre_compose_y_volumen import DockerFalso, _preparar, pa, proyecto  # noqa: F401


def _ajena(raiz):
    carpeta = raiz.parent / "airflow-medallon"
    carpeta.mkdir()
    (carpeta / "docker-compose.yaml").write_text("# de otra instalacion\n", encoding="utf-8")
    (carpeta / ".env").write_text("POSTGRES_PASSWORD=otra\n", encoding="utf-8")
    return carpeta


def test_una_carpeta_ajena_con_contenido_no_se_toca_y_el_mensaje_dice_como_seguir(proyecto):
    carpeta = _ajena(proyecto)
    antes = {p.name: p.read_bytes() for p in carpeta.iterdir()}
    with pytest.raises(pa.PrepararError) as e:
        _preparar(proyecto)
    assert "--forzar" in str(e.value) and "--destino" in str(e.value) and "no se toca" in str(e.value)
    assert {p.name: p.read_bytes() for p in carpeta.iterdir()} == antes, "no se escribió nada"


def test_con_forzar_se_usa_la_carpeta_ajena(proyecto):
    carpeta = _ajena(proyecto)
    hecho = _preparar(proyecto, forzar=True)
    assert "docker-compose.yaml" in hecho["copiados"] and (carpeta / "dags" / "medallon_etl_dag.py").exists()


def test_una_carpeta_vacia_o_inexistente_y_la_propia_del_proyecto_no_piden_forzar(proyecto):
    (proyecto.parent / "airflow-medallon").mkdir()
    _preparar(proyecto)                       # vacía: se prepara
    _preparar(proyecto)                       # la preparó este proyecto: se vuelve a preparar sin --forzar
    _preparar(proyecto, completar=True)


def test_una_carpeta_preparada_por_otro_proyecto_tampoco_se_pisa(proyecto):
    _preparar(proyecto)
    (proyecto.parent / "airflow-medallon" / ".env").write_text("PROYECTO_NOMBRE=otro proyecto\n", encoding="utf-8")
    with pytest.raises(pa.PrepararError):
        _preparar(proyecto)
