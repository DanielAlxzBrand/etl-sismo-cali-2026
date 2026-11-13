"""Conciliación de una corrida cargada contra los archivos de origen: conteos, huellas e ida y vuelta de cada valor.

Compara lo que hay en la base (MySQL o SQLite) con lo que `relacional.preparar` leyó de los CSV, fila a fila y columna a columna. Solo lee.
"""
from datetime import date, datetime
from decimal import Decimal

from src.common import ROOT
from src.load import esquema, relacional

CLAVES = {"barrio_estrato": ("codigo_barrio",), "construccion": ("objectid",), "kpi": ("kpi_id", "grupo"), "kpi_sensibilidad": ("escenario", "kpi_id", "grupo")}


def _igual(esperado, leido, tipo):
    """Compara un valor esperado (ya convertido) con el leído de la base, según el tipo de la columna."""
    if esperado is None or leido is None:
        return esperado is None and leido is None
    t = tipo.upper()
    if t.startswith("DECIMAL"):
        escala = int(t[t.index(",") + 1:t.index(")")])
        return Decimal(str(leido)).quantize(Decimal(1).scaleb(-escala)) == esperado
    if t == "DOUBLE":
        return float(leido) == float(esperado)
    if t == "DATE":
        return (leido.isoformat() if isinstance(leido, (date, datetime)) else str(leido)) == esperado
    if isinstance(esperado, int):
        return int(leido) == esperado
    return str(leido) == esperado


def conciliar(conn, dialecto, corrida_id, paquete=None, cfg=None, raiz=ROOT):
    """Devuelve {'ok': bool, 'tablas': {tabla: {esperadas, cargadas, valores, diferencias, ejemplos}}, 'archivos': {...}}.

    `valores` es el número de celdas comparadas; `diferencias` las que no coinciden (con hasta 5 ejemplos sin datos sensibles: tabla, clave y columna).
    """
    ph = relacional.ESTILO[dialecto]
    paq = paquete or relacional.preparar(cfg, raiz)
    et = esquema.tablas(esquema.leer("mysql"))
    cur = conn.cursor()
    salida, ok = {}, True
    try:
        for tabla in relacional.ORDEN_TABLAS:
            filas, columnas = paq["tablas"][tabla]
            tipos = {c["nombre"]: c["tipo"] for c in et[tabla]}
            cur.execute(f"SELECT {', '.join(columnas)} FROM {tabla} WHERE corrida_id = {ph}", (corrida_id,))
            leidas = cur.fetchall()
            idx = [columnas.index(k) for k in CLAVES[tabla]]
            por_clave = {tuple(str(f[i]) for i in idx): f for f in leidas}
            dif, ejemplos, valores = 0, [], 0
            for esperada in filas:
                clave = tuple(str(esperada[i]) for i in idx)
                leida = por_clave.get(clave)
                if leida is None:
                    dif += 1
                    ejemplos.append(f"{tabla} {clave}: fila ausente")
                    continue
                for c, e, v in zip(columnas, esperada, leida):
                    valores += 1
                    if not _igual(e, v, tipos[c]):
                        dif += 1
                        if len(ejemplos) < 5:
                            ejemplos.append(f"{tabla} {clave}: columna {c}")
            ok_t = len(leidas) == len(filas) and len(por_clave) == len(leidas) and dif == 0
            ok = ok and ok_t
            salida[tabla] = {"esperadas": len(filas), "cargadas": len(leidas), "valores": valores, "diferencias": dif, "ejemplos": ejemplos[:5], "ok": ok_t}
        cur.execute(f"SELECT nombre, sha256, filas FROM corrida_archivo WHERE corrida_id = {ph}", (corrida_id,))
        guardadas = {n: (s, f) for n, s, f in cur.fetchall()}
        archivos = {n: guardadas.get(n) == (s, f) for n, s, f in paq["huellas"]}
        cur.execute(f"SELECT n_barrios, n_construcciones, n_kpis, n_kpis_sensibilidad FROM corrida WHERE id = {ph}", (corrida_id,))
        resumen = cur.fetchone()
        coincide = resumen is not None and tuple(int(x) for x in resumen) == tuple(len(paq["tablas"][t][0]) for t in relacional.ORDEN_TABLAS)
    finally:
        cur.close()
    ok = ok and all(archivos.values()) and len(guardadas) == len(archivos) and coincide
    return {"ok": ok, "tablas": salida, "archivos": archivos, "resumen_corrida": coincide}


