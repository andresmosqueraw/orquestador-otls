def estructura_intermedia():
    """
    Guarda el script SQL de la estructura de datos intermedia
    en un archivo llamado 'estructura_intermedia.sql'.
    """
    sql_script = """    

/***********************************************************************************
             Creación de estructura de datos intermedia 
        	Migración del PARAMO  al modelo LADM_COL-POMCAS
              ----------------------------------------------------------
        begin           : 2024-10-21
        git sha         : :%H$
        copyright       : (C) 2024 by Leo Cardona (CEICOL SAS)
                          (C) 2024 by Cesar Alfonso Basurto (CEICOL SAS)        
        email           : contacto@ceicol.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 **********************************************************************************/

--====================================================
-- Creación de la extensión postgis
--====================================================
CREATE EXTENSION IF NOT EXISTS postgis;

--====================================================
-- Creación de la extensión uuid
--====================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

--====================================================
-- Inserción del sistema origen unico nacional
--====================================================
INSERT into spatial_ref_sys (
  srid, auth_name, auth_srid, proj4text, srtext
)
values
  (
    9377,
    'EPSG',
    9377,
    '+proj=tmerc +lat_0=4.0 +lon_0=-73.0 +k=0.9992 +x_0=5000000 +y_0=2000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs ',
    'PROJCRS["MAGNA-SIRGAS / Origen-Nacional", BASEGEOGCRS["MAGNA-SIRGAS", DATUM["Marco Geocentrico Nacional de Referencia", ELLIPSOID["GRS 1980",6378137,298.257222101, LENGTHUNIT["metre",1]]], PRIMEM["Greenwich",0, ANGLEUNIT["degree",0.0174532925199433]], ID["EPSG",4686]], CONVERSION["Colombia Transverse Mercator", METHOD["Transverse Mercator", ID["EPSG",9807]], PARAMETER["Latitude of natural origin",4, ANGLEUNIT["degree",0.0174532925199433], ID["EPSG",8801]], PARAMETER["Longitude of natural origin",-73, ANGLEUNIT["degree",0.0174532925199433], ID["EPSG",8802]], PARAMETER["Scale factor at natural origin",0.9992, SCALEUNIT["unity",1], ID["EPSG",8805]], PARAMETER["False easting",5000000, LENGTHUNIT["metre",1], ID["EPSG",8806]], PARAMETER["False northing",2000000, LENGTHUNIT["metre",1], ID["EPSG",8807]]], CS[Cartesian,2], AXIS["northing (N)",north, ORDER[1], LENGTHUNIT["metre",1]], AXIS["easting (E)",east, ORDER[2], LENGTHUNIT["metre",1]], USAGE[ SCOPE["unknown"], AREA["Colombia"], BBOX[-4.23,-84.77,15.51,-66.87]], ID["EPSG",9377]]'
  ) ON CONFLICT (srid) DO NOTHING;
  
--========================================
--Creación de esquema
--========================================
CREATE schema IF NOT EXISTS estructura_intermedia;

--========================================
--Fijar esquema
--========================================
set search_path to 
	estructura_intermedia,	--Nombre del esquema de estructura de datos intermedia
	public;

--=============================================
-- Agrupación Interesados
--=============================================
-- Crear tabla pmc_interesado
CREATE TABLE pmc_interesado (
    id VARCHAR(255) PRIMARY KEY, -- INT_NUMERO
    tipo VARCHAR(255),
    observacion VARCHAR(255),
    nombre VARCHAR(255),
	sigla varchar (255),
    tipo_interesado VARCHAR(255),
    tipo_documento VARCHAR(255),
    numero_documento VARCHAR(255)
);

-- Crear tabla pmc_agrupacioninteresados
CREATE TABLE pmc_agrupacioninteresados (
    id VARCHAR(255) PRIMARY KEY, -- AGR_numero
    tipo VARCHAR(255),
    nombre VARCHAR(255),
    tipo_interesado VARCHAR(255),
	car VARCHAR(255),
	area_pomca VARCHAR(255)
);


-- Crear tabla col_miembros sin claves foráneas
CREATE TABLE col_miembros (
    interesado_pmc_interesado VARCHAR(255), -- Nombre del interesado
    agrupacion VARCHAR(255),               -- Nombre de la agrupación
    area_pomca VARCHAR(255),               -- Nombre del área del páramo, 
	participacion VARCHAR(255)    
);

--=============================================
-- Área de reserva PARAMO
--=============================================
--DROP TABLE IF exists pmc_uab_areapomca;
CREATE TABLE pmc_uab_areapomca (
	uab_identificador varchar(255) NOT NULL, 
	uab_identificador_insumo varchar(255) NOT NULL, 
    uab_nombre_pomca varchar(255) NOT null,
    uab_estado varchar(255) NOT null,
	uab_fase varchar(255) NOT null,
	uab_area_hidrografica varchar(255) NOT null,
	uab_zona_hidrografica varchar(255) NOT null,
	uab_subzona_hidrografica varchar(255) NOT null,
	uab_nombre varchar(255) NULL, 
	ue_geometria public.geometry(multipolygonz, 9377) NULL, 
    pmc_interesado VARCHAR(1000),
	pmc_agrupacioninteresados VARCHAR(1000), -- Nueva columna para agrupación del interesado
	fuente_administrativa_tipo varchar(255) NOT NULL,
	fuente_administrativa_estado_disponibilidad varchar(255) NOT NULL, -- Indica si la fuente está o no disponible y en qué condiciones. También puede indicar porqué ha dejado de estar disponible, si ha ocurrido.
	fuente_administrativa_tipo_formato varchar(255) NULL, -- Tipo de formato en el que es presentada la fuente, de acuerdo con el registro de metadatos.
	fuente_administrativa_fecha_documento_fuente varchar(255) NULL, -- Fecha de expedición del documento de la fuente.
	fuente_administrativa_nombre varchar(255) null, -- Nombre de la fuente, ejemplo: número de la resolución, número de la escritura pública o número de radicado de una sentencia.
	ddr_tipo_resposabilidad varchar(255) null,
	ddr_tipo_derecho varchar(255) NULL
);


--=============================================
-- Zonificacion POMCA
--=============================================
--DROP TABLE IF exists pmc_uab_zonificacion;
CREATE TABLE estructura_intermedia.pmc_uab_zonificacion (
	uab_identificador varchar(1000) NOT NULL, 
	uab_tipo_zona varchar(1000) NULL,
	uab_detalle_zona varchar(1000) NULL,
	uab_areapomca varchar(255) NOT NULL,
	uab_nombre varchar(255) NULL, -- Nombre que recibe la unidad administrativa básica, en muchos casos toponímico, especialmente en terrenos rústicos.
	ue_geometria public.geometry(multipolygonz, 9377) NULL, -- Materialización del método createArea(). Almacena de forma permanente la geometría de tipo poligonal.
	pmc_interesado VARCHAR(1000), -- Nueva columna para agrupación del interesado
	pmc_agrupacioninteresados VARCHAR(1000), -- Nueva columna para agrupación del interesado
	fuente_administrativa_tipo varchar(255) NOT NULL,
	fuente_administrativa_estado_disponibilidad varchar(255) NOT NULL, -- Indica si la fuente está o no disponible y en qué condiciones. También puede indicar porqué ha dejado de estar disponible, si ha ocurrido.
	fuente_administrativa_tipo_formato varchar(255) NULL, -- Tipo de formato en el que es presentada la fuente, de acuerdo con el registro de metadatos.
	fuente_administrativa_fecha_documento_fuente date NULL, -- Fecha de expedición del documento de la fuente.
	fuente_administrativa_nombre varchar(255) null, -- Nombre de la fuente, ejemplo: número de la resolución, número de la escritura pública o número de radicado de una sentencia.
	ddr_tipo_resposabilidad varchar(255) null,
	ddr_tipo_derecho varchar(255) NULL
);


--=============================================
-- Fuente Administrativa PARAMO
--=============================================
--DROP TABLE IF exists pmc_fuenteadministrativa;
CREATE TABLE pmc_fuenteadministrativa (
	uab_identificador varchar(15) NOT NULL, -- Interno con el cual se identifica la reserva a la cual se está haciendo la compensación
	fuente_administrativa_fecha_documento_fuente date NULL, -- Fecha de expedición del documento de la fuente.
	fuente_administrativa_tipo_formato varchar(255) NULL, -- Tipo de formato en el que es presentada la fuente, de acuerdo con el registro de metadatos.
	fuente_administrativa_numero varchar(255) null,
	fuente_administrativa_anio int4 null
);

--=============================================
-----------------------------------------------
-- Funciones de homologacion PARAMO
-----------------------------------------------
--=============================================

--=============================================
-- Funcion de homologacion a texto
--=============================================
--DROP FUNCTION IF exists homologar_texto;
CREATE OR REPLACE FUNCTION homologar_texto(texto_input TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN upper(
        regexp_replace(
            translate(trim(texto_input), 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 
            '\s+', '', 
            'g'
        )
    );
END;
$$ LANGUAGE plpgsql;

--=============================================
-- Funcion de homologacion a numero
--=============================================
--DROP FUNCTION IF exists estructura_intermedia.homologar_numero;
CREATE OR REPLACE FUNCTION estructura_intermedia.homologar_numero(texto TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN regexp_replace(texto, '[^0-9]', '', 'g');
END;
$$ LANGUAGE plpgsql;

    """
    return sql_script

