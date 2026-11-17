"""Estrategia (docs/estrategia) y estado del checklist: existencia, rastros de elaboración, cifras, rúbrica R1, avisos de honestidad,
criterios del MVP (forma general y tabla real, D81) y tabla de los 30 ítems, con pruebas negativas sobre copias alteradas de las tablas."""
import datetime
import importlib.util
import json
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd
import pytest

from src.common import ROOT

_spec_dist = importlib.util.spec_from_file_location("make_dist_estrategia", ROOT / "scripts" / "make_dist.py")
make_dist = importlib.util.module_from_spec(_spec_dist)
_spec_dist.loader.exec_module(make_dist)

CARPETA = ROOT / "docs" / "estrategia"
ESTADO = ROOT / "docs" / "checklist" / "estado_checklist.md"
DOCS = ["01_data_thinking.md", "02_stakeholders.md", "03_objetivo_alcance_okr_kpi.md", "04_canvas_data_innovation_board.md", "05_mvp_criterios_aceptacion.md"]
ARCHIVOS = ["indice.md"] + DOCS
IMAGENES = [CARPETA / "img" / "matriz_poder_interes.png", CARPETA / "img" / "canvas_modelo_negocio.png"]
# Rastros de elaboración (las cadenas se parten para que este archivo no se detecte a sí mismo). La sigla de IA como concepto técnico está permitida.
RASTROS = ["Cla" + "ude", "Anthro" + "pic", "Chat" + "GPT", "Co" + "pilot", "Gem" + "ini", "Open" + "AI", "pro" + "mpt",
           "con ayuda de " + "IA", "asistente de " + "IA", "generado con " + "IA", "herramienta de " + "IA", "elaborado con " + "IA"]
OTROS = ["por validar por el " + "equipo", "[COMPLE" + "TAR", "TO" + "DO"]
# Lista cerrada de componentes (único lugar de las pruebas donde se define)
COMPONENTES = ["Base y orden", "Estrategia", "API, fuentes y credenciales", "Carga relacional", "Pruebas y orquestación", "Panel", "Usuarios, UX y finanzas",
               "Documentación y demostración", "Cierre y paquete"]
ESTADOS_REGLA = ["Cumple", "Cumple con matiz", "En curso", "Pendiente (hecho externo)", "No iniciado", "N/A justificado", "No cumple"]
ESTADOS_ACTUALES = ESTADOS_REGLA + ["Cumple con documentación", "Requiere desarrollo", "Requiere hecho externo"]
ETIQUETA_DE_FASE = re.compile(r"\bF[0-" + r"8]\b")  # las etiquetas de fase ya no existen en el repositorio
SUFIJOS = (".md", ".py", ".txt", ".yaml", ".yml", ".ini", ".ipynb", ".csv", ".json", ".jsonl")


def _texto(nombre):
    return (CARPETA / nombre).read_text(encoding="utf-8")


def _miles(n):
    return f"{int(n):,}".replace(",", ".")


def _pc(v, d=3):
    q = (Decimal(repr(float(v))) * 100).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return str(q).replace(".", ",") + " %"


def test_existen_los_documentos_el_indice_y_las_dos_imagenes():
    assert [n for n in ARCHIVOS if not (CARPETA / n).is_file()] == []
    assert [str(p) for p in IMAGENES if not p.is_file() or p.stat().st_size < 10_000] == []


def test_cada_documento_tiene_alcance_y_limites_y_preguntas_frecuentes():
    for n in DOCS:
        t = _texto(n)
        assert "## Cómo lo defendemos" not in t, n
        assert "## Alcance y límites" in t and "## Preguntas frecuentes" in t, n
        alcance = t.split("## Alcance y límites")[1].split("## Preguntas frecuentes")[0]
        for campo in ("Qué afirmamos", "Con qué evidencia", "Qué NO afirmamos"):
            assert f"**{campo}:**" in alcance, (n, campo)
        assert re.search(r"^- \*\*«.+»\*\* \S", t.split("## Preguntas frecuentes")[1], re.M), n


def test_sin_rastros_de_elaboracion_ni_marcas_pendientes_en_estrategia():
    for n in ARCHIVOS:
        t = _texto(n)
        for p in RASTROS + OTROS:
            assert p not in t, (n, p)


