from datetime import datetime
import logging
from functools import partial

# Airflow
from airflow import DAG

from airflow.operators.python import PythonOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

# Cambiamos el nivel a INFO para que se vea en Airflow
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

from pathlib import Path
import json
    
OTL_DIR = Path(__file__).resolve().parent.parent.parent / "otl"

local_cfg_path = OTL_DIR / "etl" / "etl_hmdr" / "config_hmdr.json"
global_cfg_path = OTL_DIR / "config_global.json"

# === 2. Función auxiliar para leer JSON ===
def load_cfg(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)

# === 3. Cargar y fusionar ===
cfg_global = load_cfg(global_cfg_path)
cfg_local  = load_cfg(local_cfg_path)

cfg = cfg_global | cfg_local

from logic.expectation import (
    reporte_expectativas_insumos
)

from logic.data_workflow import (
    ejecutar_importar_estructura_intermedia,
    ejecutar_migracion_datos_estructura_intermedia,
    ejecutar_validacion_datos,
    ejecutar_migracion_datos_ladm
)

from utils.db_utils import (
    validar_conexion_postgres,
    revisar_existencia_db,
    crear_base_datos,
    adicionar_extensiones,
    restablecer_esquema_insumos,
    restablecer_esquema_estructura_intermedia,
    restablecer_esquema_ladm
)

from utils.data_utils import (
    obtener_insumos_desde_web,
    ejecutar_copia_insumo_local,
    procesar_insumos_descargados,
    ejecutar_importacion_general_a_postgres
)      

from utils.interlis_utils import (
    importar_esquema_ladm,
    exportar_datos_ladm
)

# ------------------------- DEFINICIÓN DEL DAG -------------------------
default_args = {
    "owner": "airflow",
    "start_date": datetime(2025, 2, 25)
}

