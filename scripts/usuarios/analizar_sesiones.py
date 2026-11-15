"""Analiza las sesiones con personas usuarias del panel: tasa de éxito por tarea, tiempo, SUS y CSAT.

Uso:  python scripts/usuarios/analizar_sesiones.py             lee docs/usuarios/sesiones_reales/ y escribe docs/usuarios/resultados.md
      python scripts/usuarios/analizar_sesiones.py --simulado  lee docs/usuarios/simulacion/ y escribe SOLO docs/usuarios/resultados_simulacion.md
Las dos fuentes nunca se mezclan. Con cero sesiones reales NO calcula nada y escribe «no hay sesiones reales». Con menos de 5 personas muestra «k de n» y no porcentajes.
Rechaza (código de salida 2) cualquier fila que no sea `real` en `sesiones_reales` y cualquier fila que no sea `sintetico` en `simulacion`.
Archivos que lee en cada carpeta: `registro.csv` (una fila por tarea y persona) y `cuestionarios.csv` (una fila por persona); las plantillas no se leen.
"""
import argparse
import csv
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
    validar_registro(registro)
    for f in cuestionarios:
        puntuar_sus([f[f"sus_{i}"] for i in range(1, 11)])
        if not 1 <= int(f["csat"]) <= 5:
            raise FilaNoValida(f"cuestionarios.csv: el CSAT de {f['participante']} no está entre 1 y 5")
    return registro, cuestionarios


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
    ap.add_argument("--simulado", action="store_true", help="lee docs/usuarios/simulacion/ y escribe solo resultados_simulacion.md")
    ap.add_argument("--base", default=str(USUARIOS), help="carpeta docs/usuarios (para las pruebas)")
    a = ap.parse_args(argv)
    base = Path(a.base)
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
