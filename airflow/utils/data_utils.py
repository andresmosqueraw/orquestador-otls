import os
import zipfile
import requests
import subprocess
import logging
import pandas as pd
import shutil
import re
import sqlalchemy

from utils.utils import leer_configuracion, limpiar_carpeta_temporal
from utils.gx_utils import _obtener_engine_sqlalchemy
from utils.db_utils import ejecutar_sql

from airflow.exceptions import AirflowSkipException

# ---------------------------------------------------------------------------
# Funciones auxiliares comunes
# ---------------------------------------------------------------------------

def descargar_archivo(url, destino, chunk_size=8192, timeout=10):
    """Descarga el archivo desde URL y lo guarda en destino."""
    response = requests.get(url, stream=True, timeout=timeout)
    response.raise_for_status()
    with open(destino, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            f.write(chunk)
    return destino

def obtener_ruta_local(base_local, ruta_config):
    """Construye la ruta completa y la valida."""
    local_path = os.path.join(base_local, ruta_config.lstrip("/"))
    if os.path.exists(local_path):
        return local_path
    raise FileNotFoundError(f"Archivo no encontrado en {local_path}.")

def ejecutar_ogr2ogr(command, error_context):
    """Ejecuta un comando ogr2ogr y maneja errores de forma centralizada."""
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
        logging.info(f"Comando ejecutado correctamente: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        msg = f"Error en {error_context}: {e.stderr}"
        logging.error(msg)
        raise Exception(msg)

# ---------------------------------------------------------------------------
# Funciones de descarga y validación de insumos desde la web y respaldo local
# ---------------------------------------------------------------------------

def obtener_insumos_desde_web(cfg, **context):
    """
    Descarga los insumos definidos en la configuración.
    Si falla la descarga o el archivo descargado está vacío, 
    solo se registra el error; la recuperación desde respaldo local
    se hará en la tarea copia_insumo_local_task.
    Retorna un diccionario con { clave: ruta_zip_o_None } 
    y utiliza XCom para comunicar errores y resultados.
    """
    logging.info("Iniciando 'obtener_insumos_desde_web'...")
    # Limpieza de la carpeta temporal
    limpiar_carpeta_temporal(cfg)

    config = leer_configuracion(cfg)
    insumos_web = config.get("insumos_web", {})
    if not insumos_web:
        raise ValueError("No se encontraron 'insumos_web' en la configuración.")

    insumos_local = config.get("insumos_local", {})
    base_local   = cfg["ETL_DIR"]
    temp_folder  = cfg["TEMP_FOLDER"]
    os.makedirs(temp_folder, exist_ok=True)

    resultado = {}
    errores   = []

    for key, url in insumos_web.items():
        zip_path = os.path.join(temp_folder, f"{key}.zip")
        try:
            logging.info(f"Descargando insumo '{key}' desde {url}...")
            descargar_archivo(url, zip_path)
            # Verifica si el archivo descargado está vacío
            if os.path.getsize(zip_path) == 0:
                raise ValueError("Archivo descargado está vacío.")
            logging.info(f"Insumo '{key}' descargado exitosamente.")
        except Exception as e:
            logging.warning(f"Error al descargar '{key}': {e}.")
            # Solo registramos el error y dejamos zip_path en None
            errores.append(_crear_error(url, key, insumos_local, base_local, str(e)))
            zip_path = None

        resultado[key] = zip_path

    # Subir información de errores e insumos a XCom
    ti = context["ti"]
    ti.xcom_push(key="errores", value=errores)
    ti.xcom_push(key="insumos_web", value=resultado)
    logging.info("Descarga de insumos finalizada (solo web).")
    return resultado

def _crear_error(url, key, insumos_local, base_local, error_msg):
    """Crea un diccionario de error para el insumo."""
    return {
        "url": url,
        "key": key,
        "insumos_local": insumos_local,
        "base_local": base_local,
        "error": error_msg
    }

def ejecutar_copia_insumo_local(**context):
    """
    Si no hubo errores descargando desde web, salta esta tarea.
    En caso contrario, por cada error intenta recuperar el insumo desde respaldo local.
    """
    errores = context["ti"].xcom_pull(key="errores", task_ids="Obtener_Insumos_Web") or []
    if len(errores) == 0:
        logging.info("✅ Todos los insumos se obtuvieron desde la web; se salta copia_insumo_local_task")
        raise AirflowSkipException("No hay insumos locales que copiar")

    recuperados = {}
    for err in errores:
        try:
            zip_path = copia_insumo_local(
                err["url"],
                err["key"],
                err["insumos_local"],
                err["base_local"],
                err["error"]
            )
            recuperados[err["key"]] = zip_path
        except Exception as exc:
            logging.error(f"Fallo al recuperar '{err['key']}': {exc}")

    context["ti"].xcom_push(key="insumos_local", value=recuperados)

def copia_insumo_local(url, key, insumos_local, base_local, error_msg):
    """
    Ante un error en la descarga, intenta buscar el respaldo local.
    Lanza una excepción si no se encuentra el respaldo.
    """
    logging.error(f"Error al descargar '{url}': {error_msg}")
    logging.info("Intentando buscar respaldo local...")
    zip_path = _validar_archivo_local(key, insumos_local, base_local)
    if not zip_path or not os.path.exists(zip_path):
        msg = f"No se encontró respaldo local para '{key}'."
        logging.error(msg)
        raise FileNotFoundError(msg)
    return zip_path

def _validar_archivo_local(key, insumos_local, base_local):
    """
    Verifica que exista un respaldo local para la clave dada y retorna la ruta.
    Se maneja tanto para clave directa como para claves compuestas (e.g. "padre_hijo").
    """
    logging.info("Iniciando validación de archivo local...")

    # Caso 1: Clave directa
    if key in insumos_local and isinstance(insumos_local[key], str):
        logging.info(f"Validando archivo local para '{key}'...")
        return obtener_ruta_local(base_local, insumos_local[key])

    msg = f"No se encontró entrada local para '{key}' en la configuración."
    logging.error(msg)
    raise FileNotFoundError(msg)

# ---------------------------------------------------------------------------
# Funciones para procesar insumos descargados
# ---------------------------------------------------------------------------

def procesar_insumos_descargados(cfg, **context):
    """
    Procesa los insumos descargados o copiados localmente:
      - Archivos ZIP: si tienen estructura de Excel empaquetado se copian y renombran a .xlsx; de lo contrario se extraen.
      - En caso de error de BadZipFile se tratan como GeoJSON.
      - Archivos Excel (.xls, .xlsx) o GeoJSON (.geojson) se copian a la carpeta temporal.
      - Otros formatos se omiten.
    Se reportan los resultados mediante XCom.
    """
    logging.info("Iniciando 'procesar_insumos_descargados'...")
    ti = context["ti"]
    temp_folder = cfg["TEMP_FOLDER"]

    # Recupera insumos desde XCom
    insumos_web = ti.xcom_pull(task_ids="Obtener_Insumos_Web", key="insumos_web") or {}
    insumos_local = ti.xcom_pull(task_ids="copia_insumo_local_task", key="insumos_local") or {}
    insumos_totales = {**insumos_web, **insumos_local}

    if not insumos_totales:
        raise Exception("❌ No se encontraron insumos para procesar.")

    resultados = []
    for key, file_path in insumos_totales.items():
        if not file_path or not os.path.exists(file_path):
            msg = f"❌ Archivo para '{key}' no encontrado: {file_path}"
            logging.error(msg)
            raise Exception(msg)

        extract_folder = os.path.join(temp_folder, key)
        os.makedirs(extract_folder, exist_ok=True)
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".zip":
            resultados.append(_procesar_zip(key, file_path, extract_folder))
        elif ext in [".xls", ".xlsx", ".geojson"]:
            destino = os.path.join(extract_folder, os.path.basename(file_path))
            try:
                shutil.copy(file_path, destino)
                logging.info(f"✔ Archivo '{file_path}' copiado a '{destino}'")
                resultados.append({
                    "key": key,
                    "file": destino,
                    "folder": extract_folder,
                    "type": "file"
                })
            except Exception as e:
                msg = f"❌ Error copiando '{file_path}' a '{destino}': {e}"
                logging.error(msg)
                raise Exception(msg)
        else:
            logging.warning(f"⚠ Formato '{ext}' no soportado para '{file_path}', se omite.")

    ti.xcom_push(key="insumos_procesados", value=resultados)
    logging.info(f"✔ Insumos procesados correctamente: {resultados}")
    return resultados

def _procesar_zip(key, file_path, extract_folder):
    """
    Procesa un archivo ZIP:
      - Si contiene estructura de Excel empaquetado se copia y renombra a .xlsx.
      - Si es un ZIP tradicional se extrae el contenido.
      - Si el ZIP es inválido se intenta tratar como GeoJSON.
    Retorna un diccionario con detalles del procesamiento.
    """
    try:
        logging.info(f"Procesando ZIP '{file_path}'...")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            namelist = zip_ref.namelist()
            # Se detecta Excel empaquetado por la presencia de "[Content_Types].xml" o carpeta "xl/"
            if "[Content_Types].xml" in namelist or any(n.startswith("xl/") for n in namelist):
                destino = os.path.join(extract_folder, key + ".xlsx")
                shutil.copy(file_path, destino)
                logging.info(f"Excel empaquetado detectado. Archivo copiado y renombrado a '{destino}'")
                return {"key": key, "file": destino, "folder": extract_folder, "type": "excel"}
            else:
                logging.info(f"Descomprimiendo ZIP '{file_path}' en: {extract_folder}")
                zip_ref.extractall(extract_folder)
                logging.info(f"✔ ZIP extraído en: {extract_folder}")
                return {"key": key, "file": file_path, "folder": extract_folder, "type": "zip"}
    except zipfile.BadZipFile as e:
        logging.warning(f"El archivo '{file_path}' no es un ZIP válido: {e}. Tratando como GeoJSON empaquetado.")
        destino = os.path.join(extract_folder, key + ".geojson")
        try:
            shutil.copy(file_path, destino)
            logging.info(f"✔ Archivo copiado como GeoJSON: {destino}")
            return {"key": key, "file": destino, "folder": extract_folder, "type": "geojson"}
        except Exception as e2:
            msg = f"❌ Error tratando '{file_path}' como GeoJSON: {e2}"
            logging.error(msg)
            raise Exception(msg)
    except Exception as e:
        msg = f"❌ Error procesando '{file_path}': {e}"
        logging.error(msg)
        raise Exception(msg)

# ---------------------------------------------------------------------------
# Funciones de importación a PostgreSQL
# ---------------------------------------------------------------------------

def ejecutar_importar_shp_a_postgres(cfg, **kwargs):
    """
    Recupera la información de insumos procesados desde XCom, busca en cada carpeta
    un archivo SHP y lo importa a la base de datos en la tabla correspondiente.
    """
    logging.info("Iniciando 'ejecutar_importar_shp_a_postgres'...")
    ti = kwargs['ti']
    insumos_info = ti.xcom_pull(task_ids='Descomprimir_Insumos', key="insumos_procesados")
    logging.info(f"Datos recuperados para importar SHP: {insumos_info}")
    
    if not insumos_info or not isinstance(insumos_info, list):
        msg = "No se encontró información válida de insumos en XCom."
        logging.error(msg)
        raise Exception(msg)

    config = leer_configuracion(cfg)
    db_config = config["db"]

    for insumo in insumos_info:
        if not isinstance(insumo, dict) or "key" not in insumo:
            logging.error(f"Formato incorrecto en insumo: {insumo}")
            continue
        key = insumo["key"]
        extract_folder = os.path.join(cfg["TEMP_FOLDER"], key)
        shp_files = _buscar_archivos_en_carpeta(extract_folder, [".shp"])
        if not shp_files:
            error_msg = f"No se encontró archivo SHP en {extract_folder} para '{key}'."
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
        table_name = f"insumos.{key}"
        logging.info(f"Importando SHP '{shp_files[0]}' en la tabla '{table_name}'...")
        _importar_shp_a_postgres(db_config, shp_files[0], table_name)
    
    logging.info("\033[92m✔ 'ejecutar_importar_shp_a_postgres' finalizó sin errores.\033[0m")

def ejecutar_importacion_general_a_postgres(cfg, **kwargs):
    """
    Importa archivos SHP, GeoJSON y Excel a PostgreSQL.
    Se buscan los archivos en la carpeta temporal para cada insumo, o se usa la ruta directa
    en el caso de Excel en modo especial.
    """
    logging.info("Iniciando 'ejecutar_importacion_general_a_postgres'...")
    ti = kwargs['ti']
    insumos_info = ti.xcom_pull(task_ids='Descomprimir_Insumos', key="insumos_procesados")
    logging.info(f"Datos recuperados para importación general: {insumos_info}")

    if not insumos_info or not isinstance(insumos_info, list):
        msg = "❌ No se encontró información válida de insumos en XCom."
        logging.error(msg)
        raise Exception(msg)

    engine = _obtener_engine_sqlalchemy(cfg)
    config = leer_configuracion(cfg)
    db_config = config["db"]

    for insumo in insumos_info:
        if not isinstance(insumo, dict) or "key" not in insumo:
            logging.error(f"Formato incorrecto en insumo: {insumo}")
            continue

        key = insumo["key"]
        folder = os.path.join(cfg["TEMP_FOLDER"], key)
        logging.info(f"[DEBUG] Carpeta esperada para '{key}': {folder}")
        if os.path.exists(folder):
            logging.info(f"[DEBUG] Contenido de '{folder}': {os.listdir(folder)}")
        else:
            logging.warning(f"[DEBUG] La carpeta '{folder}' no existe.")
            archivo_directo = insumo.get("zip_path")
            if archivo_directo and archivo_directo.lower().endswith(".xlsx") and os.path.exists(archivo_directo):
                logging.info(f"Procesando Excel directo para '{key}': {archivo_directo}")
                _importar_excel_a_postgres(cfg, engine, archivo_directo, table_name=key, schema="insumos")
                continue

        shp_files = _buscar_archivos_en_carpeta(folder, [".shp"])
        geojson_files = _buscar_archivos_en_carpeta(folder, [".geojson"])
        xlsx_files = _buscar_archivos_en_carpeta(folder, [".xlsx"])

        logging.info(f"Archivos SHP encontrados: {shp_files}")
        logging.info(f"Archivos GeoJSON encontrados: {geojson_files}")
        logging.info(f"Archivos Excel encontrados: {xlsx_files}")

        if not shp_files and not geojson_files and not xlsx_files:
            msg = f"❌ El insumo '{key}' no contiene archivos compatibles."
            logging.error(msg)
            raise Exception(msg)

        for shp_file in shp_files:
            tname = f"insumos.{key}"
            logging.info(f"Importando SHP: {shp_file} -> {tname}")
            _importar_shp_a_postgres(db_config, shp_file, tname)

        for geojson_file in geojson_files:
            tname = f"insumos.{key}"
            logging.info(f"Importando GeoJSON: {geojson_file} -> {tname}")
            _importar_geojson_a_postgres(db_config, geojson_file, tname)

        for xlsx_file in xlsx_files:
            logging.info(f"Importando Excel: {xlsx_file} -> insumos.{key}")
            _importar_excel_a_postgres(cfg, engine, xlsx_file, table_name=key, schema="insumos")

    logging.info("✔ Importación a PostgreSQL completada correctamente.")

def _buscar_archivos_en_carpeta(folder, extensiones):
    """
    Busca recursivamente en 'folder' archivos que terminen con alguna de las extensiones dadas.
    Solo retorna archivos existentes con tamaño mayor a 0.
    """
    encontrados = []
    for root, _, files in os.walk(folder):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensiones):
                full_path = os.path.join(root, file)
                if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                    encontrados.append(full_path)
    return encontrados

def _importar_shp_a_postgres(db_config, shp_file, table_name):
    """
    Importa el archivo SHP a PostgreSQL utilizando ogr2ogr sin crear índices espaciales.
    """
    logging.info(f"Importando '{shp_file}' en la tabla '{table_name}'...")
    command = [
        "ogr2ogr", "-f", "PostgreSQL",
        f"PG:host={db_config['host']} port={db_config['port']} dbname={db_config['db_name']} user={db_config['user']} password={db_config['password']}",
        shp_file,
        "-nln", table_name,
        "-overwrite", "-progress",
        "-lco", "GEOMETRY_NAME=geom",
        "-lco", "FID=gid",
        "-lco", "PRECISION=NO",
        "-lco", "SPATIAL_INDEX=NONE",
        "-nlt", "PROMOTE_TO_MULTI"
        # SIN -t_srs ni -a_srs
    ]
    ejecutar_ogr2ogr(command, f"importar SHP en '{table_name}'")
    logging.info(f"Archivo '{shp_file}' importado correctamente en '{table_name}'.")
    logging.info("\033[92m✔ _importar_shp_a_postgres finalizó sin errores.\033[0m")

def _importar_geojson_a_postgres(db_config, geojson_file, table_name):
    """
    Importa el archivo GeoJSON a PostgreSQL utilizando ogr2ogr.
    """
    logging.info(f"Importando GeoJSON '{geojson_file}' en '{table_name}'...")
    command = [
        "ogr2ogr", "-f", "PostgreSQL",
        f"PG:host={db_config['host']} port={db_config['port']} dbname={db_config['db_name']} user={db_config['user']} password={db_config['password']}",
        geojson_file,
        "-nln", table_name,
        "-overwrite", "-progress",
        "-lco", "GEOMETRY_NAME=geom", "-lco", "FID=gid",
        "-nlt", "PROMOTE_TO_MULTI", "-t_srs", "EPSG:9377"
    ]
    ejecutar_ogr2ogr(command, f"importar GeoJSON en '{table_name}'")
    logging.info(f"\033[92m✔ GeoJSON '{geojson_file}' importado correctamente en '{table_name}'.\033[0m")

def _importar_excel_a_postgres(cfg, engine, xlsx_file, table_name, schema="insumos"):
    """
    Importa un archivo Excel a PostgreSQL.
    Dependiendo del directorio ETL se utiliza una función específica o se usa pandas.
    """
    config = leer_configuracion(cfg)
    db_config = config["db"]
    
    if "etl/etl_ap" in cfg["ETL_DIR"]:    
        return import_excel_to_db(db_config, xlsx_file, table_name)
    
    if "etl/etl_rfpn" in cfg["ETL_DIR"]:
        sheet = "Actos" if table_name == "informacion_area_reserva" else None
        table_name = shorten_identifier(table_name)
        return import_excel_to_db2(db_config, xlsx_file, table_name, sheet)
    
    logging.info(f"Iniciando importación de Excel '{xlsx_file}' en {schema}.{table_name}...")
    try:
        df = pd.read_excel(xlsx_file)
        df.to_sql(name=table_name, con=engine, schema=schema, if_exists='replace', index=False)
        logging.info(f"\033[92m✔ Excel '{xlsx_file}' importado correctamente en {schema}.{table_name}.\033[0m")
    except Exception as e:
        msg = f"Error importando Excel '{xlsx_file}': {e}"
        logging.error(msg)
        raise Exception(msg)

def import_excel_to_db2(db_config, excel_path, table_name, sheet_name=None):
    """Importa Excel a 'insumos.table_name' usando pandas (logs estilo RL2)."""
    logging.info(f"Iniciando import_excel_to_db para {excel_path} en tabla insumos.{table_name}...")
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name) if sheet_name else pd.read_excel(excel_path)
        logging.info(f"Excel cargado: {len(df)} filas.")
    except Exception as e:
        logging.error(f"Error leyendo Excel {excel_path}: {e}")
        logging.error("\033[91m❌ import_excel_to_db falló.\033[0m")
        raise e

    if table_name == "informacion_area_reserva" and sheet_name == "Actos":
        cond1 = (df["Categoría de manejo"] == "Reservas Forestales Protectoras Nacionales")
        cond2 = df["Tipo de acto administrativo"].isin(["Acuerdos", "Resolución"])
        cond3 = (df["Objeto del acto"] == "Declaratoria")
        df = df[cond1 & cond2 & cond3]
        logging.info(f"Filtrado para 'informacion_area_reserva' (Actos): {len(df)} filas restantes.")

    engine = sqlalchemy.create_engine(
        f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
    )
    try:
        df.to_sql(table_name, engine, schema='insumos', if_exists='replace', index=False)
        logging.info(f"Datos insertados en insumos.{table_name}")
        logging.info("\033[92m✔ import_excel_to_db finalizó sin errores.\033[0m")
    except Exception as e:
        logging.error(f"Error insertando datos en insumos.{table_name}: {e}")
        logging.error("\033[91m❌ import_excel_to_db falló.\033[0m")
        raise e