def test_sin_rastros_de_elaboracion_en_el_resto_del_repo():
    """Recorre los archivos de texto versionables (sin .venv, .git, data/, dist/ ni el documento aislado de la raíz, que es del equipo)."""
    saltar = {".venv", ".git", "data", "dist", "logs", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
    hallazgos = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if not p.is_file() or rel.parts[0] in saltar or any(x in saltar for x in rel.parts) or p.suffix not in SUFIJOS or make_dist.es_documento_aislado(rel.as_posix()):
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if rel.as_posix() == "README.md":
            from tests.test_criterio_de_texto import sin_la_linea_autorizada   # D105: la única línea que remite a la declaración, exacta y una vez
            t = sin_la_linea_autorizada("README.md", t)
        hallazgos += [(rel.as_posix(), x) for x in RASTROS if x in t]
    assert hallazgos == []


def test_cifras_de_1_3_y_1_5_coinciden_con_las_salidas():
    rep = json.loads((ROOT / "data/silver/quality_report.json").read_text(encoding="utf-8"))
    gold = pd.read_csv(ROOT / "data/gold/gold_final.csv")
    kpis = pd.read_csv(ROOT / "data/gold/kpis_gold.csv")
    cobertura, filas, n_kpis = _pc(rep["cobertura_llave"]["pct"]), _miles(len(gold)), len(kpis)
    for n in ("03_objetivo_alcance_okr_kpi.md", "05_mvp_criterios_aceptacion.md"):
        t = _texto(n)
        assert cobertura in t and f"{filas} filas" in t, n
    assert f"{n_kpis} filas con 6 indicadores" in _texto("03_objetivo_alcance_okr_kpi.md")
    assert sorted(kpis.kpi_id.unique()) == ["K1", "K2", "K3", "K4", "K5", "K6"]
    con = gold[~gold.sin_datos]
    assert f"{_miles(len(con))}" in _texto("01_data_thinking.md") and f"{_miles(len(gold))} construcciones" in _texto("03_objetivo_alcance_okr_kpi.md")


def test_rubrica_r1_y_matriz_poder_interes_son_consistentes():
    t = _texto("02_stakeholders.md")
    assert "Rúbrica R1" in t or "rúbrica R1" in t
    umbral = int(re.search(r"mayor o igual que (\d+)", t).group(1))
    filas = re.findall(r"^\| (\d+) \| ([^|]+) \| ([0-3]) \| ([0-3]) \| ([0-3]) \| ([0-3]) \| (\d) \| (\d) \| ([^|]+) \|$", t, re.M)
    assert len(filas) >= 10
    for _, nombre, c1, c2, c3, c4, poder, interes, cuadrante in filas:
        p, i = int(c1) + int(c2), int(c3) + int(c4)
        assert (int(poder), int(interes)) == (p, i), nombre
        esperado = ("Gestionar de cerca" if p >= umbral and i >= umbral else "Mantener satisfechos" if p >= umbral
                    else "Mantener informados" if i >= umbral else "Monitorear")
        assert cuadrante.strip() == esperado, nombre


def test_1_4_declara_hipotesis_sin_validar_y_no_estimado():
    t = _texto("04_canvas_data_innovation_board.md")
    assert "hipótesis sin validar" in t and "no estimado" in t and "Qué no afirmamos" in t
    assert len(re.findall(r"^\| H\d+ \|", t, re.M)) >= 8


def test_1_2_declara_que_no_hubo_contactos():
    t = _texto("02_stakeholders.md")
    assert "## 6. Contactos realizados" in t and "**Ninguno:**" in t
    assert "No hubo contacto ni validación con stakeholders" in t


FILA_AC = re.compile(r"^\| (AC\d+) \| (FE\d) \|.*\| \*\*([^*]+)\*\* \| ([^|]+) \| ([^|]+) \|$", re.M)


def revisar_criterios(texto):
    """Errores de la tabla de criterios del MVP (lista vacía si todo está en regla)."""
    errores = []
    filas = FILA_AC.findall(texto)
    ids = [f[0] for f in filas]
    if len(filas) < 24:
        errores.append(f"menos de 24 criterios ({len(filas)})")
    if len(ids) != len(set(ids)):
        errores.append("criterios repetidos")
    ejecutados = pendientes = 0
    for _id, _fe, estado, componente, fecha in filas:
        componente, fecha = componente.strip(), fecha.strip()
        if estado.startswith("no verificado aún"):
            pendientes += 1
            nombre = estado.split(":", 1)[1].strip() if ":" in estado else ""
            if nombre not in COMPONENTES:
                errores.append(f"{_id}: componente pendiente no válido ({nombre!r})")
            if componente != nombre:
                errores.append(f"{_id}: el componente de verificación no coincide con el del estado")
            if fecha != "—":
                errores.append(f"{_id}: un criterio pendiente no lleva fecha")
        elif estado in ("cumple", "no cumple"):
            ejecutados += 1
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha) is None:
                errores.append(f"{_id}: sin fecha de verificación")
            if componente not in COMPONENTES:
                errores.append(f"{_id}: componente de verificación no válido ({componente!r})")
        else:
            errores.append(f"{_id}: estado desconocido ({estado!r})")
    m = re.search(r"(\d+) de (\d+) criterios cumplen hoy; (\d+) están «no verificado aún»", texto)
    if m is None:
        errores.append("falta el encabezado con los conteos")
    elif (int(m[1]), int(m[2]), int(m[3])) != (sum(1 for f in filas if f[2] == "cumple"), len(filas), pendientes):
        errores.append(f"los conteos del encabezado no coinciden con la tabla ({m.groups()} frente a {ejecutados + pendientes})")
    return errores


