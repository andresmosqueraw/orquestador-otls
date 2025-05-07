#!/usr/bin/env bash
set -euo pipefail

# Activación del modo estricto:
# -e: termina el script al primer error
# -u: falla si se usa una variable no definida
# -o pipefail: detecta errores en cualquier comando de una tubería
echo "🔐 Modo estricto activado: 'set -euo pipefail'"

# Rutas destino relativas (basadas en la ubicación del script dentro de airflow/submodules/submodule_xx)
DEST_DAGS=../../dags
DEST_MODELOS=../../otl/modelos
DEST_ETL=../../otl/etl

echo "📁 Definiendo rutas de destino:"
echo "   - DAGs:        $DEST_DAGS"
echo "   - Modelos:     $DEST_MODELOS"
echo "   - ETL scripts: $DEST_ETL"

# Crear carpetas si no existen
echo "🛠️  Verificando o creando carpetas destino..."
mkdir -p "$DEST_DAGS" "$DEST_MODELOS" "$DEST_ETL"
echo "✅ Carpetas listas"

echo "⚙️  Iniciando configuración del submódulo ETL de RFPn..."

# Copiar carpeta dag_rfpn al directorio de DAGs
echo "📤 Copiando 'dag_rfpn' a $DEST_DAGS/"
cp -a dag_rfpn "$DEST_DAGS"/
echo "✅ 'dag_rfpn' copiado correctamente"

# Copiar carpeta modelo_rfpn al directorio de modelos
echo "📤 Copiando 'modelo_rfpn' a $DEST_MODELOS/"
cp -a modelo_rfpn "$DEST_MODELOS"/
echo "✅ 'modelo_rfpn' copiado correctamente"

# Copiar carpeta etl_rfpn al directorio ETL
echo "📤 Copiando 'etl_rfpn' a $DEST_ETL/"
cp -a etl_rfpn "$DEST_ETL"/
echo "✅ 'etl_rfpn' copiado correctamente"

echo "🏁 Submódulo ETL de RFPn configurado correctamente."