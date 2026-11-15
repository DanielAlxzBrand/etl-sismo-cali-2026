"""Los scripts de verificación en vivo movidos a `scripts/evidencias/` cumplen su forma sin necesidad de ejecutarlos (análisis estático).

Por qué existe: cuatro scripts que se escribieron durante las sesiones de trabajo (Airflow desde el zip, phpMyAdmin con la cuenta de solo lectura, el pico de memoria de la suite y el
experimento de independencia) se movieron al repositorio para que cualquiera pueda repetir esas verificaciones. Necesitan Docker, MySQL o minutos de instalación, así que la suite no
los ejecuta; esta prueba exige lo que sí se puede comprobar leyendo el código: que compilen, que expliquen qué hacen y qué no, que no traigan rutas locales, que lean y escriban texto
con codificación explícita y que nunca impriman valores de credenciales.
Qué NO demuestra: que funcionen. Su última ejecución real es la de las evidencias EV-085 (phpMyAdmin), EV-087 (Airflow desde el zip) y EV-090 (independencia), hechas con la versión de la
sesión de trabajo de la que salen; estas versiones solo se validaron de forma estática (Docker estaba apagado).
"""
import ast
import re

from src.common import ROOT

SCRIPTS = ["evidencia_airflow_desde_zip.py", "evidencia_phpmyadmin.py", "medir_memoria_suite.py", "evidencia_independencia.py"]
SECCIONES = ("Uso", "Qué hace", "Qué NO hace", "Última ejecución real")
# Las cadenas se parten para que este archivo no se detecte a sí mismo en la guardia de independencia.
RUTA_LOCAL = re.compile(r"\b[A-Z]:\\[A-Za-z]|/Us" + "ers/|C:/Us" + "ers")
NOMBRES_SECRETOS = {"clave", "usuario", "secretos", "SECRETOS", "envair", "e"}
FUNCIONES_DE_TEXTO = {"read_text", "write_text", "open"}


def _publica(nombre):
    return not nombre.startswith("_")


def _definiciones_publicas(arbol):
    """Funciones y clases públicas del módulo y los métodos públicos de sus clases (las funciones anidadas no cuentan)."""
    for nodo in arbol.body:
        if isinstance(nodo, (ast.FunctionDef, ast.ClassDef)) and _publica(nodo.name):
            yield nodo
            if isinstance(nodo, ast.ClassDef):
                yield from (m for m in nodo.body if isinstance(m, ast.FunctionDef) and _publica(m.name))


def problemas(fuente):
    """Lista de problemas de forma de un script de evidencia (vacía si cumple)."""
    try:
        arbol = ast.parse(fuente)
    except SyntaxError as e:
        return [f"no compila: {e.msg}"]
    errores = []
    doc = ast.get_docstring(arbol) or ""
    errores += [f"al docstring del módulo le falta la sección «{s}»" for s in SECCIONES if s not in doc]
    if RUTA_LOCAL.search(fuente):
        errores.append("trae una ruta local (unidad de disco o directorio de usuario)")
    for nodo in _definiciones_publicas(arbol):
        if not ast.get_docstring(nodo):
            errores.append(f"«{nodo.name}» no tiene docstring")
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Call):
            funcion = nodo.func.attr if isinstance(nodo.func, ast.Attribute) else getattr(nodo.func, "id", "")
            claves = {k.arg for k in nodo.keywords}
            if funcion in FUNCIONES_DE_TEXTO and "encoding" not in claves and not _modo_binario(nodo):
                errores.append(f"línea {nodo.lineno}: «{funcion}» sin `encoding`")
            if funcion in ("run", "Popen") and "text" in claves and "encoding" not in claves:
                errores.append(f"línea {nodo.lineno}: subproceso en modo texto sin `encoding`")
            if funcion == "print" and {n.id for a in nodo.args for n in ast.walk(a) if isinstance(n, ast.Name)} & NOMBRES_SECRETOS:
                errores.append(f"línea {nodo.lineno}: imprime una variable que puede traer una credencial")
    return errores


def _modo_binario(nodo):
    """Una apertura con modo binario no lleva codificación."""
    return any(isinstance(a, ast.Constant) and isinstance(a.value, str) and "b" in a.value and len(a.value) <= 3 for a in nodo.args[1:]) or any(
        k.arg == "mode" and isinstance(k.value, ast.Constant) and "b" in str(k.value.value) for k in nodo.keywords)


def _fuente(nombre):
    return (ROOT / "scripts" / "evidencias" / nombre).read_text(encoding="utf-8")


def test_los_scripts_de_verificacion_en_vivo_existen_y_cumplen_su_forma():
    for nombre in SCRIPTS:
        assert (ROOT / "scripts" / "evidencias" / nombre).is_file(), nombre
        assert problemas(_fuente(nombre)) == [], nombre


def test_cada_script_esta_en_el_indice_de_scripts():
    indice = (ROOT / "scripts" / "README.md").read_text(encoding="utf-8")
    for nombre in SCRIPTS:
        assert nombre in indice, f"{nombre} no está en scripts/README.md"


def test_los_documentos_dicen_cual_fue_la_ultima_ejecucion_real():
    instalacion = (ROOT / "docs" / "instalacion" / "README.md").read_text(encoding="utf-8")
    for ev in ("EV-085", "EV-087", "EV-090"):
        assert ev in instalacion, f"docs/instalacion/README.md no menciona {ev} como última ejecución real"


def test_negativas_de_la_forma_de_los_scripts():
    base = _fuente("medir_memoria_suite.py")
    assert problemas(base) == []
    assert problemas(base + "\n# " + "C:" + chr(92) + "carpeta\n"), "ruta local"
    assert problemas(base.replace('"""Corre la suite, mide el pico y escribe el resumen."""', "", 1)), "función pública sin docstring"
    assert problemas(base.replace("Qué NO hace", "Nada más", 1)), "sin la sección «Qué NO hace»"
    assert problemas(base + "\ndef f(p):\n    \"\"\"Lee.\"\"\"\n    return open(p).read()\n"), "apertura de texto sin encoding"
    assert problemas(base + "\ndef g(clave):\n    \"\"\"Imprime.\"\"\"\n    print(clave)\n"), "imprime una credencial"
    assert problemas(base + "\ndef h(:\n"), "no compila"
    assert problemas(base + "\nimport subprocess\nsubprocess.run(['x'], text=True)\n"), "subproceso en texto sin encoding"
    assert problemas(base + "\ndef k(p):\n    \"\"\"Lee bytes.\"\"\"\n    return open(p, 'rb').read()\n") == [], "una apertura binaria no necesita encoding"
