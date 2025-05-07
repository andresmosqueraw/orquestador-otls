#!/usr/bin/env bash
set -euo pipefail

# Activación de modo estricto:
# -e  → termina el script si ocurre un error
# -u  → falla si se usa una variable no definida
# -o pipefail → detecta fallos en cualquier parte de una tubería
echo "🔐 Activado modo estricto: 'set -euo pipefail'"

# Definición de rutas destino relativas desde el submódulo
DEST_DAGS=../../dags
DEST_MODELOS=../../otl/modelos
DEST_ETL=../../otl/etl

echo "📁 Rutas de destino definidas:"
echo "   - DAGs:        $DEST_DAGS"
echo "   - Modelos:     $DEST_MODELOS"
echo "   - ETL scripts: $DEST_ETL"

# Crear directorios de destino si no existen
echo "🛠️  Verificando/creando carpetas de destino..."
mkdir -p "$DEST_DAGS" "$DEST_MODELOS" "$DEST_ETL"
echo "✅ Directorios listos"

echo "⚙️  Iniciando configuración del submódulo ETL de PMC..."

# Copiar carpeta `dag_pmc` a la ruta de DAGs
echo "📤 Copiando carpeta 'dag_pmc' a $DEST_DAGS/"
cp -a dag_pmc "$DEST_DAGS"/
echo "✅ 'dag_pmc' copiado exitosamente"

# Copiar carpeta `modelo_pmc` a la ruta de modelos
echo "📤 Copiando carpeta 'modelo_pmc' a $DEST_MODELOS/"
cp -a modelo_pmc "$DEST_MODELOS"/
echo "✅ 'modelo_pmc' copiado exitosamente"

# Copiar carpeta `etl_pmc` a la ruta de ETL
echo "📤 Copiando carpeta 'etl_pmc' a $DEST_ETL/"
cp -a etl_pmc "$DEST_ETL"/
echo "✅ 'etl_pmc' copiado exitosamente"

echo "🏁 Submódulo ETL de PMC configurado correctamente."