FILA_ITEM = re.compile(r"^\| (\d\.\d) \| «.*?» \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| .*\|$", re.M)


def revisar_items(texto):
    """Errores de la tabla de los 30 ítems del checklist."""
    errores = []
    filas = FILA_ITEM.findall(texto)
    ids = [f[0] for f in filas]
    esperados = [f"{s}.{i}" for s, n in zip(range(1, 8), (5, 3, 3, 3, 6, 5, 5)) for i in range(1, n + 1)]
    if sorted(ids) != sorted(esperados):
        errores.append(f"los ítems no son exactamente los 30 esperados (faltan {sorted(set(esperados) - set(ids))}; sobran {sorted(set(ids) - set(esperados))})")
    if len(ids) != len(set(ids)):
        errores.append(f"ítems repetidos: {sorted({i for i in ids if ids.count(i) > 1})}")
    for _id, actual, cierre, evidencia, objetivo in filas:
        if actual.strip() not in ESTADOS_ACTUALES:
            errores.append(f"{_id}: estado actual no permitido ({actual.strip()!r})")
        if objetivo.strip() not in ESTADOS_REGLA:
            errores.append(f"{_id}: estado vigente no permitido ({objetivo.strip()!r})")
        if cierre.strip() not in COMPONENTES:
            errores.append(f"{_id}: componente de cierre no válido ({cierre.strip()!r})")
        comps = [c.strip() for c in re.split(r",\s+(?=(?:" + "|".join(re.escape(c) for c in COMPONENTES) + "))", evidencia.strip())]
        if not comps or any(c not in COMPONENTES for c in comps):
            errores.append(f"{_id}: componente de evidencia no válido ({evidencia.strip()!r})")
    return errores


def test_1_5_tiene_al_menos_24_criterios_y_cada_estado_es_coherente():
    assert revisar_criterios(_texto("05_mvp_criterios_aceptacion.md")) == []


def test_los_30_items_del_checklist_estan_completos_y_con_componentes_de_la_lista():
    assert revisar_items(ESTADO.read_text(encoding="utf-8")) == []


def _copia(tmp_path, texto, reemplazos):
    """Copia alterada de una tabla en una carpeta temporal; devuelve el texto leído de ella."""
    for a, b in reemplazos:
        assert a in texto, a
        texto = texto.replace(a, b, 1)
    destino = tmp_path / "copia.md"
    destino.write_text(texto, encoding="utf-8")
    return destino.read_text(encoding="utf-8")


def _con_un_criterio_pendiente(t):
    """Si todos los criterios ya cumplen, devuelve una copia en memoria con un criterio pendiente (y el encabezado ajustado) para poder alterar esa forma de fila."""
    if re.search(r"\*\*no verificado aún: ([^*]+)\*\* \| ([^|]+) \| — \|", t):
        return t
    filas = FILA_AC.findall(t)
    ultimo = filas[-1]
    fila = re.search(rf"^\| {ultimo[0]} \|.*$", t, re.M).group(0)
    pendiente = fila.replace(f"**cumple** | {ultimo[3].strip()} | {ultimo[4].strip()} |", "**no verificado aún: Panel** | Panel | — |")
    assert pendiente != fila
    encabezado = re.search(r"(\d+) de (\d+) criterios cumplen hoy; (\d+) están «no verificado aún»", t)
    nuevo = f"{int(encabezado[1]) - 1} de {encabezado[2]} criterios cumplen hoy; {int(encabezado[3]) + 1} están «no verificado aún»"
    return t.replace(fila, pendiente, 1).replace(encabezado.group(0), nuevo, 1)


def test_negativas_de_los_criterios_del_mvp(tmp_path):
    original = _texto("05_mvp_criterios_aceptacion.md")
    t = _con_un_criterio_pendiente(original)
    assert revisar_criterios(t) == []      # la copia con un pendiente es válida: las alteraciones parten de una tabla correcta
    pendiente = re.search(r"\*\*no verificado aún: ([^*]+)\*\* \| ([^|]+) \| — \|", t)
    cumple = re.search(r"\*\*cumple\*\* \| [^|]+ \| (\d{4}-\d{2}-\d{2}) \|", t)
    assert pendiente and cumple
    comp = pendiente.group(1)
    encabezado = re.search(r"(\d+) de (\d+) criterios cumplen hoy", t)
    alteraciones = {
        "componente vacío": [(f"**no verificado aún: {comp}** | {comp} | —", "**no verificado aún: ** |  | —")],
        "componente inventado": [(f"**no verificado aún: {comp}** | {comp} | —", "**no verificado aún: Fase uno** | Fase uno | —")],
        "componente por definir": [(f"**no verificado aún: {comp}** | {comp} | —", "**no verificado aún: por definir** | por definir | —")],
        "criterio pendiente con guion": [(f"**no verificado aún: {comp}** | {comp} | —", "**no verificado aún: —** | — | —")],
        "criterio cumple sin fecha": [(cumple.group(0), cumple.group(0).replace(cumple.group(1), "—"))],
        "conteo que no coincide": [(encabezado.group(0), f"{int(encabezado[1]) + 1} de {encabezado[2]} criterios cumplen hoy")],
    }
    for nombre, cambios in alteraciones.items():
        assert revisar_criterios(_copia(tmp_path, t, cambios)), nombre
    primera = re.search(r"^\| AC01 \|.*$", t, re.M).group(0)
    assert revisar_criterios(_copia(tmp_path, t, [(primera, primera + "\n" + primera)])), "criterio repetido"
    assert revisar_criterios("\n".join(l for l in t.split("\n") if not re.match(r"^\| AC(0[1-9]|1[0-9]) ", l))), "menos de 24 criterios"


