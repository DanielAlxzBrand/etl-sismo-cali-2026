"""Guardianes de lo preparado para las sesiones con personas usuarias y para los costos (D82 a D85).

Vigilan: que existan los materiales y viajen en el zip; que `sesiones_reales/` solo tenga plantillas mientras no haya filas `real`; que no haya cifras monetarias;
que todo parámetro con valor traiga fuente y fecha; que `estado_checklist.md` no marque como cumplidos los ítems que dependen de sesiones reales; y que la evaluación
heurística tenga sus ocho páginas, sus diez heurísticas, severidades de 0 a 4 y capturas que existan.
"""
import csv
import importlib.util
import re

import pytest
import yaml

from src.common import ROOT
from src.panel import registro

USUARIOS = ROOT / "docs" / "usuarios"
FINANZAS = ROOT / "docs" / "finanzas"
REALES = USUARIOS / "sesiones_reales"
EVIDENCIAS = ROOT / "docs" / "evidencias" / "usuarios"
ESTADO = ROOT / "docs" / "checklist" / "estado_checklist.md"


def _cargar(ruta, nombre):
    espec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


make_dist = _cargar(ROOT / "scripts" / "make_dist.py", "make_dist")
costos = _cargar(ROOT / "scripts" / "finanzas" / "costos.py", "costos_estructura")

ARCHIVOS = [
    "docs/usuarios/README.md", "docs/usuarios/protocolo_sesiones.md", "docs/usuarios/guion_sesion.md", "docs/usuarios/consentimiento.md", "docs/usuarios/instrumentos.md",
    "docs/usuarios/evaluacion_heuristica.md", "docs/usuarios/registro_de_friccion.md", "docs/usuarios/registro_de_friccion.csv", "docs/usuarios/trazabilidad_de_cambios.md",
    "docs/usuarios/resultados.md", "docs/usuarios/resultados_simulacion.md",
    "docs/usuarios/sesiones_reales/README.md", "docs/usuarios/sesiones_reales/plantilla_registro.csv", "docs/usuarios/sesiones_reales/plantilla_cuestionarios.csv",
    "docs/usuarios/sesiones_reales/plantilla_friccion.csv", "docs/usuarios/simulacion/README.md", "docs/usuarios/simulacion/registro.csv", "docs/usuarios/simulacion/cuestionarios.csv",
    "docs/finanzas/estructura_costos.md", "docs/finanzas/recursos_medidos.csv", "config/parametros_costos.yaml",
    "scripts/usuarios/analizar_sesiones.py", "scripts/usuarios/generar_datos_sinteticos.py", "scripts/usuarios/precargar_friccion.py",
    "scripts/finanzas/costos.py", "scripts/finanzas/medir_recursos.py",
    "scripts/evidencias/evidencia_capturas_anchos.py", "scripts/evidencias/evidencia_capturas_movil.py",
]


# ---------------------------------------------------------------- (a) estructura y zip
@pytest.mark.parametrize("ruta", ARCHIVOS)
def test_existe_cada_material_preparado(ruta):
    assert (ROOT / ruta).is_file(), ruta


def test_los_materiales_viajan_en_el_zip_de_prueba():
    nombres = {p.relative_to(ROOT).as_posix() for p in make_dist.listar(ROOT)}
    faltan = [r for r in ARCHIVOS if r not in nombres]
    assert faltan == [], f"no entran al zip: {faltan}"


# ---------------------------------------------------------------- (b) sesiones reales
CAMPOS_PLANTILLAS = {
    "plantilla_registro.csv": ("participante", "perfil", "fecha", "tarea", "resultado", "tiempo_s", "ayudas", "errores", "comentario_breve", "origen"),
    "plantilla_cuestionarios.csv": ("participante", "perfil", "fecha") + tuple(f"sus_{i}" for i in range(1, 11)) + ("csat", "origen"),
}


