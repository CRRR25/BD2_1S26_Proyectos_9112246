#!/usr/bin/env bash
# Levanta Neo4j (en segundo plano) y luego genera + carga los datos.
set -euo pipefail

cd "$(dirname "$0")/.."

echo ">>> Levantando Neo4j..."
docker compose up -d neo4j

echo ">>> Esperando a que Neo4j este saludable..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' movies_neo4j 2>/dev/null || echo starting)" = "healthy" ]; do
  sleep 2
done

echo ">>> Generando CSVs, aplicando esquema y cargando datos..."
docker compose run --rm data-generator python main.py --all

echo ">>> Listo. Neo4j Browser: http://localhost:7474 (usuario neo4j / pass movies12345)"
