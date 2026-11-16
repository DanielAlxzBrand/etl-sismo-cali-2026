"""La trazabilidad del checklist (`docs/checklist/trazabilidad.csv`) es la única fuente y coincide con `estado_checklist.md`, con el manifiesto de evidencias y con las pruebas que existen.

Por qué existe: la tabla ítem → requisito → archivos → pruebas → evidencias → comando podía desactualizarse en silencio (22 archivos de prueba y 18 evidencias no estaban asociados a ningún ítem, y
dos documentos contaban distinto los estados). Ahora cada ítem tiene su fila, cada archivo de prueba y cada número de evidencia aparece en alguna fila (o en el grupo `G` de guardianes de coherencia),
el requisito y el estado salen de `estado_checklist.md`, y `trazabilidad.md` se genera desde el CSV. `scripts/validar_checklist.py --item N` muestra y comprueba una fila.
Qué NO demuestra: que cada prueba asociada pruebe de verdad el requisito (eso lo juzgan las fichas de `guia_de_evidencias.md`) ni que los ítems pendientes se cumplan: solo que lo que el repositorio
afirma tener existe y que lo que falta se declara.
"""
import csv
import importlib.util
import io
import re
import subprocess
import sys

from src.common import ROOT

_spec = importlib.util.spec_from_file_location("validar_checklist", ROOT / "scripts" / "validar_checklist.py")
vc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vc)

ITEMS = [f"{s}.{i}" for s, n in zip(range(1, 8), (5, 3, 3, 3, 6, 5, 5)) for i in range(1, n + 1)]
CON_RESPALDO = ("Cumple", "Cumple con matiz")
PREFIJO_PYTEST = "python -m pytest -q -p no:cacheprovider "
# Comandos que no son pytest y no escriben nada en el repositorio (los demás generan documentos o necesitan MySQL, y no sirven como comando de comprobación).
COMANDOS_DE_SOLO_LECTURA = {"python scripts/escanear_secretos.py", "python scripts/validacion/verificar_regresiones.py"}


def _texto_estado():
    return vc.ESTADO.read_text(encoding="utf-8")


def _archivos_de_prueba():
    return {f"tests/{p.name}" for p in (ROOT / "tests").glob("test_*.py")}


def problemas_del_csv(filas, texto_estado, manifiesto, archivos_de_prueba):
    """Diferencias entre la trazabilidad y el resto del repositorio (lista vacía si todo coincide)."""
    errores = []
    ids = [f["item"] for f in filas]
    if sorted(i for i in ids if i != vc.GRUPO) != sorted(ITEMS) or ids.count(vc.GRUPO) != 1:
        errores.append(f"las filas no son los 30 ítems y un grupo G: {ids}")
    estados = vc.estados_del_documento(texto_estado)
    for f in filas:
        item = f["item"]
        if item != vc.GRUPO and item in estados:
            requisito, estado = estados[item]
            if f["requisito"] != requisito:
                errores.append(f"{item}: el requisito no es el literal de estado_checklist.md")
            if f["estado"] != estado:
                errores.append(f"{item}: el estado {f['estado']!r} no coincide con el vigente {estado!r}")
        errores += [f"{item}: {p}" for p in vc.comprobar_fila(f, manifiesto)]
        comando = f["comando"]
        if comando not in COMANDOS_DE_SOLO_LECTURA:
            if not comando.startswith(PREFIJO_PYTEST):
                errores.append(f"{item}: el comando no es un pytest ni uno de solo lectura: {comando!r}")
            elif set(comando[len(PREFIJO_PYTEST):].split()) != set(vc.lista(f["pruebas"])):
                errores.append(f"{item}: el comando no corre exactamente las pruebas del ítem")
        if f["estado"] in CON_RESPALDO and not (vc.lista(f["pruebas"]) and vc.lista(f["archivos"])):
            errores.append(f"{item}: afirma «{f['estado']}» sin pruebas o sin archivos")
        if f["estado"] == "En curso" and not vc.lista(f["archivos"]):
            errores.append(f"{item}: «En curso» sin ningún archivo que lo respalde")
        if f["estado"] == "No iniciado" and (vc.lista(f["archivos"]) or f["evidencias"]):
            errores.append(f"{item}: «No iniciado» con archivos o evidencias")
        if f["estado"] == "Pendiente (hecho externo)" and f["tipo"] != "externa":
            errores.append(f"{item}: pendiente por un hecho externo debe tener comprobación «externa»")
    usadas = {p.split("::")[0] for f in filas for p in vc.lista(f["pruebas"])}
    errores += [f"archivo de prueba sin ítem ni grupo G: {a}" for a in sorted(archivos_de_prueba - usadas)]
    evidencias = {n for f in filas for n in vc.expandir_evidencias(f["evidencias"])}
    errores += [f"EV-{n:03d} sin ítem ni grupo G" for n in sorted(set(manifiesto) - evidencias)]
    return errores


def test_la_trazabilidad_coincide_con_el_estado_el_manifiesto_y_las_pruebas():
    assert problemas_del_csv(vc.leer_csv(), _texto_estado(), vc.filas_del_manifiesto(), _archivos_de_prueba()) == []


def test_la_tabla_markdown_esta_generada_desde_el_csv():
    assert vc.MD.read_text(encoding="utf-8") == vc.a_markdown(vc.leer_csv())


def test_el_grupo_de_guardianes_lista_los_guardianes_declarados():
    g = next(f for f in vc.leer_csv() if f["item"] == vc.GRUPO)
    esperados = {"tests/test_cifras_de_estado.py", "tests/test_criterio_de_texto.py", "tests/test_decisiones.py", "tests/test_igualdad_de_codigo.py", "tests/test_scripts_de_evidencia.py", "tests/test_trazabilidad.py"}
    assert set(vc.lista(g["pruebas"])) == esperados
    assert vc.expandir_evidencias(g["evidencias"]) == [91, 92, 93, 94, 95]


