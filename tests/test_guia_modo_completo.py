"""Guardián de la guía del modo completo (`docs/instalacion/guia_modo_completo.md`): cada comando trae su bloque «Qué debe verse», marcado «visto» o «no probado», con los marcadores de enmascarado fijos y sin datos del equipo.

Por qué existe: la guía se sigue comando por comando en el equipo de otra persona, y un comando sin su salida esperada obliga a adivinar si lo que se ve está bien. Además quien la escribe podría copiar sin querer una ruta con el nombre de usuario de
Windows o el valor de una contraseña. Aquí se comprueba, sin Docker ni MySQL: que cada bloque de comando tenga exactamente un comando y le siga su bloque de salida con su marca; que los marcadores sean solo `<usuario>`, `<ruta>`, `<ID>`, `<PID>`, `<hash>` y
`<contraseña>`; que no aparezcan rutas locales ni valores de `.env` (se busca con el escáner de secretos y, si existe un `.env`, con sus valores como canario); que los scripts y las opciones citados existan; que los seis tropiezos de la prueba desde el zip estén en la tabla de errores con su
mensaje; y que la guía no se dé por terminada mientras queden bloques «no probado».
Qué NO demuestra: que lo que dicen los bloques sea lo que imprime el programa hoy (eso lo comprobó quien ejecutó cada comando y quedó en la evidencia), ni que la guía se entienda.
"""
import re

import pytest

from src.common import ROOT
from test_configurar_mysql import esc

GUIA = ROOT / "docs" / "instalacion" / "guia_modo_completo.md"
MARCADORES = {"<usuario>", "<ruta>", "<ID>", "<PID>", "<hash>", "<contraseña>"}
PENDIENTE = "<pendiente: se copia de la prueba desde el zip>"
ETIQUETA = re.compile(r"\*\*Qué (?:debe verse|se ve)[^*]*\((visto|no probado)\):\*\*\s*$")
SECCIONES = [f"## {n}. " for n in range(0, 13)]


def _texto():
    return GUIA.read_text(encoding="utf-8")


def bloques(texto=None):
    """[(lenguaje, contenido, línea de inicio, línea no vacía anterior, línea no vacía siguiente, líneas siguientes)] de los bloques de código del documento."""
    lineas = (texto if texto is not None else _texto()).split("\n")
    salida, i = [], 0
    while i < len(lineas):
        if lineas[i].startswith("```"):
            lenguaje, ini = lineas[i][3:].strip(), i
            i += 1
            cuerpo = []
            while i < len(lineas) and not lineas[i].startswith("```"):
                cuerpo.append(lineas[i])
                i += 1
            anterior = next((l for l in reversed(lineas[:ini]) if l.strip()), "")
            siguientes = [l for l in lineas[i + 1:i + 6] if l.strip()][:3]
            salida.append((lenguaje, "\n".join(cuerpo), ini + 1, anterior, siguientes))
        i += 1
    return salida


def _comandos():
    return [b for b in bloques() if b[0] == "powershell"]


def _salidas():
    return [b for b in bloques() if b[0] == "text"]


def test_cada_bloque_de_comando_tiene_un_solo_comando_y_le_sigue_su_bloque_que_debe_verse():
    todos = bloques()
    assert len(_comandos()) >= 30, "la guía debería traer al menos treinta comandos"
    for k, (lenguaje, cuerpo, linea, _, _) in enumerate(todos):
        if lenguaje != "powershell":
            continue
        comandos = [l for l in cuerpo.splitlines() if l.strip() and not l.strip().startswith("#")]
        assert len(comandos) == 1, f"línea {linea}: un bloque debe traer un solo comando"
        assert k + 1 < len(todos) and todos[k + 1][0] == "text", f"línea {linea}: al comando le falta su bloque «Qué debe verse»: {comandos[0][:60]}"


def test_todo_bloque_de_salida_lleva_su_etiqueta_con_la_marca_visto_o_no_probado():
    for lenguaje, cuerpo, linea, anterior, _ in _salidas():
        assert ETIQUETA.search(anterior), f"línea {linea}: el bloque de salida no tiene su etiqueta «Qué debe verse (visto|no probado):» justo antes"