def import_excel_to_db(db_config, excel_file, key):
    """
    Lee las hojas "General" y "Actos" de un archivo Excel, realiza un merge LEFT basado en 
    "Id del área protegida" y guarda el resultado en la tabla insumos.<key>_excel.
    """
    logging.info(f"Iniciando import_excel_to_db para {excel_file} en insumo '{key}'...")

    try:
        df_general = pd.read_excel(excel_file, sheet_name="General", index_col=None).reset_index(drop=True)
        logging.info(f"Hoja 'General' leída con {len(df_general)} filas.")
    except Exception as e:
        msg = f"Error leyendo la hoja 'General' de {excel_file}: {e}"
        logging.error(msg)
        raise Exception(msg)

    try:
        df_actos = pd.read_excel(excel_file, sheet_name="Actos", index_col=None).reset_index(drop=True)
        logging.info(f"Hoja 'Actos' leída con {len(df_actos)} filas.")
    except Exception as e:
        msg = f"Error leyendo la hoja 'Actos' de {excel_file}: {e}"
        logging.error(msg)
        raise Exception(msg)

    valid_objetos = ["Declaratoria", "Registro RNSC", "Declaratoria y adopcion de plan de manejo"]

    def choose_row(group):
        matching = group[group["Objeto del acto"].isin(valid_objetos)]
        return matching.iloc[0] if not matching.empty else group.iloc[0]

    try:
        df_actos_reducido = df_actos.groupby("Id del área protegida", group_keys=False).apply(choose_row).reset_index(drop=True)
        logging.info(f"Reducción de 'Actos': {len(df_actos_reducido)} filas resultantes (1 por cada id).")
    except Exception as e:
        msg = f"Error reduciendo 'Actos': {e}"
        logging.error(msg)
        raise Exception(msg)

    try:
        df_merged = pd.merge(df_general, df_actos_reducido, on="Id del área protegida", how="left")
        logging.info(f"Merge realizado: {len(df_merged)} filas resultantes (deberían ser {len(df_general)}).")
    except Exception as e:
        msg = f"Error realizando merge: {e}"
        logging.error(msg)
        raise Exception(msg)

    table_name = f"insumos.{shorten_identifier(key)}_excel"
    engine = sqlalchemy.create_engine(
        f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
    )
    try:
        df_merged.to_sql(table_name.split('.')[-1], engine, schema="insumos", if_exists="replace", index=False)
        logging.info(f"Excel importado en la tabla {table_name}.")
    except Exception as e:
        msg = f"Error insertando Excel en {table_name}: {e}"
        logging.error(msg)
        raise Exception(msg)

