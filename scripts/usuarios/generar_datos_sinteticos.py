"""Genera datos SINTÉTICOS para probar el script de análisis: tres participantes ficticios, sin texto libre.

Uso:  python scripts/usuarios/generar_datos_sinteticos.py [--salida docs/usuarios/simulacion]
Los números salen de un generador con semilla fija (`SEMILLA`): la misma semilla produce siempre los mismos archivos. Los participantes son `S01` a `S03` y la columna `origen` dice
`sintetico`. **No son personas ni representan a nadie**: no se redactó ninguna cita ni ningún relato, y estos datos no cuentan para los ítems 6.1, 6.2, 6.3, 6.5 ni 7.4.
"""
import argparse
import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analizar_sesiones import CAMPOS_CUESTIONARIOS, CAMPOS_REGISTRO, RESULTADOS, TAREAS  # noqa: E402

SEMILLA = 8231
PARTICIPANTES = ("S01", "S02", "S03")
PERFILES = ("institucional", "habitante", "academico")
FECHA = "sintetico"
PESOS_RESULTADO = (0.55, 0.30, 0.15)     # éxito, éxito con ayuda, fracaso (pesos inventados para ensayar el formato)


def generar(semilla=SEMILLA):
    """(filas del registro, filas de los cuestionarios) sintéticas y deterministas para una semilla."""
    azar = random.Random(semilla)
    registro, cuestionarios = [], []
    for p, perfil in zip(PARTICIPANTES, PERFILES):
        for t in TAREAS:
            resultado = azar.choices(RESULTADOS, weights=PESOS_RESULTADO)[0]
            registro.append({"participante": p, "perfil": perfil, "fecha": FECHA, "tarea": t, "resultado": resultado,
                             "tiempo_s": azar.randint(30, 230), "ayudas": 0 if resultado == "exito" else azar.randint(1, 2),
                             "errores": azar.randint(0, 3), "comentario_breve": "", "origen": "sintetico"})
        fila = {"participante": p, "perfil": perfil, "fecha": FECHA, "origen": "sintetico", "csat": azar.randint(1, 5)}
        fila.update({f"sus_{i}": azar.randint(1, 5) for i in range(1, 11)})
        cuestionarios.append(fila)
    return registro, cuestionarios


def escribir(carpeta, semilla=SEMILLA):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    registro, cuestionarios = generar(semilla)
    for nombre, campos, filas in (("registro.csv", CAMPOS_REGISTRO, registro), ("cuestionarios.csv", CAMPOS_CUESTIONARIOS, cuestionarios)):
        with open(carpeta / nombre, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=campos, lineterminator="\n")
            w.writeheader()
            w.writerows(filas)
    return carpeta


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", default=str(ROOT / "docs" / "usuarios" / "simulacion"))
    a = ap.parse_args(argv)
    destino = escribir(a.salida)
    print(f"datos sintéticos (semilla {SEMILLA}) escritos en {destino.name}/: 3 participantes ficticios")
    return 0


if __name__ == "__main__":
    sys.exit(main())