def test_negativas_de_los_30_items(tmp_path):
    t = ESTADO.read_text(encoding="utf-8")
    fila = re.search(r"^\| 1\.1 \| «.*$", t, re.M).group(0)
    otra = re.search(r"^\| 2\.1 \| «.*$", t, re.M).group(0)
    campos = fila.split(" | ")
    alteraciones = {
        "ítem repetido": [(fila, fila + "\n" + fila)],
        "ítem ausente": [(otra, "")],
        "componente de cierre vacío": [(fila, fila.replace(f"| {campos[3]} |", "|  |", 1))],
        "componente de cierre inventado": [(fila, fila.replace(f"| {campos[3]} |", "| Fase uno |", 1))],
        "componente de evidencia inventado": [(fila, fila.replace(f"| {campos[4]} |", "| Fase uno |", 1))],
        "estado vigente desconocido": [(fila, fila.replace(f"| {campos[5]} |", "| Casi cumple |", 1))],
        "estado actual desconocido": [(fila, fila.replace(f"| {campos[2]} |", "| Quizá |", 1))],
    }
    for nombre, cambios in alteraciones.items():
        assert revisar_items(_copia(tmp_path, t, cambios)), nombre


def _script_de_conteo():
    espec = importlib.util.spec_from_file_location("contar_estados_checklist", ROOT / "scripts" / "contar_estados_checklist.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def test_el_conteo_de_estados_lo_calcula_el_script_y_coincide_con_el_documento():
    contar = _script_de_conteo()
    texto = ESTADO.read_text(encoding="utf-8")
    assert contar.revisar(texto) == []
    assert sum(contar.contar(texto).values()) == 30


def test_negativas_del_conteo_de_estados(tmp_path):
    contar = _script_de_conteo()
    t = ESTADO.read_text(encoding="utf-8")
    linea = contar.LINEA_CONTEO.search(t).group(0)
    assert contar.revisar(_copia(tmp_path, t, [(linea, "Conteo por estado vigente: Cumple con matiz: 8, Cumple: 17, Pendiente (hecho externo): 5.")]))
    assert contar.revisar(_copia(tmp_path, t, [(linea, "")]))
    assert contar.revisar(_copia(tmp_path, t, [(linea, linea + "\n" + linea)]))
    otra = re.search(r"^\| 7\.5 \| «.*$", t, re.M).group(0)
    assert contar.revisar(_copia(tmp_path, t, [(otra, _con_estado_vigente(otra, "Cumple"))])), "un estado cambia y el conteo no"


def _con_estado_vigente(fila, nuevo):
    campos = fila.split(" | ")
    campos[5] = nuevo
    return " | ".join(campos)


def _estado_de(texto, item):
    return re.search(rf"^\| {re.escape(item)} \| «.*?» \| [^|]+ \| [^|]+ \| [^|]+ \| ([^|]+) \|", texto, re.M).group(1).strip()


def estados_que_superan_su_evidencia(texto, readme, hay_guion_de_demostracion):
    """Un estado nunca supera su evidencia (D96): 7.2 no es «Cumple» sin diagrama de arquitectura y sección de primera vez en el README,
    y 7.5 no pasa de «No iniciado» sin un guion de demostración en `docs/`."""
    errores = []
    tiene_diagrama = re.search(r"!\[[^\]]*[Aa]rquitectura[^\]]*\]\(", readme) is not None
    tiene_primera_vez = re.search(r"^#+ .*[Pp]rimera vez", readme, re.M) is not None
    if _estado_de(texto, "7.2") == "Cumple" and not (tiene_diagrama and tiene_primera_vez):
        errores.append("7.2 figura «Cumple» y el README no tiene el diagrama de arquitectura y la sección de primera vez")
    if _estado_de(texto, "7.5") != "No iniciado" and not hay_guion_de_demostracion:
        errores.append("7.5 pasa de «No iniciado» y no existe un guion de demostración en docs/")
    return errores


def _hay_guion_de_demostracion():
    return any("demo" in p.name.lower() for p in (ROOT / "docs").rglob("*.md") if "evidencias" not in p.parts)


def test_ningun_estado_supera_su_evidencia():
    assert estados_que_superan_su_evidencia(ESTADO.read_text(encoding="utf-8"), (ROOT / "README.md").read_text(encoding="utf-8"), _hay_guion_de_demostracion()) == []


def test_negativas_de_la_regla_un_estado_nunca_supera_su_evidencia(tmp_path):
    t = ESTADO.read_text(encoding="utf-8")
    r = "# Proyecto\n\nUn README de ejemplo sin diagrama de arquitectura ni sección de primera vez.\n"   # el README real ya los tiene: las negativas usan un texto sintético
    fila72 = re.search(r"^\| 7\.2 \| «.*$", t, re.M).group(0)
    fila75 = re.search(r"^\| 7\.5 \| «.*$", t, re.M).group(0)
    sube72 = _copia(tmp_path, t, [(fila72, _con_estado_vigente(fila72, "Cumple"))])
    sube75 = _copia(tmp_path, t, [(fila75, _con_estado_vigente(fila75, "En curso"))])
    assert estados_que_superan_su_evidencia(sube72, r, True), "7.2 «Cumple» sin diagrama ni sección de primera vez"
    assert estados_que_superan_su_evidencia(sube75, r, False), "7.5 avanza sin guion de demostración"
    assert estados_que_superan_su_evidencia(sube75, r, True) == [], "con guion de demostración, 7.5 puede avanzar"
    assert estados_que_superan_su_evidencia(sube72, r + "\n## Primera vez\n![Arquitectura del sistema](docs/x.png)\n", False) == [], "con diagrama y sección, 7.2 puede cumplir"


def test_ningun_documento_conserva_etiquetas_de_fase_como_fase_de_trabajo():
    """Las salidas crudas de las evidencias, las imágenes, el documento aislado de la raíz y los datos se excluyen: conservan lo que tenían al capturarse."""
    saltar = {".venv", ".git", "data", "dist", "logs", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
    hallazgos = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if (not p.is_file() or any(x in saltar for x in rel.parts) or p.suffix not in SUFIJOS or make_dist.es_documento_aislado(rel.as_posix())
                or rel.as_posix().startswith(("docs/evidencias/base/", "docs/evidencias/estrategia/", "docs/evidencias/api/", "tests/test_estrategia.py"))):
            continue
        if ETIQUETA_DE_FASE.search(p.read_text(encoding="utf-8", errors="ignore")):
            hallazgos.append(rel.as_posix())
    assert hallazgos == []


# Términos de proceso y rutas antiguas (partidos para que este archivo no se detecte a sí mismo)
TERMINOS_DE_PROCESO = [r"Entre" + r"ga 3", r"entre" + r"ga_3", r"Avan" + r"ce 2", r"avan" + r"ce_2", r"segunda entre" + r"ga", r"entre" + r"ga3-f", r"base-entre" + r"ga-3", r"D-E" + r"3", r"guion de vi" + r"deo",
                       r"seccion" + r"_1", r"verificacion_seccion" + r"_2", r"MANIFIESTO" + r"_EVIDENCIAS", r"test_entrega_3" + r"_seccion_1", r"Cómo lo defen" + r"demos"]


def test_ningun_documento_conserva_terminos_de_proceso_ni_rutas_antiguas():
    """Excluye lo protegido (evidencias crudas, imágenes, PDF, retroalimentación original, documento aislado de la raíz y datos) y las listas de cadenas de las pruebas."""
    saltar = {".venv", ".git", "data", "dist", "logs", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
    hallazgos = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if (not p.is_file() or any(x in saltar for x in rel.parts) or p.suffix not in SUFIJOS or make_dist.es_documento_aislado(rel.as_posix())
                or rel.as_posix().startswith(("docs/evidencias/base/", "docs/evidencias/estrategia/", "docs/evidencias/api/", "docs/retroalimentacion/retroalimentacion_recibida.txt", "tests/test_estrategia.py"))):
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        hallazgos += [(rel.as_posix(), x) for x in TERMINOS_DE_PROCESO if re.search(x, t)]
    assert hallazgos == []


# ---------------------------------------------------------------- tabla REAL de criterios del MVP (D81)
# `revisar_criterios` valida la forma de una tabla cualquiera; aquí se vigila la tabla verdadera de
# docs/estrategia/05_mvp_criterios_aceptacion.md: que no pierda filas, que cada «cumple» tenga con qué comprobarse y que sus rutas existan.
PISO_DE_CRITERIOS = 29    # número mínimo de filas; solo sube cuando se agregan criterios
PISO_DE_CUMPLEN = 29      # criterios que ya cumplen; solo sube: bajar uno es un retroceso que debe verse
VACIOS = {"", "—", "-", "n/d", "N/D"}
MARCADORES_DE_RUTA = {"ruta"}   # `ruta` es el ejemplo de la leyenda de etiquetas, no un archivo
ENCABEZADO_DE_CONTEOS = re.compile(r"(\d+) de (\d+) criterios cumplen hoy; (\d+) están «no verificado aún»")
ETIQUETA_DE_RUTAS = re.compile(r"\[Evidencia en el repo:([^\]]*)\]")


def _filas_de_criterios(texto):
    """Líneas de la tabla de criterios: cada una empieza por `| ACnn |`."""
    return [l for l in texto.splitlines() if re.match(r"^\| AC\d+ \|", l)]


def revisar_tabla_real(texto, raiz, hoy):
    """Errores de la tabla real de criterios del MVP (lista vacía si todo está en regla).

    Reglas: ids consecutivos AC01 a ACnn; conteos del encabezado y de «Alcance y límites» iguales al recuento propio de las filas;
    pisos de filas y de criterios que cumplen; toda fila «cumple» con comando, evidencia, resultado y fecha ISO no futura
    (y de las que declara el encabezado); rutas citadas como «[Evidencia en el repo: …]» existentes; ningún «cumple» que diga pendiente.
    """
    errores = []
    filas = _filas_de_criterios(texto)
    ids = [re.match(r"^\| (AC\d+) \|", l).group(1) for l in filas]
    if ids != [f"AC{i:02d}" for i in range(1, len(ids) + 1)]:
        errores.append(f"los ids no son consecutivos desde AC01 sin saltos ni repetidos: {ids}")
    if len(filas) < PISO_DE_CRITERIOS:
        errores.append(f"menos criterios que el piso: {len(filas)} frente a {PISO_DE_CRITERIOS}")
    cumplen = pendientes = 0
    encabezado = ENCABEZADO_DE_CONTEOS.search(texto)
    fechas_declaradas = set(re.findall(r"\d{4}-\d{2}-\d{2}", texto[encabezado.start():].split("\n", 1)[0])) if encabezado else set()
    for linea in filas:
        c = linea[2:-2].split(" | ")
        if len(c) != 9:
            errores.append(f"{c[0].strip()}: la fila tiene {len(c)} celdas y no 9")
            continue
        _id, estado = c[0].strip(), c[6].strip().replace("*", "")
        if estado.startswith("no verificado aún"):
            pendientes += 1
        if estado != "cumple":
            continue
        cumplen += 1
        for nombre, valor in (("cómo se verifica", c[3]), ("evidencia", c[4]), ("resultado actual", c[5])):
            if valor.strip() in VACIOS:
                errores.append(f"{_id}: «cumple» sin {nombre}")
        if re.search(r"(?i)no verificado|pendiente", c[5]):
            errores.append(f"{_id}: «cumple» con un resultado que dice no verificado o pendiente")
        try:
            fecha = datetime.date.fromisoformat(c[8].strip())
        except ValueError:
            errores.append(f"{_id}: la fecha {c[8].strip()!r} no es una fecha ISO válida")
        else:
            if fecha > hoy:
                errores.append(f"{_id}: fecha futura ({fecha})")
            if fecha.isoformat() not in fechas_declaradas:
                errores.append(f"{_id}: la fecha {fecha} no está entre las que declara el encabezado ({sorted(fechas_declaradas)})")
    if cumplen < PISO_DE_CUMPLEN:
        errores.append(f"menos criterios que cumplen que el piso: {cumplen} frente a {PISO_DE_CUMPLEN}")
    if encabezado is None:
        errores.append("falta el encabezado con los conteos")
    elif (int(encabezado[1]), int(encabezado[2]), int(encabezado[3])) != (cumplen, len(filas), pendientes):
        errores.append(f"el encabezado dice {encabezado.groups()} y el recuento de filas da {(cumplen, len(filas), pendientes)}")
    alcance = re.search(r"con ocho funcionalidades y (\d+) criterios", texto)
    if alcance is None or int(alcance[1]) != len(filas):
        errores.append(f"«Alcance y límites» dice {alcance[1] if alcance else 'nada'} criterios y la tabla tiene {len(filas)}")
    for etiqueta in ETIQUETA_DE_RUTAS.finditer(texto):
        for ruta in re.findall(r"`([^`]+)`", etiqueta.group(1)):
            ruta = re.sub(r"\s*\(.*\)$", "", ruta)
            if ruta in MARCADORES_DE_RUTA:
                continue
            existe = any(raiz.glob(ruta)) if "*" in ruta else (raiz / ruta).exists()
            if not existe:
                errores.append(f"la ruta citada no existe: {ruta}")
    return errores


def _con_celda_cambiada(texto, ac, indice, nuevo):
    """Copia en memoria con la celda `indice` (0 a 8) de la fila `ac` reemplazada por `nuevo`."""
    fila = re.search(rf"^\| {ac} \|.*$", texto, re.M).group(0)
    celdas = fila[2:-2].split(" | ")
    celdas[indice] = nuevo
    return texto.replace(fila, "| " + " | ".join(celdas) + " |", 1)


def _sin_la_fila(texto, ac):
    return re.sub(rf"^\| {ac} \|.*\n", "", texto, count=1, flags=re.M)


def _fila(texto, ac):
    return re.search(rf"^\| {ac} \|.*$", texto, re.M).group(0)


def test_la_tabla_real_de_criterios_cumple_las_reglas():
    assert revisar_tabla_real(_texto("05_mvp_criterios_aceptacion.md"), ROOT, datetime.date.today()) == []


MUTACIONES_DE_LA_TABLA = {
    # nombre: (cambio sobre el texto real, fragmento que debe aparecer en el error)
    "un criterio pasa a «no verificado aún» con el encabezado ajustado": (lambda t: _con_un_criterio_pendiente(t), "menos criterios que cumplen que el piso"),
    "comando de verificación vacío en AC28": (lambda t: _con_celda_cambiada(t, "AC28", 3, ""), "AC28: «cumple» sin cómo se verifica"),
    "evidencia vacía en AC10": (lambda t: _con_celda_cambiada(t, "AC10", 4, "—"), "AC10: «cumple» sin evidencia"),
    "resultado vacío en AC05": (lambda t: _con_celda_cambiada(t, "AC05", 5, " "), "AC05: «cumple» sin resultado actual"),
    "resultado que dice pendiente": (lambda t: _con_celda_cambiada(t, "AC07", 5, "pendiente de revisar"), "AC07: «cumple» con un resultado"),
    "encabezado «28 de 29»": (lambda t: t.replace("29 de 29 criterios cumplen", "28 de 29 criterios cumplen", 1), "el encabezado dice"),
    "borrar una fila del medio": (lambda t: _sin_la_fila(t, "AC12"), "no son consecutivos"),
    "borrar la última fila": (lambda t: _sin_la_fila(t, "AC29"), "menos criterios que el piso"),
    "repetir un id": (lambda t: t.replace(_fila(t, "AC13"), _fila(t, "AC12"), 1), "no son consecutivos"),
    "fecha futura": (lambda t: _con_celda_cambiada(t, "AC28", 8, (datetime.date.today() + datetime.timedelta(days=1)).isoformat()), "fecha futura"),
    "fecha que el encabezado no declara": (lambda t: _con_celda_cambiada(t, "AC28", 8, "2026-11-01"), "no está entre las que declara"),
    "fecha que no es una fecha": (lambda t: _con_celda_cambiada(t, "AC28", 8, "2026-13-45"), "no es una fecha ISO válida"),
    "ruta citada que no existe": (lambda t: t.replace("`docs/panel/trazabilidad_ui.md`", "`docs/panel/no_existe.md`", 1), "la ruta citada no existe"),
    "conteo de «Alcance y límites»": (lambda t: t.replace("ocho funcionalidades y 29 criterios", "ocho funcionalidades y 30 criterios", 1), "«Alcance y límites» dice 30"),
}


@pytest.mark.parametrize("nombre", list(MUTACIONES_DE_LA_TABLA))
def test_negativa_cada_alteracion_de_la_tabla_real_se_detecta(nombre):
    cambio, esperado = MUTACIONES_DE_LA_TABLA[nombre]
    original = _texto("05_mvp_criterios_aceptacion.md")
    alterada = cambio(original)
    assert alterada != original, f"la alteración «{nombre}» no cambió nada: la prueba está mal armada"
    errores = revisar_tabla_real(alterada, ROOT, datetime.date.today())
    assert any(esperado in e for e in errores), f"«{nombre}» no produjo el error esperado ({esperado!r}): {errores}"


# --- la figura de la matriz poder-interés sale de la tabla de puntajes y no usa el rótulo anterior ---
def _script_de_la_matriz():
    espec = importlib.util.spec_from_file_location("make_matriz_poder_interes", ROOT / "scripts" / "make_matriz_poder_interes.py")
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def atestado_de_la_figura(ruta):
    """Los puntos y nombres que el script dejó como metadato del PNG (None si la imagen no salió del script)."""
    d = _texto_png(ruta).get("Description")
    return json.loads(d) if d else None


def _texto_png(ruta):
    """Pares clave-valor de los fragmentos de texto (`tEXt` e `iTXt`) de un PNG, leídos sin librerías de imágenes."""
    datos = Path(ruta).read_bytes()
    assert datos[:8] == b"\x89PNG\r\n\x1a\n"
    textos, pos = {}, 8
    while pos < len(datos):
        largo = int.from_bytes(datos[pos:pos + 4], "big")
        tipo, cuerpo = datos[pos + 4:pos + 8], datos[pos + 8:pos + 8 + largo]
        if tipo == b"tEXt":
            clave, _, valor = cuerpo.partition(b"\x00")
            textos[clave.decode("latin-1")] = valor.decode("latin-1")
        elif tipo == b"iTXt":
            clave, _, resto = cuerpo.partition(b"\x00")
            comprimido, resto = resto[0], resto[2:]
            _, _, resto = resto.partition(b"\x00")      # etiqueta de idioma
            _, _, valor = resto.partition(b"\x00")      # clave traducida
            if not comprimido:
                textos[clave.decode("latin-1")] = valor.decode("utf-8")
        pos += 12 + largo
    return textos


def errores_de_la_figura(atestado, tabla):
    """Diferencias entre lo que dice la figura y la tabla de puntajes (lista vacía si coinciden)."""
    matriz = _script_de_la_matriz()
    if atestado is None:
        return ["la imagen no trae el atestado del script que la genera"]
    esperado = [list(p) for p in matriz.leer_puntos(tabla)]
    errores = []
    if atestado["puntos"] != esperado:
        errores.append("los puntos o nombres de la figura no coinciden con la tabla")
    if "Pro" + "fesor" in json.dumps(atestado, ensure_ascii=False) or "Pro" + "fesor" in tabla:
        errores.append("la figura o la tabla traen el rótulo anterior del equipo docente")
    return errores


def test_la_figura_de_stakeholders_sale_de_la_tabla_y_no_trae_el_rotulo_anterior(tmp_path):
    tabla = _texto("02_stakeholders.md")
    imagen = CARPETA / "img" / "matriz_poder_interes.png"
    assert errores_de_la_figura(atestado_de_la_figura(imagen), tabla) == []
    matriz = _script_de_la_matriz()
    regenerada = matriz.dibujar(matriz.leer_puntos(tabla), tmp_path / "otra.png")      # el script reproduce el mismo atestado
    assert regenerada == atestado_de_la_figura(imagen)


def test_negativas_de_la_figura_de_stakeholders(tmp_path):
    tabla = _texto("02_stakeholders.md")
    imagen = CARPETA / "img" / "matriz_poder_interes.png"
    atestado = atestado_de_la_figura(imagen)
    con_profesor = tabla.replace("Equipo docente (evaluación del curso)", "Pro" + "fesor del curso (evaluador de la entrega)")
    assert con_profesor != tabla and errores_de_la_figura(atestado, con_profesor), "la tabla vuelve a traer el rótulo anterior del equipo docente"
    alterado = json.loads(json.dumps(atestado))
    alterado["puntos"][8][1] = "Pro" + "fesor del curso (evaluador de la entrega)"
    assert errores_de_la_figura(alterado, tabla), "la figura vuelve a traer el rótulo anterior del equipo docente"
    desplazado = json.loads(json.dumps(atestado))
    desplazado["puntos"][0][3] += 1
    assert errores_de_la_figura(desplazado, tabla), "un punto cambia de lugar sin cambiar la tabla"
    assert errores_de_la_figura(None, tabla), "una imagen que no salió del script (la anterior)"
    sin_tabla = tabla.replace("| 11 | Equipo del proyecto | 3 | 3 | 3 | 3 | 6 | 6 |", "| 11 | Equipo del proyecto | 3 | 3 | 3 | 3 | 6 | 5 |")
    with pytest.raises(ValueError):
        _script_de_la_matriz().leer_puntos(sin_tabla)      # un puntaje que no suma lo que dice la rúbrica


# --- las subfilas de detalle: etiquetas de subcriterio, que no entran al conteo de los 30 ítems ---
ETIQUETAS_DE_SUBFILA = ["Preparado", "Probado con datos sintéticos", "No realizada", "Hecho (iteración técnica)"]
SUBFILA = re.compile(r"^\| (\d\.\d) \| (?!«)([^|]+) \| ([^|]+) \| ", re.M)


def estados_de_subfila_no_permitidos(texto):
    """Estados de las filas de detalle (ítem | subcriterio | estado | …) que no son del vocabulario del repositorio ni una etiqueta de subfila conocida."""
    permitidos = set(ESTADOS_REGLA) | set(ETIQUETAS_DE_SUBFILA)
    return sorted({f"{m.group(1)}: {m.group(3).strip().replace('*', '')}" for m in SUBFILA.finditer(texto) if m.group(3).strip().replace("*", "") not in permitidos})


def test_las_subfilas_de_detalle_solo_usan_estados_del_vocabulario_o_etiquetas_conocidas():
    assert estados_de_subfila_no_permitidos(ESTADO.read_text(encoding="utf-8")) == []


def test_negativas_de_las_subfilas_de_detalle_y_el_conteo_las_ignora(tmp_path):
    t = ESTADO.read_text(encoding="utf-8")
    fila = re.search(r"^\| 6\.3 \| Registro de fricciones con severidad \| [^|]+ \|.*$", t, re.M).group(0)
    campos = fila.split(" | ")
    inventado = " | ".join(campos[:2] + ["Casi cumple"] + campos[3:])
    assert estados_de_subfila_no_permitidos(_copia(tmp_path, t, [(fila, inventado)])) == ["6.3: Casi cumple"]
    contar = _script_de_conteo()
    # una etiqueta de subfila no entra al conteo de los 30 ítems: cambiarla no mueve el conteo, y el estado vigente de 6.3 sigue siendo el de la tabla principal
    assert contar.contar(_copia(tmp_path, t, [(fila, inventado)])) == contar.contar(t)
    assert contar.estados_por_item(t)["6.3"] == "Pendiente (hecho externo)"
