"""Carga real a la base `sismo_cali` (principal), conciliación y consultas de coherencia; guarda la evidencia saneada.

Uso:  python scripts/evidencias/evidencia_carga_real.py [--nombre EV-029_carga_real_mysql.txt]
Hace la carga (o responde «ya cargada» si la corrida existe), repite la carga para demostrar la idempotencia, concilia al 100 % contra los archivos de origen,
revisa la integridad referencial y compara tres cifras de MySQL con las de los CSV. No imprime credenciales.
"""
import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.common import load_config  # noqa: E402
from src.load import conciliacion, conexion, relacional  # noqa: E402

import evidencia  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--nombre", default="carga_real_mysql.txt")
    a = ap.parse_args(argv)
    cfg = load_config()
    t0 = time.perf_counter()
    conn = conexion.conectar_mysql()
    lineas, ok = [], True
    try:
        base = conn.cursor()
        base.execute("SELECT DATABASE(), VERSION()")
        nombre_base, version = base.fetchone()
        base.close()
        lineas.append(f"Base: {nombre_base} (MySQL {version}); usuario del proyecto con privilegios mínimos.\n")
        paq = relacional.preparar(cfg)
        r1 = relacional.cargar(conn, "mysql", paquete=paq, cfg=cfg)
        lineas.append(f"1. Carga: estado {r1['estado']}, corrida {r1['corrida_id']}, clave {r1['clave'][:16]}…, {r1['duracion_s']:.2f} s, filas {r1['filas']}")
        r2 = relacional.cargar(conn, "mysql", paquete=paq, cfg=cfg)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM corrida")
        n_corridas = c.fetchone()[0]
        idem = r2["estado"] == "ya_cargada" and r2["corrida_id"] == r1["corrida_id"]
        ok &= idem
        lineas.append(f"2. Idempotencia: la segunda carga responde «{r2['estado']}» (corrida {r2['corrida_id']}); corridas en la base: {n_corridas}.")
        conc = conciliacion.conciliar(conn, "mysql", r1["corrida_id"], paquete=paq)
        ok &= conc["ok"]
        lineas += ["", f"3. Conciliación contra los archivos de origen (corrida {r1['corrida_id']}): {'100 %' if conc['ok'] else 'CON DIFERENCIAS'}",
                   "| Tabla | Filas esperadas | Filas cargadas | Valores comparados | Diferencias |", "|---|---|---|---|---|"]
        for t, v in conc["tablas"].items():
            lineas.append(f"| {t} | {v['esperadas']} | {v['cargadas']} | {v['valores']} | {v['diferencias']} |")
        lineas.append(f"Huellas sha256 de los {len(conc['archivos'])} archivos de entrada guardadas en la corrida: {'todas iguales' if all(conc['archivos'].values()) else 'DIFERENTES'}.")
        hu = conciliacion.estado_de_integridad(conn, "mysql")
        ok &= all(v == 0 for v in hu.values())
        lineas += ["", "4. Integridad referencial (filas huérfanas por relación):"] + [f"- {k}: {v}" for k, v in hu.items()]
        gold = list(csv.DictReader(open(ROOT / relacional.ENTRADAS_GOLD["construccion"], encoding="utf-8", newline="")))
        csv_total = len(gold)
        csv_severos = sum(1 for f in gold if f["severo_estricto"] == "True")
        csv_sin_datos = sum(1 for f in gold if f["sin_datos"] == "True")
        csv_sin_cruce = sum(1 for f in gold if f["cruza_llave"] == "False")
        c.execute("SELECT COUNT(*), SUM(severo_estricto = 1), SUM(sin_datos = 1), SUM(cruza_llave = 0) FROM construccion WHERE corrida_id = %s", (r1["corrida_id"],))
        m = tuple(int(x) for x in c.fetchone())
        esperado = (csv_total, csv_severos, csv_sin_datos, csv_sin_cruce)
        ok &= m == esperado
        lineas += ["", "5. Coherencia de cifras (MySQL frente a gold_final.csv):",
                   f"- construcciones: {m[0]} frente a {esperado[0]}", f"- severas (cambio satelital severo, severo estricto): {m[1]} frente a {esperado[1]}",
                   f"- sin datos satelitales: {m[2]} frente a {esperado[2]}", f"- sin cruce con el CSV de estrato 2015 (enlace de barrio nulo): {m[3]} frente a {esperado[3]}"]
        c.execute("SELECT cobertura_llave, cobertura_estrato_valido, pct_nombre_validado, llave_confianza, fecha_corte FROM corrida WHERE id = %s", (r1["corrida_id"],))
        cob = c.fetchone()
        lineas.append(f"- cobertura de llave {cob[0]}, estrato válido {cob[1]}, nombre validado {cob[2]}, confianza de la llave «{cob[3]}», fecha de corte {cob[4]}")
        c.close()
    finally:
        conn.close()
    lineas += ["", f"Resultado: {'todo correcto' if ok else 'HAY DIFERENCIAS'}."]
    cuerpo = "\n".join(lineas) + "\n"
    print(cuerpo)
    ruta = evidencia.guardar("almacenamiento", a.nombre, "Carga real a la base principal, conciliación e idempotencia",
                             "python scripts/evidencias/evidencia_carga_real.py", 0 if ok else 1, time.perf_counter() - t0, cuerpo)
    print("evidencia:", ruta.relative_to(ROOT))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
