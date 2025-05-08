#!/usr/bin/env python
import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import tempfile
import shutil
import zipfile
import subprocess
import pandas as pd
import json
import re

# Agregamos al path la ubicación del módulo a probar
import utils.data_utils

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Test credentials from environment variables with defaults for testing
TEST_DB_USER = os.getenv('TEST_DB_USER', 'test_user')
TEST_DB_PASSWORD = os.getenv('TEST_DB_PASSWORD', 'test_pass')
TEST_DB_HOST = os.getenv('TEST_DB_HOST', 'localhost')
TEST_DB_PORT = os.getenv('TEST_DB_PORT', '5432')
TEST_DB_NAME = os.getenv('TEST_DB_NAME', 'test_db')

class TestDataUtils(unittest.TestCase):
    def setUp(self):
        # Creamos un directorio temporal para simular ETL_DIR y TEMP_FOLDER
        self.temp_dir = tempfile.mkdtemp()
        self.cfg = {
            "ETL_DIR": self.temp_dir,
            "TEMP_FOLDER": os.path.join(self.temp_dir, "temp"),
            "CONFIG_PATH": os.path.join(self.temp_dir, "config.json")
        }
        os.makedirs(self.cfg["TEMP_FOLDER"], exist_ok=True)
        # Se crea un archivo JSON dummy para CONFIG_PATH
        dummy_config = {"insumos_web": {}, "insumos_local": {}, "db": {}}
        with open(self.cfg["CONFIG_PATH"], "w") as f:
            json.dump(dummy_config, f)
        
        # Standard test database configuration
        self.test_db_config = {
            "user": TEST_DB_USER,
            "password": TEST_DB_PASSWORD,
            "host": TEST_DB_HOST,
            "port": TEST_DB_PORT,
            "db_name": TEST_DB_NAME
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    # -----------------------------
    # Pruebas existentes ya implementadas
    # -----------------------------
    @patch("utils.data_utils.limpiar_carpeta_temporal")
    @patch("utils.data_utils.leer_configuracion")
    def test_obtener_insumos_desde_web_no_insumos(self, mock_leer_config, mock_limpiar):
        mock_leer_config.return_value = {}
        fake_ti = MagicMock()
        context = {"ti": fake_ti}
        with self.assertRaises(ValueError):
            utils.data_utils.obtener_insumos_desde_web(self.cfg, **context)

    @patch("utils.data_utils.requests.get")
    @patch("utils.data_utils.limpiar_carpeta_temporal")
    @patch("utils.data_utils.leer_configuracion")
    def test_obtener_insumos_desde_web_success(self, mock_leer_config, mock_limpiar, mock_requests_get):
        insumos_web = {"test": "https://example.com/test.zip"}
        insumos_local = {"test": "local/test.zip"}
        mock_leer_config.return_value = {
            "insumos_web": insumos_web,
            "insumos_local": insumos_local,
            "db": {}
        }
        fake_response = MagicMock()
        fake_response.iter_content = lambda chunk_size: [b"data"]
        fake_response.raise_for_status = lambda: None
        mock_requests_get.return_value = fake_response
        fake_ti = MagicMock()
        context = {"ti": fake_ti}
        with patch("os.path.getsize", return_value=10):
            resultado = utils.data_utils.obtener_insumos_desde_web(self.cfg, **context)
        self.assertIn("test", resultado)
        self.assertIsNotNone(resultado["test"])
        fake_ti.xcom_push.assert_any_call(key="errores", value=[])
        fake_ti.xcom_push.assert_any_call(key="insumos_web", value=resultado)
        
    @patch("utils.data_utils.requests.get")
    @patch("utils.data_utils.limpiar_carpeta_temporal")
    @patch("utils.data_utils.leer_configuracion")
    def test_obtener_insumos_desde_web_archivo_vacio(self, mock_leer_config, mock_limpiar, mock_requests_get):
        insumos_web = {"test": "https://example.com/test.zip"}
        insumos_local = {"test": "local/test.zip"}
        mock_leer_config.return_value = {
            "insumos_web": insumos_web,
            "insumos_local": insumos_local,
            "db": {}
        }
        fake_response = MagicMock()
        fake_response.iter_content = lambda chunk_size: [b""]
        fake_response.raise_for_status = lambda: None
        mock_requests_get.return_value = fake_response
        fake_ti = MagicMock()
        context = {"ti": fake_ti}

        with patch("os.path.getsize", return_value=0):
            resultado = utils.data_utils.obtener_insumos_desde_web(self.cfg, **context)

        self.assertIsNone(resultado["test"])
        fake_ti.xcom_push.assert_any_call(key="errores", value=unittest.mock.ANY)


    def test_validar_archivo_local_success(self):
        key = "test"
        insumos_local = {"test": "/dummy/test.zip"}
        base_local = self.temp_dir
        local_dir = os.path.join(base_local, "dummy")
        os.makedirs(local_dir, exist_ok=True)
        full_path = os.path.join(local_dir, "test.zip")
        with open(full_path, "w") as f:
            f.write("contenido")
        resultado = utils.data_utils._validar_archivo_local(key, insumos_local, base_local)
        self.assertEqual(resultado, full_path)

    def test_validar_archivo_local_no_entry(self):
        key = "not_exist"
        insumos_local = {"test": "/dummy/test.zip"}
        base_local = self.temp_dir
        with self.assertRaises(FileNotFoundError):
            utils.data_utils._validar_archivo_local(key, insumos_local, base_local)

    def test_validar_archivo_local_file_missing(self):
        key = "test"
        insumos_local = {"test": "/dummy/missing.zip"}
        base_local = self.temp_dir
        with self.assertRaises(FileNotFoundError):
            utils.data_utils._validar_archivo_local(key, insumos_local, base_local)
    
    def test_validar_archivo_local_unsupported_format(self):
        key = "composite_key"
        insumos_local = {"composite_key": 123}  # No es string
        base_local = self.temp_dir
        with self.assertRaises(FileNotFoundError):
            utils.data_utils._validar_archivo_local(key, insumos_local, base_local)

    def test_procesar_insumos_descargados_sin_insumos(self):
        fake_ti = MagicMock()
        fake_ti.xcom_pull.side_effect = [None, None]
        context = {"ti": fake_ti}
        with self.assertRaises(Exception) as cm:
            utils.data_utils.procesar_insumos_descargados(self.cfg, **context)
        self.assertIn("no se encontraron insumos", str(cm.exception).lower())

    def test_procesar_insumos_descargados_archivo_inexistente(self):
        fake_ti = MagicMock()
        fake_ti.xcom_pull.side_effect = [{"test": "/ruta/falsa.zip"}, {}]
        context = {"ti": fake_ti}
        with self.assertRaises(Exception) as cm:
            utils.data_utils.procesar_insumos_descargados(self.cfg, **context)
        self.assertIn("archivo para", str(cm.exception).lower())

    def test_ejecutar_importacion_general_archivo_directo_excel_inexistente(self):
        self.cfg["db"] = self.test_db_config
        file_path = os.path.join(self.temp_dir, "missing.xlsx")  # No se crea
        fake_ti = MagicMock()
        fake_ti.xcom_pull.return_value = [{"key": "test", "zip_path": file_path}]
        context = {"ti": fake_ti}
        with patch("utils.data_utils._obtener_engine_sqlalchemy", return_value=MagicMock()):
            with self.assertRaises(Exception) as cm:
                utils.data_utils.ejecutar_importacion_general_a_postgres(self.cfg, **context)
            self.assertIn("no contiene archivos compatibles", str(cm.exception).lower())

    def test_importar_excel_a_postgres_falla_import_ap(self):
        cfg_ap = self.cfg.copy()
        cfg_ap["ETL_DIR"] = os.path.join(self.temp_dir, "etl/etl_ap")
        os.makedirs(cfg_ap["ETL_DIR"], exist_ok=True)
        engine = MagicMock()
        with patch("utils.data_utils.import_excel_to_db", side_effect=Exception("fallo")):
            with self.assertRaises(Exception) as cm:
                utils.data_utils._importar_excel_a_postgres(cfg_ap, engine, "archivo.xlsx", "test")
            self.assertIn("fallo", str(cm.exception).lower())

    @patch("utils.data_utils.copia_insumo_local")
    def test_ejecutar_copia_insumo_local(self, mock_copia):
        fake_ti = MagicMock()
        context = {"ti": fake_ti}
        error_entry = {
            "url": "https://example.com",
            "key": "test",
            "insumos_local": {"test": "dummy/test.zip"},
            "base_local": self.temp_dir,
            "error": "error de descarga",
        }
        fake_ti.xcom_pull.return_value = [error_entry]
        mock_copia.return_value = "/dummy/test.zip"
        utils.data_utils.ejecutar_copia_insumo_local(**context)
        fake_ti.xcom_push.assert_called_with(key="insumos_local", value={"test": "/dummy/test.zip"})

    def test_procesar_insumos_descargados_zip_success(self):
        temp_folder = self.cfg["TEMP_FOLDER"]
        dummy_zip_path = os.path.join(temp_folder, "test.zip")
        with zipfile.ZipFile(dummy_zip_path, 'w') as zipf:
            zipf.writestr("dummy.txt", "contenido dummy")
        fake_ti = MagicMock()
        fake_ti.xcom_pull.side_effect = [
            {"test": dummy_zip_path},
            {}
        ]
        context = {"ti": fake_ti}
        resultado = utils.data_utils.procesar_insumos_descargados(self.cfg, **context)
        self.assertIsInstance(resultado, list)
        self.assertEqual(resultado[0]["key"], "test")
        extract_folder = resultado[0]["folder"]
        self.assertTrue(os.path.exists(extract_folder))
        self.assertIn("dummy.txt", os.listdir(extract_folder))
    
    def test_procesar_insumos_descargados_error_copiando(self):
        temp_folder = self.cfg["TEMP_FOLDER"]
        file_path = os.path.join(temp_folder, "test.xlsx")
        with open(file_path, "w") as f:
            f.write("contenido")
        
        fake_ti = MagicMock()
        fake_ti.xcom_pull.side_effect = [
            {},  # insumos_web vacío
            {"test": file_path}  # insumos_local
        ]
        context = {"ti": fake_ti}

        with patch("utils.data_utils.shutil.copy", side_effect=Exception("copy failed")):
            with self.assertRaises(Exception) as cm:
                utils.data_utils.procesar_insumos_descargados(self.cfg, **context)
            self.assertIn("❌ Error copiando", str(cm.exception))

    def test_buscar_archivos_en_carpeta(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            file1 = os.path.join(tmp_dir, "archivo.shp")
            file2 = os.path.join(tmp_dir, "archivo.txt")
            with open(file1, "w") as f:
                f.write("contenido")
            with open(file2, "w") as f:
                f.write("contenido")
            encontrados = utils.data_utils._buscar_archivos_en_carpeta(tmp_dir, [".shp"])
            self.assertIn(file1, encontrados)
            self.assertNotIn(file2, encontrados)

    @patch("utils.data_utils.subprocess.run")
    def test_importar_shp_a_postgres_success(self, mock_run):
        utils.data_utils._importar_shp_a_postgres(self.test_db_config, "dummy.shp", "insumos.test")
        mock_run.assert_called()

    @patch("utils.data_utils.subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd", stderr="error"))
    def test_importar_shp_a_postgres_failure(self, mock_run):
        with self.assertRaises(Exception) as context_exc:
            utils.data_utils._importar_shp_a_postgres(self.test_db_config, "dummy.shp", "insumos.test")
        self.assertIn("error", str(context_exc.exception))

    @patch("utils.data_utils.subprocess.run")
    def test_importar_geojson_a_postgres_success(self, mock_run):
        utils.data_utils._importar_geojson_a_postgres(self.test_db_config, "dummy.geojson", "insumos.test")
        mock_run.assert_called()

    @patch("utils.data_utils.subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd", stderr="geo error"))
    def test_importar_geojson_a_postgres_failure(self, mock_run):
        with self.assertRaises(Exception) as context_exc:
            utils.data_utils._importar_geojson_a_postgres(self.test_db_config, "dummy.geojson", "insumos.test")
        self.assertIn("geo error", str(context_exc.exception))

    @patch("utils.data_utils.pd.read_excel")
    @patch("utils.data_utils.pd.DataFrame.to_sql")
    def test_importar_excel_a_postgres_success(self, mock_to_sql, mock_read_excel):
        df_dummy = pd.DataFrame({"col": [1, 2, 3]})
        mock_read_excel.return_value = df_dummy
        dummy_engine = MagicMock()
        utils.data_utils._importar_excel_a_postgres(self.cfg, dummy_engine, "dummy.xlsx", "test_table")
        mock_read_excel.assert_called_with("dummy.xlsx")
        mock_to_sql.assert_called_with(
            name="test_table",
            con=dummy_engine,
            schema="insumos",
            if_exists="replace",
            index=False,
        )

    @patch("utils.data_utils.pd.read_excel", side_effect=Exception("read error"))
    def test_importar_excel_a_postgres_failure(self, mock_read_excel):
        dummy_engine = MagicMock()
        with self.assertRaises(Exception) as context_exc:
            utils.data_utils._importar_excel_a_postgres(self.cfg, dummy_engine, "dummy.xlsx", "test_table")
        self.assertIn("read error", str(context_exc.exception))

    def test_ejecutar_importacion_general_a_postgres_no_insumos(self):
        fake_ti = MagicMock()
        fake_ti.xcom_pull.return_value = None
        with self.assertRaises(Exception) as context_exc:
            utils.data_utils.ejecutar_importacion_general_a_postgres(self.cfg, ti=fake_ti)
        self.assertIn("No se encontró información válida de insumos", str(context_exc.exception))
        
    @patch("utils.data_utils._importar_excel_a_postgres")
    @patch("utils.data_utils._obtener_engine_sqlalchemy")
    def test_importacion_excel_directo(self, mock_get_engine, mock_import_excel):
        file_path = os.path.join(self.temp_dir, "test.xlsx")
        with open(file_path, "w") as f:
            f.write("dummy")

        self.cfg["db"] = self.test_db_config

        fake_ti = MagicMock()
        fake_ti.xcom_pull.return_value = [{"key": "test", "zip_path": file_path}]
        context = {"ti": fake_ti}

        mock_get_engine.return_value = MagicMock()
        mock_import_excel.return_value = "ok"

        utils.data_utils.ejecutar_importacion_general_a_postgres(self.cfg, **context)
        mock_import_excel.assert_called_once()
        
    def test_importacion_general_sin_archivos(self):
        folder = os.path.join(self.cfg["TEMP_FOLDER"], "empty")
        os.makedirs(folder, exist_ok=True)
        
        self.cfg["db"] = {  # Necesario para _obtener_engine_sqlalchemy
            "user": TEST_DB_USER,
            "password": TEST_DB_PASSWORD,
            "host": TEST_DB_HOST,
            "port": TEST_DB_PORT,
            "db_name": TEST_DB_NAME
        }

        fake_ti = MagicMock()
        fake_ti.xcom_pull.return_value = [{"key": "empty"}]
        context = {"ti": fake_ti}

        # Mockear _obtener_engine_sqlalchemy para evitar conexión real
        with patch("utils.data_utils._obtener_engine_sqlalchemy", return_value=MagicMock()):
            with self.assertRaises(Exception) as cm:
                utils.data_utils.ejecutar_importacion_general_a_postgres(self.cfg, **context)
            self.assertIn("no contiene archivos compatibles", str(cm.exception).lower())


    # -----------------------------
    # NUEVAS PRUEBAS PARA CUBRIR FUNCIONES ADICIONALES
    # -----------------------------
    def test_descargar_archivo_success(self):
        dest_file = os.path.join(self.temp_dir, "downloaded_file.txt")
        fake_response = MagicMock()
        fake_response.iter_content = lambda chunk_size: [b"test data"]
        fake_response.raise_for_status = lambda: None
        with patch("utils.data_utils.requests.get", return_value=fake_response):
            resultado = utils.data_utils.descargar_archivo("https://dummy", dest_file)
        self.assertEqual(resultado, dest_file)
        with open(dest_file, "rb") as f:
            self.assertEqual(f.read(), b"test data")

    def test_obtener_ruta_local_success(self):
        file_path = os.path.join(self.temp_dir, "dummy.txt")
        with open(file_path, "w") as f:
            f.write("content")
        ruta = utils.data_utils.obtener_ruta_local(self.temp_dir, "/dummy.txt")
        self.assertEqual(ruta, file_path)

    def test_obtener_ruta_local_failure(self):
        with self.assertRaises(FileNotFoundError):
            utils.data_utils.obtener_ruta_local(self.temp_dir, "/nonexistent.txt")

    def test_ejecutar_ogr2ogr_success(self):
        command = ["echo", "hello"]
        with patch("utils.data_utils.subprocess.run") as mock_run:
            utils.data_utils.ejecutar_ogr2ogr(command, "test error context")
            mock_run.assert_called_with(command, capture_output=True, text=True, check=True)

    def test_ejecutar_ogr2ogr_failure(self):
        command = ["bad", "command"]
        with patch("utils.data_utils.subprocess.run", side_effect=subprocess.CalledProcessError(1, command, stderr="failed")):
            with self.assertRaises(Exception) as cm:
                utils.data_utils.ejecutar_ogr2ogr(command, "test failure")
            self.assertIn("failed", str(cm.exception))

    def test__crear_error(self):
        error_dict = utils.data_utils._crear_error("https://dummy", "key1", {"key1": "path"}, "base", "error msg")
        expected = {
            "url": "https://dummy",
            "key": "key1",
            "insumos_local": {"key1": "path"},
            "base_local": "base",
            "error": "error msg"
        }
        self.assertEqual(error_dict, expected)

    def test_copia_insumo_local_success(self):
        dummy_dir = os.path.join(self.temp_dir, "dummy")
        os.makedirs(dummy_dir, exist_ok=True)
        file_path = os.path.join(dummy_dir, "test.zip")
        with open(file_path, "w") as f:
            f.write("content")
        insumos_local = {"test": "/dummy/test.zip"}
        resultado = utils.data_utils.copia_insumo_local("https://dummy", "test", insumos_local, self.temp_dir, "some error")
        self.assertEqual(resultado, file_path)

    def test_copia_insumo_local_failure(self):
        insumos_local = {"test": "/dummy/missing.zip"}
        with self.assertRaises(FileNotFoundError):
            utils.data_utils.copia_insumo_local("https://dummy", "test", insumos_local, self.temp_dir, "some error")

    def test__procesar_zip_excel_detected(self):
        extract_folder = os.path.join(self.temp_dir, "extract")
        os.makedirs(extract_folder, exist_ok=True)
        zip_file = os.path.join(self.temp_dir, "excel.zip")
        with zipfile.ZipFile(zip_file, 'w') as zipf:
            zipf.writestr("[Content_Types].xml", "dummy")
        resultado = utils.data_utils._procesar_zip("excel_key", zip_file, extract_folder)
        self.assertEqual(resultado["type"], "excel")
        self.assertTrue(resultado["file"].endswith(".xlsx"))

    def test__procesar_zip_zip_extraction(self):
        extract_folder = os.path.join(self.temp_dir, "extract2")
        os.makedirs(extract_folder, exist_ok=True)
        zip_file = os.path.join(self.temp_dir, "normal.zip")
        with zipfile.ZipFile(zip_file, 'w') as zipf:
            zipf.writestr("dummy.txt", "content")
        resultado = utils.data_utils._procesar_zip("normal_key", zip_file, extract_folder)
        self.assertEqual(resultado["type"], "zip")
        self.assertEqual(resultado["file"], zip_file)
        self.assertIn("dummy.txt", os.listdir(extract_folder))

    def test__procesar_zip_badzip(self):
        extract_folder = os.path.join(self.temp_dir, "extract3")
        os.makedirs(extract_folder, exist_ok=True)
        bad_zip = os.path.join(self.temp_dir, "bad.zip")
        with open(bad_zip, "w") as f:
            f.write("not a zip")
        resultado = utils.data_utils._procesar_zip("bad_key", bad_zip, extract_folder)
        self.assertEqual(resultado["type"], "geojson")
        self.assertTrue(resultado["file"].endswith(".geojson"))
    
    def test__procesar_zip_unexpected_exception(self):
        zip_file = os.path.join(self.temp_dir, "bad.zip")
        extract_folder = os.path.join(self.temp_dir, "extract_error")
        os.makedirs(extract_folder, exist_ok=True)
        with open(zip_file, "w") as f:
            f.write("not a zip")

        with patch("utils.data_utils.shutil.copy", side_effect=Exception("unexpected error")):
            with self.assertRaises(Exception) as cm:
                utils.data_utils._procesar_zip("key", zip_file, extract_folder)
            self.assertIn("❌ Error tratando", str(cm.exception))

    def test_importar_excel_a_postgres_etl_ap(self):
        cfg_ap = self.cfg.copy()
        cfg_ap["ETL_DIR"] = os.path.join(self.temp_dir, "etl/etl_ap")
        os.makedirs(cfg_ap["ETL_DIR"], exist_ok=True)
        engine = MagicMock()
        with patch("utils.data_utils.import_excel_to_db", return_value="ap result") as mock_import:
            resultado = utils.data_utils._importar_excel_a_postgres(cfg_ap, engine, "dummy.xlsx", "table_ap")
            mock_import.assert_called()
            self.assertEqual(resultado, "ap result")

    def test_importar_excel_a_postgres_etl_rfpn(self):
        cfg_rfpn = self.cfg.copy()
        cfg_rfpn["ETL_DIR"] = os.path.join(self.temp_dir, "etl/etl_rfpn")
        os.makedirs(cfg_rfpn["ETL_DIR"], exist_ok=True)
        engine = MagicMock()
        with patch("utils.data_utils.import_excel_to_db2", return_value="rfpn result") as mock_import:
            resultado = utils.data_utils._importar_excel_a_postgres(cfg_rfpn, engine, "dummy.xlsx", "informacion_area_reserva")
            mock_import.assert_called()
            self.assertEqual(resultado, "rfpn result")

    def test_shorten_identifier(self):
        resultado = utils.data_utils.shorten_identifier("Test-Identifier!")
        self.assertEqual(resultado, "test_identifier_")

    def test_crear_cruce_area_reserva_directo(self):
        with patch("utils.data_utils.ejecutar_sql") as mock_ejecutar_sql:
            utils.data_utils.crear_cruce_area_reserva_directo(self.cfg)
            self.assertTrue(mock_ejecutar_sql.called)
            calls = mock_ejecutar_sql.call_args_list
            self.assertIn("DROP TABLE IF EXISTS insumos.cruce_area_reserva", calls[0][0][1])

    @patch("utils.data_utils.pd.DataFrame.to_sql")
    @patch("utils.data_utils.pd.read_excel")
    def test_import_excel_to_db2_success(self, mock_read_excel, mock_to_sql):
        db_config = {"user": "u", "password": TEST_DB_PASSWORD, "host": "h", "port": "5432", "db_name": "d"}
        dummy_df = pd.DataFrame({
            "Id del área protegida": [1, 2],
            "Objeto del acto": ["Declaratoria", "Other"],
            "Categoría de manejo": ["Reservas Forestales Protectoras Nacionales", "Other"],
            "Tipo de acto administrativo": ["Acuerdos", "Other"],
        })
        mock_read_excel.return_value = dummy_df
        # Con sheet_name se invoca la lectura de Excel y se invoca to_sql que ahora se patchéa.
        utils.data_utils.import_excel_to_db2(db_config, "dummy.xlsx", "table_test", sheet_name="Actos")
        mock_read_excel.assert_called_with("dummy.xlsx", sheet_name="Actos")
        # Verificamos que se llamó al método to_sql (el cual ahora está parcheado)
        self.assertTrue(mock_to_sql.called)


    def test_import_excel_to_db_success(self):
        db_config = {"user": "u", "password": TEST_DB_PASSWORD, "host": "h", "port": "5432", "db_name": "d"}
        df_general = pd.DataFrame({"Id del área protegida": [1, 2], "A": [10, 20]})
        df_actos = pd.DataFrame({
            "Id del área protegida": [1, 2],
            "Objeto del acto": ["Declaratoria", "Other"],
            "Categoría de manejo": ["Reservas Forestales Protectoras Nacionales", "Other"],
            "Tipo de acto administrativo": ["Acuerdos", "Other"],
        })
        with patch("utils.data_utils.pd.read_excel", side_effect=[df_general, df_actos]) as mock_read_excel:
            with patch("utils.data_utils.sqlalchemy.create_engine") as mock_engine:
                engine_instance = MagicMock()
                mock_engine.return_value = engine_instance
                utils.data_utils.import_excel_to_db(db_config, "dummy.xlsx", "table_key")
                self.assertEqual(mock_read_excel.call_count, 2)
    
    def test_import_excel_to_db_error_actos(self):
        db_config = {"user": "u", "password": TEST_DB_PASSWORD, "host": "h", "port": "5432", "db_name": "d"}
        df_general = pd.DataFrame({"Id del área protegida": [1]})

        with patch("utils.data_utils.pd.read_excel", side_effect=[df_general, Exception("fallo actos")]):
            with self.assertRaises(Exception) as cm:
                utils.data_utils.import_excel_to_db(db_config, "dummy.xlsx", "tabla")
            self.assertIn("fallo actos", str(cm.exception).lower())

    def test_import_excel_to_db_error_merge(self):
        db_config = {"user": "u", "password": TEST_DB_PASSWORD, "host": "h", "port": "5432", "db_name": "d"}
        df_general = pd.DataFrame({"Id del área protegida": [1]})
        df_actos = pd.DataFrame({"Id del área protegida": [1], "Objeto del acto": ["Declaratoria"]})

        with patch("utils.data_utils.pd.read_excel", side_effect=[df_general, df_actos]), \
            patch("utils.data_utils.pd.merge", side_effect=Exception("merge error")):
            with self.assertRaises(Exception) as cm:
                utils.data_utils.import_excel_to_db(db_config, "dummy.xlsx", "tabla")
            self.assertIn("merge error", str(cm.exception).lower())

    def test_import_excel_to_db_error_to_sql(self):
        db_config = {"user": "u", "password": TEST_DB_PASSWORD, "host": "h", "port": "5432", "db_name": "d"}
        df_general = pd.DataFrame({"Id del área protegida": [1]})
        df_actos = pd.DataFrame({
            "Id del área protegida": [1],
            "Objeto del acto": ["Declaratoria"]
        })

        with patch("utils.data_utils.pd.read_excel", side_effect=[df_general, df_actos]), \
            patch("utils.data_utils.sqlalchemy.create_engine"), \
            patch("utils.data_utils.pd.DataFrame.to_sql", side_effect=Exception("sql error")):
            with self.assertRaises(Exception) as cm:
                utils.data_utils.import_excel_to_db(db_config, "dummy.xlsx", "tabla")
            self.assertIn("sql error", str(cm.exception).lower())
            
        # ------------------------------------------------------------------
    # ⚡️ PRUEBAS EXTRA para alcanzar el 100 % de coverage en data_utils.py
    # ------------------------------------------------------------------

    def test_buscar_archivos_en_carpeta_ignora_vacios(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            good = os.path.join(tmp_dir, "ok.geojson")
            bad  = os.path.join(tmp_dir, "empty.geojson")
            with open(good, "w") as f:
                f.write("data")
            open(bad, "w").close()                          # tamaño 0
            encontrados = utils.data_utils._buscar_archivos_en_carpeta(
                tmp_dir, [".geojson"]
            )
            self.assertIn(good, encontrados)
            self.assertNotIn(bad, encontrados)

    # ──────────────────────────────────────────────────────────────────
    # import_excel_to_db2  → leer error (líneas 457-460)
    # ──────────────────────────────────────────────────────────────────
    def test_import_excel_to_db2_read_error(self):
        db = {"user":"u","password": TEST_DB_PASSWORD,"host":"h","port":"5432","db_name":"d"}
        with patch("utils.data_utils.pd.read_excel", side_effect=Exception("read-fail")):
            with self.assertRaises(Exception) as cm:
                utils.data_utils.import_excel_to_db2(db, "fail.xlsx", "table_x")
            self.assertIn("read-fail", str(cm.exception).lower())

    # ──────────────────────────────────────────────────────────────────
    # import_excel_to_db2  → rama de filtrado Actos (líneas 463-467)
    # ──────────────────────────────────────────────────────────────────
    @patch("utils.data_utils.pd.read_excel")
    def test_import_excel_to_db2_filtrado_actos(self, mock_read_excel):
        db = {"user": "u", "password": TEST_DB_PASSWORD, "host": "h", "port": "5432", "db_name": "d"}
        df = pd.DataFrame({
            "Id del área protegida": [1, 2, 3, 4],
            "Objeto del acto": ["Declaratoria", "Other", "Declaratoria", "Declaratoria"],
            "Categoría de manejo": [
                "Reservas Forestales Protectoras Nacionales",
                "Other",
                "Reservas Forestales Protectoras Nacionales",
                "Reservas Forestales Protectoras Nacionales"
            ],
            "Tipo de acto administrativo": ["Acuerdos", "Other", "Resolución", "Decreto"]
        })
        mock_read_excel.return_value = df

        def fake_to_sql(*args, **kwargs):
            called_df = args[0]  # el primer argumento es el DataFrame
            actual_ids = called_df["Id del área protegida"].tolist()
            expected_ids = [1, 3]
            assert actual_ids == expected_ids

        with patch("pandas.DataFrame.to_sql", new=fake_to_sql):
            utils.data_utils.import_excel_to_db2(db, "dummy.xlsx", "informacion_area_reserva", sheet_name="Actos")


    # ──────────────────────────────────────────────────────────────────
    # import_excel_to_db2  → fallo en to_sql (líneas 491-494)
    # ──────────────────────────────────────────────────────────────────
    def test_import_excel_to_db2_to_sql_failure(self):
        db = {"user":"u","password": TEST_DB_PASSWORD,"host":"h","port":"5432","db_name":"d"}
        df = pd.DataFrame({"x":[1]})
        with patch("utils.data_utils.pd.read_excel", return_value=df), \
             patch("utils.data_utils.sqlalchemy.create_engine"), \
             patch("utils.data_utils.pd.DataFrame.to_sql", side_effect=Exception("sql-boom")):
            with self.assertRaises(Exception) as cm:
                utils.data_utils.import_excel_to_db2(db, "x.xlsx", "t")
            self.assertIn("sql-boom", str(cm.exception).lower())

    # ──────────────────────────────────────────────────────────────────
    # import_excel_to_db  → choose_row sin coincidencias válidas (513-516)
    # ──────────────────────────────────────────────────────────────────
    @patch("utils.data_utils.sqlalchemy.create_engine")
    @patch("utils.data_utils.pd.read_excel")
    def test_import_excel_to_db_choose_row_default(self, mock_read_excel, mock_engine):
        db = {"user": "u", "password": TEST_DB_PASSWORD, "host": "h", "port": "5432", "db_name": "d"}
        df_general = pd.DataFrame({"Id del área protegida": [1]})
        df_actos = pd.DataFrame({
            "Id del área protegida": [1, 1],
            "Objeto del acto": ["Invalido", "Tampoco"]
        })
        mock_read_excel.side_effect = [df_general, df_actos]
        utils.data_utils.import_excel_to_db(db, "fake.xlsx", "testkey")
        self.assertEqual(mock_read_excel.call_count, 2)

    # ──────────────────────────────────────────────────────────────────
    # _importar_shp_a_postgres → captura de CalledProcessError (275-303)
    # ──────────────────────────────────────────────────────────────────
    @patch("utils.data_utils.subprocess.run", side_effect=subprocess.CalledProcessError(2, "cmd", stderr="boom"))
    def test_importar_shp_a_postgres_subprocess_error(self, mock_run):
        db = {"host":"h","port":"p","db_name":"d","user":"u","password": TEST_DB_PASSWORD}
        with self.assertRaises(Exception) as cm:
            utils.data_utils._importar_shp_a_postgres(db, "dummy.shp", "insumos.tbl")
        self.assertIn("boom", str(cm.exception).lower())

    # ──────────────────────────────────────────────────────────────────
    # _importar_geojson_a_postgres → captura de CalledProcessError (209-210 / 221)
    # ──────────────────────────────────────────────────────────────────
    @patch("utils.data_utils.subprocess.run", side_effect=subprocess.CalledProcessError(2, "cmd", stderr="geo-err"))
    def test_importar_geojson_a_postgres_subprocess_error(self, mock_run):
        db = {"host":"h","port":"p","db_name":"d","user":"u","password": TEST_DB_PASSWORD}
        with self.assertRaises(Exception) as cm:
            utils.data_utils._importar_geojson_a_postgres(db, "d.geojson", "insumos.t")
        self.assertIn("geo-err", str(cm.exception).lower())

    # ──────────────────────────────────────────────────────────────────
    # _procesar_zip → ruta BadZipFile + fallo al copiar (146-148)
    # ──────────────────────────────────────────────────────────────────
    def test_procesar_zip_badzip_copy_fails(self):
        bad = os.path.join(self.temp_dir, "bad.zip")
        open(bad, "w").write("xxx")        # no es zip real
        carpeta = os.path.join(self.temp_dir, "out")
        os.makedirs(carpeta, exist_ok=True)
        with patch("utils.data_utils.shutil.copy", side_effect=Exception("copy-oops")):
            with self.assertRaises(Exception) as cm:
                utils.data_utils._procesar_zip("k", bad, carpeta)
            self.assertIn("copy-oops", str(cm.exception).lower())

if __name__ == "__main__":
    unittest.main()