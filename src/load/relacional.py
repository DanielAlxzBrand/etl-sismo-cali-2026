"""Carga relacional por lotes con historial: una corrida por conjunto de entradas distinto, en una sola transacción.

Genérico sobre DB-API (pymysql y sqlite3; solo cambia el marcador de parámetros). Lee únicamente los CSV de Silver y Gold y
`quality_report.json`; nunca escribe en `data/`. Todo el SQL lleva parámetros: los nombres de tablas y columnas salen del esquema, no del usuario.
"""
import csv
import hashlib
import json
import sqlite3
import subprocess
import time
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from src.common import ROOT, load_config, sha256_file
from src.load import esquema
from src.logger import get_logger

log = get_logger(__name__)
sqlite3.register_adapter(Decimal, str)   # sqlite3 no sabe guardar Decimal; la afinidad NUMERIC del esquema lo convierte en número
ESTILO = {"mysql": "%s", "sqlite": "?"}
BOOLEANOS = {"True": 1, "False": 0}      # tabla cerrada: cualquier otro valor es un error, no un NULL silencioso
ENTRADAS_GOLD = {"construccion": "data/gold/gold_final.csv", "kpi": "data/gold/kpis_gold.csv", "kpi_sensibilidad": "data/gold/kpis_sensibilidad.csv"}
ORDEN_TABLAS = ("barrio_estrato", "construccion", "kpi", "kpi_sensibilidad")


class ConversionError(ValueError):
    """Un valor del CSV no se puede convertir al tipo de la columna sin perder información."""


def convertir(valor, tipo, no_nulo, contexto=""):
    """Convierte un texto del CSV al tipo de la columna. Vacío es NULL (error si la columna es NOT NULL); nunca redondea ni trunca."""
    t = tipo.upper()
    donde = f" ({contexto})" if contexto else ""
    if valor == "":
        if no_nulo:
            raise ConversionError(f"valor vacío en una columna obligatoria{donde}")
        return None
    try:
        if t == "TINYINT(1)":
            if valor not in BOOLEANOS:
                raise ConversionError(f"booleano desconocido {valor!r}{donde}")
            return BOOLEANOS[valor]
        if t.split("(")[0].split()[0] in ("TINYINT", "SMALLINT", "INT", "BIGINT"):
            d = Decimal(valor)
            if d != d.to_integral_value():
                raise ConversionError(f"entero con parte decimal {valor!r}{donde}")
            if "UNSIGNED" in t and d < 0:
                raise ConversionError(f"negativo en una columna sin signo {valor!r}{donde}")
            return int(d)
        if t.startswith("DECIMAL"):
            p, s = (int(x) for x in t[t.index("(") + 1:t.index(")")].split(","))
            d = Decimal(valor)
            q = d.quantize(Decimal(1).scaleb(-s))
            if q != d or len(q.as_tuple().digits) > p:
                raise ConversionError(f"el decimal {valor!r} no cabe sin pérdida en DECIMAL({p},{s}){donde}")
            return q
        if t == "DOUBLE":
            return float(valor)
        if t == "DATE":
            date.fromisoformat(valor)
            return valor
        if t.startswith(("CHAR", "VARCHAR")):
            n = int(t[t.index("(") + 1:t.index(")")])
            if len(valor) > n:
                raise ConversionError(f"texto de {len(valor)} caracteres en una columna de {n}{donde}")
            return valor
    except ConversionError:
        raise
    except (InvalidOperation, ValueError):
        raise ConversionError(f"valor no válido {valor!r}{donde}") from None
    raise ConversionError(f"tipo no soportado {tipo}{donde}")


def _leer_csv(ruta, raiz=ROOT):
    with open(Path(raiz) / ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _commit_codigo():
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=10)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "desconocido"
    except (OSError, subprocess.SubprocessError):
        return "desconocido"


def entradas(cfg=None):
    """Archivos de entrada: {tabla: ruta} de los CSV y la ruta de quality_report.json."""
    cfg = cfg or load_config()
    return {"barrio_estrato": cfg["paths_silver"]["estrato_barrio"], **ENTRADAS_GOLD}, cfg["paths_silver"]["quality_report"]


