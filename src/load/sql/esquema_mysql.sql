-- Esquema relacional del proyecto para MySQL 8.0 (InnoDB, utf8mb4). Las columnas de datos conservan los nombres de los CSV.
-- Cada tabla de datos lleva corrida_id: una corrida es una fotografia completa y la historia es la suma de corridas.
-- Los comentarios de columna de este archivo alimentan el diccionario de docs/almacenamiento/modelo_datos.md.
-- Version del esquema: 1 (parte de la clave de corrida).

CREATE TABLE IF NOT EXISTS corrida (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'identificador de la corrida',
  clave_corrida CHAR(64) NOT NULL COMMENT 'sha256 de las huellas de los archivos de entrada ordenadas mas la version del esquema',
  cargada_en DATETIME(6) NOT NULL COMMENT 'momento de la carga en UTC',
  commit_codigo VARCHAR(40) NOT NULL COMMENT 'commit de git del codigo que cargo (desconocido si no hay git)',
  fecha_corte DATE NOT NULL COMMENT 'fecha de edicion de la capa de origen (config.yaml)',
  version_esquema SMALLINT UNSIGNED NOT NULL COMMENT 'version de este esquema',
  n_barrios INT UNSIGNED NOT NULL COMMENT 'filas cargadas en barrio_estrato',
  n_construcciones INT UNSIGNED NOT NULL COMMENT 'filas cargadas en construccion',
  n_kpis INT UNSIGNED NOT NULL COMMENT 'filas cargadas en kpi',
  n_kpis_sensibilidad INT UNSIGNED NOT NULL COMMENT 'filas cargadas en kpi_sensibilidad',
  cobertura_llave DECIMAL(7,6) NOT NULL COMMENT 'cobertura de la llave (quality_report.json)',
  cobertura_estrato_valido DECIMAL(7,6) NOT NULL COMMENT 'cobertura de estrato valido (quality_report.json)',
  pct_nombre_validado DECIMAL(7,6) NOT NULL COMMENT 'proporcion de nombres validados (quality_report.json)',
  llave_confianza VARCHAR(10) NOT NULL COMMENT 'confianza de la llave (quality_report.json)',
  PRIMARY KEY (id),
  UNIQUE KEY uq_corrida_clave (clave_corrida),
  CONSTRAINT ck_corrida_coberturas CHECK (cobertura_llave BETWEEN 0 AND 1 AND cobertura_estrato_valido BETWEEN 0 AND 1 AND pct_nombre_validado BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='una fila por carga con datos distintos';

CREATE TABLE IF NOT EXISTS corrida_archivo (
  corrida_id BIGINT UNSIGNED NOT NULL COMMENT 'corrida a la que pertenece',
  nombre VARCHAR(120) NOT NULL COMMENT 'ruta relativa del archivo de entrada',
  sha256 CHAR(64) NOT NULL COMMENT 'huella del archivo',
  filas INT UNSIGNED NULL COMMENT 'filas de datos del archivo (nulo si no es tabular)',
  PRIMARY KEY (corrida_id, nombre),
  CONSTRAINT fk_corrida_archivo_corrida FOREIGN KEY (corrida_id) REFERENCES corrida (id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='archivos de entrada de cada corrida con su huella';

CREATE TABLE IF NOT EXISTS comuna (
  codigo CHAR(2) NOT NULL COMMENT 'codigo de la comuna con dos digitos',
  nombre VARCHAR(20) NOT NULL COMMENT 'nombre derivado del codigo (Comuna N)',
  PRIMARY KEY (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='comunas presentes en el CSV de estrato y en las construcciones';

CREATE TABLE IF NOT EXISTS barrio_estrato (
  corrida_id BIGINT UNSIGNED NOT NULL COMMENT 'corrida a la que pertenece',
  codigo_barrio VARCHAR(6) NOT NULL COMMENT 'llave comuna por 100 mas barrio',
  barrio VARCHAR(64) NOT NULL COMMENT 'nombre del barrio en el CSV de estrato 2015',
  comuna CHAR(2) NOT NULL COMMENT 'comuna derivada del codigo del barrio',
  lados_e1 INT UNSIGNED NOT NULL COMMENT 'lados de manzana de estrato 1',
  lados_e2 INT UNSIGNED NOT NULL COMMENT 'lados de manzana de estrato 2',
  lados_e3 INT UNSIGNED NOT NULL COMMENT 'lados de manzana de estrato 3',
  lados_e4 INT UNSIGNED NOT NULL COMMENT 'lados de manzana de estrato 4',
  lados_e5 INT UNSIGNED NOT NULL COMMENT 'lados de manzana de estrato 5',
  lados_e6 INT UNSIGNED NOT NULL COMMENT 'lados de manzana de estrato 6',
  sin_vivienda INT UNSIGNED NOT NULL COMMENT 'lados de manzana sin vivienda',
  lados_total INT UNSIGNED NOT NULL COMMENT 'suma de los lados de manzana por estrato',
  estrato_moda_original VARCHAR(2) NOT NULL COMMENT 'estrato moda tal como viene en el CSV',
  estrato TINYINT UNSIGNED NULL COMMENT 'estrato moda validado de 1 a 6 (nulo si no aplica)',
  pureza_estrato DECIMAL(7,6) NULL COMMENT 'maximo de lados por estrato sobre su suma',
  PRIMARY KEY (corrida_id, codigo_barrio),
  KEY ix_barrio_estrato_comuna (comuna),
  CONSTRAINT fk_barrio_estrato_corrida FOREIGN KEY (corrida_id) REFERENCES corrida (id) ON DELETE RESTRICT,
  CONSTRAINT fk_barrio_estrato_comuna FOREIGN KEY (comuna) REFERENCES comuna (codigo) ON DELETE RESTRICT,
  CONSTRAINT ck_barrio_estrato_estrato CHECK (estrato IS NULL OR estrato BETWEEN 1 AND 6),
  CONSTRAINT ck_barrio_estrato_pureza CHECK (pureza_estrato IS NULL OR pureza_estrato BETWEEN 0 AND 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='estrato por barrio de 2015 (incluye barrios sin construcciones)';

CREATE TABLE IF NOT EXISTS construccion (
  corrida_id BIGINT UNSIGNED NOT NULL COMMENT 'corrida a la que pertenece',
  objectid INT UNSIGNED NOT NULL COMMENT 'identificador de la construccion en la capa',
  comuna CHAR(2) NULL COMMENT 'codigo catastral de la comuna (nulo si venia en blanco)',
  barrio CHAR(2) NULL COMMENT 'codigo catastral del barrio dentro de la comuna',
  codigo_barrio VARCHAR(6) NULL COMMENT 'llave comuna por 100 mas barrio tal como esta en Gold',
  nombre_barrio_csv VARCHAR(64) NULL COMMENT 'nombre del barrio en el CSV de estrato (nulo si no cruza)',
  cruza_llave TINYINT(1) NOT NULL COMMENT 'la llave existe en el CSV de estrato',
  barrio_estrato_codigo VARCHAR(6) NULL COMMENT 'enlace a barrio_estrato (nulo si la construccion no cruza)',
  estrato TINYINT UNSIGNED NULL COMMENT 'estrato moda del barrio',
  pureza_estrato DECIMAL(7,6) NULL COMMENT 'pureza del estrato del barrio',
  n_con_datos_estrato INT UNSIGNED NULL COMMENT 'construcciones con datos del estrato',
  n_severos_estrato INT UNSIGNED NULL COMMENT 'severos del estrato',
  muestra_baja TINYINT(1) NULL COMMENT 'menos de 30 severos en el estrato',
  npisos SMALLINT UNSIGNED NULL COMMENT 'numero de pisos',
  npisos_cero TINYINT(1) NULL COMMENT 'bandera de cero pisos',
  indice_escombros DECIMAL(18,12) NULL COMMENT 'indice continuo de cambio de textura (nulo si no hay datos satelitales)',
  estado_estructural VARCHAR(48) NOT NULL COMMENT 'etiqueta original de la capa',
  clase_dano VARCHAR(16) NOT NULL COMMENT 'clase estable derivada de la etiqueta',
  sin_datos TINYINT(1) NOT NULL COMMENT 'sin datos satelitales',
  severo_estricto TINYINT(1) NULL COMMENT 'cambio satelital severo (severo estricto, proxy de dano) - nulo si no hay datos',
  dano_visible TINYINT(1) NULL COMMENT 'sensibilidad: escombros o techo - nulo si no hay datos',
  geom_duplicada TINYINT(1) NOT NULL COMMENT 'comparte geometria con otra construccion',
  lon DECIMAL(10,7) NOT NULL COMMENT 'longitud del centroide en grados',
  lat DECIMAL(10,7) NOT NULL COMMENT 'latitud del centroide en grados',
  codigo_poligono VARCHAR(6) NOT NULL COMMENT 'codigo del poligono donde cae el centroide',
  nombre_poligono VARCHAR(80) NOT NULL COMMENT 'nombre del poligono',
  coincide_poligono TINYINT(1) NULL COMMENT 'el codigo del poligono coincide con el codigo del barrio',
  nombre_validado TINYINT(1) NULL COMMENT 'el nombre del CSV coincide con el del poligono dominante',
  PRIMARY KEY (corrida_id, objectid),
  KEY ix_construccion_barrio (corrida_id, barrio_estrato_codigo),
  KEY ix_construccion_comuna (comuna),
  KEY ix_construccion_estrato (corrida_id, estrato),
  KEY ix_construccion_severo (corrida_id, severo_estricto),
  KEY ix_construccion_nombre_validado (corrida_id, nombre_validado),
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='construcciones evaluadas por satelite (gold_final)';

CREATE TABLE IF NOT EXISTS kpi (
  corrida_id BIGINT UNSIGNED NOT NULL COMMENT 'corrida a la que pertenece',
  orden SMALLINT UNSIGNED NOT NULL COMMENT 'posicion de la fila en kpis_gold.csv',
  kpi_id VARCHAR(4) NOT NULL COMMENT 'identificador del indicador (K1 a K6)',
  nombre VARCHAR(80) NOT NULL COMMENT 'nombre del indicador',
  valor DOUBLE NOT NULL COMMENT 'valor del indicador (tasa, razon o proporcion)',
  numerador DOUBLE NULL COMMENT 'numerador',
  denominador DOUBLE NULL COMMENT 'denominador (construcciones con datos satelitales)',
  grupo VARCHAR(48) NOT NULL COMMENT 'grupo o corte del indicador',
  fecha_corte DATE NOT NULL COMMENT 'fecha de corte de la capa',
  fuente VARCHAR(255) NOT NULL COMMENT 'fuente declarada del calculo',
  ic95_inf DOUBLE NULL COMMENT 'limite inferior del intervalo al 95 por ciento',
  ic95_sup DOUBLE NULL COMMENT 'limite superior del intervalo al 95 por ciento',
  n_sin_datos DOUBLE NULL COMMENT 'construcciones sin datos satelitales',
  pct_sin_datos DOUBLE NULL COMMENT 'proporcion sin datos satelitales',
  muestra_baja TINYINT(1) NOT NULL COMMENT 'menos de 30 severos',
  cota_inf DOUBLE NULL COMMENT 'cota inferior por sin datos',
  cota_sup DOUBLE NULL COMMENT 'cota superior por sin datos',
  nota VARCHAR(512) NULL COMMENT 'nota del indicador',
  PRIMARY KEY (corrida_id, kpi_id, grupo),
  KEY ix_kpi_orden (corrida_id, orden),
  CONSTRAINT fk_kpi_corrida FOREIGN KEY (corrida_id) REFERENCES corrida (id) ON DELETE RESTRICT,
  CONSTRAINT ck_kpi_valor CHECK (grupo LIKE 'razon%' OR valor BETWEEN 0 AND 1),
  CONSTRAINT ck_kpi_intervalo CHECK (grupo LIKE 'razon%' OR grupo LIKE 'diferencia%' OR ((ic95_inf IS NULL OR ic95_inf BETWEEN 0 AND 1) AND (ic95_sup IS NULL OR ic95_sup BETWEEN 0 AND 1)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='indicadores de Gold (kpis_gold)';

CREATE TABLE IF NOT EXISTS kpi_sensibilidad (
  corrida_id BIGINT UNSIGNED NOT NULL COMMENT 'corrida a la que pertenece',
  orden SMALLINT UNSIGNED NOT NULL COMMENT 'posicion de la fila en kpis_sensibilidad.csv',
  escenario VARCHAR(4) NOT NULL COMMENT 'escenario de sensibilidad (S0 a S5)',
  kpi_id VARCHAR(4) NOT NULL COMMENT 'indicador',
  grupo VARCHAR(48) NOT NULL COMMENT 'grupo o corte',
  k INT UNSIGNED NULL COMMENT 'severos',
  n INT UNSIGNED NULL COMMENT 'construcciones con datos',
  tasa DOUBLE NULL COMMENT 'k sobre n, razon o diferencia segun el grupo',
  ic95_inf DOUBLE NULL COMMENT 'limite inferior del intervalo al 95 por ciento',
  ic95_sup DOUBLE NULL COMMENT 'limite superior del intervalo al 95 por ciento',
  nota VARCHAR(512) NOT NULL COMMENT 'descripcion del escenario',
  PRIMARY KEY (corrida_id, escenario, kpi_id, grupo),
  KEY ix_kpi_sensibilidad_orden (corrida_id, orden),
  CONSTRAINT fk_kpi_sensibilidad_corrida FOREIGN KEY (corrida_id) REFERENCES corrida (id) ON DELETE RESTRICT,
  CONSTRAINT ck_kpi_sensibilidad_tasa CHECK (tasa IS NULL OR grupo LIKE 'razon%' OR grupo LIKE 'diferencia%' OR tasa BETWEEN 0 AND 1),
  CONSTRAINT ck_kpi_sensibilidad_intervalo CHECK (grupo LIKE 'razon%' OR grupo LIKE 'diferencia%' OR ((ic95_inf IS NULL OR ic95_inf BETWEEN 0 AND 1) AND (ic95_sup IS NULL OR ic95_sup BETWEEN 0 AND 1)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='sensibilidades de los indicadores (kpis_sensibilidad)';
