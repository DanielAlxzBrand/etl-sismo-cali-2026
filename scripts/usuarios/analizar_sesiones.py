"""Analiza las sesiones con personas usuarias del panel: tasa de éxito por tarea, tiempo, SUS y CSAT.

Uso:  python scripts/usuarios/analizar_sesiones.py             lee docs/usuarios/sesiones_reales/ y escribe docs/usuarios/resultados.md
      python scripts/usuarios/analizar_sesiones.py --simulado  lee docs/usuarios/simulacion/ y escribe SOLO docs/usuarios/resultados_simulacion.md
      python scripts/usuarios/analizar_sesiones.py --simuladas lee docs/usuarios/sesiones_simuladas/ y escribe SOLO docs/usuarios/resultados_sesiones_simuladas.md
Las tres fuentes nunca se mezclan. Con cero sesiones reales NO calcula nada y escribe «no hay sesiones reales». Con menos de 5 personas muestra «k de n» y no porcentajes.
Rechaza (código de salida 2) cualquier fila que no sea `real` en `sesiones_reales`, cualquier fila que no sea `sintetico` en `simulacion` y cualquier fila que no sea `simulada` en `sesiones_simuladas`.
Una sesión simulada (D109 y D112) no se hizo con una persona real: sus participantes se llaman «Participante simulado N» y toda cifra vale exactamente «simulado, no medido», con una sola excepción: las diez
respuestas del SUS y el CSAT pueden ser una estimación de la persona simulada escrita «simulado: N» (N entero de 1 a 5), todas o ninguna de una fila. Tres guardas: (1) el modo real y el sintético rechazan
cualquier valor «simulado…», así que ninguna cifra simulada entra en el análisis de sesiones reales; (2) el modo simulado acepta una cifra solo con el prefijo «simulado:» y con origen `simulada`, y los resultados,
tiempos, ayudas y errores siguen valiendo «simulado, no medido»; (3) todo resumen o promedio que imprime con esas estimaciones lleva la marca «simulado:» y se calcula solo con filas simuladas. Rechaza una cifra de
verdad en esa carpeta y no calcula nunca tasas ni tiempos con ellas.
Archivos que lee en cada carpeta: `registro.csv` (una fila por tarea y persona) y `cuestionarios.csv` (una fila por persona); las plantillas no se leen.
"""
import argparse
import csv
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.transform.build_gold import wilson  # noqa: E402  (el intervalo de Wilson del proyecto, sin copiar su código)

USUARIOS = ROOT / "docs" / "usuarios"
TAREAS = ("T1", "T2", "T3", "T4", "T5", "T6")
RESULTADOS = ("exito", "exito_con_ayuda", "fracaso")
N_MINIMO_PORCENTAJE = 5
ORIGEN_SIMULADA = "simulada"
NO_MEDIDO = "simulado, no medido"
ESTIMACION_SIMULADA = re.compile(r"simulado: ([1-5])")   # D112: la estimación del SUS y del CSAT de una persona simulada; nunca una medición
CIFRAS_ESTIMABLES = tuple(f"sus_{i}" for i in range(1, 11)) + ("csat",)
PARTICIPANTE_SIMULADO = re.compile(r"Participante simulado \d+")
ENCABEZADO_SIMULADA = "Sesión simulada, no realizada con una persona real"
AVISO_SINTETICO = "DATOS SINTÉTICOS: no son personas. Los generó `scripts/usuarios/generar_datos_sinteticos.py` con una semilla fija solo para probar este script; no cuentan para ningún ítem del checklist."
CAMPOS_REGISTRO = ("participante", "perfil", "fecha", "tarea", "resultado", "tiempo_s", "ayudas", "errores", "comentario_breve", "origen")
CAMPOS_CUESTIONARIOS = ("participante", "perfil", "fecha") + tuple(f"sus_{i}" for i in range(1, 11)) + ("csat", "origen")


class FilaNoValida(ValueError):
    """Una fila de las carpetas de sesiones no cumple el formato o no tiene el origen que la carpeta admite."""


