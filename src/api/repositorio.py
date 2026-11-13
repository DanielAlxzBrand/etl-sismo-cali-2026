"""Acceso a datos de Gold detrás de una interfaz; hoy SQLite en solo lectura (la carga relacional agregará MySQL por configuración)."""
import sqlite3
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from pathlib import Path

from src.api.errores import BaseNoDisponible

TABLAS = ("silver_integrated", "gold_final", "kpis_gold", "kpis_sensibilidad")  # lista blanca: nunca viene del usuario
COLUMNAS_CONSTRUCCION = ("objectid", "comuna", "barrio", "codigo_barrio", "nombre_barrio_csv", "estrato", "sin_datos", "severo_estricto",
                         "estado_estructural", "clase_dano", "lon", "lat", "coincide_poligono", "nombre_validado")
BOOLEANAS = {"sin_datos", "severo_estricto", "coincide_poligono", "nombre_validado", "muestra_baja"}
GRUPO_ESTRATO = "CASE WHEN estrato IN (1, 2) THEN '1-2' WHEN estrato IN (3, 4, 5) THEN '3-5' WHEN estrato = 6 THEN '6' END"


class RepositorioGold(ABC):
    """Operaciones de lectura que necesitan los endpoints."""

    @abstractmethod
    def filas_por_tabla(self): ...
    @abstractmethod
    def fecha_corte(self): ...
    @abstractmethod
    def kpis(self, kpi_id=None, grupo=None): ...
    @abstractmethod
    def sensibilidad(self, escenario=None): ...
    @abstractmethod
    def comunas(self): ...
    @abstractmethod
    def composicion(self): ...
    @abstractmethod
    def poblacion(self): ...
    @abstractmethod
    def construcciones(self, limit, offset, comuna=None, estrato=None, severo_estricto=None): ...
    @abstractmethod
    def revision_llave(self): ...
    @abstractmethod
    def cerrar(self): ...


def _filas(cursor):
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, f)) for f in cursor.fetchall()]


def _bool(fila):
    for c in BOOLEANAS & fila.keys():
        if fila[c] is not None:
            fila[c] = bool(fila[c])
    return fila


class RepositorioSqlite(RepositorioGold):
    """Una instancia = una conexión abierta con URI de solo lectura; se cierra con cerrar()."""

    def __init__(self, ruta):
        ruta = Path(ruta)
        if not ruta.is_file():
            raise BaseNoDisponible(f"no existe {ruta.name}")
        self._conn = None
        try:
            # mode=ro: cualquier INSERT/UPDATE/DELETE falla con OperationalError; check_same_thread=False porque FastAPI
            # puede abrir la conexión en un hilo y usarla en otro, siempre de forma secuencial dentro de una solicitud
            self._conn = sqlite3.connect(f"{ruta.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False)
        except sqlite3.Error as e:
            self.cerrar()
            raise BaseNoDisponible(str(e)) from e

    def cerrar(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _sql(self, sql, params=()):
        try:
            return _filas(self._conn.execute(sql, params))
        except sqlite3.DatabaseError as e:
            raise BaseNoDisponible(str(e)) from e

    def filas_por_tabla(self):
        return {t: self._sql(f"SELECT COUNT(*) AS n FROM {t}")[0]["n"] for t in TABLAS}  # t sale de la lista blanca

    def fecha_corte(self):
        f = self._sql("SELECT MAX(fecha_corte) AS f FROM kpis_gold")
        return f[0]["f"] if f else None

    def kpis(self, kpi_id=None, grupo=None):
        sql, params = "SELECT * FROM kpis_gold WHERE 1=1", []
        if kpi_id is not None:
            sql += " AND kpi_id = ?"
            params.append(kpi_id)
        if grupo is not None:
            sql += " AND grupo = ?"
            params.append(grupo)
        return [_bool(f) for f in self._sql(sql + " ORDER BY rowid", params)]

    def sensibilidad(self, escenario=None):
        sql, params = "SELECT * FROM kpis_sensibilidad", []
        if escenario is not None:
            sql += " WHERE escenario = ?"
            params.append(escenario)
        return self._sql(sql + " ORDER BY rowid", params)

    def comunas(self):
        filas = self._sql("SELECT grupo, numerador, denominador, valor, ic95_inf, ic95_sup, n_sin_datos, pct_sin_datos, muestra_baja "
                          "FROM kpis_gold WHERE kpi_id = 'K6' ORDER BY rowid")
        return [_bool({"comuna": f["grupo"].removeprefix("comuna_"), "n_con_datos": f["denominador"], "severos": f["numerador"], "tasa": f["valor"],
                       "ic95_inf": f["ic95_inf"], "ic95_sup": f["ic95_sup"], "n_sin_datos": f["n_sin_datos"], "pct_sin_datos": f["pct_sin_datos"],
                       "muestra_baja": f["muestra_baja"]}) for f in filas]

    def composicion(self):
        # solo COUNT y SUM de indicadores ya calculados por fila; no se recalcula ningún KPI
        return self._sql(f"SELECT comuna, {GRUPO_ESTRATO} AS grupo_estrato, COUNT(*) AS n_con_datos, SUM(severo_estricto) AS severos "
                         "FROM gold_final WHERE sin_datos = 0 AND comuna IS NOT NULL AND estrato IS NOT NULL "
                         "GROUP BY comuna, grupo_estrato ORDER BY comuna, grupo_estrato")

    def poblacion(self):
        return self._sql("SELECT COUNT(*) AS construcciones, SUM(sin_datos = 0) AS con_datos_satelitales, COUNT(DISTINCT comuna) AS comunas, "
                         "COUNT(DISTINCT codigo_barrio) AS codigos_barrio FROM gold_final")[0]

    def construcciones(self, limit, offset, comuna=None, estrato=None, severo_estricto=None):
        donde, params = "WHERE 1=1", []
        if comuna is not None:
            donde += " AND comuna = ?"
            params.append(comuna)
        if estrato is not None:
            donde += " AND estrato = ?"
            params.append(estrato)
        if severo_estricto is not None:
            donde += " AND severo_estricto = ?"
            params.append(int(severo_estricto))
        total = self._sql(f"SELECT COUNT(*) AS n FROM gold_final {donde}", params)[0]["n"]
        cols = ", ".join(COLUMNAS_CONSTRUCCION)  # lista blanca
        items = self._sql(f"SELECT {cols} FROM gold_final {donde} ORDER BY objectid LIMIT ? OFFSET ?", [*params, limit, offset])
        return total, [_bool(f) for f in items]

    def revision_llave(self):
        filas = self._sql("SELECT codigo_barrio, nombre_barrio_csv, nombre_poligono, coincide_poligono FROM silver_integrated "
                          "WHERE nombre_validado = 0 AND codigo_barrio IS NOT NULL ORDER BY objectid")
        por_codigo = defaultdict(list)
        for f in filas:
            por_codigo[f["codigo_barrio"]].append(f)
        salida = []
        for codigo in sorted(por_codigo):
            g = por_codigo[codigo]
            dominante = Counter(f["nombre_poligono"] for f in g if f["nombre_poligono"]).most_common(1)
            salida.append({"codigo_barrio": codigo, "n_construcciones": len(g), "nombre_csv_2015": g[0]["nombre_barrio_csv"],
                           "nombre_poligono_dominante": dominante[0][0] if dominante else None,
                           "pct_coincide_poligono": sum(1 for f in g if f["coincide_poligono"]) / len(g)})
        return salida
