"""Estrategia (docs/estrategia) y estado del checklist: existencia, rastros de elaboración, cifras, rúbrica R1, avisos de honestidad,
criterios del MVP y tabla de los 30 ítems, con pruebas negativas sobre copias alteradas de las tablas."""
import json
import re
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

from src.common import ROOT

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
ESTADOS_REGLA = ["Cumple", "Cumple con matiz", "Pendiente (hecho externo)", "N/A justificado", "No cumple"]
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
    """Recorre los archivos de texto versionables (sin .venv, .git, data/, dist/ ni la declaración de uso, que es del equipo)."""
    saltar = {".venv", ".git", "data", "dist", "logs", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
    hallazgos = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if not p.is_file() or rel.parts[0] in saltar or any(x in saltar for x in rel.parts) or p.suffix not in SUFIJOS or p.name == "DECLARACION_USO_IA.md":
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
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
            errores.append(f"{_id}: estado objetivo no permitido ({objetivo.strip()!r})")
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


def test_negativas_de_los_criterios_del_mvp(tmp_path):
    t = _texto("05_mvp_criterios_aceptacion.md")
    pendiente = re.search(r"\*\*no verificado aún: ([^*]+)\*\* \| ([^|]+) \| — \|", t)
    cumple = re.search(r"\*\*cumple\*\* \| [^|]+ \| (\d{4}-\d{2}-\d{2}) \|", t)
    assert pendiente and cumple
    comp = pendiente.group(1)
    alteraciones = {
        "componente vacío": [(f"**no verificado aún: {comp}** | {comp} | —", "**no verificado aún: ** |  | —")],
        "componente inventado": [(f"**no verificado aún: {comp}** | {comp} | —", "**no verificado aún: Fase uno** | Fase uno | —")],
        "componente por definir": [(f"**no verificado aún: {comp}** | {comp} | —", "**no verificado aún: por definir** | por definir | —")],
        "criterio pendiente con guion": [(f"**no verificado aún: {comp}** | {comp} | —", "**no verificado aún: —** | — | —")],
        "criterio cumple sin fecha": [(cumple.group(0), cumple.group(0).replace(cumple.group(1), "—"))],
        "conteo que no coincide": [("23 de 29 criterios cumplen hoy", "24 de 29 criterios cumplen hoy")],
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
        "estado objetivo desconocido": [(fila, fila.replace(f"| {campos[5]} |", "| Casi cumple |", 1))],
        "estado actual desconocido": [(fila, fila.replace(f"| {campos[2]} |", "| Quizá |", 1))],
    }
    for nombre, cambios in alteraciones.items():
        assert revisar_items(_copia(tmp_path, t, cambios)), nombre


def test_ningun_documento_conserva_etiquetas_de_fase_como_fase_de_trabajo():
    """Las salidas crudas de las evidencias, las imágenes, la declaración de uso y los datos se excluyen: conservan lo que tenían al capturarse."""
    saltar = {".venv", ".git", "data", "dist", "logs", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}
    hallazgos = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if (not p.is_file() or any(x in saltar for x in rel.parts) or p.suffix not in SUFIJOS or p.name == "DECLARACION_USO_IA.md"
                or rel.as_posix().startswith(("docs/evidencias/base/", "docs/evidencias/estrategia/", "docs/evidencias/api/", "tests/test_estrategia.py"))):
            continue
        if ETIQUETA_DE_FASE.search(p.read_text(encoding="utf-8", errors="ignore")):
            hallazgos.append(rel.as_posix())
    assert hallazgos == []
