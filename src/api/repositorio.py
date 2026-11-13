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


def _errores_de_base():
    """Excepciones de base de datos que significan «no disponible» (sqlite3 y, si está instalado, pymysql)."""
    try:
        import pymysql
        return (sqlite3.DatabaseError, pymysql.MySQLError)
    except ImportError:
        return (sqlite3.DatabaseError,)


class RepositorioRelacional(RepositorioGold):
    """Sirve las mismas respuestas desde las tablas relacionales de la ÚLTIMA corrida (MySQL o SQLite con el esquema relacional).

    Una instancia = una conexión ya abierta (de solo lectura en cuanto el motor lo permite); se cierra con cerrar(). SQL siempre con parámetros.
    """

    def __init__(self, conn, dialecto):
        self._conn, self._ph, self._dialecto = conn, {"mysql": "%s", "sqlite": "?"}[dialecto], dialecto
        fila = self._sql("SELECT MAX(id) AS id FROM corrida")
        if not fila or fila[0]["id"] is None:
            self.cerrar()
            raise BaseNoDisponible("la base relacional no tiene ninguna corrida cargada")
        self._corrida = fila[0]["id"]

    def cerrar(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def _sql(self, sql, params=()):
        cur = None
        try:
            cur = self._conn.cursor()
            cur.execute(sql.replace("?", self._ph), params)
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, f)) for f in cur.fetchall()]
        except _errores_de_base() as e:
            raise BaseNoDisponible(type(e).__name__) from e
        finally:
            if cur is not None:
                cur.close()

    def _n(self, tabla):
        return int(self._sql(f"SELECT COUNT(*) AS n FROM {tabla} WHERE corrida_id = ?", (self._corrida,))[0]["n"])  # tabla sale de una lista fija

    def filas_por_tabla(self):
        n_construccion = self._n("construccion")   # silver_integrated y gold_final tienen las mismas construcciones
        return {"silver_integrated": n_construccion, "gold_final": n_construccion, "kpis_gold": self._n("kpi"), "kpis_sensibilidad": self._n("kpi_sensibilidad")}

    def fecha_corte(self):
        f = self._sql("SELECT fecha_corte FROM corrida WHERE id = ?", (self._corrida,))[0]["fecha_corte"]
        return str(f) if f is not None else None

    def kpis(self, kpi_id=None, grupo=None):
        sql, params = ("SELECT kpi_id, nombre, valor, numerador, denominador, grupo, fecha_corte, fuente, ic95_inf, ic95_sup, n_sin_datos, pct_sin_datos, muestra_baja, cota_inf, cota_sup, nota "
                       "FROM kpi WHERE corrida_id = ?"), [self._corrida]
        if kpi_id is not None:
            sql += " AND kpi_id = ?"
            params.append(kpi_id)
        if grupo is not None:
            sql += " AND grupo = ?"
            params.append(grupo)
        filas = self._sql(sql + " ORDER BY orden", params)
        for f in filas:
            f["fecha_corte"] = str(f["fecha_corte"])
        return [_bool(f) for f in filas]

    def sensibilidad(self, escenario=None):
        sql, params = "SELECT escenario, kpi_id, grupo, k, n, tasa, ic95_inf, ic95_sup, nota FROM kpi_sensibilidad WHERE corrida_id = ?", [self._corrida]
        if escenario is not None:
            sql += " AND escenario = ?"
            params.append(escenario)
        return self._sql(sql + " ORDER BY orden", params)

    def comunas(self):
        filas = self._sql("SELECT grupo, numerador, denominador, valor, ic95_inf, ic95_sup, n_sin_datos, pct_sin_datos, muestra_baja FROM kpi WHERE corrida_id = ? AND kpi_id = 'K6' ORDER BY orden", (self._corrida,))
        return [_bool({"comuna": f["grupo"].removeprefix("comuna_"), "n_con_datos": f["denominador"], "severos": f["numerador"], "tasa": f["valor"], "ic95_inf": f["ic95_inf"],
                       "ic95_sup": f["ic95_sup"], "n_sin_datos": f["n_sin_datos"], "pct_sin_datos": f["pct_sin_datos"], "muestra_baja": f["muestra_baja"]}) for f in filas]

    def composicion(self):
        filas = self._sql(f"SELECT comuna, {GRUPO_ESTRATO} AS grupo_estrato, COUNT(*) AS n_con_datos, SUM(severo_estricto) AS severos FROM construccion "
                          "WHERE corrida_id = ? AND sin_datos = 0 AND comuna IS NOT NULL AND estrato IS NOT NULL GROUP BY comuna, grupo_estrato ORDER BY comuna, grupo_estrato", (self._corrida,))
        return [{"comuna": f["comuna"], "grupo_estrato": f["grupo_estrato"], "n_con_datos": int(f["n_con_datos"]), "severos": int(f["severos"])} for f in filas]

    def poblacion(self):
        f = self._sql("SELECT COUNT(*) AS construcciones, SUM(sin_datos = 0) AS con_datos_satelitales, COUNT(DISTINCT comuna) AS comunas, COUNT(DISTINCT codigo_barrio) AS codigos_barrio "
                      "FROM construccion WHERE corrida_id = ?", (self._corrida,))[0]
        return {k: int(v) for k, v in f.items()}

    def construcciones(self, limit, offset, comuna=None, estrato=None, severo_estricto=None):
        donde, params = "WHERE corrida_id = ?", [self._corrida]
        if comuna is not None:
            donde += " AND comuna = ?"
            params.append(comuna)
        if estrato is not None:
            donde += " AND estrato = ?"
            params.append(estrato)
        if severo_estricto is not None:
            donde += " AND severo_estricto = ?"
            params.append(int(severo_estricto))
        total = int(self._sql(f"SELECT COUNT(*) AS n FROM construccion {donde}", params)[0]["n"])
        cols = ", ".join(COLUMNAS_CONSTRUCCION)  # lista blanca
        items = self._sql(f"SELECT {cols} FROM construccion {donde} ORDER BY objectid LIMIT ? OFFSET ?", [*params, limit, offset])
        for f in items:
            for c in ("estrato", "lon", "lat"):
                if f[c] is not None:
                    f[c] = float(f[c])
        return total, [_bool(f) for f in items]

    def revision_llave(self):
        filas = self._sql("SELECT codigo_barrio, nombre_barrio_csv, nombre_poligono, coincide_poligono FROM construccion "
                          "WHERE corrida_id = ? AND nombre_validado = 0 AND codigo_barrio IS NOT NULL ORDER BY objectid", (self._corrida,))
        por_codigo = defaultdict(list)
        for f in filas:
            por_codigo[f["codigo_barrio"]].append(f)
        salida = []
        for codigo in sorted(por_codigo):
            g = por_codigo[codigo]
            dominante = Counter(f["nombre_poligono"] for f in g if f["nombre_poligono"]).most_common(1)
            salida.append({"codigo_barrio": codigo, "n_construcciones": len(g), "nombre_csv_2015": g[0]["nombre_barrio_csv"], "nombre_poligono_dominante": dominante[0][0] if dominante else None,
                           "pct_coincide_poligono": sum(1 for f in g if f["coincide_poligono"]) / len(g)})
        return salida