def shorten_identifier(identifier):
    """
    Convierte una cadena eliminando caracteres no válidos y pasándola a minúsculas.
    """
    return re.sub(r'\W+', '_', identifier).lower()

def crear_cruce_area_reserva_directo(cfg):
    """
    Crea la tabla insumos.cruce_area_reserva uniendo area_reserva_* con insumos.informacion_area_reserva.
    """
    logging.info("Iniciando crear_cruce_area_reserva_directo...")
    drop_sql = "DROP TABLE IF EXISTS insumos.cruce_area_reserva CASCADE;"
    ejecutar_sql(cfg, drop_sql)

    sql_script = r"""
    DO $$
    DECLARE
        rec record;
        col_name text;
        sql_text text := '';
        first_table boolean := true;
    BEGIN
        FOR rec IN
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'insumos'
              AND table_name LIKE 'area_reserva_%'
            ORDER BY table_name
        LOOP
            SELECT CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema='insumos' AND table_name=rec.table_name AND column_name='ap_id'
                    ) THEN 'ap_id'
                    WHEN EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema='insumos' AND table_name=rec.table_name AND column_name='apid'
                    ) THEN 'apid'
                    WHEN EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_schema='insumos' AND table_name=rec.table_name AND column_name='idpnn'
                    ) THEN 'idpnn'
                    ELSE NULL
                END INTO col_name;

            IF col_name IS NULL THEN
                RAISE NOTICE 'La tabla % no tiene columna de identificación; se omite.', rec.table_name;
            ELSE
                IF first_table THEN
                    sql_text := sql_text || format($f$
                        CREATE TABLE insumos.cruce_area_reserva AS
                        SELECT
                            t.gid,
                            ST_Force2D(t.geom) AS geom,
                            COALESCE((t.%I)::text, '') AS ap_id_norm,
                            i.*
                        FROM insumos.%I t
                        LEFT JOIN insumos.informacion_area_reserva i
                            ON COALESCE((t.%I)::text, '')::bigint = i."Id del área protegida";
                    $f$, col_name, rec.table_name, col_name);
                    first_table := false;
                ELSE
                    sql_text := sql_text || format($f$
                        INSERT INTO insumos.cruce_area_reserva
                        SELECT
                            t.gid,
                            ST_Force2D(t.geom) AS geom,
                            COALESCE((t.%I)::text, '') AS ap_id_norm,
                            i.*
                        FROM insumos.%I t
                        LEFT JOIN insumos.informacion_area_reserva i
                            ON COALESCE((t.%I)::text, '')::bigint = i."Id del área protegida";
                    $f$, col_name, rec.table_name, col_name);
                END IF;
            END IF;
        END LOOP;
        EXECUTE sql_text;
    END $$;
    """
    ejecutar_sql(cfg, sql_script)
    logging.info("Tabla insumos.cruce_area_reserva creada exitosamente (directo).")
    logging.info("\033[92m✔ crear_cruce_area_reserva_directo finalizó sin errores.\033[0m")