def huellas(cfg=None, raiz=ROOT):
    """[(ruta, sha256, filas)] de los archivos de entrada, ordenadas por ruta (filas es None para el JSON). `raiz` permite apuntar a una copia."""
    csvs, qr = entradas(cfg)
    out = [(ruta, sha256_file(Path(raiz) / ruta), len(_leer_csv(ruta, raiz))) for ruta in csvs.values()]
    out.append((qr, sha256_file(Path(raiz) / qr), None))
    return sorted(out)


def clave_corrida(hue, version=esquema.VERSION_ESQUEMA):
    """sha256 de las huellas de entrada ordenadas más la versión del esquema: mismas entradas, misma clave."""
    texto = "\n".join(f"{ruta}:{sha}" for ruta, sha, _ in sorted(hue)) + f"\nesquema:{version}"
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _filas_de_tabla(tabla, columnas, filas_csv, esquema_tablas):
    """Convierte las filas del CSV (más las columnas derivadas) a tuplas en el orden de las columnas de la tabla, sin corrida_id."""
    cols = [c for c in esquema_tablas[tabla] if c["nombre"] != "corrida_id"]
    faltan = [c["nombre"] for c in cols if c["nombre"] not in columnas and c["nombre"] not in DERIVADAS[tabla]]
    sobran = [c for c in columnas if c not in {x["nombre"] for x in cols}]
    if faltan or sobran:
        raise ConversionError(f"las columnas de {tabla} no coinciden con el esquema (faltan {faltan}, sobran {sobran})")
    salida = []
    for i, fila in enumerate(filas_csv, 1):
        crudo = dict(fila)
        if tabla == "barrio_estrato":
            crudo["comuna"] = f"{int(crudo['codigo_barrio']) // 100:02d}"
        elif tabla == "construccion":
            crudo["barrio_estrato_codigo"] = crudo["codigo_barrio"] if crudo["cruza_llave"] == "True" else ""
        else:
            crudo["orden"] = str(i)
        salida.append(tuple(convertir(crudo[c["nombre"]], c["tipo"], c["no_nulo"], f"{tabla}, fila {i}, columna {c['nombre']}") for c in cols))
    return salida, [c["nombre"] for c in cols]


DERIVADAS = {"barrio_estrato": {"comuna"}, "construccion": {"barrio_estrato_codigo"}, "kpi": {"orden"}, "kpi_sensibilidad": {"orden"}}


def preparar(cfg=None, raiz=ROOT):
    """Lee y convierte TODAS las entradas antes de tocar la base: un error de conversión no deja nada a medias. Devuelve el paquete de datos de la corrida."""
    cfg = cfg or load_config()
    csvs, qr_ruta = entradas(cfg)
    et = esquema.tablas(esquema.leer("mysql"))
    hue = huellas(cfg, raiz)
    qr = json.loads((Path(raiz) / qr_ruta).read_text(encoding="utf-8"))
    tablas, crudas = {}, {}
    for tabla, ruta in csvs.items():
        crudas[tabla] = _leer_csv(ruta, raiz)
        tablas[tabla] = _filas_de_tabla(tabla, list(crudas[tabla][0].keys()), crudas[tabla], et)
    comunas = {f"{int(r['codigo_barrio']) // 100:02d}" for r in crudas["barrio_estrato"]}
    comunas |= {r["comuna"] for r in crudas["construccion"] if r["comuna"] != ""}
    cob = lambda v: convertir(repr(float(v)) if not isinstance(v, str) else v, "DECIMAL(7,6)", True, "quality_report.json")  # noqa: E731
    corrida = {"clave": clave_corrida(hue), "commit": _commit_codigo(), "fecha_corte": cfg["fechas"]["fecha_edicion_capa"],
               "n": {t: len(tablas[t][0]) for t in ORDEN_TABLAS},
               "cob": (cob(qr["cobertura_llave"]["pct"]), cob(qr["cobertura_estrato_valido"]["pct"]), cob(qr["pct_nombre_validado"]["global"]["pct"])), "confianza": qr["llave_confianza"]}
    return {"huellas": hue, "tablas": tablas, "comunas": sorted(comunas), "corrida": corrida}