def _copia(filas):
    return [dict(f) for f in filas]


def _fila(filas, item):
    return next(f for f in filas if f["item"] == item)


def test_negativas_de_la_trazabilidad():
    filas, texto, man, tests = vc.leer_csv(), _texto_estado(), vc.filas_del_manifiesto(), _archivos_de_prueba()
    assert problemas_del_csv(filas, texto, man, tests) == []
    c = _copia(filas)
    _fila(c, "5.4")["estado"] = "Cumple"
    assert problemas_del_csv(c, texto, man, tests), "un estado que no coincide con el documento"
    c = _copia(filas)
    _fila(c, "4.2")["pruebas"] += ";tests/test_que_no_existe.py"
    assert problemas_del_csv(c, texto, man, tests), "una prueba inexistente"
    c = _copia(filas)
    _fila(c, "4.2")["pruebas"] += ";tests/test_carga_relacional.py::test_que_no_existe"
    assert problemas_del_csv(c, texto, man, tests), "una función inexistente"
    c = _copia(filas)
    _fila(c, "2.1")["evidencias"] += ";EV-053"
    assert problemas_del_csv(c, texto, man, tests), "una evidencia que el manifiesto asocia a otro ítem"
    c = _copia(filas)
    _fila(c, "2.1")["evidencias"] += ";EV-999"
    assert problemas_del_csv(c, texto, man, tests), "una evidencia que no está en el manifiesto"
    c = _copia(filas)
    _fila(c, vc.GRUPO)["pruebas"] = ";".join(vc.lista(_fila(c, vc.GRUPO)["pruebas"])[1:])
    assert problemas_del_csv(c, texto, man, tests), "un archivo de prueba que queda sin ítem"
    c = _copia(filas)
    _fila(c, vc.GRUPO)["evidencias"] = "EV-091..EV-093"
    assert problemas_del_csv(c, texto, man, tests), "una evidencia que queda sin ítem"
    c = _copia(filas)
    _fila(c, "7.5")["archivos"] = "README.md"
    assert problemas_del_csv(c, texto, man, tests), "«No iniciado» con archivos"
    c = _copia(filas)
    _fila(c, "6.1")["tipo"] = "automática"
    assert problemas_del_csv(c, texto, man, tests), "un pendiente por hecho externo que se declara automático"
    c = _copia(filas)
    _fila(c, "2.1")["pruebas"] = ""
    assert problemas_del_csv(c, texto, man, tests), "«Cumple» sin pruebas"
    c = _copia(filas)
    _fila(c, "1.1")["requisito"] = "Otro requisito"
    assert problemas_del_csv(c, texto, man, tests), "un requisito que no es el literal"
    c = _copia(filas)
    _fila(c, "7.2")["comando"] = "python scripts/make_dist.py"
    assert problemas_del_csv(c, texto, man, tests), "un comando que escribe archivos en lugar de correr las pruebas del ítem"
    c = _copia(filas)
    _fila(c, "5.4")["comando"] = PREFIJO_PYTEST + "tests/test_dag_estatico.py"
    assert problemas_del_csv(c, texto, man, tests), "un comando que no corre todas las pruebas del ítem"
    assert problemas_del_csv(filas[:-1], texto, man, tests), "falta el grupo G"
    assert problemas_del_csv(filas + [dict(filas[0])], texto, man, tests), "un ítem repetido"
    assert vc.a_markdown(c) != vc.MD.read_text(encoding="utf-8"), "la tabla generada cambia si el CSV cambia"


def test_los_rangos_de_evidencias_se_expanden_y_se_comprimen_sin_perder_numeros():
    for numeros in ([1, 2], [1, 2, 3], [5], [1, 3, 4, 5, 9, 10], list(range(66, 70)) + [71]):
        assert vc.expandir_evidencias(vc.comprimir_evidencias(numeros)) == sorted(numeros)
    assert vc.expandir_evidencias("EV-066..EV-068;EV-070") == [66, 67, 68, 70]
    for mala in ("EV-1x", "066", "EV-066..068"):
        try:
            vc.expandir_evidencias(mala)
        except ValueError:
            continue
        raise AssertionError(f"debía rechazar {mala!r}")


def _correr(*args):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "validar_checklist.py"), *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout


def test_el_script_muestra_y_comprueba_un_item_y_rechaza_uno_inexistente():
    codigo, salida = _correr("--item", "4.2")
    assert codigo == 0 and "Resultado: OK" in salida and "Estado vigente: Cumple" in salida and "tests/test_carga_relacional.py" in salida and "EV-028" in salida
    codigo, salida = _correr("--item", "7.5")
    assert codigo == 0 and "ninguno" in salida and "No iniciado" in salida
    assert _correr("--item", "9.9")[0] == 2
    codigo, salida = _correr("--todos")
    assert codigo == 0 and "31 de 31 filas sin problemas" in salida


def test_el_csv_se_lee_y_se_escribe_sin_cambiar_su_contenido():
    texto = vc.CSV.read_text(encoding="utf-8")
    filas = list(csv.DictReader(io.StringIO(texto)))
    salida = io.StringIO()
    w = csv.DictWriter(salida, fieldnames=vc.COLUMNAS, lineterminator="\n")
    w.writeheader()
    w.writerows(filas)
    assert salida.getvalue() == texto and re.match(r"item,requisito,estado", texto)