def test_los_bloques_vistos_dicen_que_varia_y_cuanto_tardaron_y_no_traen_pendientes():
    for lenguaje, cuerpo, linea, anterior, siguientes in _salidas():
        marca = ETIQUETA.search(anterior).group(1)
        if marca == "visto":
            assert PENDIENTE not in cuerpo, f"línea {linea}: un bloque «visto» no puede traer el texto pendiente"
            texto = " ".join(siguientes)
            assert "**Varía:**" in texto and "**Tiempo:**" in texto, f"línea {linea}: un bloque «visto» debe decir qué varía y cuánto tardó"
        else:
            assert PENDIENTE in cuerpo, f"línea {linea}: un bloque «no probado» solo trae el texto pendiente"


def test_los_marcadores_de_enmascarado_son_solo_los_seis_fijos():
    for lenguaje, cuerpo, linea, _, _ in _salidas():
        for m in re.findall(r"<[^<>\n]+>", cuerpo):
            assert m in MARCADORES or m == PENDIENTE, f"línea {linea}: marcador no permitido {m}"


def test_la_guia_no_trae_rutas_del_equipo_ni_nombres_de_usuario_de_windows():
    texto = _texto()
    assert not re.search(r"(?i)[a-z]:\\|\\users\\|/users/|appdata|/c/|\\temp\\|onedrive", texto), "hay una ruta o un nombre de usuario del equipo"


def test_la_guia_no_trae_secretos_ni_valores_del_env():
    texto = _texto().encode("utf-8")
    assert esc.escanear_bytes("guia_modo_completo.md", texto) == []
    if (ROOT / ".env").exists():
        valores = esc.canarios(ROOT)
        assert esc._buscar_en("guia_modo_completo.md", texto, valores) == []


def _scripts_y_opciones():
    for _, cuerpo, linea, _, _ in _comandos():
        comando = next(l for l in cuerpo.splitlines() if l.strip() and not l.strip().startswith("#"))
        for ruta in re.findall(r"scripts\\[\w\\]+\.py", comando):
            yield linea, comando, ruta.replace("\\", "/")


def test_cada_script_citado_existe_y_acepta_las_opciones_que_la_guia_le_pasa():
    n = 0
    for linea, comando, ruta in _scripts_y_opciones():
        script = ROOT / ruta
        assert script.is_file(), f"línea {linea}: no existe {ruta}"
        fuente = script.read_text(encoding="utf-8")
        for opcion in re.findall(r"(?<![\w-])--[a-z][a-z-]+", comando):
            assert f'"{opcion}"' in fuente, f"línea {linea}: {ruta} no tiene la opción {opcion}"
            n += 1
    assert n >= 5


def test_los_comandos_son_de_una_lista_cerrada_de_programas():
    permitidos = (".\\.venv\\Scripts\\python.exe", "py -3.13", "docker ", "Set-Location", "Select-String", "(Select-String", "(Invoke-WebRequest")
    for _, cuerpo, linea, _, _ in _comandos():
        comando = next(l for l in cuerpo.splitlines() if l.strip() and not l.strip().startswith("#"))
        assert comando.startswith(permitidos), f"línea {linea}: comando fuera de la lista: {comando[:50]}"
        assert "docker compose down -v" not in comando and not re.search(r"\bdown\b.*\s-v\b", comando), "ningún comando de la guía borra volúmenes"


def test_las_secciones_estan_todas_y_en_orden():
    texto = _texto()
    posiciones = [texto.find("\n" + s) for s in SECCIONES]
    assert all(p >= 0 for p in posiciones) and posiciones == sorted(posiciones)


