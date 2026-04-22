#!/usr/bin/env bash
# Vacia la base de datos y recarga todo desde cero.
set -euo pipefail

cd "$(dirname "$0")/.."
docker compose run --rm data-generator python main.py --reset --all