def transformacion_datos():
    """
    Guarda el script SQL de la estructura de datos intermedia
    en un archivo llamado 'estructura_intermedia.sql'.
    """
    sql_script = """    
/**********************************************************************************
            ETL de tranformación de insumos a datos de estructura intermedia
        			Migración de Pomcas al modelo LADM_COL-PMC
              ----------------------------------------------------------
        begin           : 2024-10-21
        git sha         : :%H$
        email           : contacto@ceicol.com
 **********************************************************************************/
/***************************************************************************
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 ***************************************************************************/
---------------------------------------------------------------------------
-- Fijar esquema
---------------------------------------------------------------------------
SET search_path TO public,estructura_intermedia;

---------------------------------------------------------------------------
-- INTERESADOS
---------------------------------------------------------------------------
-- TRUNCATE TABLE pmc_interesado;
-- Insertar datos en ladm_pmc_interesado con un SELECT
INSERT INTO pmc_interesado (
    id, 
    nombre,
    tipo_interesado,
    tipo_documento,
    sigla,
    numero_documento
)
SELECT 
    ('INT_' || row_number() OVER (ORDER BY nombre))::varchar(255) AS id,
    nombre::varchar(255) AS nombre,
    'Persona_Juridica'::varchar(255) AS tipo_interesado,
    'NIT'::varchar(255) AS tipo_documento,
    autoridad_ambiental::varchar(255) AS sigla,
    nit::varchar(255) AS numero_documento
FROM insumos.corporaciones
GROUP BY nombre, autoridad_ambiental, nit;

-- TRUNCATE TABLE estructura_intermedia.pmc_agrupacioninteresados;
INSERT INTO estructura_intermedia.pmc_agrupacioninteresados (
    id, 
    tipo,
    nombre,
    tipo_interesado,
    car,
    area_pomca
)
SELECT
    ('AGR_' || row_number() OVER (ORDER BY cod_pomca))::varchar(255)AS id,
    'Grupo_Empresarial'::varchar(255) AS tipo,
    ('Comisión Conjunta POMCA ' || cod_pomca || ' - ' || nom_pomca)
        ::varchar(255) AS nombre,
    'Persona_Juridica'::varchar(255) AS tipo_interesado,
    CASE 
        WHEN car_cc ~ '\(.*\)'
             THEN SUBSTRING(car_cc FROM '\(([^)]*)\)')
        ELSE car_cc
    END::varchar(255) AS car,
    cod_pomca::varchar(255) AS area_pomca
FROM insumos.area_pomca
WHERE
      (
          -- Variantes de “comisión conjunta”
          car_cc ~* 'C[O0]M+I+S+I+[ÓO]?[NÑ][^A-Z0-9]{0,5}C[O0]N+[JH]+[UO]+[N]?T+A*'
          OR
          -- Al menos dos patrones “NOMBRE + número”
          car_cc ~ '([A-ZÁÉÍÓÚÑ]{2,}\s?[0-9]+[,\.]?[0-9]*.*){2,}'
      )
  AND cod_pomca IS NOT NULL;


-- TRUNCATE TABLE estructura_intermedia.col_miembros;
INSERT INTO estructura_intermedia.col_miembros (
    interesado_pmc_interesado,
    agrupacion,
    area_pomca,
    participacion
)
SELECT
    COALESCE(pi.nombre, m.sigla_normalizada) AS interesado_pmc_interesado,
    pai.nombre                               AS agrupacion,
    pai.area_pomca                           AS area_pomca,
    CASE
        WHEN m.participacion_txt IS NOT NULL
        THEN (m.participacion_txt::NUMERIC / 100)::NUMERIC(11,10)  -- aquí la corrección
        ELSE NULL
    END                                      AS participacion
FROM estructura_intermedia.pmc_agrupacioninteresados AS pai
CROSS JOIN LATERAL (
    SELECT
        CASE
            WHEN upper(r[1]) = 'CBS'         THEN 'CSB'
            WHEN upper(r[1]) = 'CORPOMAG'    THEN 'CORPAMAG'
            WHEN upper(r[1]) = 'COPPOCESAR'  THEN 'CORPOCESAR'
            WHEN upper(r[1]) = 'CORPOBOYACÁ' THEN 'CORPOBOYACA'
            ELSE r[1]
        END  AS sigla_normalizada,
        r[2] AS participacion_txt
    FROM regexp_matches(
            replace(pai.car, ',', '.'),
            '([A-ZÁÉÍÓÚÑ]{2,})(?:\s+([0-9]+(?:\.[0-9]+)?))?',
            'g'
        ) AS r
) AS m
LEFT JOIN estructura_intermedia.pmc_interesado AS pi
       ON upper(pi.sigla) = upper(m.sigla_normalizada)
ORDER BY pai.area_pomca, m.sigla_normalizada;
---------------------------------------------------------------------------
-- Área de reserva PMC
---------------------------------------------------------------------------

INSERT INTO pmc_uab_areapomca (
  uab_identificador,
  uab_identificador_insumo,
  uab_nombre_pomca,
  uab_estado,
  uab_fase,
  uab_area_hidrografica,
  uab_zona_hidrografica,
  uab_subzona_hidrografica,
  uab_nombre,
  ue_geometria,
  pmc_interesado,
  pmc_agrupacioninteresados,
  fuente_administrativa_tipo,
  fuente_administrativa_estado_disponibilidad,
  fuente_administrativa_tipo_formato,
  fuente_administrativa_fecha_documento_fuente,
  fuente_administrativa_nombre,
  ddr_tipo_resposabilidad,
  ddr_tipo_derecho
)
SELECT
  'PMC_' || lpad(row_number() OVER (ORDER BY ap.cod_pomca)::text, 3, '0')                                                     AS uab_identificador,
  ap.cod_pomca                                                                                                              AS uab_identificador_insumo,
  ap.nom_pomca                                                                                                              AS uab_nombre_pomca,
  CASE ap.nom_fase
    WHEN 'Actividades Previas'        THEN 'Actividades_Previas'
    WHEN 'Aprestamiento'              THEN 'Aprestamiento'
    WHEN 'Diagnóstico'                THEN 'Diagnostico'
    WHEN 'Formulación'                THEN 'Formulacion'
    WHEN 'Prospectiva y Zonificación' THEN 'Prospectiva_y_Zonificacion'
    WHEN 'Aprobado'                   THEN 'Aprobado'
    ELSE NULL
  END                                                                                                                       AS uab_estado,
  CASE cast(ap.fase AS integer)
    WHEN 1 THEN 'Aprestamiento'
    WHEN 2 THEN 'Diagnostico'
    WHEN 3 THEN 'Prospectiva_y_Zonificacion_Ambiental'
    WHEN 4 THEN 'Formulacion'
    WHEN 5 THEN 'Ejecucion'
    WHEN 6 THEN 'Seguimiento_y_evaluacion'
    ELSE NULL
  END AS uab_fase,
  ap.ah AS uab_area_hidrografica,
  ap.zh AS uab_zona_hidrografica,
  ap.szh AS uab_subzona_hidrografica,
  'pmc_uab_areapomca'::varchar(255) AS uab_nombre,
  ST_Force3DZ(ST_Transform(ap.geom, 9377), 0) AS ue_geometria,
  pi.nombre AS pmc_interesado,
  pa.nombre AS pmc_agrupacioninteresados,
  'Documento_Publico' AS fuente_administrativa_tipo,
  'Disponible' AS fuente_administrativa_estado_disponibilidad,
  'Documento' AS fuente_administrativa_tipo_formato,
  COALESCE(NULLIF(hfa.fecha_homologada, ''), ap.año_res::text) AS fuente_administrativa_fecha_documento_fuente,
 hfa.acto_homologado AS fuente_administrativa_nombre,
  'Administrar' AS ddr_tipo_resposabilidad,
  'Declarar' AS ddr_tipo_derecho
FROM insumos.area_pomca ap
LEFT JOIN estructura_intermedia.pmc_interesado pi
  ON ap.car_cc ~ '^[^ ]+ [0-9]+' 
     AND pi.sigla = split_part(ap.car_cc, ' ', 1)
LEFT JOIN estructura_intermedia.pmc_agrupacioninteresados pa
  ON pa.area_pomca = ap.cod_pomca
LEFT JOIN insumos.insumos_secundarios hfa
  ON hfa.cod_pomca = ap.cod_pomca
WHERE ap.nom_fase NOT IN ('No objeto de POMCA','Sin Inicio')
ORDER BY ap.cod_pomca;


---------------------------------------------------------------------------
-- Zonificación
---------------------------------------------------------------------------
INSERT INTO estructura_intermedia.pmc_uab_zonificacion (
    uab_identificador,
    uab_tipo_zona,
    uab_detalle_zona,
    uab_areapomca,
    uab_nombre,
    ue_geometria,
    pmc_interesado,
    pmc_agrupacioninteresados,
    fuente_administrativa_tipo,
    fuente_administrativa_estado_disponibilidad,
    fuente_administrativa_tipo_formato,
    fuente_administrativa_fecha_documento_fuente,
    fuente_administrativa_nombre,
    ddr_tipo_resposabilidad,
    ddr_tipo_derecho
)
WITH const_3510 AS (
  SELECT
    pmc_interesado,
    pmc_agrupacioninteresados,
    fuente_administrativa_fecha_documento_fuente::date AS fecha_doc,
    fuente_administrativa_nombre
  FROM estructura_intermedia.pmc_uab_areapomca
  WHERE uab_identificador_insumo = '3510'
  LIMIT 1
),
zonas AS (
  SELECT
    ROW_NUMBER() OVER (ORDER BY ST_AsText(zn.geom)) AS rn,
    ST_Force3D(zn.geom)::geometry(MULTIPOLYGONZ, 9377) AS ue_geometria,
    (CASE zn.cat_ord
        WHEN '01' THEN 'Conservacion_Y_Proteccion_Ambiental'
        WHEN '02' THEN 'Uso_Multiple'
     END || '.' ||
     CASE zn.zo_us_ma
        WHEN '01' THEN 'Areas_Protegidas'
        WHEN '02' THEN 'Areas_de_Proteccion'
        WHEN '03' THEN 'Areas_de_Restauracion'
        WHEN '04' THEN 'Areas_de_Produccion_Y_Uso_Sostenible'
        WHEN '05' THEN 'Areas_Urbanas'
        WHEN '06' THEN 'Areas_Desarrollo'
     END || '.' ||
     CASE zn.szo_us_m
        WHEN '01' THEN 'Areas_del_SINAP'
        WHEN '02' THEN 'Areas_Complementarias_Conservacion'
        WHEN '03' THEN 'Areas_Importancia_Ambiental'
        WHEN '04' THEN 'Areas_Reglamentacion_Especial'
        WHEN '05' THEN 'Areas_Amenazas_Naturales'
        WHEN '06' THEN 'Areas_Restauracion_Ecologica'
        WHEN '07' THEN 'Areas_de_Rehabilitacion'
        WHEN '08' THEN 'Area_Recuperacion_Uso_Multiple'
        WHEN '09' THEN 'Areas_Agricolas'
        WHEN '10' THEN 'Areas_Agrosilvopastoriles'
        WHEN '11' THEN 'Areas_Urbanas_Municipales_y_Distritales'
        WHEN '12' THEN 'Areas_Licenciadas_Ambientalmente'
     END) AS zone_concat
  FROM insumos.zonificacion zn
),
validos AS (
  SELECT unnest(ARRAY[
    'Conservacion_Y_Proteccion_Ambiental.Areas_Protegidas.Areas_del_SINAP',
    'Conservacion_Y_Proteccion_Ambiental.Areas_de_Proteccion.Areas_Importancia_Ambiental',
    'Uso_Multiple.Areas_Urbanas.Areas_Urbanas_Municipales_y_Distritales',
    'Conservacion_Y_Proteccion_Ambiental.Areas_de_Restauracion.Areas_de_Rehabilitacion',
    'Conservacion_Y_Proteccion_Ambiental.Areas_de_Proteccion.Areas_Complementarias_Conservacion',
    'Conservacion_Y_Proteccion_Ambiental.Areas_de_Proteccion.Areas_Amenazas_Naturales',
    'Uso_Multiple.Areas_de_Produccion_Y_Uso_Sostenible.Areas_Agrosilvopastoriles',
    'Conservacion_Y_Proteccion_Ambiental.Areas_de_Restauracion.Areas_Restauracion_Ecologica',
    'Uso_Multiple.Areas_de_Restauracion.Area_Recuperacion_Uso_Multiple',
    'Conservacion_Y_Proteccion_Ambiental.Areas_de_Proteccion.Areas_Reglamentacion_Especial',
    'Uso_Multiple.Areas_de_Produccion_Y_Uso_Sostenible.Areas_Agricolas'
  ]) AS v
),
cte AS (
  SELECT
    z.rn,
    z.ue_geometria,
    z.zone_concat,
    c.pmc_interesado,
    c.pmc_agrupacioninteresados,
    c.fecha_doc,
    c.fuente_administrativa_nombre
  FROM zonas z
  CROSS JOIN const_3510 c
)
SELECT
  'ZNPMC_' || rn AS uab_identificador,
  CASE WHEN zone_concat = ANY (SELECT v FROM validos)
       THEN zone_concat ELSE 'Otro' END AS uab_tipo_zona,
  CASE WHEN zone_concat = ANY (SELECT v FROM validos)
       THEN NULL ELSE zone_concat END AS uab_detalle_zona,
  (SELECT uab_nombre_pomca
   FROM estructura_intermedia.pmc_uab_areapomca
   WHERE uab_identificador_insumo = '3510'
   LIMIT 1) AS uab_areapomca,
  'pmc_uab_zonificacion' AS uab_nombre,
  ue_geometria,
  pmc_interesado,
  pmc_agrupacioninteresados,
  'Documento_Publico' AS fuente_administrativa_tipo,
  'Disponible' AS fuente_administrativa_estado_disponibilidad,
  'Documento' AS fuente_administrativa_tipo_formato,
  fecha_doc  AS fuente_administrativa_fecha_documento_fuente,
  fuente_administrativa_nombre AS fuente_administrativa_nombre,
  'Zonificar' AS ddr_tipo_resposabilidad,
  NULL AS ddr_tipo_derecho
FROM cte;


---------------------------------------------------------------------------
-- Fuentes Administrativas de Áreas de Reserva
---------------------------------------------------------------------------
-- TRUNCATE TABLE estructura_intermedia.pmc_fuenteadministrativa;
INSERT INTO estructura_intermedia.pmc_fuenteadministrativa (
    uab_identificador,
    fuente_administrativa_fecha_documento_fuente,
    fuente_administrativa_tipo_formato,
    fuente_administrativa_numero,        
    fuente_administrativa_anio
)
WITH src AS (
  SELECT 
      uab_identificador,
      fuente_administrativa_nombre,
      fuente_administrativa_fecha_documento_fuente
  FROM estructura_intermedia.pmc_uab_areapomca
  WHERE fuente_administrativa_nombre IS NOT NULL
),
nom_arr AS (
  SELECT
      uab_identificador,
      string_to_array(fuente_administrativa_nombre, '/') AS nombres,
      string_to_array(fuente_administrativa_fecha_documento_fuente, '/') AS fechas_raw
  FROM src
),
exploded AS (
  SELECT
      n.uab_identificador,
      trim( nombres[idx] ) AS nom_part,
      trim( COALESCE( fechas_raw[idx], fechas_raw[1] ) )  AS fecha_part
  FROM nom_arr n
  CROSS JOIN LATERAL generate_subscripts(n.nombres,1) AS idx
)
SELECT
    /*── identificador ───────────────────────────────────────────────*/
    uab_identificador,

    /*── fecha completa sólo si es YYYY-MM-DD ───────────────────────*/
    CASE
        WHEN fecha_part ~ '^\d{4}-\d{2}-\d{2}$'
        THEN fecha_part::date
        ELSE NULL
    END AS fuente_administrativa_fecha_documento_fuente,

    /*── tipo ────────────────*/
    CASE
        WHEN nom_part ~* '^\s*(Resoluci[oó]n|Resolucioon)\s+' THEN 'Resolucion'
        WHEN nom_part ~* '^\s*Acuerdo\s+' THEN 'Acuerdo'
        ELSE split_part(nom_part, ' ', 1)
    END AS fuente_administrativa_tipo_formato,

    /*── número: quita la palabra tipo ───────────────────────────────*/
    NULLIF(
        trim(
            regexp_replace(
                nom_part,
                '^\s*(Resoluci[oó]n|Resolucioon|Acuerdo)\s*',
                '',
                'i'
            )
        ),
        ''
    ) AS fuente_administrativa_numero,

    /*── año: extrae 4 dígitos al principio ─────────────────────────*/
    NULLIF(
        substring(fecha_part FROM '^\d{4}'),
        ''
    )::int4 AS fuente_administrativa_anio
FROM exploded;

---------------------------------------------------------------------------
-- Fuentes Administrativas de Zonificación
---------------------------------------------------------------------------
-- TRUNCATE TABLE estructura_intermedia.pmc_fuenteadministrativa;
INSERT INTO estructura_intermedia.pmc_fuenteadministrativa (
    uab_identificador,
    fuente_administrativa_fecha_documento_fuente,
    fuente_administrativa_tipo_formato,
    fuente_administrativa_numero,      -- varchar
    fuente_administrativa_anio
)
SELECT
    /* 1. identificador ------------------------------------------------*/
    uab_identificador,

    /* 2. fecha (ya es DATE) ------------------------------------------*/
    fuente_administrativa_fecha_documento_fuente,

    /* 3. tipo-formato (primera palabra; normaliza “Resolucion”) ------*/
    CASE
        WHEN fuente_administrativa_nombre ILIKE 'Resolución %'
          OR fuente_administrativa_nombre ILIKE 'Resolucion %'
        THEN 'Resolucion'
        ELSE split_part(fuente_administrativa_nombre,' ',1)
    END                                                  AS fuente_administrativa_tipo_formato,

    /* 4. número (todo después de “Resolución ”, sin tocar) -----------*/
    NULLIF(
        regexp_replace(
            fuente_administrativa_nombre,
            '^(Resoluci[oó]n)\s*',   -- quita la palabra inicial
            '',
            'i'
        ),
        ''
    )                                                    AS fuente_administrativa_numero,

    /* 5. año (EXTRACT directamente de la fecha) ----------------------*/
    EXTRACT(YEAR FROM fuente_administrativa_fecha_documento_fuente)::int4
                                                       AS fuente_administrativa_anio
FROM estructura_intermedia.pmc_uab_zonificacion
WHERE fuente_administrativa_nombre IS NOT NULL;


    """

    return sql_script