def archivos_no_permitidos(nombres, filas_por_archivo):
    """Errores de una carpeta de sesiones reales: solo README y plantillas vacías, o CSV cuyas filas son todas `real`."""
    errores = []
    for nombre in nombres:
        filas = filas_por_archivo.get(nombre, [])
        if nombre == "README.md":
            continue
        if nombre.startswith("plantilla_"):
            if filas:
                errores.append(f"{nombre}: una plantilla no puede tener filas")
        elif nombre.endswith(".csv"):
            malas = [f.get("origen") for f in filas if f.get("origen") != "real"]
            if malas:
                errores.append(f"{nombre}: filas con origen distinto de real: {sorted(set(map(str, malas)))}")
        else:
            errores.append(f"{nombre}: archivo no previsto en sesiones_reales")
    return errores


def _filas_reales():
    nombres = sorted(p.name for p in REALES.iterdir() if p.is_file())
    salida = {}
    for n in nombres:
        if n.endswith(".csv"):
            with open(REALES / n, encoding="utf-8", newline="") as f:
                salida[n] = list(csv.DictReader(f))
    return nombres, salida


def test_sesiones_reales_solo_tiene_plantillas_o_filas_reales():
    nombres, filas = _filas_reales()
    assert archivos_no_permitidos(nombres, filas) == []


def test_las_plantillas_tienen_las_columnas_del_script_de_analisis():
    for nombre, campos in CAMPOS_PLANTILLAS.items():
        with open(REALES / nombre, encoding="utf-8", newline="") as f:
            assert tuple(csv.DictReader(f).fieldnames) == campos, nombre


def test_mientras_no_haya_sesiones_reales_los_resultados_lo_dicen():
    nombres, _ = _filas_reales()
    if not any(n in nombres for n in ("registro.csv", "cuestionarios.csv")):
        assert "No hay sesiones reales" in (USUARIOS / "resultados.md").read_text(encoding="utf-8")


def test_negativa_una_fila_simulada_o_una_plantilla_con_filas_se_detecta():
    assert archivos_no_permitidos(["registro.csv"], {"registro.csv": [{"origen": "real"}, {"origen": "simulado"}]})
    assert archivos_no_permitidos(["plantilla_registro.csv"], {"plantilla_registro.csv": [{"origen": "real"}]})
    assert archivos_no_permitidos(["notas_con_nombres.txt"], {})
    assert archivos_no_permitidos(["README.md", "plantilla_registro.csv", "registro.csv"], {"registro.csv": [{"origen": "real"}]}) == []


def test_ningun_archivo_de_usuarios_trae_correos_ni_telefonos():
    patron = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+|\b3\d{9}\b|\b\+?57\s?\d{10}\b")
    for p in list(USUARIOS.rglob("*.md")) + list(USUARIOS.rglob("*.csv")):
        assert not patron.search(p.read_text(encoding="utf-8")), p.relative_to(ROOT).as_posix()


# ---------------------------------------------------------------- (c) ninguna cifra monetaria
MONETARIO = re.compile(r"(\$\s*\d|(?<![\w-])\d[\d.,]*\s*\$(?=[\s.,;:)]|$)|\b(?:COP|USD|EUR)\s*\$?\s*\d|\d[\d.,]*\s*(?:COP|USD|EUR|pesos|dólares|dolares)\b|\b(?:pesos|dólares|dolares)\s+[\d$])", re.I)
PERMITIDOS_MONETARIOS = ()      # lista de excepciones de la prueba (vacía: no hay ninguna cifra monetaria en estos archivos)


def cifras_monetarias(texto):
    return [m.group(0) for m in MONETARIO.finditer(texto) if m.group(0) not in PERMITIDOS_MONETARIOS]


def _archivos_de_costos():
    return [p for base, patrones in ((FINANZAS, ("*.md", "*.csv")), (ROOT / "scripts" / "finanzas", ("*.py",))) for pat in patrones for p in base.glob(pat)] + [ROOT / "config" / "parametros_costos.yaml"]


def test_ninguna_cifra_monetaria_en_docs_finanzas_scripts_finanzas_ni_parametros():
    encontradas = {p.relative_to(ROOT).as_posix(): cifras_monetarias(p.read_text(encoding="utf-8")) for p in _archivos_de_costos()}
    assert {k: v for k, v in encontradas.items() if v} == {}