def _insertar(cur, dialecto, tabla, columnas, filas, lote):
    ph = ", ".join([ESTILO[dialecto]] * len(columnas))
    sql = f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({ph})"
    for i in range(0, len(filas), lote):
        cur.executemany(sql, filas[i:i + lote])   # un lote por llamada: menos viajes al servidor


def corrida_existente(conn, dialecto, clave):
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT id FROM corrida WHERE clave_corrida = {ESTILO[dialecto]}", (clave,))
        fila = cur.fetchone()
        return fila[0] if fila else None
    finally:
        cur.close()


def cargar(conn, dialecto, lote=None, cfg=None, gancho=None, paquete=None, raiz=ROOT):
    """Carga una corrida. Si la clave ya existe devuelve {'estado': 'ya_cargada'} sin escribir; si no, inserta todo en UNA transacción (o nada).

    `gancho(tabla)` se llama tras insertar cada tabla (las pruebas lo usan para inyectar un error a mitad de la carga). `raiz` apunta a una copia de data/ (pruebas).
    """
    cfg = cfg or load_config()
    lote = int(lote or cfg["almacenamiento"]["lote"])
    t0 = time.perf_counter()
    paq = paquete or preparar(cfg, raiz)
    c = paq["corrida"]
    esquema.aplicar(conn, dialecto)   # el DDL de MySQL confirma implícitamente: va antes de abrir la transacción
    existente = corrida_existente(conn, dialecto, c["clave"])
    if existente is not None:
        log.info("corrida %s ya cargada (id %s): no se escribe nada", c["clave"][:12], existente)
        return {"estado": "ya_cargada", "corrida_id": existente, "clave": c["clave"], "filas": c["n"], "duracion_s": time.perf_counter() - t0}
    et = esquema.tablas(esquema.leer("mysql"))
    cur = None
    try:
        cur = conn.cursor()
        ph = ESTILO[dialecto]
        ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
        cur.execute(f"INSERT INTO corrida (clave_corrida, cargada_en, commit_codigo, fecha_corte, version_esquema, n_barrios, n_construcciones, n_kpis, n_kpis_sensibilidad, "
                    f"cobertura_llave, cobertura_estrato_valido, pct_nombre_validado, llave_confianza) VALUES ({', '.join([ph] * 13)})",
                    (c["clave"], ahora, c["commit"], c["fecha_corte"], esquema.VERSION_ESQUEMA, c["n"]["barrio_estrato"], c["n"]["construccion"], c["n"]["kpi"], c["n"]["kpi_sensibilidad"], *c["cob"], c["confianza"]))
        corrida_id = cur.lastrowid
        _insertar(cur, dialecto, "corrida_archivo", ["corrida_id", "nombre", "sha256", "filas"], [(corrida_id, n, s, f) for n, s, f in paq["huellas"]], lote)
        cur.execute("SELECT codigo FROM comuna")
        existentes = {f[0] for f in cur.fetchall()}
        nuevas = [(cod, f"Comuna {int(cod)}") for cod in paq["comunas"] if cod not in existentes]
        if nuevas:
            _insertar(cur, dialecto, "comuna", ["codigo", "nombre"], nuevas, lote)
        for tabla in ORDEN_TABLAS:   # padres antes que hijos: barrio_estrato antes que construccion
            filas, columnas = paq["tablas"][tabla]
            _insertar(cur, dialecto, tabla, ["corrida_id", *columnas], [(corrida_id, *f) for f in filas], lote)
            if gancho:
                gancho(tabla)
        conn.commit()
    except Exception:
        conn.rollback()   # cualquier error deja la base exactamente como estaba
        log.error("la carga falló: rollback completo")
        raise
    finally:
        if cur is not None:
            cur.close()
    dur = time.perf_counter() - t0
    log.info("corrida %s cargada (id %s): %s filas en %.2f s", c["clave"][:12], corrida_id, c["n"], dur)
    return {"estado": "cargada", "corrida_id": corrida_id, "clave": c["clave"], "filas": c["n"], "duracion_s": dur}