def test_la_tabla_de_errores_trae_los_seis_tropiezos_marcados_y_ninguna_fila_sin_marca():
    texto = _texto()
    seccion = texto.split("\n## 10. ")[1].split("\n## 11. ")[0]
    filas = [l for l in seccion.splitlines() if re.match(r"\| \d+ \|", l)]
    assert len(filas) >= 8
    for f in filas:
        assert re.search(r"\((visto|deducido)\) \|\s*$", f), f"fila sin marca (visto) o (deducido): {f[:60]}"
    for mensaje in (".env no está ignorado por git o está versionado", "no configuration file provided", "Read-only file system", "password authentication failed for user airflow", "_AIRFLOW_WWW_USER_PASSWORD", "`root`"):
        assert mensaje in seccion, f"falta en la tabla de errores: {mensaje}"
    marcadas = {int(re.match(r"\| (\d+) \|", f).group(1)): re.search(r"\((visto|deducido)\)", f).group(1) for f in filas}
    assert all(marcadas[n] == "visto" for n in (1, 2, 3, 4, 5, 6)), "los seis tropiezos de la prueba desde el zip son vistos"


def test_la_guia_dice_lo_que_hay_que_decir_sobre_root_las_cuentas_la_limitacion_y_down_v():
    texto = _texto()
    for frase in ("fuera de cualquier repositorio de Git", "no la palabra `root`", "Contraseña del administrador de MySQL (root); no se muestra al escribir:", "sismo_etl", "sismo_airflow", "sismo_lectura",
                  "`docker compose down -v`", "--nombre-compose", "**cada cuenta tiene una sola contraseña vigente**", "deducida", "Set-Location ..\\airflow-medallon"):
        assert frase in texto, f"falta en la guía: {frase}"
    assert "cambian las contraseñas de `sismo_etl`, `sismo_airflow` y `sismo_lectura`" in texto


def test_la_guia_no_se_da_por_terminada_mientras_quedan_bloques_no_probados():
    texto = _texto()
    marcas = [ETIQUETA.search(a).group(1) for _, _, _, a, _ in _salidas()]
    assert len(marcas) == len(_salidas()) and set(marcas) <= {"visto", "no probado"}
    if "**Estado:** borrador" not in texto:
        assert "no probado" not in marcas, "la guía ya no dice «borrador» pero quedan bloques sin probar"
        assert re.search(r"\*\*Evidencia:\*\* \[EV-\d{3}\]", texto), "una guía terminada cita la evidencia de la prueba desde el zip"
    else:
        assert marcas.count("no probado") >= 0


def test_la_guia_esta_enlazada_desde_el_modo_completo_y_desde_el_indice_de_instalacion():
    assert "guia_modo_completo.md" in (ROOT / "docs" / "instalacion" / "modo_completo.md").read_text(encoding="utf-8")
    assert "guia_modo_completo.md" in (ROOT / "docs" / "instalacion" / "README.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("cambio, pieza", [
    (lambda t: t.replace("```powershell\ndocker ps\n```\n**Qué debe verse (no probado):**\n```text\n" + PENDIENTE + "\n```\n", "```powershell\ndocker ps\n```\n", 1), "falta su bloque"),
    (lambda t: t.replace("**Qué debe verse (no probado):**", "**Qué debe verse:**", 1), "etiqueta"),
    (lambda t: t.replace(PENDIENTE, "<ruta secreta>", 1), "marcador"),
    (lambda t: t.replace(PENDIENTE, "C:\\Users\\alguien\\proyecto", 1), "ruta"),
], ids=["comando sin salida", "etiqueta sin marca", "marcador inventado", "ruta del equipo"])
def test_negativa_la_comprobacion_detecta_cada_clase_de_defecto(cambio, pieza):
    """Aplica el defecto a una copia del texto y comprueba que las reglas de arriba lo rechazan (las pruebas de arriba leen el archivo real; esta aplica sus mismas reglas a la copia dañada)."""
    texto = cambio(_texto())
    assert texto != _texto()
    todos = bloques(texto)
    fallos = []
    for k, (lenguaje, cuerpo, linea, anterior, _) in enumerate(todos):
        if lenguaje == "powershell" and not (k + 1 < len(todos) and todos[k + 1][0] == "text"):
            fallos.append("falta su bloque")
        if lenguaje == "text" and not ETIQUETA.search(anterior):
            fallos.append("etiqueta")
        if lenguaje == "text":
            fallos += ["marcador" for m in re.findall(r"<[^<>\n]+>", cuerpo) if m not in MARCADORES and m != PENDIENTE]
    if re.search(r"(?i)[a-z]:\\|\\users\\", texto):
        fallos.append("ruta")
    assert pieza in fallos