@pytest.mark.parametrize("texto", ["cuesta $ 5", "cuesta $5", "cuesta 5$", "5 USD", "COP 1000", "1.500 pesos", "pesos 300", "12 dólares", "usd 4"])
def test_negativa_el_detector_reconoce_una_cifra_monetaria(texto):
    assert cifras_monetarias(texto)


@pytest.mark.parametrize("texto", ["precio por hora de cómputo", "moneda por GB-mes", "3,6 a 13,9 ms", "una moneda por definir", "pesos de las barras", "re.sub(r'^a-|-1$', x)"])
def test_negativa_el_detector_no_confunde_texto_sin_cifras(texto):
    assert cifras_monetarias(texto) == []


# ---------------------------------------------------------------- (d) parámetros con fuente y fecha
def test_todo_parametro_con_valor_trae_fuente_y_fecha():
    assert costos.revisar_parametros(costos.cargar_parametros()) == []


def test_negativa_un_parametro_con_valor_y_sin_fuente_se_detecta():
    p = costos.cargar_parametros()
    p["tarifa_hora_equipo"] = dict(p["tarifa_hora_equipo"], valor=1)
    assert costos.revisar_parametros(p)
    p["tarifa_hora_equipo"].update(fuente="x", fecha="2000-01-01")
    assert costos.revisar_parametros(p) == []


# ---------------------------------------------------------------- (e) estado del checklist
DEPENDEN_DE_SESIONES = ("6.1", "6.2", "6.3", "6.5", "7.4")
# D111: estos cinco ítems solo pueden estar en «Cumple con matiz» con el matiz de la decisión; nunca en «Cumple» a secas.
MATIZ = "evidencia simulada, sin personas reales. Las dos sesiones son de participantes simulados y no sustituyen sesiones con personas"


def _celdas(linea):
    return [c.strip().replace("*", "") for c in linea.strip().strip("|").split("|")]


def items_marcados_como_cumple_a_secas(texto):
    """Ids de los ítems que dependen de sesiones con alguna celda «Cumple» a secas en cualquier tabla del documento (con la excepción, solo valen «Cumple con matiz»)."""
    marcados = set()
    for linea in texto.splitlines():
        m = re.match(r"^\| (\d\.\d) \|", linea)
        if m and m.group(1) in DEPENDEN_DE_SESIONES and "Cumple" in _celdas(linea):
            marcados.add(m.group(1))
    return sorted(marcados)


def items_con_matiz_incompleto(texto):
    """Ids de la tabla principal que dependen de sesiones y no están en «Cumple con matiz» con el matiz y el matiz de la decisión D111."""
    mal = []
    for i in DEPENDEN_DE_SESIONES:
        linea = next((l for l in texto.splitlines() if l.startswith(f"| {i} | «")), "")
        celdas = _celdas(linea) if linea else []
        if len(celdas) < 6 or celdas[5] != "Cumple con matiz" or MATIZ not in linea:
            mal.append(i)
    return mal


def _hay_sesiones_reales():
    _, filas = _filas_reales()
    return any(f for n, f in filas.items() if not n.startswith("plantilla_"))


def test_ninguna_fila_que_depende_de_sesiones_dice_cumple_a_secas():
    assert items_marcados_como_cumple_a_secas(ESTADO.read_text(encoding="utf-8")) == []


def test_las_cinco_filas_estan_en_cumple_con_matiz_y_tienen_el_matiz_en_el_estado_la_trazabilidad_y_la_decision():
    assert items_con_matiz_incompleto(ESTADO.read_text(encoding="utf-8")) == []
    import csv
    with open(ROOT / "docs" / "checklist" / "trazabilidad.csv", encoding="utf-8-sig", newline="") as f:
        filas = {r["item"]: r for r in csv.DictReader(f)}
    for i in DEPENDEN_DE_SESIONES:
        assert filas[i]["estado"] == "Cumple con matiz" and MATIZ in filas[i]["que_no_demuestra"], i
    decision = (ROOT / "docs" / "DECISIONES.md").read_text(encoding="utf-8")
    d111 = next(l for l in decision.splitlines() if l.startswith("**D111 "))
    assert "evidencia simulada, sin personas reales" in d111 and "nunca «Cumple» a secas" in d111 and "tiempo disponible" not in d111 and "excepción" not in d111
    regla = ESTADO.read_text(encoding="utf-8").splitlines()[4]
    assert regla.startswith("**Regla de estado.**") and "mientras ese evento no ocurra, el estado es «Pendiente (hecho externo)»" in regla and "D111" not in regla, "la regla de la línea 5 no se edita"


