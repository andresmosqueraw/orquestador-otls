#!/usr/bin/env bash
set -euo pipefail

# Activar modo estricto:
# -e: termina el script si un comando falla
# -u: error si se usa una variable no definida
# -o pipefail: falla si algún comando en una tubería falla
echo "🔐 Modo estricto de bash activado: 'set -euo pipefail'"

# Definir rutas destino relativas al submódulo
DEST_DAGS=../../dags
DEST_MODELOS=../../otl/modelos
DEST_ETL=../../otl/etl

echo "📁 Definiendo rutas de destino:"
echo "   - DAGs:        $DEST_DAGS"
echo "   - Modelos:     $DEST_MODELOS"
echo "   - ETL scripts: $DEST_ETL"

# Crear carpetas si no existen
echo "🛠️  Verificando/creando carpetas de destino..."
mkdir -p "$DEST_DAGS" "$DEST_MODELOS" "$DEST_ETL"
echo "✅ Directorios listos"

echo "⚙️  Iniciando configuración del submódulo ETL de RFPP..."

# Copiar carpeta `dag_rfpp` a DAGs
echo "📤 Copiando 'dag_rfpp' a $DEST_DAGS/"
cp -a dag_rfpp "$DEST_DAGS"/
echo "✅ 'dag_rfpp' copiado correctamente"

# Copiar carpeta `modelo_rfpp` a Modelos
echo "📤 Copiando 'modelo_rfpp' a $DEST_MODELOS/"
cp -a modelo_rfpp "$DEST_MODELOS"/
echo "✅ 'modelo_rfpp' copiado correctamente"

# Copiar carpeta `etl_rfpp` a ETL
echo "📤 Copiando 'etl_rfpp' a $DEST_ETL/"
cp -a etl_rfpp "$DEST_ETL"/
echo "✅ 'etl_rfpp' copiado correctamente"

echo "🏁 Submódulo ETL de RFPP configurado correctamente."