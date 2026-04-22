# Segundo Proyecto - Sistema de Recomendacion de Peliculas con Neo4j

Curso: Sistemas de Bases de Datos 2
Repositorio: `BD2_1S26_Proyectos_9112246`

Todo el proyecto se ejecuta sobre Docker. **No es necesario instalar
Neo4j ni Python en la maquina anfitriona**: el `docker-compose.yml`
levanta:

- `movies_neo4j` -> Neo4j 5.x Community con plugin APOC.
- `movies_data_generator` -> contenedor Python que genera los CSV con
  Faker, aplica el esquema y dispara los `LOAD CSV` contra Neo4j via
  el driver oficial.

---

## Como ejecutarlo

Desde esta carpeta (`Segundo Proyecto/`):

```bash
# 1. Levantar Neo4j en segundo plano
docker compose up -d neo4j

# 2. Generar CSVs + aplicar esquema + cargar datos + ver conteos
docker compose run --rm data-generator python main.py --all
```

O todo en uno con el helper:

```bash
./scripts/run.sh
```

Cuando termine, abre **Neo4j Browser** en http://localhost:7474 y
conecta con:

- URL: `bolt://localhost:7687`
- Usuario: `neo4j`
- Password: `movies12345`

---

## Como probar que esta bien

1. **Conteos minimos** (en el Browser o con `cypher-shell`):

   ```cypher
   MATCH (n) RETURN labels(n)[0] AS tipo, count(*) AS cantidad
   ORDER BY cantidad DESC;
   ```

   Debes ver al menos:
   - 500 Usuario, 200 Pelicula, 100 Actor, 50 Director, 15 Genero
   - relaciones CALIFICO, VIO, ES_AMIGO_DE, PERTENECE_A, ACTUO_EN, DIRIGIO, LE_GUSTA

2. **Consultas obligatorias**: ejecutar cada archivo de
   `queries/01_*.cypher` ... `queries/08_*.cypher` y revisar que
   devuelvan filas (los ids estan listos para usar).

3. **Analisis de redes**: ejecutar `queries/09_*.cypher` y
   `queries/10_*.cypher`.

4. **Ejecucion rapida desde shell**:

   ```bash
   ./scripts/run_query.sh queries/01_calificaciones_usuario_mayor_4.cypher
   ./scripts/run_query.sh queries/05_ruta_amistad_mas_corta.cypher
   ./scripts/run_query.sh queries/10_peliculas_altamente_conectadas.cypher
   ```

---

## Estructura

```
Segundo Proyecto/
|-- docker-compose.yml         # Neo4j + Python data-generator
|-- README.md                  # este archivo
|-- data-generator/            # imagen Python
|   |-- Dockerfile
|   |-- requirements.txt       # faker, neo4j
|   |-- main.py                # CLI: --all, --generate, --schema, --load, --reset, --stats
|   |-- generator.py           # crea los CSV con Faker
|   `-- loader.py              # ejecuta los .cypher contra Neo4j
|-- schema/
|   |-- 01_schema.cypher       # constraints e indices
|   `-- 02_load_data.cypher    # LOAD CSV de nodos y relaciones
|-- queries/
|   |-- 01_calificaciones_usuario_mayor_4.cypher
|   |-- 02_peliculas_amigos_no_vistas.cypher
|   |-- 03_promedio_calificaciones_pelicula.cypher
|   |-- 04_generos_favoritos_usuario.cypher
|   |-- 05_ruta_amistad_mas_corta.cypher
|   |-- 06_peliculas_populares_por_genero.cypher
|   |-- 07_actores_por_director.cypher
|   |-- 08_recomendaciones_basadas_en_amigos.cypher
|   |-- 09_analisis_grados_separacion.cypher
|   `-- 10_peliculas_altamente_conectadas.cypher
|-- data/                      # CSVs generados (montados en Neo4j /import)
|-- scripts/
|   |-- run.sh                 # arranque completo
|   |-- reset.sh               # borra y recarga
|   `-- run_query.sh           # ejecuta un .cypher
`-- docs/
    |-- Documentacion_Tecnica.md
    `-- Manual_Usuario.md
```

---

## CLI del data-generator

```bash
docker compose run --rm data-generator python main.py [opcion]
```

| Opcion        | Que hace                                                   |
| ------------- | ---------------------------------------------------------- |
| `--all`       | genera CSV + aplica esquema + carga + muestra conteos      |
| `--generate`  | solo regenera los CSV                                      |
| `--schema`    | solo aplica `01_schema.cypher` (constraints/indexes)       |
| `--load`      | solo ejecuta `02_load_data.cypher` (`LOAD CSV`)            |
| `--reset`     | vacia toda la base de datos                                |
| `--stats`     | imprime conteos por etiqueta y relacion                    |

Estas se pueden combinar: `--reset --all` para borrar y recargar desde
cero.

---

## Limpieza

```bash
docker compose down            # detiene contenedores
docker compose down -v         # tambien borra el volumen de Neo4j
```

---

## Documentacion completa

- `docs/Documentacion_Tecnica.md` -> modelo, propiedades, esquema,
  consultas y ventajas de Neo4j.
- `docs/Manual_Usuario.md` -> instalacion paso a paso, ejecucion de
  consultas con ejemplos y resolucion de problemas.