def test_el_estado_dice_que_el_material_esta_preparado_y_faltan_las_sesiones_reales():
    texto = ESTADO.read_text(encoding="utf-8")
    for i in ("6.1", "6.2", "6.3"):
        linea = next(l for l in texto.splitlines() if l.startswith(f"| {i} | «"))
        assert "Cumple con matiz" in linea and "faltan las sesiones reales" in linea, i
    assert "material preparado y script probado; faltan las sesiones reales" in texto.lower()


def test_negativas_de_la_excepcion_cumple_a_secas_matiz_sin_referencia_o_estado_pendiente_se_detectan():
    base = "| 6.1 | «texto» | Requiere hecho externo | x | y | Cumple con matiz | Matiz: " + MATIZ + ". z |"
    assert items_marcados_como_cumple_a_secas(base) == [] and items_con_matiz_incompleto(base).count("6.1") == 0
    assert items_marcados_como_cumple_a_secas(base.replace("Cumple con matiz | Matiz", "**Cumple** | Matiz")) == ["6.1"], "«Cumple» a secas aunque cambie el formato de la fila"
    assert items_marcados_como_cumple_a_secas("| 6.1 | Casos | Cumple | a |") == ["6.1"] and items_marcados_como_cumple_a_secas("| 5.1 | Casos | Cumple | a |") == []
    assert items_con_matiz_incompleto(base.replace(MATIZ, "evidencia simulada, sin personas reales")).count("6.1") == 1, "el matiz recortado"
    assert items_con_matiz_incompleto(base.replace("evidencia simulada, sin personas reales", "evidencia")).count("6.1") == 1, "el matiz incompleto"
    assert items_con_matiz_incompleto(base.replace("| Cumple con matiz |", "| Pendiente (hecho externo) |")).count("6.1") == 1, "un estado que no es «Cumple con matiz»"
    assert items_con_matiz_incompleto(base.replace("Las dos sesiones son de participantes simulados", "Las sesiones")).count("6.1") == 1, "el matiz con otra segunda frase"


# ---------------------------------------------------------------- (f) evaluación heurística
def leer_evaluacion(texto):
    """(hallazgos, filas de la matriz) de la evaluación heurística; cada hallazgo es un diccionario con id, severidad, capturas y recomendación."""
    hallazgos, matriz = [], []
    for linea in texto.splitlines():
        if re.match(r"^\| F-\d+ \|", linea):
            c = [x.strip() for x in linea[2:-2].split(" | ")]
            n_celdas = len(c)
            c += [""] * (7 - len(c))
            hallazgos.append({"id": c[0], "pagina": c[1], "heuristica": c[2], "capturas": re.findall(r"`([^`]+\.png)`", c[4]), "severidad": c[5], "recomendacion": c[6], "celdas": n_celdas})
        elif re.match(r"^\| H\d+ ", linea):
            matriz.append([x.strip() for x in linea.strip().strip("|").split("|")])
    return hallazgos, matriz