def estado_de_integridad(conn, dialecto):
    """Filas huérfanas por cada relación (debe ser 0 en todas) y filas sin su corrida; usa LEFT JOIN, no depende de que el motor haya validado las claves."""
    consultas = {
        "construccion sin corrida": "SELECT COUNT(*) FROM construccion c LEFT JOIN corrida k ON k.id = c.corrida_id WHERE k.id IS NULL",
        "barrio_estrato sin corrida": "SELECT COUNT(*) FROM barrio_estrato b LEFT JOIN corrida k ON k.id = b.corrida_id WHERE k.id IS NULL",
        "kpi sin corrida": "SELECT COUNT(*) FROM kpi b LEFT JOIN corrida k ON k.id = b.corrida_id WHERE k.id IS NULL",
        "kpi_sensibilidad sin corrida": "SELECT COUNT(*) FROM kpi_sensibilidad b LEFT JOIN corrida k ON k.id = b.corrida_id WHERE k.id IS NULL",
        "corrida_archivo sin corrida": "SELECT COUNT(*) FROM corrida_archivo b LEFT JOIN corrida k ON k.id = b.corrida_id WHERE k.id IS NULL",
        "construccion con barrio inexistente": "SELECT COUNT(*) FROM construccion c LEFT JOIN barrio_estrato b ON b.corrida_id = c.corrida_id AND b.codigo_barrio = c.barrio_estrato_codigo "
                                               "WHERE c.barrio_estrato_codigo IS NOT NULL AND b.codigo_barrio IS NULL",
        "construccion con comuna inexistente": "SELECT COUNT(*) FROM construccion c LEFT JOIN comuna m ON m.codigo = c.comuna WHERE c.comuna IS NOT NULL AND m.codigo IS NULL",
        "barrio_estrato con comuna inexistente": "SELECT COUNT(*) FROM barrio_estrato b LEFT JOIN comuna m ON m.codigo = b.comuna WHERE m.codigo IS NULL",
    }
    cur = conn.cursor()
    try:
        salida = {}
        for nombre, sql in consultas.items():
            cur.execute(sql)
            salida[nombre] = int(cur.fetchone()[0])
        return salida
    finally:
        cur.close()


RUTAS_EQUIVALENCIA = ["/health", "/metadata", "/fuentes", "/kpis", "/kpis/K1", "/kpis?kpi_id=K2&grupo=global", "/kpis/sensibilidad", "/kpis/sensibilidad?escenario=S1", "/comunas", "/composicion",
                      "/construcciones", "/construcciones?limit=100&offset=1000", "/construcciones?comuna=02&limit=100", "/construcciones?estrato=3&limit=100",
                      "/construcciones?comuna=02&estrato=3", "/calidad", "/llave/revision"]
CAMPOS_PROPIOS_DEL_ALMACEN = ("almacenamiento",)   # /health y /metadata informan el motor: es lo único que debe diferir


def _sin_motor(cuerpo):
    if isinstance(cuerpo, dict):
        return {k: _sin_motor(v) for k, v in cuerpo.items() if k not in CAMPOS_PROPIOS_DEL_ALMACEN}
    if isinstance(cuerpo, list):
        return [_sin_motor(v) for v in cuerpo]
    return cuerpo


def equivalencia_endpoints(cliente_a, cliente_b, rutas=RUTAS_EQUIVALENCIA):
    """[(ruta, igual, codigo_a, codigo_b)] comparando cuerpo y código de dos clientes de la API (ignora solo el campo que nombra el motor)."""
    salida = []
    for ruta in rutas:
        a, b = cliente_a.get(ruta), cliente_b.get(ruta)
        igual = a.status_code == b.status_code and _sin_motor(a.json()) == _sin_motor(b.json())
        salida.append((ruta, igual, a.status_code, b.status_code))
    return salida