def puntuar_sus(respuestas):
    """Puntuación SUS (de 0 a 100) de una persona a partir de sus diez respuestas de 1 a 5, con la fórmula de Brooke (1996).

    Ítems impares (1, 3, 5, 7, 9): respuesta menos 1. Ítems pares (2, 4, 6, 8, 10): 5 menos la respuesta. Se suman y se multiplica por 2,5.
    """
    r = [int(x) for x in respuestas]
    if len(r) != 10 or any(not 1 <= x <= 5 for x in r):
        raise FilaNoValida("el SUS necesita diez respuestas enteras de 1 a 5")
    return 2.5 * sum((x - 1) if i % 2 == 0 else (5 - x) for i, x in enumerate(r))


def leer_csv(ruta, campos):
    """Filas (diccionarios) de un CSV con exactamente las columnas `campos`; lista vacía si el archivo no existe."""
    if not ruta.is_file():
        return []
    with open(ruta, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        if tuple(lector.fieldnames or ()) != campos:
            raise FilaNoValida(f"{ruta.name}: las columnas no son las esperadas {campos}")
        return list(lector)


def validar_origen(filas, origen, ruta):
    """Falla si alguna fila no tiene el origen que admite la carpeta (`real` en sesiones_reales, `sintetico` en simulacion)."""
    for i, f in enumerate(filas, 2):
        if f["origen"] != origen:
            raise FilaNoValida(f"{ruta.name}, fila {i}: origen «{f['origen']}»; esta carpeta solo admite «{origen}»")


def rechazar_valores_simulados(filas, donde):
    """Guarda 1: ninguna celda que empiece por «simulado» entra en el análisis de sesiones reales ni sintéticas, aunque la fila diga otro origen."""
    for i, f in enumerate(filas, 2):
        for campo, valor in f.items():
            if isinstance(valor, str) and valor.strip().lower().startswith("simulado"):
                raise FilaNoValida(f"fila {i}: el campo {campo} trae un valor simulado ({valor!r}); una cifra simulada no entra en {donde}")


def validar_registro(filas):
    for i, f in enumerate(filas, 2):
        if f["tarea"] not in TAREAS or f["resultado"] not in RESULTADOS:
            raise FilaNoValida(f"registro.csv, fila {i}: tarea o resultado no válidos ({f['tarea']!r}, {f['resultado']!r})")
        try:
            if float(f["tiempo_s"]) < 0 or int(f["ayudas"]) < 0 or int(f["errores"]) < 0:
                raise ValueError
        except ValueError:
            raise FilaNoValida(f"registro.csv, fila {i}: tiempo, ayudas o errores no son números no negativos") from None


def cargar(carpeta, origen):
    """(filas del registro, filas de los cuestionarios) de una carpeta, ya validadas."""
    registro = leer_csv(carpeta / "registro.csv", CAMPOS_REGISTRO)
    cuestionarios = leer_csv(carpeta / "cuestionarios.csv", CAMPOS_CUESTIONARIOS)
    validar_origen(registro, origen, carpeta / "registro.csv")
    validar_origen(cuestionarios, origen, carpeta / "cuestionarios.csv")
    rechazar_valores_simulados(registro + cuestionarios, "una sesión real o sintética")
    validar_registro(registro)
    for f in cuestionarios:
        puntuar_sus([f[f"sus_{i}"] for i in range(1, 11)])
        if not 1 <= int(f["csat"]) <= 5:
            raise FilaNoValida(f"cuestionarios.csv: el CSAT de {f['participante']} no está entre 1 y 5")
    return registro, cuestionarios


def cargar_simuladas(carpeta):
    """(registro, cuestionarios) de `sesiones_simuladas`, validados: origen `simulada`, «Participante simulado N», toda cifra igual a «simulado, no medido» y, solo en el SUS y el CSAT, una estimación «simulado: N» (guarda 2)."""
    registro = leer_csv(carpeta / "registro.csv", CAMPOS_REGISTRO)
    cuestionarios = leer_csv(carpeta / "cuestionarios.csv", CAMPOS_CUESTIONARIOS)
    validar_origen(registro, ORIGEN_SIMULADA, carpeta / "registro.csv")
    validar_origen(cuestionarios, ORIGEN_SIMULADA, carpeta / "cuestionarios.csv")
    for nombre, filas, cifras in (("registro.csv", registro, ("resultado", "tiempo_s", "ayudas", "errores")),
                                  ("cuestionarios.csv", cuestionarios, tuple(f"sus_{i}" for i in range(1, 11)) + ("csat",))):
        for i, f in enumerate(filas, 2):
            if not PARTICIPANTE_SIMULADO.fullmatch(f["participante"]):
                raise FilaNoValida(f"{nombre}, fila {i}: el participante debe llamarse «Participante simulado N», no {f['participante']!r}")
            if nombre == "registro.csv" and f["tarea"] not in TAREAS:
                raise FilaNoValida(f"{nombre}, fila {i}: la tarea {f['tarea']!r} no es de T1 a T6")
            for c in cifras:
                if f[c] != NO_MEDIDO and not (c in CIFRAS_ESTIMABLES and ESTIMACION_SIMULADA.fullmatch(f[c])):
                    raise FilaNoValida(f"{nombre}, fila {i}: la cifra {c} de una sesión simulada debe valer «{NO_MEDIDO}»" + (" o «simulado: N» con N de 1 a 5" if c in CIFRAS_ESTIMABLES else "") + f", no {f[c]!r}: no se midió nada")
            if nombre == "cuestionarios.csv" and len({f[c] == NO_MEDIDO for c in CIFRAS_ESTIMABLES}) > 1:
                raise FilaNoValida(f"{nombre}, fila {i}: los diez ítems del SUS y el CSAT son todos «{NO_MEDIDO}» o todos «simulado: N», no una mezcla")
    return registro, cuestionarios


def estimaciones_simuladas(cuestionarios):
    """[(participante, SUS simulado de 0 a 100, CSAT simulado)] de las filas con estimaciones «simulado: N». Guarda 3: solo calcula con filas simuladas; una fila real o sintética (o con otro origen) lo rechaza."""
    salida = []
    for f in cuestionarios:
        if f["origen"] != ORIGEN_SIMULADA or not PARTICIPANTE_SIMULADO.fullmatch(f["participante"]):
            raise FilaNoValida(f"{f['participante']!r} no es una fila simulada: una cifra simulada no se calcula junto con datos reales")
        if all(ESTIMACION_SIMULADA.fullmatch(f[c]) for c in CIFRAS_ESTIMABLES):
            n = {c: int(ESTIMACION_SIMULADA.fullmatch(f[c]).group(1)) for c in CIFRAS_ESTIMABLES}
            salida.append((f["participante"], puntuar_sus([n[f"sus_{i}"] for i in range(1, 11)]), n["csat"]))
    return salida


def _simulado(x, d=1):
    """Una cifra simulada, siempre con su marca."""
    return f"simulado: {_coma(x, d)}"


def registros_de_etapa_1(carpeta):
    """Nombres de los registros de la etapa 1 en texto (`participante_simulado_N_etapa_1.md`) de la carpeta de sesiones simuladas; no traen cifras y no se cuentan como filas."""
    return sorted(p.name for p in carpeta.glob("participante_simulado_*_etapa_1.md")) if carpeta.is_dir() else []


def redactar_simuladas(registro, cuestionarios, registros_etapa_1=()):
    """Texto Markdown del resumen de las sesiones simuladas: cuántas filas y participantes hay y que ninguna cifra se midió; no calcula tasas, tiempos ni puntuaciones."""
    personas = sorted({f["participante"] for f in registro} | {f["participante"] for f in cuestionarios})
    est = estimaciones_simuladas(cuestionarios)
    L = ["# Sesiones simuladas (no realizadas con personas reales)", "", f"> **{ENCABEZADO_SIMULADA}.** Lo que está aquí no cuenta como sesión real; cuenta como evidencia simulada según la decisión D111, y no es feedback de personas usuarias: ni las sesiones reales ni los datos sintéticos de prueba se mezclan con esto.", ""]
    if not personas:
        L += ["**No hay sesiones simuladas registradas.** Cuando el equipo guarde `registro.csv` y `cuestionarios.csv` en `docs/usuarios/sesiones_simuladas/` con `origen = simulada`, este archivo contará lo registrado.", ""]
    else:
        L += [f"**Participantes simulados:** {len(personas)} ({', '.join(personas)}). **Filas de tareas:** {len(registro)}. **Cuestionarios:** {len(cuestionarios)}.", "",
              (f"Ninguna cifra se midió: el resultado, el tiempo, el número de ayudas y de errores valen «{NO_MEDIDO}». Las respuestas del SUS y el CSAT de {len(est)} de {len(cuestionarios)} cuestionarios son "
               "**estimaciones de la persona simulada** escritas «simulado: N», no mediciones." if est else
               f"Ninguna cifra se midió: cada resultado, tiempo, número de ayudas y de errores, respuesta del SUS y CSAT vale «{NO_MEDIDO}». Por eso no se calcula ninguna tasa, tiempo ni puntuación."), ""]
    if registros_etapa_1:
        L += [f"**Registros de la etapa 1 en texto:** {len(registros_etapa_1)} ({', '.join(f'`{n}`' for n in registros_etapa_1)}). No traen cifras y no son filas de los CSV: un participante que no tenga filas en `registro.csv` y `cuestionarios.csv` no se cuenta aquí como sesión registrada.", ""]
    if est:
        L += ["## Estimaciones simuladas del SUS y del CSAT (no son mediciones)", "",
              "Cada cifra de esta sección es una estimación de una persona simulada y lleva la marca «simulado:». No se mezclan con sesiones reales ni cuentan como satisfacción de personas usuarias.", ""]
        L += [f"- {p}: SUS {_simulado(s)} de 100; CSAT {_simulado(c, 0)} de 5." for p, s, c in est]
        L += ["", f"Promedio de estas estimaciones (con {len(est)} personas simuladas, sin intervalo): SUS {_simulado(statistics.mean(s for _, s, _ in est))} de 100; CSAT {_simulado(statistics.mean(c for _, _, c in est))} de 5.", ""]
    L += ["## Qué NO demuestra", "Que el panel sea usable o no lo sea, ni que alguien lo haya usado: una sesión simulada no se hizo con una persona real y no mide nada.", ""]
    return "\n".join(L)


def calcular(registro, cuestionarios):
    """Cifras por tarea, SUS y CSAT. Con n < 5 personas no se calcula ningún intervalo."""
    personas = sorted({f["participante"] for f in registro} | {f["participante"] for f in cuestionarios})
    n = len(personas)
    por_tarea = {}
    for t in TAREAS:
        filas = [f for f in registro if f["tarea"] == t]
        if not filas:
            continue
        k = sum(f["resultado"] == "exito" for f in filas)
        tiempos = [float(f["tiempo_s"]) for f in filas]
        d = {"n": len(filas), "exito": k, "con_ayuda": sum(f["resultado"] == "exito_con_ayuda" for f in filas), "fracaso": sum(f["resultado"] == "fracaso" for f in filas),
             "mediana_s": statistics.median(tiempos), "min_s": min(tiempos), "max_s": max(tiempos), "intervalo": None}
        if len(filas) >= N_MINIMO_PORCENTAJE:
            d["tasa"] = k / len(filas)
            d["intervalo"] = wilson(k, len(filas))
        por_tarea[t] = d
    sus = {f["participante"]: puntuar_sus([f[f"sus_{i}"] for i in range(1, 11)]) for f in cuestionarios}
    csat = {f["participante"]: int(f["csat"]) for f in cuestionarios}
    return {"personas": personas, "n": n, "por_tarea": por_tarea, "sus": sus, "sus_media": statistics.mean(sus.values()) if sus else None,
            "csat": csat, "csat_media": statistics.mean(csat.values()) if csat else None}


def _coma(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def redactar(r, simulado):
    """Texto Markdown de los resultados a partir de lo que devuelve `calcular`."""
    titulo = "# Resultados de la simulación (datos sintéticos)" if simulado else "# Resultados de las sesiones con personas usuarias"
    L = [titulo, ""]
    if simulado:
        L += [f"> **{AVISO_SINTETICO}**", ""]
    L += ["**Ítems del checklist:** 6.2 (tasa de éxito, tiempo, SUS y CSAT)." if not simulado else "Sirve para probar el script de análisis y ensayar el formato de los resultados.", ""]
    if r["n"] == 0:
        L += ["**No hay sesiones reales.** No se calculó ninguna tasa, tiempo ni puntuación porque no se ha hecho ninguna sesión con personas usuarias. Cuando el equipo guarde `registro.csv` y `cuestionarios.csv` en `sesiones_reales/`, este archivo se vuelve a generar.", ""]
    else:
        pocas = r["n"] < N_MINIMO_PORCENTAJE
        L += [f"**Personas:** {r['n']} ({', '.join(r['personas'])}). " + ("Con menos de 5 personas se muestra «k de n» y no porcentajes, porque un porcentaje parecería más preciso de lo que es." if pocas else "Con 5 o más intentos por tarea se agrega el intervalo de Wilson al 95 %."), "",
              "## Éxito y tiempo por tarea", "", "| Tarea | Intentos | Éxito sin ayuda (k de n) | Éxito con ayuda | Fracaso | Tasa de éxito sin ayuda (IC de Wilson 95 %) | Tiempo: mediana (s) | Tiempo: rango (s) |", "|---|---|---|---|---|---|---|---|"]
        for t, d in r["por_tarea"].items():
            tasa = f"{_coma(d['tasa'] * 100)} % ({_coma(d['intervalo'][0] * 100)} a {_coma(d['intervalo'][1] * 100)} %)" if d["intervalo"] else "no se informa (n < 5)"
            L.append(f"| {t} | {d['n']} | {d['exito']} de {d['n']} | {d['con_ayuda']} | {d['fracaso']} | {tasa} | {_coma(d['mediana_s'], 0)} | {_coma(d['min_s'], 0)} a {_coma(d['max_s'], 0)} |")
        L += ["", "## SUS y CSAT", ""]
        if r["sus"]:
            L += ["| Participante | SUS (0 a 100) | CSAT (1 a 5) |", "|---|---|---|"] + [f"| {p} | {_coma(v)} | {r['csat'][p]} |" for p, v in r["sus"].items()]
            L += ["", f"**Media del SUS:** {_coma(r['sus_media'])}; **media del CSAT:** {_coma(r['csat_media'])}. Con tan pocas personas la media solo describe a esas personas."]
        else:
            L += ["No hay cuestionarios guardados."]
        L += [""]
    if r["n"] == 0:
        L += ["## Qué NO demuestra", "Que el panel sea usable o no lo sea: mientras no haya sesiones reales, este archivo no dice nada sobre personas usuarias.", ""]
        return "\n".join(L)
    L += ["## Qué NO demuestra",
          "No demuestra que el panel sea fácil o difícil para otras personas ni permite comparar perfiles: son pocas personas, no elegidas al azar" + ("; y en esta simulación ni siquiera son personas." if simulado else "; si alguna era conocida del equipo, tendió a ser más amable.") +
          " Tampoco mide si entienden los límites de las cifras más allá de lo que se anotó en cada tarea.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    grupo = ap.add_mutually_exclusive_group()
    grupo.add_argument("--simulado", action="store_true", help="lee docs/usuarios/simulacion/ y escribe solo resultados_simulacion.md")
    grupo.add_argument("--simuladas", action="store_true", help="lee docs/usuarios/sesiones_simuladas/ y escribe solo resultados_sesiones_simuladas.md")
    ap.add_argument("--base", default=str(USUARIOS), help="carpeta docs/usuarios (para las pruebas)")
    a = ap.parse_args(argv)
    base = Path(a.base)
    if a.simuladas:
        try:
            registro, cuestionarios = cargar_simuladas(base / "sesiones_simuladas")
        except FilaNoValida as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        salida = base / "resultados_sesiones_simuladas.md"
        salida.write_text(redactar_simuladas(registro, cuestionarios, registros_de_etapa_1(base / "sesiones_simuladas")), encoding="utf-8", newline="\n")
        print(f"escrito {salida.name}: sesiones simuladas, {len({f['participante'] for f in registro} | {f['participante'] for f in cuestionarios})} participantes simulados")
        return 0
    carpeta = base / ("simulacion" if a.simulado else "sesiones_reales")
    salida = base / ("resultados_simulacion.md" if a.simulado else "resultados.md")
    try:
        registro, cuestionarios = cargar(carpeta, "sintetico" if a.simulado else "real")
    except FilaNoValida as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    texto = redactar(calcular(registro, cuestionarios), a.simulado)
    salida.write_text(texto, encoding="utf-8", newline="\n")
    print(f"escrito {salida.name}: {'simulación' if a.simulado else 'sesiones reales'}, {len({f['participante'] for f in registro} | {f['participante'] for f in cuestionarios})} personas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