def errores_de_la_evaluacion(texto, existe=lambda nombre: (EVIDENCIAS / nombre).is_file()):
    errores = []
    hallazgos, matriz = leer_evaluacion(texto)
    if not hallazgos:
        errores.append("no hay hallazgos")
    for h in hallazgos:
        if h["celdas"] != 7:
            errores.append(f"{h['id']}: la fila no tiene 7 celdas")
        if not re.fullmatch(r"[0-4]", h["severidad"]):
            errores.append(f"{h['id']}: severidad {h['severidad']!r} fuera de 0 a 4")
        if not h["capturas"]:
            errores.append(f"{h['id']}: sin captura")
        errores += [f"{h['id']}: la captura {c} no existe" for c in h["capturas"] if not existe(c)]
        if not h["recomendacion"]:
            errores.append(f"{h['id']}: sin recomendación")
    if len(matriz) != 10 or [f[0].split()[0] for f in matriz] != [f"H{i}" for i in range(1, 11)]:
        errores.append("la matriz no tiene las diez heurísticas H1 a H10")
    elif any(len(f) != 9 for f in matriz):
        errores.append("la matriz no tiene ocho páginas por heurística")
    else:
        en_matriz = {i for f in matriz for celda in f[1:] for i in re.findall(r"F-\d+", celda)}
        ids = {h["id"] for h in hallazgos}
        errores += [f"{i} está en la matriz y no en la tabla" for i in sorted(en_matriz - ids)] + [f"{i} no aparece en la matriz" for i in sorted(ids - en_matriz)]
    return errores


def test_la_evaluacion_heuristica_tiene_ocho_paginas_diez_heuristicas_severidades_y_capturas_existentes():
    assert errores_de_la_evaluacion((USUARIOS / "evaluacion_heuristica.md").read_text(encoding="utf-8")) == []


def test_la_matriz_de_la_evaluacion_tiene_una_columna_por_pagina_del_panel():
    texto = (USUARIOS / "evaluacion_heuristica.md").read_text(encoding="utf-8")
    encabezado = next(l for l in texto.splitlines() if l.startswith("| Heurística | Respuesta"))
    columnas = [c.strip() for c in encabezado.strip().strip("|").split("|")][1:]
    assert len(columnas) == len(registro.PAGINAS) == 8
    assert columnas[0] == registro.PAGINAS[0].titulo


def test_la_evaluacion_lleva_su_titulo_y_el_pie_acordados():
    texto = (USUARIOS / "evaluacion_heuristica.md").read_text(encoding="utf-8")
    assert texto.startswith("# Evaluación heurística interna")
    assert texto.rstrip().endswith("Revisión del equipo: pendiente")
    assert "el equipo la revisó" not in texto and "revisada por el equipo" not in texto


def test_el_registro_de_friccion_tiene_los_mismos_hallazgos_que_la_evaluacion():
    precargar = _cargar(ROOT / "scripts" / "usuarios" / "precargar_friccion.py", "precargar_friccion_estructura")
    hallazgos = precargar.leer_hallazgos((USUARIOS / "evaluacion_heuristica.md").read_text(encoding="utf-8"))
    with open(USUARIOS / "registro_de_friccion.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert [f["id"] for f in filas] == [h["id"] for h in hallazgos]
    assert all(f["fuente"] in precargar.FUENTES and f["decision"] in precargar.DECISIONES and 0 <= int(f["severidad"]) <= 4 for f in filas)
    for f in filas:
        if f["fuente"] == "heuristica":
            assert f["participante"] == ""
        else:
            assert re.fullmatch(r"P\d{2}", f["participante"]), f"{f['id']}: una fricción de sesión necesita el código del participante"
        if f["decision"] != "pendiente":
            assert f["razon"].strip(), f"{f['id']}: una decisión sin razón"


def test_negativa_una_evaluacion_con_defectos_se_detecta():
    bueno = (USUARIOS / "evaluacion_heuristica.md").read_text(encoding="utf-8")
    sin_severidad = re.sub(r"(\| F-01 \|(?:[^|]*\|){4}) 3 \|", r"\1 |", bueno, count=1)
    assert any("severidad" in e for e in errores_de_la_evaluacion(sin_severidad))
    severidad_5 = re.sub(r"(\| F-01 \|(?:[^|]*\|){4}) 3 \|", r"\1 5 |", bueno, count=1)
    assert any("fuera de 0 a 4" in e for e in errores_de_la_evaluacion(severidad_5))
    captura_falsa = bueno.replace("EV-066_captura_respuesta_1024.png", "EV-066_captura_no_existe.png", 1)
    assert any("no existe" in e for e in errores_de_la_evaluacion(captura_falsa))
    sin_h10 = "\n".join(l for l in bueno.splitlines() if not l.startswith("| H10 "))
    assert any("diez heurísticas" in e for e in errores_de_la_evaluacion(sin_h10))


# ---------------------------------------------------------------- sesiones simuladas (D109)
SIMULADAS = USUARIOS / "sesiones_simuladas"
BANNER = "Sesión simulada, no realizada con una persona real"
NO_MEDIDO = "simulado, no medido"


def test_sesiones_reales_no_contiene_nada_simulado():
    assert sorted(p.name for p in REALES.iterdir()) == ["README.md", "plantilla_cuestionarios.csv", "plantilla_friccion.csv", "plantilla_registro.csv"], "ninguna carpeta ni archivo de más"
    for ruta in sorted(REALES.glob("*.csv")):
        with open(ruta, encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f))
        assert filas == [], f"{ruta.name}: una plantilla de sesiones reales no trae filas"
        texto = ruta.read_text(encoding="utf-8").lower()
        assert "simulad" not in texto and NO_MEDIDO not in texto and "participante simulado" not in texto, ruta.name