with DAG(
    "etl_hmdr_xtf",
    default_args=default_args,
    schedule_interval=None,
    catchup=False
) as dag:

    inicio_etl = EmptyOperator(task_id="Inicio_ETL_LADM_HMDR")
    
    validar_conexion_postgres_task = PythonOperator(
        task_id="Validar_Conexion_Postgres",
        python_callable=lambda: validar_conexion_postgres(cfg),
        retries=0
    )
    
    revisar_existencia_db_task = BranchPythonOperator(
        task_id="Revisar_Existencia_DB",
        python_callable=lambda: revisar_existencia_db(cfg),
        retries=0
    )
    
    crear_base_datos_task = PythonOperator(
        task_id="Crear_Base_Datos",
        python_callable=lambda: crear_base_datos(cfg),
        retries=0
    )
    
    adicionar_extensiones_task = PythonOperator(
        task_id="Adicionar_Extensiones",
        python_callable=lambda: adicionar_extensiones(cfg),
        retries=0,
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    )
    
    conexion_postgres_fallida = EmptyOperator(
        task_id="Conexion_Postgres_Fallida",
        trigger_rule=TriggerRule.ONE_FAILED
    )

    restablecer_esquema_insumos_task = PythonOperator(
        task_id="Restablecer_Esquema_Insumos",
        python_callable=lambda: restablecer_esquema_insumos(cfg),
        retries=0
    )

    obtener_insumos_desde_web_task = PythonOperator( 
        task_id="Obtener_Insumos_Web",
        python_callable=partial(obtener_insumos_desde_web, cfg=cfg),
        provide_context=True
    )

    copia_insumo_local_task = PythonOperator(
        task_id="copia_insumo_local_task",
        python_callable=ejecutar_copia_insumo_local,
        provide_context=True,
        trigger_rule=TriggerRule.ONE_SUCCESS  # Se ejecuta si hay éxito o fallo parcial
    )
    
    descomprimir_insumos_task = PythonOperator(
        task_id="Descomprimir_Insumos",
        python_callable=partial(procesar_insumos_descargados, cfg=cfg),
        provide_context=True,
        trigger_rule=TriggerRule.ALL_DONE  # Asegura que se ejecute después de ambas tareas
    )
    
    importar_archivos_postgres_task = PythonOperator(
        task_id="Importar_Archivos_Postgres",
        python_callable=partial(ejecutar_importacion_general_a_postgres, cfg=cfg),
        provide_context=True,
        retries=0
    )
    
    reporte_expectativas_insumos_task = PythonOperator(
        task_id="Reporte_Expectativas_Insumos",
        python_callable=lambda: reporte_expectativas_insumos("gx_insumos.yml", "insumos", cfg),
        retries=0
    )
    
    restablecer_estructura_intermedia_task = PythonOperator(
        task_id="Restablecer_Estructura_Intermedia",
        python_callable=lambda: restablecer_esquema_estructura_intermedia(cfg),
        retries=0
    )
    
    importar_estructura_intermedia_task = PythonOperator(
        task_id="Importar_Estructura_Intermedia",
        python_callable=lambda: ejecutar_importar_estructura_intermedia(cfg),
        retries=0
    )
    
    reporte_expectativas_estructura_task = PythonOperator(
        task_id="Reporte_Expectativas_Estructura",
        python_callable=lambda: reporte_expectativas_insumos("gx_estructura_intermedia.yml", "estructura_intermedia", cfg),
        retries=0
    )
    
    restablecer_esquema_ladm_task = PythonOperator(
        task_id="Restablecer_Esquema_LADM",
        python_callable=lambda: restablecer_esquema_ladm(cfg),
        retries=0
    )
    
    importar_esquema_ladm_task = PythonOperator(
        task_id="Importar_Esquema_LADM",
        python_callable=lambda: importar_esquema_ladm(cfg),
        retries=0
    )
    
    reporte_expectativas_ladm_task = PythonOperator(
        task_id="Reporte_Expectativas_LADM",
        python_callable=lambda: reporte_expectativas_insumos("gx_ladm.yml", "ladm", cfg),
        retries=0
    )
    
    migracion_datos_estructura_intermedia_task = PythonOperator(
        task_id="Migracion_Datos_Estructura_Intermedia",
        python_callable=lambda: ejecutar_migracion_datos_estructura_intermedia(cfg),
        retries=0
    )
    
    validacion_datos_task = PythonOperator(
        task_id="Validacion_Datos",
        python_callable=lambda: ejecutar_validacion_datos(cfg),
        retries=0
    )
    
    migracion_datos_ladm_task = PythonOperator(
        task_id="Migracion_Datos_LADM",
        python_callable=lambda: ejecutar_migracion_datos_ladm(cfg),
        retries=0
    )
    
    reporte_expectativas_ladm_despues_task = PythonOperator(
        task_id="Reporte_Expectativas_LADM_Despues",
        python_callable=lambda: reporte_expectativas_insumos("gx_ladm.yml", "ladm", cfg),
        retries=0
    )
    
    exportar_datos_ladm_task = PythonOperator(
        task_id="Exportar_Datos_LADM",
        python_callable=lambda: exportar_datos_ladm(cfg),
        retries=0
    )
    
    fin_etl = EmptyOperator(task_id="Finaliza_ETL_LADM_HMDR")

    # Cadena de ejecución del DAG
    inicio_etl >> validar_conexion_postgres_task
    validar_conexion_postgres_task >> revisar_existencia_db_task
    validar_conexion_postgres_task >> conexion_postgres_fallida
    revisar_existencia_db_task >> crear_base_datos_task
    revisar_existencia_db_task >> adicionar_extensiones_task
    crear_base_datos_task >> adicionar_extensiones_task
    adicionar_extensiones_task >> [
        restablecer_esquema_insumos_task,
        restablecer_estructura_intermedia_task,
        restablecer_esquema_ladm_task
    ]
    restablecer_esquema_insumos_task >> obtener_insumos_desde_web_task >> copia_insumo_local_task >> descomprimir_insumos_task >> importar_archivos_postgres_task >> reporte_expectativas_insumos_task
    restablecer_esquema_insumos_task >> obtener_insumos_desde_web_task >> descomprimir_insumos_task >> importar_archivos_postgres_task >> reporte_expectativas_insumos_task
    restablecer_estructura_intermedia_task >> importar_estructura_intermedia_task >> reporte_expectativas_estructura_task
    restablecer_esquema_ladm_task >> importar_esquema_ladm_task >> reporte_expectativas_ladm_task
    [reporte_expectativas_insumos_task, reporte_expectativas_estructura_task, reporte_expectativas_ladm_task] >> migracion_datos_estructura_intermedia_task
    migracion_datos_estructura_intermedia_task >> validacion_datos_task
    validacion_datos_task >> migracion_datos_ladm_task
    migracion_datos_ladm_task >> reporte_expectativas_ladm_despues_task >> exportar_datos_ladm_task
    exportar_datos_ladm_task >> fin_etl
