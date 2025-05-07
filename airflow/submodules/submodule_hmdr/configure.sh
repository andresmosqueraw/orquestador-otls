#!/usr/bin/env bash
set -euo pipefail

# Activación del modo estricto de bash:
# -e: finaliza el script si un comando falla
# -u: lanza error si se intenta usar una variable no definida
# -o pipefail: si algún comando en una tubería falla, todo el pipeline falla
echo "🔐 Modo estricto de bash activado: 'set -euo pipefail'"

# Definición de rutas destino relativas (desde dentro del submódulo)
DEST_DAGS=../../dags
DEST_MODELOS=../../otl/modelos
DEST_ETL=../../otl/etl

echo "📁 Definiendo rutas de destino:"
echo "   - DAGs:        $DEST_DAGS"
echo "   - Modelos:     $DEST_MODELOS"
echo "   - ETL scripts: $DEST_ETL"

# Crear directorios destino si aún no existen
echo "🛠️  Verificando o creando carpetas necesarias..."
mkdir -p "$DEST_DAGS" "$DEST_MODELOS" "$DEST_ETL"
echo "✅ Carpetas listas"

echo "⚙️  Iniciando configuración del submódulo ETL de HMDR..."

# Copiar carpeta `dag_hmdr` al directorio de DAGs
echo "📤 Copiando 'dag_hmdr' a $DEST_DAGS/"
cp -a dag_hmdr "$DEST_DAGS"/
echo "✅ 'dag_hmdr' copiado correctamente"

# Copiar carpeta `modelo_hmdr` al directorio de modelos
echo "📤 Copiando 'modelo_hmdr' a $DEST_MODELOS/"
cp -a modelo_hmdr "$DEST_MODELOS"/
echo "✅ 'modelo_hmdr' copiado correctamente"

# Copiar carpeta `etl_hmdr` al directorio de scripts ETL
echo "📤 Copiando 'etl_hmdr' a $DEST_ETL/"
cp -a etl_hmdr "$DEST_ETL"/
echo "✅ 'etl_hmdr' copiado correctamente"

echo "🏁 Submódulo ETL de HMDR configurado exitosamente."