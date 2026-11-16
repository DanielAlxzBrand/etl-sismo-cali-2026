"""Guardián de la guía del modo completo (`docs/instalacion/guia_modo_completo.md`): cada comando trae su «Para qué sirve» y su bloque «Qué debe verse», marcado «visto» o «no probado», con marcadores de enmascarado fijos y sin datos del equipo.

Por qué existe: la guía se sigue comando por comando en el equipo de otra persona, y un comando sin su salida esperada obliga a adivinar si lo que se ve está bien. Además, quien la escribe podría copiar sin querer una ruta con el nombre de usuario de
Windows, el valor de una contraseña o una afirmación que el código ya no cumple. Aquí se comprueba, sin Docker ni MySQL, que: cada bloque de comando traiga un solo comando, su «Para qué sirve» y su bloque de salida con su marca; que los marcadores sean solo
los seis fijos (y en los comandos solo `<ID>` y `<carpeta del proyecto>`, cada uno con su «Reemplace»); que no aparezcan rutas locales, valores de `.env` ni contraseñas en un comando; que todo comando que lee un `.env` termine copiando al portapapeles y que a cada copia le siga su limpieza;
que el número de comandos que dice la guía salga de contarlos; que los scripts, las opciones, los enlaces y las afirmaciones sobre el código (variables, rutas de salud, DAG en pausa, cuatro tareas, `--modo completo`, el comando de `airflow-init`) sigan siendo ciertos; que los
tropiezos de la prueba desde el zip estén en la tabla de errores; y que la guía no se dé por terminada mientras queden bloques «no probado» ni sin la evidencia de su prueba en el manifiesto.
Cada regla es una función de texto que devuelve sus problemas: las pruebas la aplican al archivo real y las pruebas negativas, al mismo texto dañado a propósito, de modo que no hay reglas duplicadas.
Qué NO demuestra: que lo que dicen los bloques sea lo que imprime el programa hoy (eso lo comprobó quien ejecutó cada comando y quedó en la evidencia), ni que la guía se entienda.
"""
import hashlib
import posixpath
import re

import pytest

from src.common import ROOT
from test_configurar_mysql import esc

GUIA = ROOT / "docs" / "instalacion" / "guia_modo_completo.md"
CARPETA_GUIA = "docs/instalacion"
MANIFIESTO = "docs/evidencias/manifiesto.md"
MARCADORES = {"<usuario>", "<ruta>", "<ID>", "<PID>", "<hash>", "<contraseña>"}
TEXTO_DEL_PROGRAMA = {"<otro nombre>"}   # lo imprime el propio programa (preparar_airflow.py sugiere «--nombre-compose <otro nombre>»); no es un dato enmascarado
MARCADORES_EN_COMANDOS ={"<ID>", "<carpeta del proyecto>"}
PENDIENTE = "<pendiente: se copia de la prueba desde el zip>"
SIN_SALIDA = "(sin salida)"
LIMPIAR = "Set-Clipboard -Value $null"
ETIQUETA = re.compile(r"\*\*Qué (?:debe verse|se ve)[^*]*\((visto|no probado)\):\*\*\s*$")
SECCIONES = [f"## {n}. " for n in range(0, 13)]
PROGRAMAS = (".\\.venv\\Scripts\\python.exe", "py -3.13", "docker ", "Set-Location", "Select-String", "(Select-String", "(Invoke-WebRequest", "Set-Clipboard")
RUTA_DEL_EQUIPO = re.compile(r"(?i)[a-z]:\\|\\users\\|/users/|appdata|/c/|\\temp\\")   # a propósito sin «OneDrive»: advertir de esa carpeta no es una ruta del equipo
CONTRASENA_EN_COMANDO = re.compile(r"--password|(?<![\w-])-p\S|MYSQL_PWD")
LEE_ENV = re.compile(r"(?<![\w.\\])\.env(?![\w.])")
COPIA_AL_PORTAPAPELES = re.compile(r"\|\s*Set-Clipboard$")
CONTEO = re.compile(r"trae \*\*(\d+) comandos\*\*: \*\*(\d+)\*\* con su salida vista y \*\*(\d+)\*\* sin probar")
FRASES = ("fuera de cualquier repositorio de Git", "fuera de carpetas sincronizadas con OneDrive", "no la palabra `root`", "Contraseña del administrador de MySQL (root); no se muestra al escribir:", "sismo_etl", "sismo_airflow", "sismo_lectura",
          "`docker compose down -v`", "--nombre-compose", "**cada cuenta tiene una sola contraseña vigente**", "deducida", "Set-Location ..\\airflow-medallon", "cambian las contraseñas de `sismo_etl`, `sismo_airflow` y `sismo_lectura`",
          LIMPIAR, "1.970 MiB", "8 GB de RAM", "no trae pasos para instalarlos", "no garantiza una base correcta", "docker compose ps -a", "**Reemplace", "Orden de los pasos",
          "no es una señal fiable", "con todo «(healthy)» y el código de salida de `docker compose up -d` (0)", "/entrypoint airflow db check", "siempre a través de `/entrypoint`")
PROHIBIDAS = (r"(?<!no )garantiza una base correcta",)


def _texto():
    return GUIA.read_text(encoding="utf-8")


