-- Esquema relacional equivalente para SQLite (pruebas sin MySQL). Mismas tablas, mismas columnas y mismas reglas que esquema_mysql.sql.
-- Requiere PRAGMA foreign_keys = ON en cada conexion para que se apliquen las claves foraneas.
-- Version del esquema: 1 (parte de la clave de corrida).

CREATE TABLE IF NOT EXISTS corrida (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  clave_corrida TEXT NOT NULL,
  cargada_en TEXT NOT NULL,
  commit_codigo TEXT NOT NULL,
  fecha_corte TEXT NOT NULL,
  version_esquema INTEGER NOT NULL,
  n_barrios INTEGER NOT NULL,
  n_construcciones INTEGER NOT NULL,
  n_kpis INTEGER NOT NULL,
  n_kpis_sensibilidad INTEGER NOT NULL,
  cobertura_llave NUMERIC NOT NULL,
  cobertura_estrato_valido NUMERIC NOT NULL,
  pct_nombre_validado NUMERIC NOT NULL,
  llave_confianza TEXT NOT NULL,
  CONSTRAINT uq_corrida_clave UNIQUE (clave_corrida),
  CONSTRAINT ck_corrida_coberturas CHECK (cobertura_llave BETWEEN 0 AND 1 AND cobertura_estrato_valido BETWEEN 0 AND 1 AND pct_nombre_validado BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS corrida_archivo (
  corrida_id INTEGER NOT NULL,
  nombre TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  filas INTEGER NULL,
  PRIMARY KEY (corrida_id, nombre),
  CONSTRAINT fk_corrida_archivo_corrida FOREIGN KEY (corrida_id) REFERENCES corrida (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS comuna (
  codigo TEXT NOT NULL,
  nombre TEXT NOT NULL,
  PRIMARY KEY (codigo)
);

CREATE TABLE IF NOT EXISTS barrio_estrato (
  corrida_id INTEGER NOT NULL,
  codigo_barrio TEXT NOT NULL,
  barrio TEXT NOT NULL,
  comuna TEXT NOT NULL,
  lados_e1 INTEGER NOT NULL,
  lados_e2 INTEGER NOT NULL,
  lados_e3 INTEGER NOT NULL,
  lados_e4 INTEGER NOT NULL,
  lados_e5 INTEGER NOT NULL,
  lados_e6 INTEGER NOT NULL,
  sin_vivienda INTEGER NOT NULL,
  lados_total INTEGER NOT NULL,
  estrato_moda_original TEXT NOT NULL,
  estrato INTEGER NULL,
  pureza_estrato NUMERIC NULL,
  PRIMARY KEY (corrida_id, codigo_barrio),
  CONSTRAINT fk_barrio_estrato_corrida FOREIGN KEY (corrida_id) REFERENCES corrida (id) ON DELETE RESTRICT,
  CONSTRAINT fk_barrio_estrato_comuna FOREIGN KEY (comuna) REFERENCES comuna (codigo) ON DELETE RESTRICT,
  CONSTRAINT ck_barrio_estrato_estrato CHECK (estrato IS NULL OR estrato BETWEEN 1 AND 6),
  CONSTRAINT ck_barrio_estrato_pureza CHECK (pureza_estrato IS NULL OR pureza_estrato BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS construccion (
  corrida_id INTEGER NOT NULL,
  objectid INTEGER NOT NULL,
  comuna TEXT NULL,
  barrio TEXT NULL,
  codigo_barrio TEXT NULL,
  nombre_barrio_csv TEXT NULL,
  cruza_llave INTEGER NOT NULL,
  barrio_estrato_codigo TEXT NULL,
  estrato INTEGER NULL,
  pureza_estrato NUMERIC NULL,
  n_con_datos_estrato INTEGER NULL,
  n_severos_estrato INTEGER NULL,
  muestra_baja INTEGER NULL,
  npisos INTEGER NULL,
  npisos_cero INTEGER NULL,
  indice_escombros NUMERIC NULL,
  estado_estructural TEXT NOT NULL,
  clase_dano TEXT NOT NULL,
  sin_datos INTEGER NOT NULL,
  severo_estricto INTEGER NULL,
  dano_visible INTEGER NULL,
  geom_duplicada INTEGER NOT NULL,
  lon NUMERIC NOT NULL,
  lat NUMERIC NOT NULL,
  codigo_poligono TEXT NOT NULL,
  nombre_poligono TEXT NOT NULL,
  coincide_poligono INTEGER NULL,
  nombre_validado INTEGER NULL,
  PRIMARY KEY (corrida_id, objectid),
  CONSTRAINT fk_construccion_corrida FOREIGN KEY (corrida_id) REFERENCES corrida (id) ON DELETE RESTRICT,
  CONSTRAINT fk_construccion_barrio FOREIGN KEY (corrida_id, barrio_estrato_codigo) REFERENCES barrio_estrato (corrida_id, codigo_barrio) ON DELETE RESTRICT,
  CONSTRAINT fk_construccion_comuna FOREIGN KEY (comuna) REFERENCES comuna (codigo) ON DELETE RESTRICT,
  CONSTRAINT ck_construccion_estrato CHECK (estrato IS NULL OR estrato BETWEEN 1 AND 6),
  CONSTRAINT ck_construccion_pureza CHECK (pureza_estrato IS NULL OR pureza_estrato BETWEEN 0 AND 1),
  CONSTRAINT ck_construccion_lon CHECK (lon BETWEEN -77 AND -76),
  CONSTRAINT ck_construccion_lat CHECK (lat BETWEEN 3 AND 4),
  CONSTRAINT ck_construccion_banderas CHECK (cruza_llave IN (0, 1) AND sin_datos IN (0, 1) AND geom_duplicada IN (0, 1)),
  CONSTRAINT ck_construccion_enlace CHECK ((cruza_llave = 1 AND barrio_estrato_codigo IS NOT NULL) OR (cruza_llave = 0 AND barrio_estrato_codigo IS NULL)),
  CONSTRAINT ck_construccion_severo CHECK ((sin_datos = 1 AND severo_estricto IS NULL AND dano_visible IS NULL) OR (sin_datos = 0 AND severo_estricto IN (0, 1) AND dano_visible IN (0, 1)))
);
CREATE INDEX IF NOT EXISTS ix_construccion_barrio ON construccion (corrida_id, barrio_estrato_codigo);
CREATE INDEX IF NOT EXISTS ix_construccion_comuna ON construccion (comuna);
CREATE INDEX IF NOT EXISTS ix_construccion_estrato ON construccion (corrida_id, estrato);
CREATE INDEX IF NOT EXISTS ix_construccion_severo ON construccion (corrida_id, severo_estricto);
CREATE INDEX IF NOT EXISTS ix_construccion_nombre_validado ON construccion (corrida_id, nombre_validado);

CREATE TABLE IF NOT EXISTS kpi (
  corrida_id INTEGER NOT NULL,
  orden INTEGER NOT NULL,
  kpi_id TEXT NOT NULL,
  nombre TEXT NOT NULL,
  valor REAL NOT NULL,
  numerador REAL NULL,
  denominador REAL NULL,
  grupo TEXT NOT NULL,
  fecha_corte TEXT NOT NULL,
  fuente TEXT NOT NULL,
  ic95_inf REAL NULL,
  ic95_sup REAL NULL,
  n_sin_datos REAL NULL,
  pct_sin_datos REAL NULL,
  muestra_baja INTEGER NOT NULL,
  cota_inf REAL NULL,
  cota_sup REAL NULL,
  nota TEXT NULL,
  PRIMARY KEY (corrida_id, kpi_id, grupo),
  CONSTRAINT fk_kpi_corrida FOREIGN KEY (corrida_id) REFERENCES corrida (id) ON DELETE RESTRICT,
  CONSTRAINT ck_kpi_valor CHECK (grupo LIKE 'razon%' OR valor BETWEEN 0 AND 1),
  CONSTRAINT ck_kpi_intervalo CHECK (grupo LIKE 'razon%' OR grupo LIKE 'diferencia%' OR ((ic95_inf IS NULL OR ic95_inf BETWEEN 0 AND 1) AND (ic95_sup IS NULL OR ic95_sup BETWEEN 0 AND 1)))
);
CREATE INDEX IF NOT EXISTS ix_kpi_orden ON kpi (corrida_id, orden);

CREATE TABLE IF NOT EXISTS kpi_sensibilidad (
  corrida_id INTEGER NOT NULL,
  orden INTEGER NOT NULL,
  escenario TEXT NOT NULL,
  kpi_id TEXT NOT NULL,
  grupo TEXT NOT NULL,
  k INTEGER NULL,
  n INTEGER NULL,
  tasa REAL NULL,
  ic95_inf REAL NULL,
  ic95_sup REAL NULL,
  nota TEXT NOT NULL,
  PRIMARY KEY (corrida_id, escenario, kpi_id, grupo),
  CONSTRAINT fk_kpi_sensibilidad_corrida FOREIGN KEY (corrida_id) REFERENCES corrida (id) ON DELETE RESTRICT,
  CONSTRAINT ck_kpi_sensibilidad_tasa CHECK (tasa IS NULL OR grupo LIKE 'razon%' OR grupo LIKE 'diferencia%' OR tasa BETWEEN 0 AND 1),
  CONSTRAINT ck_kpi_sensibilidad_intervalo CHECK (grupo LIKE 'razon%' OR grupo LIKE 'diferencia%' OR ((ic95_inf IS NULL OR ic95_inf BETWEEN 0 AND 1) AND (ic95_sup IS NULL OR ic95_sup BETWEEN 0 AND 1)))
);
CREATE INDEX IF NOT EXISTS ix_kpi_sensibilidad_orden ON kpi_sensibilidad (corrida_id, orden);
