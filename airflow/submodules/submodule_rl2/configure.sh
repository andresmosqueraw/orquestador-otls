#!/usr/bin/env bash
set -euo pipefail

# Activar modo estricto:
# -e: finaliza el script al primer error
# -u: error si se usa una variable no definida
# -o pipefail: detecta errores en cualquier parte de una tubería
echo "🔐 Modo estricto de bash activado: 'set -euo pipefail'"

# Definición de rutas destino relativas (ubicación esperada: airflow/submodules/submodule_rl2/)
DEST_DAGS=../../dags
DEST_MODELOS=../../otl/modelos
DEST_ETL=../../otl/etl

echo "📁 Definiendo rutas de destino:"
echo "   - DAGs:        $DEST_DAGS"
echo "   - Modelos:     $DEST_MODELOS"
echo "   - ETL scripts: $DEST_ETL"

# Crear las carpetas destino si no existen
echo "🛠️  Verificando o creando carpetas necesarias..."
mkdir -p "$DEST_DAGS" "$DEST_MODELOS" "$DEST_ETL"
echo "✅ Carpetas listas para recibir contenido"

echo "⚙️  Iniciando configuración del submódulo ETL de RL2..."

# Copiar carpeta dag_rl2 al destino de DAGs
echo "📤 Copiando 'dag_rl2' a $DEST_DAGS/"
cp -a dag_rl2 "$DEST_DAGS"/
echo "✅ 'dag_rl2' copiado correctamente"

# Copiar carpeta modelo_rl2 al destino de Modelos
echo "📤 Copiando 'modelo_rl2' a $DEST_MODELOS/"
cp -a modelo_rl2 "$DEST_MODELOS"/
echo "✅ 'modelo_rl2' copiado correctamente"

# Copiar carpeta etl_rl2 al destino de scripts ETL
echo "📤 Copiando 'etl_rl2' a $DEST_ETL/"
cp -a etl_rl2 "$DEST_ETL"/
echo "✅ 'etl_rl2' copiado correctamente"

echo "🏁 Submódulo ETL de RL2 configurado correctamente."