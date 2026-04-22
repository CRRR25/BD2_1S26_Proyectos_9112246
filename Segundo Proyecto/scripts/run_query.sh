#!/usr/bin/env bash
# Ejecuta un archivo .cypher dentro del contenedor de Neo4j.
# Uso: ./scripts/run_query.sh queries/01_calificaciones_usuario_mayor_4.cypher
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Uso: $0 <ruta-al-archivo.cypher>"
  exit 1
fi

cd "$(dirname "$0")/.."

docker exec -i movies_neo4j cypher-shell -u neo4j -p movies12345 < "$1"