def test_la_carpeta_de_sesiones_simuladas_trae_solo_plantillas_registros_de_etapa_1_rotulados_y_las_filas_del_participante_2_y_los_conteos_reales_siguen_en_cero():
    assert sorted(p.name for p in SIMULADAS.iterdir()) == ["README.md", "cuestionarios.csv", "participante_simulado_1_etapa_1.md", "participante_simulado_2_etapa_1.md", "plantilla_registro.csv", "plantilla_registro.md", "registro.csv"], \
        "los CSV son solo del participante 2: el texto original de la etapa 2 del 1 está pendiente"
    for nombre in ("participante_simulado_1_etapa_1.md", "participante_simulado_2_etapa_1.md"):
        assert BANNER in (SIMULADAS / nombre).read_text(encoding="utf-8")
    leer = lambda n: (SIMULADAS / n).read_text(encoding="utf-8")   # noqa: E731
    assert BANNER in leer("README.md") and leer("plantilla_registro.md").startswith(f"# {BANNER}\n")
    with open(SIMULADAS / "plantilla_registro.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 1 and re.fullmatch(r"Participante simulado \d+", filas[0]["participante"]) and filas[0]["origen"] == "simulada"
    assert all(filas[0][c] == NO_MEDIDO for c in ("resultado", "tiempo_s", "ayudas", "errores"))
    an = _cargar(ROOT / "scripts" / "usuarios" / "analizar_sesiones.py", "analizar_sesiones_estructura")
    registro, cuestionarios = an.cargar_simuladas(SIMULADAS)
    assert (USUARIOS / "resultados_sesiones_simuladas.md").read_text(encoding="utf-8") == an.redactar_simuladas(registro, cuestionarios, an.registros_de_etapa_1(SIMULADAS)), "el resumen versionado es el que escribe el script con las filas de la carpeta"
    assert "No hay sesiones reales" in (USUARIOS / "resultados.md").read_text(encoding="utf-8")
    from tests.test_readme_cifras import hay_sesiones_reales
    assert hay_sesiones_reales(REALES) is False and hay_sesiones_reales(SIMULADAS) is False, "ninguna sesión real, y las simuladas no cuentan como reales"


def test_d109_y_la_guia_dicen_donde_va_una_sesion_simulada_y_no_dejan_pendientes():
    d109 = next(l for l in (ROOT / "docs" / "DECISIONES.md").read_text(encoding="utf-8").splitlines() if l.startswith("**D109 · "))
    assert "docs/usuarios/sesiones_simuladas/" in d109 and "origen = simulada" in d109 and BANNER in d109 and "Pendiente de Daniel" not in d109
    parte_d = (USUARIOS / "guia_simulacion" / "05_parte_d_que_anotar.md").read_text(encoding="utf-8")
    assert "Si la sesión es una simulación" in parte_d and "origen = simulada" in parte_d and "nunca va en `sesiones_reales/`" in parte_d