def leer(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def leer_bytes(rel):
    return (ROOT / rel).read_bytes()


def bloques(texto):
    """[(lenguaje, contenido, línea de inicio, línea no vacía anterior, tres líneas no vacías siguientes)] de los bloques de código del documento."""
    lineas = texto.split("\n")
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


def _comando(cuerpo):
    return next((l.strip() for l in cuerpo.splitlines() if l.strip() and not l.strip().startswith("#")), "")


def _comandos(texto):
    return [(linea, _comando(cuerpo), anterior, siguientes) for lenguaje, cuerpo, linea, anterior, siguientes in bloques(texto) if lenguaje == "powershell"]


def _salidas(texto):
    return [(linea, cuerpo, anterior, siguientes) for lenguaje, cuerpo, linea, anterior, siguientes in bloques(texto) if lenguaje == "text"]


def _marca(anterior):
    m = ETIQUETA.search(anterior)
    return m.group(1) if m else None


def _exigir(problemas):
    """Falla con el listado de problemas y nada más: así un valor del `.env` nunca llega al mensaje de pytest."""
    __tracebackhide__ = True
    if problemas:
        raise AssertionError("\n".join(problemas))


# ---------------------------------------------------------------- reglas: cada una recibe el texto y devuelve sus problemas

def p_estructura(texto):
    todos = bloques(texto)
    out = []
    for k, (lenguaje, cuerpo, linea, _, _) in enumerate(todos):
        if lenguaje != "powershell":
            continue
        if len([l for l in cuerpo.splitlines() if l.strip() and not l.strip().startswith("#")]) != 1:
            out.append(f"línea {linea}: un bloque debe traer un solo comando")
        if not (k + 1 < len(todos) and todos[k + 1][0] == "text"):
            out.append(f"línea {linea}: al comando le falta su bloque «Qué debe verse»: {_comando(cuerpo)[:60]}")
    return out


def p_etiquetas(texto):
    return [f"línea {linea}: el bloque de salida no tiene su etiqueta «Qué debe verse (visto|no probado):» justo antes" for linea, _, anterior, _ in _salidas(texto) if _marca(anterior) is None]


def p_salidas(texto):
    out = []
    for linea, cuerpo, anterior, siguientes in _salidas(texto):
        marca = _marca(anterior)
        if marca is None:
            continue   # lo reporta p_etiquetas
        if marca == "visto":
            if PENDIENTE in cuerpo:
                out.append(f"línea {linea}: un bloque «visto» no puede traer el texto pendiente")
            elif not cuerpo.strip():
                out.append(f"línea {linea}: un bloque «visto» no puede estar vacío")
            elif cuerpo.strip() != SIN_SALIDA:
                resto = " ".join(siguientes)
                if "**Varía:**" not in resto or "**Tiempo:**" not in resto:
                    out.append(f"línea {linea}: un bloque «visto» con salida debe decir qué varía y cuánto tardó")
        elif cuerpo.strip() != PENDIENTE:
            out.append(f"línea {linea}: un bloque «no probado» solo trae el texto pendiente")
    return out


def p_marcadores(texto):
    out = []
    for linea, cuerpo, _, _ in _salidas(texto):
        out += [f"línea {linea}: marcador no permitido en una salida: {m}" for m in re.findall(r"<[^<>\n]+>", cuerpo) if m not in MARCADORES and m not in TEXTO_DEL_PROGRAMA and m != PENDIENTE]
    for linea, comando, _, _ in _comandos(texto):
        out += [f"línea {linea}: marcador no permitido en un comando: {m}" for m in re.findall(r"<[^<>\n]+>", comando) if m not in MARCADORES_EN_COMANDOS]
    return out


def p_rutas(texto):
    return [f"línea {n}: ruta o nombre de usuario del equipo" for n, l in enumerate(texto.splitlines(), 1) if RUTA_DEL_EQUIPO.search(l)]


def p_secretos(texto, raiz):
    """Hallazgos del escáner de secretos y, si hay `.env`, de sus valores como canario. Solo devuelve línea y nombre del patrón o de la variable, nunca un valor."""
    datos = texto.encode("utf-8")
    hallazgos = esc.escanear_bytes("guia_modo_completo.md", datos)
    if (raiz / ".env").exists():
        hallazgos += esc._buscar_en("guia_modo_completo.md", datos, esc.canarios(raiz))
    return [f"línea {n}: {patron}" for _, n, patron in hallazgos]


def p_contrasenas_en_comandos(texto):
    return [f"línea {linea}: el comando lleva una contraseña: {c[:25]}" for linea, c, _, _ in _comandos(texto) if CONTRASENA_EN_COMANDO.search(c)]


def p_env_al_portapapeles(texto):
    return [f"línea {linea}: el comando lee un .env y no termina copiando al portapapeles: {c[:40]}" for linea, c, _, _ in _comandos(texto) if LEE_ENV.search(c) and not COPIA_AL_PORTAPAPELES.search(c)]


def p_portapapeles_limpio(texto):
    cmds = _comandos(texto)
    return [f"línea {linea}: tras copiar al portapapeles falta el comando que lo limpia ({LIMPIAR})" for i, (linea, c, _, _) in enumerate(cmds)
            if COPIA_AL_PORTAPAPELES.search(c) and (cmds[i + 1][1] if i + 1 < len(cmds) else "") != LIMPIAR]


def p_para_que_sirve(texto):
    return [f"línea {linea}: falta la línea «**Para qué sirve:**» justo antes del comando" for linea, _, anterior, _ in _comandos(texto) if not anterior.startswith("**Para qué sirve:**")]


def p_reemplace(texto):
    out = []
    for linea, comando, _, siguientes in _comandos(texto):
        resto = " ".join(siguientes)
        for m in sorted(set(re.findall(r"<[^<>\n]+>", comando))):
            if "Reemplace" not in resto or f"`{m}`" not in resto:
                out.append(f"línea {linea}: el comando trae {m} y debajo no dice «Reemplace `{m}`»")
    return out


def p_conteo(texto):
    todos = bloques(texto)
    total = visto = sin_probar = 0
    for k, (lenguaje, _, _, _, _) in enumerate(todos):
        if lenguaje != "powershell":
            continue
        total += 1
        marca = _marca(todos[k + 1][3]) if k + 1 < len(todos) and todos[k + 1][0] == "text" else None
        visto += marca == "visto"
        sin_probar += marca == "no probado"
    dicho = CONTEO.search(texto)
    if not dicho:
        return ["la guía no dice cuántos comandos trae con la forma «trae **N comandos**: **V** con su salida vista y **P** sin probar»"]
    real = (total, visto, sin_probar)
    return [] if tuple(int(x) for x in dicho.groups()) == real and visto + sin_probar == total else [f"la guía dice {dicho.groups()} y el conteo automático da {real} (comandos, vistos, sin probar)"]


def p_scripts_y_opciones(texto, leer_fuente):
    citas = [(linea, c) for linea, c, _, _ in _comandos(texto)]
    citas += [(n, span) for n, l in enumerate(texto.splitlines(), 1) for span in re.findall(r"`([^`\n]+)`", l) if "scripts\\" in span]
    out = []
    for linea, cita in citas:
        for ruta in re.findall(r"scripts\\[\w\\]+\.py", cita):
            rel = ruta.replace("\\", "/")
            try:
                fuente = leer_fuente(rel)
            except FileNotFoundError:
                out.append(f"línea {linea}: no existe {rel}")
                continue
            out += [f"línea {linea}: {rel} no tiene la opción {o}" for o in re.findall(r"(?<![\w-])--[a-z][a-z-]+", cita) if f'"{o}"' not in fuente]
    return out


def p_db_check_solo_con_entrypoint(texto):
    """`airflow db check` no se recomienda suelto: ningún comando de la guía lo trae y toda mención en la prosa es `/entrypoint airflow db check`."""
    out = [f"línea {linea}: el comando ejecuta airflow db check suelto: {c[:50]}" for linea, c, _, _ in _comandos(texto) if "db check" in c]
    return out + [f"línea {n}: «airflow db check» sin /entrypoint delante" for n, l in enumerate(texto.splitlines(), 1) if re.search(r"(?<!/entrypoint )airflow db check", l)]


def p_programas(texto):
    out = [f"línea {linea}: comando fuera de la lista: {c[:50]}" for linea, c, _, _ in _comandos(texto) if not c.startswith(PROGRAMAS)]
    return out + [f"línea {linea}: ningún comando de la guía borra volúmenes" for linea, c, _, _ in _comandos(texto) if re.search(r"\bdown\b.*\s-v\b", c)]


def p_secciones(texto):
    posiciones = [texto.find("\n" + s) for s in SECCIONES]
    return [] if all(p >= 0 for p in posiciones) and posiciones == sorted(posiciones) else ["faltan secciones o no están en orden 0 a 12"]


def p_errores(texto):
    if "\n## 10. " not in texto or "\n## 11. " not in texto:
        return ["falta la sección 10 o la 11"]
    seccion = texto.split("\n## 10. ")[1].split("\n## 11. ")[0]
    filas = [l for l in seccion.splitlines() if re.match(r"\| \d+ \|", l)]
    out = [] if len(filas) >= 8 else ["la tabla de errores debe tener al menos ocho filas"]
    out += [f"fila sin marca (visto) o (deducido): {f[:60]}" for f in filas if not re.search(r"\((visto|deducido)\) \|\s*$", f)]
    out += [f"falta en la tabla de errores: {m}" for m in (".env no está ignorado por git o está versionado", "no configuration file provided", "Read-only file system", "password authentication failed for user airflow", "_AIRFLOW_WWW_USER_PASSWORD", "`root`") if m not in seccion]
    marcadas = {int(re.match(r"\| (\d+) \|", f).group(1)): re.search(r"\((visto|deducido)\)", f).group(1) for f in filas if re.search(r"\((visto|deducido)\)", f)}
    out += [f"el tropiezo {n} de la prueba desde el zip debe ser (visto)" for n in (1, 2, 3, 4, 5, 6) if marcadas.get(n) != "visto"]
    return out


def p_frases(texto):
    return [f"falta en la guía: {f}" for f in FRASES if f not in texto] + [f"no debe decir: {p}" for p in PROHIBIDAS if re.search(p, texto)]


def p_borrador(texto):
    marcas = [_marca(a) for _, _, a, _ in _salidas(texto)]
    sin_probar = "no probado" in marcas
    borrador = "**Estado:** borrador" in texto
    if borrador and not sin_probar:
        return ["la guía dice «borrador» pero ya no queda ningún bloque «no probado»: debe pasar a terminada"]
    if not borrador and sin_probar:
        return ["la guía ya no dice «borrador» pero quedan bloques «no probado»"]
    return []


def p_evidencia(texto, leer_texto, leer_binario):
    """Una guía terminada cita la evidencia de su prueba y esa evidencia está en el manifiesto con el sha256 del archivo."""
    if "**Estado:** borrador" in texto:
        return []
    citada = re.search(r"\*\*Evidencia:\*\* \[(EV-\d{3})\]", texto)
    if not citada:
        return ["una guía terminada cita la evidencia de la prueba desde el zip («**Evidencia:** [EV-nnn]»)"]
    fila = next((l for l in leer_texto(MANIFIESTO).splitlines() if l.startswith(f"| {citada.group(1)} |")), None)
    if fila is None:
        return [f"{citada.group(1)} no está en el manifiesto"]
    celdas = [c.strip() for c in fila.strip().strip("|").split("|")]
    ruta, sha = celdas[-2], celdas[-1]
    try:
        real = hashlib.sha256(leer_binario(ruta)).hexdigest()
    except FileNotFoundError:
        return [f"{citada.group(1)}: no existe el archivo {ruta}"]
    return [] if real == sha else [f"{citada.group(1)}: el sha256 del manifiesto no coincide con el del archivo {ruta}"]


def _ancla(titulo):
    return re.sub(r"[^\w\- ]", "", titulo.lower()).replace(" ", "-")


def p_enlaces(texto, leer_fuente):
    out = []
    for n, l in enumerate(texto.splitlines(), 1):
        for destino in re.findall(r"\]\(([^)\s]+)\)", l):
            if destino.startswith(("http:", "https:", "mailto:")):
                continue
            ruta, _, ancla = destino.partition("#")
            rel = posixpath.normpath(posixpath.join(CARPETA_GUIA, ruta)) if ruta else f"{CARPETA_GUIA}/guia_modo_completo.md"
            try:
                fuente = leer_fuente(rel)
            except (FileNotFoundError, OSError):
                out.append(f"línea {n}: el enlace {destino} no lleva a un archivo")
                continue
            if ancla and ancla not in {_ancla(t) for t in re.findall(r"^#{1,6} (.+)$", fuente, flags=re.M)}:
                out.append(f"línea {n}: el enlace {destino} no lleva a un título")
    return out


def _servicio_y_script_de_init(compose):
    """(servicio airflow-init completo, solo el script de su `command`)."""
    servicio = compose.split("\n  airflow-init:\n")[-1].split("\n  airflow-cli:")[0]
    return servicio, servicio.split("# yamllint enable")[0]


def p_afirmaciones(texto, leer_fuente):
    """Cada afirmación de la prosa sobre el código se comprueba contra el código."""
    out = []
    compose = leer_fuente("orquestacion/docker-compose.yaml")
    dag = leer_fuente("dags/medallon_etl_dag.py")

    def exige(afirmacion, cumple):
        if not cumple:
            out.append(f"afirmación sin respaldo en el código: {afirmacion}")

    if "MYSQL_LECTURA_PASSWORD" in texto:
        exige("MYSQL_LECTURA_PASSWORD", re.search(r'NOMBRES_ENV_LECTURA\s*=\s*\([^)]*"MYSQL_LECTURA_PASSWORD"', leer_fuente("scripts/mysql/configurar_mysql.py")))
    if "/api/v2/monitor/health" in texto:
        exige("/api/v2/monitor/health", "http://localhost:8080/api/v2/monitor/health" in compose)
    if "Nace en pausa" in texto:
        exige("el DAG nace en pausa", "AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'" in compose)
    if "--modo completo" in texto:
        fuente = leer_fuente("scripts/preparar_entorno.py")
        exige("--modo completo", 'MINIMO, COMPLETO = "minimo", "completo"' in fuente and "AMBOS = (MINIMO, COMPLETO)" in fuente and '"--modo", choices=AMBOS' in fuente)
    if "EV-040" in texto:
        exige("el origen localhost medido en EV-040", "**`localhost`**" in leer_fuente("docs/evidencias/orquestacion/EV-040_origen_mysql_desde_docker.txt"))
    if "no usa `set -e`" in texto:
        servicio, script = _servicio_y_script_de_init(compose)
        ultimo = [l.strip() for l in script.splitlines() if l.strip() and not l.strip().startswith("#")]
        exige("el comando de airflow-init no usa set -e", "set -e" not in script)
        exige("el último comando de airflow-init es un ls", bool(ultimo) and ultimo[-1].startswith("ls "))
        exige("airflow-init activa la migración y la creación del usuario", "_AIRFLOW_DB_MIGRATE: 'true'" in servicio and "_AIRFLOW_WWW_USER_CREATE: 'true'" in servicio)
    if "airflow db check" in texto:
        script = _servicio_y_script_de_init(compose)[1]
        exige("airflow-init comprueba la conexión con airflow db check y termina con exit 1 si falla", "if /entrypoint airflow db check" in script and "exit 1" in script)
    if "`medallon_etl_sismo`" in texto:
        exige("el DAG medallon_etl_sismo", 'dag_id="medallon_etl_sismo"' in dag)
        exige("el DAG corre a las 06:00 hora de Bogotá", 'schedule="0 6 * * *"' in dag and "America/Bogota" in dag)
        posiciones = [dag.find(f"def {t}(") for t in ("validar_bronze", "transformar_a_silver", "integrar_a_gold", "cargar_datawarehouse")]
        exige("las cuatro tareas del DAG, en ese orden", all(p >= 0 for p in posiciones) and posiciones == sorted(posiciones))
    if "usuario es **`airflow`**" in texto:
        exige("el usuario de la interfaz es airflow", "_AIRFLOW_WWW_USER_USERNAME:-airflow}" in compose)
    if "_AIRFLOW_WWW_USER_PASSWORD" in texto:
        exige("_AIRFLOW_WWW_USER_PASSWORD", "_AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD" in compose)
    if "8081" in texto:
        exige("phpMyAdmin en el puerto 8081", "${PMA_PUERTO:-8081}" in leer_fuente("servicios/phpmyadmin/docker-compose.yaml"))
    if "kpi_sensibilidad" in texto:
        exige("las siete tablas de sismo_cali", "barrio_estrato, comuna, construccion, corrida, corrida_archivo, kpi, kpi_sensibilidad" in leer_fuente("docs/evidencias/servicios/EV-085_phpmyadmin_en_vivo.txt"))
    if "#1142" in texto:
        exige("el rechazo #1142 de la escritura", "#1142" in leer_fuente("docs/evidencias/servicios/EV-085_phpmyadmin_en_vivo.txt"))
    if "1.970 MiB" in texto:
        exige("1.970 MiB de memoria en reposo", "1.970 MiB" in leer_fuente("docs/instalacion/README.md"))
    return out


REGLAS = {
    "estructura": p_estructura,
    "etiquetas": p_etiquetas,
    "salidas": p_salidas,
    "marcadores": p_marcadores,
    "rutas": p_rutas,
    "secretos": lambda t: p_secretos(t, ROOT),
    "contraseñas en comandos": p_contrasenas_en_comandos,
    "env al portapapeles": p_env_al_portapapeles,
    "portapapeles limpio": p_portapapeles_limpio,
    "para qué sirve": p_para_que_sirve,
    "reemplace": p_reemplace,
    "conteo": p_conteo,
    "scripts y opciones": lambda t: p_scripts_y_opciones(t, leer),
    "programas": p_programas,
    "db check solo con entrypoint": p_db_check_solo_con_entrypoint,
    "secciones": p_secciones,
    "errores": p_errores,
    "frases": p_frases,
    "borrador": p_borrador,
    "evidencia": lambda t: p_evidencia(t, leer, leer_bytes),
    "enlaces": lambda t: p_enlaces(t, leer),
    "afirmaciones": lambda t: p_afirmaciones(t, leer),
}


# ---------------------------------------------------------------- pruebas sobre el archivo real

@pytest.mark.parametrize("regla", list(REGLAS))
def test_la_guia_cumple_la_regla(regla):
    _exigir(REGLAS[regla](_texto()))


def test_la_guia_trae_al_menos_treinta_comandos_y_cada_script_citado_cuenta_sus_opciones():
    assert len(_comandos(_texto())) >= 30, "la guía debería traer al menos treinta comandos"
    opciones = [o for _, c, _, _ in _comandos(_texto()) if "scripts\\" in c for o in re.findall(r"(?<![\w-])--[a-z][a-z-]+", c)]
    assert len(opciones) >= 5


def test_advertir_de_onedrive_no_cuenta_como_ruta_del_equipo():
    assert "OneDrive" in _texto() and p_rutas(_texto() + "\nNo use carpetas de OneDrive.\n") == []


def test_los_bloques_vistos_sin_salida_se_admiten_sin_varia_ni_tiempo():
    texto = re.sub(r"\*\*Varía:[^\n]*\n\*\*Tiempo:[^\n]*\n", "", _en_la_primera_salida_vista(_texto(), SIN_SALIDA), count=1)
    assert texto != _texto() and p_salidas(texto) == []


def test_la_guia_esta_enlazada_desde_el_modo_completo_y_desde_el_indice_de_instalacion():
    assert "guia_modo_completo.md" in leer("docs/instalacion/modo_completo.md")
    assert "guia_modo_completo.md" in leer("docs/instalacion/README.md")


def _terminada(texto):
    """La misma guía con todo «visto» y sin «borrador», como quedaría al terminar la prueba desde el zip."""
    return re.sub(r"\(no probado\):\*\*", "(visto):**", texto).replace(PENDIENTE, SIN_SALIDA).replace("**Estado:** borrador", "**Estado:** terminada")


def test_una_guia_terminada_cita_su_evidencia_y_el_manifiesto_trae_el_sha256_del_archivo():
    contenido = b"salida de la prueba"
    sha = hashlib.sha256(contenido).hexdigest()
    ruta = "docs/evidencias/modo_completo/EV-900_prueba.txt"
    texto = _terminada(_texto()).replace("**Estado:** terminada", "**Estado:** terminada · **Evidencia:** [EV-900](../evidencias/modo_completo/EV-900_prueba.txt)", 1)
    fila = f"| EV-900 | 1.1 | descripción | archivo | comando | 2026-11-16 | {ruta} | {{}} |"

    def con(manifiesto, binario=lambda rel: contenido):
        return p_evidencia(texto, lambda rel: manifiesto, binario)

    assert con(fila.format(sha)) == []
    assert "sha256" in " ".join(con(fila.format("0" * 64)))
    assert "no está en el manifiesto" in " ".join(con("| EV-901 | x | x | x | x | x | a | b |"))
    assert "no existe el archivo" in " ".join(con(fila.format(sha), binario=lambda rel: (_ for _ in ()).throw(FileNotFoundError(rel))))
    assert "cita la evidencia" in " ".join(p_evidencia(_terminada(_texto()), leer, leer_bytes))


def test_la_guia_terminada_con_un_bloque_sin_probar_o_borrador_sin_pendientes_se_rechaza():
    assert "ya no dice «borrador»" in " ".join(p_borrador(_texto().replace("**Estado:** borrador", "**Estado:** terminada")))
    assert "debe pasar a terminada" in " ".join(p_borrador(re.sub(r"\(no probado\):\*\*", "(visto):**", _texto()).replace(PENDIENTE, SIN_SALIDA)))


def test_un_valor_del_env_en_la_guia_se_detecta_sin_imprimirlo_en_el_mensaje(tmp_path):
    valor = "Valor_de_prueba_ZQ81xk"
    variable = "MYSQL_" + "PASSWORD"   # partida: así el escáner de secretos no ve una asignación en este archivo
    (tmp_path / ".env").write_text(f"{variable}={valor}\n", encoding="utf-8")
    problemas = p_secretos(_texto() + f"\nclave: {valor}\n", tmp_path)
    assert any("canario:MYSQL_PASSWORD" in p for p in problemas)
    assert not any(valor in p for p in problemas)
    with pytest.raises(AssertionError) as error:
        _exigir(problemas)
    assert valor not in str(error.value) and "canario:MYSQL_PASSWORD" in str(error.value)
    assert p_secretos(_texto(), tmp_path) == []


# ---------------------------------------------------------------- pruebas negativas: el mismo texto, dañado a propósito, debe ser rechazado por la regla que le corresponde

def _reemplaza(antes, despues, veces=1):   # veces=-1: todas las apariciones
    def cambio(t):
        assert antes in t, f"el texto a dañar no está en la guía: {antes[:50]!r}"
        return t.replace(antes, despues, veces)
    return cambio


def _en_la_primera_salida_vista(t, cuerpo):
    return re.sub(r"(\*\*Qué debe verse \(visto\):\*\*\n```text\n).*?(\n```)", lambda m: m[1] + cuerpo + m[2], t, count=1, flags=re.S)


def _sin_bloque_de_salida_de_docker_ps(t):
    """Quita, tras el primer `docker ps`, su etiqueta, su bloque de salida y sus líneas «Varía» y «Tiempo»."""
    return re.sub(r"(```powershell\ndocker ps\n```\n)\*\*Qué debe verse \(visto\):\*\*\n```text\n.*?\n```\n\*\*Varía:[^\n]*\n\*\*Tiempo:[^\n]*\n", r"\1", t, count=1, flags=re.S)


NEGATIVAS = [
    ("estructura", "comando sin salida", _sin_bloque_de_salida_de_docker_ps, "falta su bloque"),
    ("estructura", "dos comandos en un bloque", _reemplaza("```powershell\ndocker ps\n```", "```powershell\ndocker ps\ndocker ps\n```"), "un solo comando"),
    ("etiquetas", "etiqueta sin marca", _reemplaza("**Qué debe verse (visto):**", "**Qué debe verse:**"), "no tiene su etiqueta"),
    ("salidas", "visto con texto pendiente", lambda t: _en_la_primera_salida_vista(t, PENDIENTE), "no puede traer el texto pendiente"),
    ("salidas", "visto con salida sin varía ni tiempo", lambda t: re.sub(r"\*\*Varía:[^\n]*\n\*\*Tiempo:[^\n]*\n", "", t, count=1), "qué varía"),
    ("salidas", "visto vacío", lambda t: _en_la_primera_salida_vista(t, ""), "vacío"),
    ("salidas", "no probado con salida inventada", _reemplaza(PENDIENTE, "salida inventada"), "solo trae el texto pendiente"),
    ("salidas", "no probado con «(sin salida)»", _reemplaza(PENDIENTE, SIN_SALIDA), "solo trae el texto pendiente"),
    ("marcadores", "marcador inventado en una salida", _reemplaza(PENDIENTE, "<ruta secreta>"), "marcador no permitido en una salida"),
    ("marcadores", "marcador inventado en un comando", _reemplaza("airflow tasks states-for-dag-run medallon_etl_sismo <ID>", "airflow tasks states-for-dag-run medallon_etl_sismo <otro>"), "marcador no permitido en un comando"),
    ("rutas", "ruta de Windows", _reemplaza(PENDIENTE, "C:\\Users\\alguien\\proyecto"), "ruta o nombre de usuario"),
    ("rutas", "carpeta AppData", _reemplaza(PENDIENTE, "<ruta>\\AppData\\Local"), "ruta o nombre de usuario"),
    ("contraseñas en comandos", "--password en un comando", _reemplaza("scripts\\mysql\\configurar_mysql.py --solo-verificar", "scripts\\mysql\\configurar_mysql.py --solo-verificar --password x"), "lleva una contraseña"),
    ("contraseñas en comandos", "-p pegado a la contraseña", _reemplaza("```powershell\ndocker compose build\n```", "```powershell\ndocker compose build -pClave123\n```"), "lleva una contraseña"),
    ("contraseñas en comandos", "MYSQL_PWD en un comando", _reemplaza("```powershell\ndocker compose build\n```", "```powershell\n$env:MYSQL_PWD='x'; docker compose build\n```"), "lleva una contraseña"),
    ("env al portapapeles", "lee el .env y no lo copia al portapapeles", _reemplaza("^_AIRFLOW_WWW_USER_PASSWORD=').Line.Split('=', 2)[1] | Set-Clipboard", "^_AIRFLOW_WWW_USER_PASSWORD=').Line.Split('=', 2)[1]"), "lee un .env"),
    ("env al portapapeles", "Get-Content del .env", _reemplaza("```powershell\ndocker compose build\n```", "```powershell\nGet-Content .env\n```"), "lee un .env"),
    ("portapapeles limpio", "no se limpia tras copiar", _reemplaza("```powershell\nSet-Clipboard -Value $null\n```", "```powershell\ndocker ps\n```"), "falta el comando que lo limpia"),
    ("para qué sirve", "comando sin «Para qué sirve»", _reemplaza("**Para qué sirve:** comprobar que los paquetes del entorno no tienen conflictos antes de usar los scripts.", "Comprobar que los paquetes del entorno no tienen conflictos."), "Para qué sirve"),
    ("reemplace", "falta «Reemplace» del ID", _reemplaza("**Reemplace `<ID>`**", "Cambie `<ID>`"), "no dice «Reemplace"),
    ("reemplace", "falta «Reemplace» de la carpeta", _reemplaza("**Reemplace `<carpeta del proyecto>`**", "Cambie `<carpeta del proyecto>`"), "no dice «Reemplace"),
    ("conteo", "número de comandos que no cuadra", _reemplaza("trae **33 comandos**", "trae **31 comandos**"), "conteo automático"),
    ("conteo", "un comando sin su bloque aunque el conteo dicho coincida", lambda t: _sin_bloque_de_salida_de_docker_ps(t).replace("**33** con su salida vista", "**32** con su salida vista"), "conteo automático"),
    ("conteo", "no dice cuántos comandos trae",_reemplaza("Esta guía trae **33 comandos**", "Esta guía trae muchos comandos"), "no dice cuántos"),
    ("scripts y opciones", "opción que el script no tiene", _reemplaza("configurar_mysql.py --solo-verificar", "configurar_mysql.py --opcion-inventada"), "no tiene la opción"),
    ("scripts y opciones", "script que no existe", _reemplaza("scripts\\orquestacion\\preparar_airflow.py --nombre-compose", "scripts\\orquestacion\\no_existe.py --nombre-compose"), "no existe"),
    ("scripts y opciones", "opción inventada en una cita de la prosa", _reemplaza("configurar_mysql.py --rotar", "configurar_mysql.py --rotar-todo"), "no tiene la opción"),
    ("programas", "programa fuera de la lista", _reemplaza("```powershell\ndocker compose build\n```", "```powershell\ncurl http://ejemplo.invalido\n```"), "fuera de la lista"),
    ("programas", "down -v en un comando", _reemplaza("```powershell\ndocker compose down\n```", "```powershell\ndocker compose down -v\n```"), "borra volúmenes"),
    ("db check solo con entrypoint", "la prosa recomienda airflow db check suelto", _reemplaza("`/entrypoint airflow db check`", "`airflow db check`"), "sin /entrypoint delante"),
    ("db check solo con entrypoint", "un comando ejecuta airflow db check suelto", _reemplaza("```powershell\ndocker compose build\n```", "```powershell\ndocker compose exec airflow-init airflow db check\n```"), "suelto"),
    ("frases", "desaparece que el código de up airflow-init no es fiable", _reemplaza("no es una señal fiable", "es una señal razonable"), "no es una señal fiable"),
    ("frases", "desaparece la señal fiable con el código de up -d", _reemplaza("y el código de salida de `docker compose up -d` (0)", ""), "código de salida de `docker compose up -d`"),
    ("secciones", "sección fuera de orden", _reemplaza("## 3. Las tres cuentas", "## 13. Las tres cuentas"), "secciones"),
    ("errores", "fila de error sin marca", _reemplaza("`Set-Location ..\\airflow-medallon` y repetir | (visto) |", "`Set-Location ..\\airflow-medallon` y repetir | |"), "sin marca"),
    ("errores", "un tropiezo de la prueba pasa a deducido", _reemplaza("`Set-Location ..\\airflow-medallon` y repetir | (visto) |", "`Set-Location ..\\airflow-medallon` y repetir | (deducido) |"), "debe ser (visto)"),
    ("errores", "falta el mensaje del chown", _reemplaza("Read-only file system", "Sistema de archivos", -1), "Read-only file system"),
    ("frases", "desaparece la advertencia de OneDrive", _reemplaza("fuera de carpetas sincronizadas con OneDrive", "en cualquier carpeta"), "OneDrive"),
    ("frases", "la guía vuelve a decir que terminar en 0 garantiza", _reemplaza("no garantiza una base correcta", "garantiza una base correcta"), "no debe decir"),
    ("frases", "desaparece la nota de memoria", _reemplaza("con 8 GB de RAM apague", "con poca memoria apague"), "8 GB de RAM"),
    ("frases", "desaparece qué hacer si falta MySQL o Docker", _reemplaza("no trae pasos para instalarlos", "trae pasos"), "no trae pasos para instalarlos"),
    ("borrador", "terminada con bloques sin probar", _reemplaza("**Estado:** borrador", "**Estado:** terminada"), "ya no dice «borrador»"),
    ("evidencia", "terminada sin evidencia", lambda t: _terminada(t), "cita la evidencia"),
    ("enlaces", "ancla que no existe", _reemplaza("modo_minimo.md#3-crear-el-entorno-e-instalar", "modo_minimo.md#9-inexistente"), "no lleva a un título"),
    ("enlaces", "archivo que no existe", _reemplaza("(errores_comunes.md)", "(errores_inexistentes.md)"), "no lleva a un archivo"),
    ("enlaces", "ancla interna que no existe", _reemplaza("(#10-si-algo-falla)", "(#10-si-algo-no-falla)"), "no lleva a un título"),
]

CODIGO = [
    ("la salud de Airflow ya no está en esa ruta", "orquestacion/docker-compose.yaml", lambda s: s.replace("/api/v2/monitor/health", "/health"), "/api/v2/monitor/health"),
    ("el DAG ya no nace en pausa", "orquestacion/docker-compose.yaml", lambda s: s.replace("DAGS_ARE_PAUSED_AT_CREATION: 'true'", "DAGS_ARE_PAUSED_AT_CREATION: 'false'"), "nace en pausa"),
    ("airflow-init gana un set -e", "orquestacion/docker-compose.yaml", lambda s: s.replace("        one_meg=1048576", "        set -e\n        one_meg=1048576", 1), "no usa set -e"),
    ("airflow-init ya no termina en ls", "orquestacion/docker-compose.yaml", lambda s: s.replace('        echo "Files in shared volumes:"\n        echo\n        ls -la /opt/airflow/{logs,dags,plugins,config}\n\n    # yamllint enable', '        echo "Listo"\n\n    # yamllint enable'), "es un ls"),
    ("airflow-init pierde la comprobación de la base", "orquestacion/docker-compose.yaml", lambda s: s.replace("if /entrypoint airflow db check > /tmp/db_check.log 2>&1; then", "if true; then"), "airflow db check"),
    ("airflow-init ya no termina con exit 1 si la base falla", "orquestacion/docker-compose.yaml", lambda s: s.replace("          exit 1\n        fi\n", "          exit 0\n        fi\n"), "airflow db check"),
    ("airflow-init ya no migra la base", "orquestacion/docker-compose.yaml", lambda s: s.replace("_AIRFLOW_DB_MIGRATE: 'true'", "_AIRFLOW_DB_MIGRATE: 'false'"), "migración"),
    ("el DAG cambia de hora", "dags/medallon_etl_dag.py", lambda s: s.replace('schedule="0 6 * * *"', 'schedule="0 7 * * *"'), "06:00"),
    ("el DAG cambia el orden de las tareas", "dags/medallon_etl_dag.py", lambda s: s.replace("def validar_bronze(", "def validar_bronze_x(", 1).replace("def cargar_datawarehouse(", "def validar_bronze(", 1).replace("def validar_bronze_x(", "def cargar_datawarehouse(", 1), "cuatro tareas"),
    ("la variable de lectura cambia de nombre", "scripts/mysql/configurar_mysql.py", lambda s: s.replace('NOMBRES_ENV_LECTURA = ("MYSQL_LECTURA_USER", "MYSQL_LECTURA_PASSWORD")', 'NOMBRES_ENV_LECTURA = ("MYSQL_LECTURA_USER", "MYSQL_LECTURA_CLAVE")'), "MYSQL_LECTURA_PASSWORD"),
    ("preparar_entorno pierde el modo completo", "scripts/preparar_entorno.py", lambda s: s.replace("AMBOS = (MINIMO, COMPLETO)", "AMBOS = (MINIMO,)"), "--modo completo"),
    ("EV-040 ya no mide localhost", "docs/evidencias/orquestacion/EV-040_origen_mysql_desde_docker.txt", lambda s: s.replace("**`localhost`**", "**otro**"), "EV-040"),
    ("phpMyAdmin cambia de puerto", "servicios/phpmyadmin/docker-compose.yaml", lambda s: s.replace("${PMA_PUERTO:-8081}", "${PMA_PUERTO:-8090}"), "8081"),
    ("EV-085 pierde una tabla", "docs/evidencias/servicios/EV-085_phpmyadmin_en_vivo.txt", lambda s: s.replace("kpi_sensibilidad", "kpi_sens"), "siete tablas"),
    ("EV-085 deja de mostrar el rechazo #1142", "docs/evidencias/servicios/EV-085_phpmyadmin_en_vivo.txt", lambda s: s.replace("#1142", "#1000"), "#1142"),
    ("el usuario de la interfaz cambia", "orquestacion/docker-compose.yaml", lambda s: s.replace("_AIRFLOW_WWW_USER_USERNAME:-airflow}", "_AIRFLOW_WWW_USER_USERNAME:-admin}"), "usuario de la interfaz"),
    ("la memoria medida cambia", "docs/instalacion/README.md", lambda s: s.replace("1.970 MiB", "2.500 MiB"), "1.970 MiB"),
]


def _leer_con(rel_cambiada, cambio):
    return lambda rel: cambio(leer(rel)) if rel == rel_cambiada else leer(rel)


@pytest.mark.parametrize("regla, caso, cambio, pieza", NEGATIVAS, ids=[f"{n[0]}: {n[1]}" for n in NEGATIVAS])
def test_negativa_la_regla_rechaza_el_texto_danado(regla, caso, cambio, pieza):
    """Aplica el defecto a una copia del texto y comprueba que la MISMA regla que revisa el archivo real lo rechaza."""
    dañado = cambio(_texto())
    assert dañado != _texto()
    assert pieza in " ".join(REGLAS[regla](dañado)), f"la regla «{regla}» no rechazó: {caso}"


@pytest.mark.parametrize("caso, rel, cambio, pieza", CODIGO, ids=[c[0] for c in CODIGO])
def test_negativa_una_afirmacion_de_la_guia_se_rechaza_cuando_el_codigo_deja_de_cumplirla(caso, rel, cambio, pieza):
    assert cambio(leer(rel)) != leer(rel)
    assert pieza in " ".join(p_afirmaciones(_texto(), _leer_con(rel, cambio))), f"la regla de afirmaciones no rechazó: {caso}"


def test_las_negativas_cubren_cada_regla_de_la_guia():
    assert {n[0] for n in NEGATIVAS} | {"afirmaciones", "secretos"} >= set(REGLAS)