def validar_estructura():
    """
    Guarda el script SQL de la estructura de datos intermedia
    en un archivo llamado 'estructura_intermedia.sql'.
    """
    sql_script = """    
/**********************************************************************************
            ETL de tranformación de insumos a estructura de datos intermedia
        			Migración de pomcas  al modelo LADM_COL-PMC
              ----------------------------------------------------------
        begin           : 2024-10-21
        git sha         : :%H$
        copyright       : (C) 2024 by Leo Cardona (CEICOL SAS)
                          (C) 2024 by Cesar Alfonso Basurto (CEICOL SAS)        
        email           : contacto@ceicol.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 **********************************************************************************/

--========================================
--Fijar esquema
--========================================
set search_path to 
	estructura_intermedia, -- Esquema de estructura de datos intermedia
	public;

/*════════════════════════════════════════════════════════════════════
  1 ▌ AGRUPACIONES POR POMCA
  ════════════════════════════════════════════════════════════════════*/

/* 1-A. Totales de POMCA, con y sin agrupación */
WITH
totales AS (
  SELECT COUNT(DISTINCT cod_pomca) AS total_pomcas
  FROM insumos.area_pomca          -- fuente completa
),
agr AS (
  SELECT COUNT(DISTINCT area_pomca) AS pomcas_con_agrup
  FROM estructura_intermedia.pmc_agrupacioninteresados
)
SELECT
  total_pomcas                          AS pomcas_totales,
  pomcas_con_agrup                      AS pomcas_con_agrupaciones,
  total_pomcas - pomcas_con_agrup       AS pomcas_sin_agrupaciones
FROM totales, agr;

/* 1-B. ¿Qué POMCAs NO tienen agrupación? — listado */
SELECT cod_pomca AS pomca_sin_agrupacion
FROM insumos.area_pomca
WHERE cod_pomca NOT IN (
  SELECT DISTINCT area_pomca
  FROM estructura_intermedia.pmc_agrupacioninteresados
)
ORDER BY cod_pomca;


/*════════════════════════════════════════════════════════════════════
  2 ▌ INTERESADOS POR POMCA
  ════════════════════════════════════════════════════════════════════*/

/* 2-A. Cuántos POMCAs tienen al menos UN interesado */
WITH
pomca_con_interesados AS (
  SELECT DISTINCT p.area_pomca
  FROM estructura_intermedia.pmc_agrupacioninteresados  AS p
  JOIN estructura_intermedia.col_miembros               AS m
       ON m.agrupacion = p.nombre
),
tot AS (
  SELECT COUNT(DISTINCT cod_pomca) AS total_pomcas
  FROM insumos.area_pomca
),
contado AS (
  SELECT COUNT(*) AS con_interesados FROM pomca_con_interesados
)
SELECT
  tot.total_pomcas                               AS pomcas_totales,
  contado.con_interesados                        AS pomcas_con_interesados,
  tot.total_pomcas - contado.con_interesados     AS pomcas_sin_interesados
FROM tot, contado;

/* 2-B. POMCAs sin interesados — listado */
SELECT cod_pomca AS pomca_sin_interesados
FROM insumos.area_pomca
WHERE cod_pomca NOT IN (
  SELECT p.area_pomca
  FROM estructura_intermedia.pmc_agrupacioninteresados AS p
  JOIN estructura_intermedia.col_miembros              AS m
       ON m.agrupacion = p.nombre
)
ORDER BY cod_pomca;


/*════════════════════════════════════════════════════════════════════
  3 ▌ CONTEOS DE ZONIFICACIÓN
  ════════════════════════════════════════════════════════════════════*/

/* 3-A. Conteo por código original */
SELECT
  cat_ord                  AS cat_ord_cod,
  COUNT(*)                 AS total
FROM insumos.zonificacion
GROUP BY cat_ord
ORDER BY cat_ord;

SELECT
  zo_us_ma                 AS zo_us_ma_cod,
  COUNT(*)                 AS total
FROM insumos.zonificacion
GROUP BY zo_us_ma
ORDER BY zo_us_ma;

SELECT
  szo_us_m                 AS szo_us_m_cod,
  COUNT(*)                 AS total
FROM insumos.zonificacion
GROUP BY szo_us_m
ORDER BY szo_us_m;


/* 3-B. Conteo por combinación `zone_concat` */
WITH zonas AS (
  SELECT
    ( CASE cat_ord
        WHEN '01' THEN 'Conservacion_Y_Proteccion_Ambiental'
        WHEN '02' THEN 'Uso_Multiple'
      END || '.' ||
      CASE zo_us_ma
        WHEN '01' THEN 'Areas_Protegidas'
        WHEN '02' THEN 'Areas_de_Proteccion'
        WHEN '03' THEN 'Areas_de_Restauracion'
        WHEN '04' THEN 'Areas_de_Produccion_Y_Uso_Sostenible'
        WHEN '05' THEN 'Areas_Urbanas'
        WHEN '06' THEN 'Areas_Desarrollo'
      END || '.' ||
      CASE szo_us_m
        WHEN '01' THEN 'Areas_del_SINAP'
        WHEN '02' THEN 'Areas_Complementarias_Conservacion'
        WHEN '03' THEN 'Areas_Importancia_Ambiental'
        WHEN '04' THEN 'Areas_Reglamentacion_Especial'
        WHEN '05' THEN 'Areas_Amenazas_Naturales'
        WHEN '06' THEN 'Areas_Restauracion_Ecologica'
        WHEN '07' THEN 'Areas_de_Rehabilitacion'
        WHEN '08' THEN 'Area_Recuperacion_Uso_Multiple'
        WHEN '09' THEN 'Areas_Agricolas'
        WHEN '10' THEN 'Areas_Agrosilvopastoriles'
        WHEN '11' THEN 'Areas_Urbanas_Municipales_y_Distritales'
        WHEN '12' THEN 'Areas_Licenciadas_Ambientalmente'
      END )                            AS zone_concat
  FROM insumos.zonificacion
)
SELECT
  zone_concat,
  COUNT(*) AS total
FROM zonas
GROUP BY zone_concat
ORDER BY total DESC;


/*════════════════════════════════════════════════════════════════════
  4 ▌ LISTADOS COMPLETOS (por si necesitas revisar)
  ════════════════════════════════════════════════════════════════════*/

/* 4-A. Agrupaciones por POMCA — detalle */
SELECT
  area_pomca,
  COUNT(*) AS agrupaciones
FROM estructura_intermedia.pmc_agrupacioninteresados
GROUP BY area_pomca
ORDER BY area_pomca;

/* 4-B. Conteo de miembros por agrupación — detalle */
SELECT
  agrupacion,
  COUNT(*)                            AS miembros,
  COUNT(*) FILTER (WHERE participacion IS NULL) AS sin_porcentaje
FROM estructura_intermedia.col_miembros
GROUP BY agrupacion
ORDER BY agrupacion;

    """

    return sql_script

