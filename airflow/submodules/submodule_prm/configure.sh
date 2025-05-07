#!/usr/bin/env bash
set -euo pipefail

# Activar modo estricto:
# -e: aborta si un comando falla
# -u: error si se usa una variable no definida
# -o pipefail: falla si algún comando dentro de una tubería falla
echo "🔐 Modo estricto de bash activado: 'set -euo pipefail'"

# Definición de rutas destino relativas al submódulo
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
echo "✅ Carpetas creadas o ya existentes"

echo "⚙️  Iniciando configuración del submódulo ETL de PRM..."

# Copiar carpeta `dag_prm`
echo "📤 Copiando 'dag_prm' a $DEST_DAGS/"
cp -a dag_prm "$DEST_DAGS"/
echo "✅ 'dag_prm' copiado correctamente"

# Copiar carpeta `modelo_prm`
echo "📤 Copiando 'modelo_prm' a $DEST_MODELOS/"
cp -a modelo_prm "$DEST_MODELOS"/
echo "✅ 'modelo_prm' copiado correctamente"

# Copiar carpeta `etl_prm`
echo "📤 Copiando 'etl_prm' a $DEST_ETL/"
cp -a etl_prm "$DEST_ETL"/
echo "✅ 'etl_prm' copiado correctamente"

echo "🏁 Submódulo ETL de PRM configurado correctamente."