def importar_al_modelo():
    """
    Guarda el script SQL de la estructura de datos intermedia
    en un archivo llamado 'estructura_intermedia.sql'.
    """
    sql_script = """    
/**********************************************************************************
            ETL de tranformación de insumos a estructura de datos intermedia
        			Migración de los POMCA  al modelo LADM_COL-PMC
              ----------------------------------------------------------
        begin           : 2024-10-21
        git sha         : :%H$
        copyright       : (C) 2024 by Leo Cardona (CEICOL SAS)
                          (C) 2024 by Cesar Alfonso Basurto (CEICOL SAS)        
        email           : contacto@ceicol.com
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License v3.0 as          *
 *   published by the Free Software Foundation.                            *
 *                                                                         *
 **********************************************************************************/
--========================================
--Fijar esquema
--========================================
set search_path to
	estructura_intermedia,	-- Esquema de estructura de datos intermedia
	ladm,		-- Esquema modelo LADM-PRM
	public;


--================================================================================
-- 1. Define Basket si este no existe
--================================================================================
INSERT INTO ladm.t_ili2db_dataset
(t_id, datasetname)
VALUES(1, 'Baseset');

INSERT INTO ladm.t_ili2db_basket(
	t_id, 
	dataset, 
	topic, 
	t_ili_tid, 
	attachmentkey, 
	domains)
VALUES(
	1,
	1, 
	'LADM_COL_v_1_0_0_Ext_PMC.PMC',
	uuid_generate_v4(),
	'ETL de importación de datos',
	NULL );

--================================================================================
-- 2. Migración de pmc_interesado
--================================================================================
--truncate table ladm.pmc_interesado cascade
INSERT INTO ladm.pmc_interesado(
    t_basket, 
    t_ili_tid, 
    observacion, 
    nombre, 
    tipo_interesado, 
    tipo_documento, 
    numero_documento, 
    comienzo_vida_util_version, 
    fin_vida_util_version, 
    espacio_de_nombres, 
    local_id
)
SELECT 
    (SELECT t_id FROM ladm.t_ili2db_basket WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    uuid_generate_v4() AS t_ili_tid,
    NULL AS observacion,
    nombre AS nombre, 
    (SELECT t_id FROM ladm.col_interesadotipo WHERE ilicode LIKE tipo_interesado) AS tipo_interesado,
    (SELECT t_id FROM ladm.col_documentotipo WHERE ilicode LIKE tipo_documento) AS tipo_documento,
    numero_documento AS numero_documento,
    NOW() AS comienzo_vida_util_version,
    NULL AS fin_vida_util_version,
    'pmc_interesado' AS espacio_de_nombres, 
    ROW_NUMBER() OVER (ORDER BY nombre) AS local_id    ------------ identificador texto tal cual 
FROM estructura_intermedia.pmc_interesado;

----------------------------------------------------------------------------------------------------------
---2.1 migración de agrupacioninteresados
----------------------------------------------------------------------------------------------------------
--truncate table pmc_agrupacioninteresados cascade
INSERT INTO ladm.pmc_agrupacioninteresados (
    t_basket,
    t_ili_tid, 
    tipo, 
    nombre, 
    tipo_interesado, 
    tipo_documento, 
    numero_documento, 
    comienzo_vida_util_version, 
    fin_vida_util_version, 
    espacio_de_nombres, 
    local_id
)
SELECT 
    (SELECT t_id FROM ladm.t_ili2db_basket WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    uuid_generate_v4() AS t_ili_tid,
    (SELECT t_id FROM ladm.col_grupointeresadotipo WHERE ilicode = ei.tipo) AS tipo, -- Ajuste para usar igualdad exacta
    ei.nombre AS nombre,
    (SELECT t_id FROM ladm.col_interesadotipo WHERE ilicode = ei.tipo_interesado) AS tipo_interesado, -- Igualdad exacta
    NULL AS tipo_documento, -- Define un valor si es obligatorio
    NULL AS numero_documento, -- Define un valor si es obligatorio
    NOW() AS comienzo_vida_util_version,
    NULL AS fin_vida_util_version,
    'pmc_interesado' AS espacio_de_nombres,
    ei.id AS local_id
FROM estructura_intermedia.pmc_agrupacioninteresados ei
WHERE ei.nombre IS NOT NULL -- Excluir nombres nulos
  AND TRIM(ei.nombre) <> ''; -- Excluir nombres vacíos o con solo espacios


----------------------------------------------------------------------------------------------------------
---2.2 migración de col_miembros
----------------------------------------------------------------------------------------------------------
INSERT INTO ladm.col_miembros(
    t_basket,
    interesado_pmc_interesado,
    interesado_pmc_agrupacioninteresados,
    agrupacion,
    participacion        
)
SELECT
    -- Obtener el t_basket
    (SELECT t_id FROM ladm.t_ili2db_basket WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    -- Obtener el t_id del interesado_pmc_interesado
    (SELECT t_id 
     FROM ladm.pmc_interesado 
     WHERE nombre = e.interesado_pmc_interesado 
     LIMIT 1) AS interesado_pmc_interesado,
    -- Agrupación de interesados (nulo)
    NULL AS interesado_pmc_agrupacioninteresados,
    -- Obtener el t_id de la agrupación
    (SELECT t_id 
     FROM ladm.pmc_agrupacioninteresados 
     WHERE nombre = e.agrupacion 
     LIMIT 1) AS agrupacion,
    -- Participación (nulo)
    NULL AS participacion
FROM 
    estructura_intermedia.col_miembros e
where e.agrupacion is not null;


--================================================================================
-- 3. Migración de  Area de Reserva
--================================================================================
--3.1 diligenciamiento de la tabla  pmc_uab_areapomca

INSERT INTO ladm.pmc_uab_areapomca(
    t_basket,
    t_ili_tid,
    identificador,
    nombre_pomca,
    estado,
    fase,
    area_hidrografica,
    zona_hidrografica,
    subzona_hidrografica,
    nombre,
    tipo,
    comienzo_vida_util_version,
    fin_vida_util_version,
    espacio_de_nombres,
    local_id)
SELECT
    (SELECT t_id FROM ladm.t_ili2db_basket WHERE topic='LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    uuid_generate_v4() AS t_ili_tid,
    uab_identificador_insumo AS identificador,
    uab_nombre_pomca AS nombre_pomca,
    (SELECT t_id FROM ladm.pmc_estadotipo WHERE ilicode=uab_estado LIMIT 1) AS estado,
    (SELECT t_id FROM ladm.pmc_fasetipo WHERE ilicode=uab_fase LIMIT 1) AS fase,
    uab_area_hidrografica AS area_hidrografica,
    uab_zona_hidrografica AS zona_hidrografica,
    uab_subzona_hidrografica AS subzona_hidrografica,
    uab_nombre AS nombre,
    (SELECT t_id FROM ladm.col_unidadadministrativabasicatipo WHERE ilicode='Ambiente_Desarrollo_Sostenible' LIMIT 1) AS tipo,
    NOW() AS comienzo_vida_util_version,
    NULL AS fin_vida_util_version,
    'pmc_uab_areapomca' AS espacio_de_nombres,
    uab_identificador AS local_id
FROM estructura_intermedia.pmc_uab_areapomca;


--3.2 diligenciamiento de la tabla  pmc_ue_areapomca

INSERT INTO ladm.pmc_ue_areapomca(
	t_basket, 
	t_ili_tid, 
	area_ha, 
	etiqueta, 
	relacion_superficie, 
	geometria, 
	comienzo_vida_util_version, 
	fin_vida_util_version, 
	espacio_de_nombres, 
	local_id)
select
	(select t_id from ladm.t_ili2db_basket where topic like 'LADM_COL_v_1_0_0_Ext_PMC.PMC' limit 1) as t_basket,
	uuid_generate_v4() as t_ili_tid,
	(st_area(ue_geometria)/10000)::numeric(13, 4) as area_ha,
	uab_nombre_pomca as etiqueta,
	(select t_id from ladm.col_relacionsuperficietipo where ilicode like 'En_Rasante') as relacion_superficie,
	ue_geometria,	
	now() as comienzo_vida_util_version,
	null as fin_vida_util_version,
	'pmc_ue_areapomca' as espacio_de_nombres, 
	uab_identificador  local_id
from  estructura_intermedia.pmc_uab_areapomca; 

--3.3 diligenciamiento de derecho
INSERT INTO ladm.pmc_derecho(
    t_basket, 
    t_ili_tid, 
    tipo, 
    descripcion, 
    interesado_pmc_interesado, 
    interesado_pmc_agrupacioninteresados, 
    unidad_pmc_uab_zonificacion, 
    unidad_pmc_uab_areapomca, 
    comienzo_vida_util_version, 
    fin_vida_util_version, 
    espacio_de_nombres, 
    local_id
)
SELECT
    (SELECT t_id FROM ladm.t_ili2db_basket WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    uuid_generate_v4() AS t_ili_tid,
    (SELECT t_id FROM ladm.pmc_derechotipo WHERE ilicode ILIKE ddr_tipo_derecho) AS tipo,
    NULL AS descripcion,
    -- Vinculamos con pmc_interesado utilizando ILIKE para buscar coincidencias con Ministerio de Ambiente
    (SELECT t_id 
     FROM ladm.pmc_interesado 
     WHERE nombre ILIKE pmc_interesado) AS interesado_pmc_interesado,

     (SELECT t_id 
     FROM ladm.pmc_agrupacioninteresados
     WHERE nombre ILIKE pmc_agrupacioninteresados) AS nteresado_pmc_agrupacioninteresados,
     
    NULL AS unidad_pmc_uab_zonificacion, 
    (SELECT t_id 
     FROM ladm.pmc_uab_areapomca 
     WHERE local_id ILIKE uab_identificador LIMIT 1) AS unidad_pmc_uab_areapomca,
    NOW() AS comienzo_vida_util_version,
    NULL AS fin_vida_util_version,
    'pmc_responsabilidad' AS espacio_de_nombres, 
    uab_identificador AS local_id
FROM 
    estructura_intermedia.pmc_uab_areapomca;

--3.4 diligenciamiento de responsabilidad


INSERT INTO ladm.pmc_responsabilidad(
    t_basket, 
    t_ili_tid, 
    tipo, 
    descripcion, 
    interesado_pmc_interesado, 
    interesado_pmc_agrupacioninteresados, 
    unidad_pmc_uab_zonificacion, 
    unidad_pmc_uab_areapomca, 
    comienzo_vida_util_version, 
    fin_vida_util_version, 
    espacio_de_nombres, 
    local_id)
SELECT
    -- Obtener el t_basket
    (SELECT t_id 
     FROM ladm.t_ili2db_basket 
     WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    -- Generar un nuevo UUID para t_ili_tid
    uuid_generate_v4() AS t_ili_tid,
    -- Obtener el tipo de responsabilidad desde ladm.pmc_responsabilidadtipo
    (SELECT t_id 
     FROM ladm.pmc_responsabilidadtipo 
     WHERE ilicode LIKE ea.ddr_tipo_resposabilidad) AS tipo,
    -- Descripción nula
    NULL AS descripcion,
    -- Obtener el t_id del interesado usando pmc_interesado = nombre
    (SELECT t_id 
     FROM ladm.pmc_interesado 
     WHERE nombre = ea.pmc_interesado
     LIMIT 1) AS interesado_pmc_interesado,
    -- Obtener el t_id de agrupacioninteresados utilizando el nombre como referencia
    (SELECT t_id 
     FROM ladm.pmc_agrupacioninteresados 
     WHERE nombre = ea.pmc_agrupacioninteresados
     LIMIT 1) AS interesado_pmc_agrupacioninteresados,
    -- Dejar nulo el campo de zonificación
    NULL AS unidad_pmc_uab_zonificacion,
    -- Obtener el t_id del área páramo
    (SELECT t_id 
     FROM ladm.pmc_uab_areapomca 
     WHERE local_id = ea.uab_identificador
     LIMIT 1) AS unidad_pmc_uab_areapomca,
    -- Fecha de comienzo de la vida útil
    NOW() AS comienzo_vida_util_version,
    -- Fecha de fin de la vida útil como NULL
    NULL AS fin_vida_util_version,
    -- Espacio de nombres fijo
    'pmc_responsabilidad' AS espacio_de_nombres,
    -- Identificador local
    ea.uab_identificador AS local_id
FROM 
    estructura_intermedia.pmc_uab_areapomca ea;


--3.5 diligenciamiento de la tabla  fuente administrativa
INSERT INTO ladm.pmc_fuenteadministrativa(
	t_basket, 
	t_ili_tid, 
	tipo, 
	fecha_fin, 
	estado_disponibilidad, 
	tipo_formato, 
	fecha_documento_fuente, 
	nombre, 
	descripcion, 
	url, 
	espacio_de_nombres, 
	local_id)	
SELECT
    (SELECT t_id FROM ladm.t_ili2db_basket WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    uuid_generate_v4() AS t_ili_tid,
    (SELECT cf.t_id FROM ladm.col_fuenteadministrativatipo cf WHERE cf.ilicode ILIKE a.fuente_administrativa_tipo || '.' || f.fuente_administrativa_tipo_formato LIMIT 1) AS tipo,
    NULL AS fecha_fin,
    (SELECT ce.t_id FROM ladm.col_estadodisponibilidadtipo ce WHERE ce.ilicode ILIKE a.fuente_administrativa_estado_disponibilidad LIMIT 1) AS estado_disponibilidad,
    (SELECT cf.t_id FROM ladm.col_formatotipo cf WHERE cf.ilicode ILIKE a.fuente_administrativa_tipo_formato LIMIT 1) AS tipo_formato,
    CASE WHEN a.fuente_administrativa_fecha_documento_fuente ~ '^\d{4}-\d{2}-\d{2}$' THEN a.fuente_administrativa_fecha_documento_fuente::date ELSE NULL END AS fecha_documento_fuente,
    f.fuente_administrativa_tipo_formato || ' ' || f.fuente_administrativa_numero || ' de ' || f.fuente_administrativa_anio AS nombre,
    NULL AS descripcion,
    NULL AS url,
    'pmc_fuenteadministrativa' AS espacio_de_nombres,
    f.uab_identificador AS local_id
FROM estructura_intermedia.pmc_fuenteadministrativa f
JOIN estructura_intermedia.pmc_uab_areapomca a ON f.uab_identificador = a.uab_identificador;


--==============================================================================
-- 4. Migración de  zonificacion
--================================================================================

--4.2 diligenciamiento de la tabla   zonificación

INSERT INTO ladm.pmc_uab_zonificacion(
    t_basket, 
    t_ili_tid, 
    tipo_zona, 
    detalle_zona,
    uab_areapomca, 
    nombre, 
    tipo, 
    comienzo_vida_util_version, 
    fin_vida_util_version, 
    espacio_de_nombres, 
    local_id
)
SELECT
    -- Obtener t_basket
    (SELECT t_id 
     FROM ladm.t_ili2db_basket 
     WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    -- Generar un nuevo UUID para t_ili_tid
    uuid_generate_v4() AS t_ili_tid,
    -- Obtener el tipo de zona desde ladm.pmc_zonificaciontipo
    (SELECT t_id 
     FROM ladm.pmc_zonificaciontipo 
     WHERE ilicode LIKE z.uab_tipo_zona LIMIT 1) AS tipo_zona,
    -- Detalle de la zona directamente desde la tabla origen
    z.uab_detalle_zona AS detalle_zona,
    -- Extraer el t_id de ladm.pmc_regimenusosactividades basado en el id_local de estructura_intermedia.pmc_uab_zonificacion
    -- Obtener el área páramo desde ladm.pmc_uab_areapomca
	(SELECT t_id FROM ladm.pmc_uab_areapomca WHERE nombre_pomca = z.uab_areapomca 
	AND identificador = '3510' LIMIT 1) AS pmc_areapomca,

    -- Nombre directamente desde la tabla origen
    z.uab_nombre AS nombre,
    -- Tipo fijo basado en un ilicode específico
    (SELECT t_id 
     FROM ladm.col_unidadadministrativabasicatipo 
     WHERE ilicode LIKE 'Ambiente_Desarrollo_Sostenible' LIMIT 1) AS tipo,
    -- Fecha de comienzo de la vida útil
    NOW() AS comienzo_vida_util_version,
    -- Fecha de fin de la vida útil (nula)
    NULL AS fin_vida_util_version,
    -- Espacio de nombres fijo
    'pmc_uab_zonificacion' AS espacio_de_nombres, 
    -- Identificador local
    z.uab_identificador AS local_id
FROM 
    estructura_intermedia.pmc_uab_zonificacion z;


--4.3 diligenciamiento de la tabla  pmc_ue_zonificacion

INSERT INTO ladm.pmc_ue_zonificacion (
	t_basket, 
	t_ili_tid, 
	area_ha, 
	etiqueta, 
	relacion_superficie, 
	geometria, 
	comienzo_vida_util_version, 
	fin_vida_util_version, 
	espacio_de_nombres, 
	local_id)
select
	(select t_id from ladm.t_ili2db_basket where topic like 'LADM_COL_v_1_0_0_Ext_PMC.PMC' limit 1) as t_basket,
	uuid_generate_v4() as t_ili_tid,
	(st_area(ue_geometria)/10000)::numeric(13, 4) as area_ha,
	null as etiqueta,
	(select t_id from ladm.col_relacionsuperficietipo where ilicode like 'En_Rasante') as relacion_superficie,
	ue_geometria,	
	now() as comienzo_vida_util_version,
	null as fin_vida_util_version,
	'pmc_ue_zonificacion' as espacio_de_nombres, 
	uab_identificador  local_id
from  estructura_intermedia.pmc_uab_zonificacion; 

------------------------------------------------------------------------------------
--4.4 diligenciamiento de la tabla  pmc_responsabilidad para pmc_uab_zonificacion

INSERT INTO ladm.pmc_responsabilidad(
    t_basket, 
    t_ili_tid, 
    tipo, 
    descripcion, 
    interesado_pmc_interesado, 
    interesado_pmc_agrupacioninteresados, 
    unidad_pmc_uab_zonificacion, 
    unidad_pmc_uab_areapomca, 
    comienzo_vida_util_version, 
    fin_vida_util_version, 
    espacio_de_nombres, 
    local_id
)
SELECT
    -- Obtener el t_basket
    (SELECT t_id 
     FROM ladm.t_ili2db_basket 
     WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    -- Generar un nuevo UUID para t_ili_tid
    uuid_generate_v4() AS t_ili_tid,
    -- Obtener el tipo de responsabilidad desde ladm.pmc_responsabilidadtipo
    (SELECT t_id 
     FROM ladm.pmc_responsabilidadtipo 
     WHERE ilicode LIKE ea.ddr_tipo_resposabilidad) AS tipo,
    -- Descripción nula
    NULL AS descripcion,
    -- Obtener el t_id del interesado usando pmc_interesado = nombre
    (SELECT t_id 
     FROM ladm.pmc_interesado 
     WHERE nombre = ea.pmc_interesado
     LIMIT 1) AS interesado_pmc_interesado,
    -- Obtener el t_id de agrupacioninteresados utilizando el nombre como referencia
    (SELECT t_id 
     FROM ladm.pmc_agrupacioninteresados 
     WHERE nombre = ea.pmc_agrupacioninteresados
     LIMIT 1) AS interesado_pmc_agrupacioninteresados,
    -- Relacionar con zonificación
    (SELECT t_id 
     FROM ladm.pmc_uab_zonificacion 
     WHERE local_id = ea.uab_identificador
     LIMIT 1) AS unidad_pmc_uab_zonificacion,
    -- Dejar nulo el campo de área páramo
    NULL AS unidad_pmc_uab_areapomca,
    -- Fecha de comienzo de la vida útil
    NOW() AS comienzo_vida_util_version,
    -- Fecha de fin de la vida útil como NULL
    NULL AS fin_vida_util_version,
    -- Espacio de nombres fijo
    'pmc_responsabilidad' AS espacio_de_nombres,
    -- Identificador local
    ea.uab_identificador AS local_id
FROM 
    estructura_intermedia.pmc_uab_zonificacion ea;

--4.5 diligenciamiento de la tabla pmc_fuenteadministrativa para pmc_uab_areapomca
INSERT INTO ladm.pmc_fuenteadministrativa(
	t_basket, 
	t_ili_tid, 
	tipo, 
	fecha_fin, 
	estado_disponibilidad, 
	tipo_formato, 
	fecha_documento_fuente, 
	nombre, 
	descripcion, 
	url, 
	espacio_de_nombres, 
	local_id)	
SELECT
    (SELECT t_id FROM ladm.t_ili2db_basket WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    uuid_generate_v4() AS t_ili_tid,
    (SELECT cf.t_id FROM ladm.col_fuenteadministrativatipo cf WHERE cf.ilicode ILIKE a.fuente_administrativa_tipo || '.' || f.fuente_administrativa_tipo_formato LIMIT 1) AS tipo,
    NULL AS fecha_fin,
    (SELECT ce.t_id FROM ladm.col_estadodisponibilidadtipo ce WHERE ce.ilicode ILIKE a.fuente_administrativa_estado_disponibilidad LIMIT 1) AS estado_disponibilidad,
    (SELECT cf.t_id FROM ladm.col_formatotipo cf WHERE cf.ilicode ILIKE a.fuente_administrativa_tipo_formato LIMIT 1) AS tipo_formato,
    a.fuente_administrativa_fecha_documento_fuente AS fecha_documento_fuente,
    f.fuente_administrativa_tipo_formato || ' ' || f.fuente_administrativa_numero || ' de ' || f.fuente_administrativa_anio AS nombre,
    NULL AS descripcion,
    NULL AS url,
    'pmc_fuenteadministrativa' AS espacio_de_nombres,
    f.uab_identificador AS local_id
FROM estructura_intermedia.pmc_fuenteadministrativa f
JOIN estructura_intermedia.pmc_uab_zonificacion a ON f.uab_identificador = a.uab_identificador;


--================================================================================
-- 7. Migración de col_rrrfuente
--================================================================================
INSERT INTO ladm.col_rrrfuente(
	t_basket, 
	fuente_administrativa, 
	rrr_pmc_derecho, 
	rrr_pmc_responsabilidad)
select
(select t_id from ladm.t_ili2db_basket where topic like 'LADM_COL_v_1_0_0_Ext_PMC.PMC' limit 1) as t_basket,
fuente_administrativa,
rrr_pmc_derecho,
rrr_pmc_responsabilidad
from (
	select distinct 
	f.t_id as fuente_administrativa,
	null::int8 as rrr_pmc_derecho,
	r.t_id as rrr_pmc_responsabilidad
	from ladm.pmc_fuenteadministrativa f,
	ladm.pmc_responsabilidad r
	where f.local_id=r.local_id 
	union  
	select distinct 
	f.t_id as fuente_administrativa,
	d.t_id as rrr_pmc_derecho,
	null::int4 as rrr_pmc_responsabilidad
	from ladm.pmc_fuenteadministrativa f,
	ladm.pmc_derecho d
	where f.local_id=d.local_id
) t;



















SELECT
    /* 1. identificador ------------------------------------------------*/
    uab_identificador,

    /* 2. fecha (ya es DATE) ------------------------------------------*/
    fuente_administrativa_fecha_documento_fuente,

    /* 3. tipo-formato (primera palabra; normaliza “Resolucion”) ------*/
    CASE
        WHEN fuente_administrativa_nombre ILIKE 'Resolución %'
          OR fuente_administrativa_nombre ILIKE 'Resolucion %'
        THEN 'Resolucion'
        ELSE split_part(fuente_administrativa_nombre,' ',1)
    END                                                  AS fuente_administrativa_tipo_formato,

    /* 4. número (todo después de “Resolución ”, sin tocar) -----------*/
    NULLIF(
        regexp_replace(
            fuente_administrativa_nombre,
            '^(Resoluci[oó]n)\s*',   -- quita la palabra inicial
            '',
            'i'
        ),
        ''
    )                                                    AS fuente_administrativa_numero,

    /* 5. año (EXTRACT directamente de la fecha) ----------------------*/
    EXTRACT(YEAR FROM fuente_administrativa_fecha_documento_fuente)::int4
                                                       AS fuente_administrativa_anio
FROM estructura_intermedia.pmc_uab_zonificacion
WHERE fuente_administrativa_nombre IS NOT NULL;

--================================================================================
-- 8. Migración de col_uebaunit
--================================================================================
INSERT INTO ladm.col_uebaunit(
    t_basket, 
    ue_pmc_ue_zonificacion, 
    ue_pmc_ue_areapomca, 
    baunit_pmc_uab_zonificacion,	 
    baunit_pmc_uab_areapomca
)
SELECT
    (SELECT t_id FROM ladm.t_ili2db_basket WHERE topic LIKE 'LADM_COL_v_1_0_0_Ext_PMC.PMC' LIMIT 1) AS t_basket,
    ue_pmc_ue_zonificacion, 
    ue_pmc_ue_areapomca, 
    baunit_pmc_uab_zonificacion,	 
    baunit_pmc_uab_areapomca
FROM (
    -- Zonificación
    SELECT 
        uez.t_id::int8 AS ue_pmc_ue_zonificacion,
        NULL::int8     AS ue_pmc_ue_areapomca,
        uabz.t_id::int8 AS baunit_pmc_uab_zonificacion,
        NULL::int8     AS baunit_pmc_uab_areapomca
    FROM ladm.pmc_ue_zonificacion uez
    JOIN ladm.pmc_uab_zonificacion uabz
      ON uez.local_id = uabz.local_id

    UNION ALL	

    -- Área Páramo o Reserva
    SELECT 
        NULL::int8     AS ue_pmc_ue_zonificacion,
        uez.t_id::int8 AS ue_pmc_ue_areapomca,
        NULL::int8     AS baunit_pmc_uab_zonificacion,
        uabz.t_id::int8 AS baunit_pmc_uab_areapomca
    FROM ladm.pmc_ue_areapomca uez
    JOIN ladm.pmc_uab_areapomca uabz
      ON uez.local_id = uabz.local_id
) t;

    """

    return sql_script


