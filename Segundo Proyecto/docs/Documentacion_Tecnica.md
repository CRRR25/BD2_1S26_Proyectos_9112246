# Documentacion Tecnica
## Sistema de Recomendacion de Peliculas con Neo4j

Curso: Sistemas de Bases de Datos 2
Proyecto: Segundo Proyecto
Repositorio: `BD2_1S26_Proyectos_9112246`

---

## 1. Modelo Conceptual de Grafos

### 1.1 Tipos de nodos y propiedades

| Etiqueta   | Propiedades                                            |
| ---------- | ------------------------------------------------------ |
| `Usuario`  | `id`, `nombre`, `email`, `edad`, `pais`                |
| `Pelicula` | `id`, `titulo`, `anio`, `duracion`, `sinopsis`         |
| `Genero`   | `nombre` (PK natural), `descripcion`                   |
| `Actor`    | `id`, `nombre`, `fechaNacimiento`, `nacionalidad`      |
| `Director` | `id`, `nombre`, `fechaNacimiento`, `nacionalidad`      |

### 1.2 Tipos de relaciones y propiedades

| Relacion        | Origen   -> Destino   | Propiedades                                              |
| --------------- | --------------------- | -------------------------------------------------------- |
| `CALIFICO`      | Usuario  -> Pelicula  | `puntuacion` (1-5), `fecha`, `comentario`                |
| `VIO`           | Usuario  -> Pelicula  | `fechaVisualizacion`, `completo` (bool)                  |
| `ES_AMIGO_DE`   | Usuario  -> Usuario   | `fechaAmistad` (se trata como bidireccional al consultar)|
| `PERTENECE_A`   | Pelicula -> Genero    | (sin propiedades)                                        |
| `ACTUO_EN`      | Actor    -> Pelicula  | `personaje`                                              |
| `DIRIGIO`       | Director -> Pelicula  | (sin propiedades)                                        |
| `LE_GUSTA`      | Usuario  -> Genero    | `nivelInteres` (1-5)                                     |

### 1.3 Diagrama del modelo

```
                       +-----------+
                       |  Genero   |
                       +-----+-----+
                             ^
              PERTENECE_A    |    LE_GUSTA (nivelInteres)
             +---------------+--------------------+
             |                                    |
             |                                    |
+----------+ |    CALIFICO (puntuacion,fecha)   +-+--------+
| Pelicula |<+-------------------------------- |  Usuario |
|----------|                                   |----------|
| id       |    VIO (fechaVisualizacion,       | id       |
| titulo   |<--------- completo) -------------- nombre   |
| anio     |                                   | email    |
| duracion |                                   | edad     |
| sinopsis |                                   | pais     |
+----------+                                   +----+-----+
   ^   ^                                            ^
   |   |                                            | ES_AMIGO_DE
   |   |  ACTUO_EN (personaje)                      | (fechaAmistad)
   |   +------------------- Actor ------------------+
   |                                                |
   | DIRIGIO                                        |
   +-------------------- Director ------------------+
```

### 1.4 Reglas de negocio modeladas

1. Una calificacion siempre cumple `1 <= puntuacion <= 5` (validado en la
   generacion de datos).
2. La amistad se almacena con una sola arista `(:Usuario)-[:ES_AMIGO_DE]->(:Usuario)`
   y todas las consultas la recorren con `MATCH (a)-[:ES_AMIGO_DE]-(b)` para
   ignorar la direccion.
3. La unicidad de un actor en un personaje dentro de una pelicula esta dada
   por la firma `(actor, pelicula, personaje)`, garantizada con
   `MERGE (a)-[:ACTUO_EN {personaje: row.personaje}]->(p)`.
4. Una pelicula puede pertenecer a varios generos y tener varios actores,
   pero un solo director.
5. Un usuario puede calificar / ver multiples peliculas (con `MERGE`
   evitamos duplicados sobre la misma pareja usuario-pelicula).

---

## 2. Esquema fisico (constraints e indices)

Archivo: `schema/01_schema.cypher`

- Constraints `UNIQUE` en `Usuario.id`, `Pelicula.id`, `Genero.nombre`,
  `Actor.id`, `Director.id`.
- Indices auxiliares en `Usuario.email`, `Pelicula.titulo`, `Pelicula.anio`
  para mejorar las consultas de filtrado.

---

## 3. Carga masiva con LOAD CSV

Archivo: `schema/02_load_data.cypher`.

Los CSV viven en `Segundo Proyecto/data/` y se montan dentro del
contenedor Neo4j en `/var/lib/neo4j/import`, por lo que se acceden con
URI `file:///<archivo>.csv`.

Volumen de datos generados:

| Archivo                  | Filas aprox. |
| ------------------------ | ------------ |
| `usuarios.csv`           | 500          |
| `peliculas.csv`          | 200          |
| `actores.csv`            | 100          |
| `directores.csv`         | 50           |
| `generos.csv`            | 15           |
| `pelicula_genero.csv`    | ~400         |
| `director_pelicula.csv`  | 200          |
| `actor_pelicula.csv`     | ~1100        |
| `usuario_genero.csv`     | ~1750        |
| `amistades.csv`          | ~1500        |
| `vio.csv`                | ~7500        |
| `califico.csv`           | ~4500        |

Cada `LOAD CSV` usa `MERGE` para que la carga sea idempotente.

---

## 4. Consultas Cypher implementadas

Las consultas estan en `Segundo Proyecto/queries/`.

| #  | Archivo                                          | Proposito                                                            |
| -- | ------------------------------------------------ | -------------------------------------------------------------------- |
| 1  | `01_calificaciones_usuario_mayor_4.cypher`       | Peliculas de un usuario con puntuacion > 4                           |
| 2  | `02_peliculas_amigos_no_vistas.cypher`           | Peliculas vistas por amigos pero no por el usuario                   |
| 3  | `03_promedio_calificaciones_pelicula.cypher`     | Promedio de calificaciones de una pelicula                           |
| 4  | `04_generos_favoritos_usuario.cypher`            | Generos favoritos segun calificaciones del usuario                   |
| 5  | `05_ruta_amistad_mas_corta.cypher`               | Ruta mas corta entre dos usuarios (`shortestPath`)                   |
| 6  | `06_peliculas_populares_por_genero.cypher`       | Peliculas mas populares (visualizaciones) por genero                 |
| 7  | `07_actores_por_director.cypher`                 | Actores que han trabajado con un director                            |
| 8  | `08_recomendaciones_basadas_en_amigos.cypher`    | Recomendaciones combinando calificaciones de amigos + gustos         |
| 9  | `09_analisis_grados_separacion.cypher`           | Distribucion de grados de separacion en la red                       |
| 10 | `10_peliculas_altamente_conectadas.cypher`       | Peliculas con mas actores/directores reconocidos                     |

Las consultas 1-8 cubren los puntos solicitados tanto en la seccion
"Alcance" como en la "Rubrica" del enunciado.  Las consultas 9 y 10
corresponden a los dos analisis de redes obligatorios.

### 4.1 Documentacion por consulta

#### Consulta 1 - Calificaciones > 4 de un usuario

Recorrido: `(:Usuario)-[:CALIFICO]->(:Pelicula)`. Filtra por
`c.puntuacion > 4` y proyecta titulo, año y puntuacion.

#### Consulta 2 - Peliculas vistas por amigos

Patron: `(u)-[:ES_AMIGO_DE]-(amigo)-[:VIO]->(p)` con `NOT (u)-[:VIO]->(p)`.
Agrupa por pelicula y cuenta amigos distintos.

#### Consulta 3 - Promedio de calificaciones

Agregacion `avg(c.puntuacion)` con `count(c)`, `min`, `max` para
contextualizar la calificacion.

#### Consulta 4 - Generos favoritos por calificaciones

Atraviesa 3 niveles: `Usuario -[CALIFICO]-> Pelicula -[PERTENECE_A]-> Genero`
y promedia por genero.

#### Consulta 5 - Ruta de amistad mas corta

Usa `shortestPath((a)-[:ES_AMIGO_DE*..6]-(b))` y muestra la cadena de
nombres recorrida.

#### Consulta 6 - Peliculas populares por genero

Combina `:PERTENECE_A` con `count` de relaciones `:VIO`.

#### Consulta 7 - Actores por director

Patron `(:Director)-[:DIRIGIO]->(:Pelicula)<-[:ACTUO_EN]-(:Actor)`.

#### Consulta 8 - Recomendaciones basadas en amigos

Combina amigos que dieron puntaje >= 4 con un `OPTIONAL MATCH` a los
generos preferidos del usuario para componer un score.

#### Consulta 9 - Grados de separacion

Calcula `shortestPath` desde un usuario semilla hacia todos los demas
usuarios y agrupa por longitud de ruta.

#### Consulta 10 - Peliculas altamente conectadas

Identifica actores y directores con mas de 3 trabajos y suma cuantos de
ellos aparecen en cada pelicula.

---

## 5. Ventajas de Neo4j en este problema

1. **Modelado natural**: las "amistades", "actuaciones", "calificaciones"
   son aristas del mundo real.  No requieren tablas puente con joins.
2. **Consultas multi-salto baratas**: encontrar peliculas que vieron los
   amigos de mis amigos es un patron de 3 saltos directo en Cypher; en
   SQL serian 3 self-joins encadenados.
3. **Algoritmos de grafos integrados**: `shortestPath`, `allShortestPaths`,
   y los plugins APOC/GDS permiten centralidades y deteccion de
   comunidades sin mover los datos a otro motor.
4. **Esquema flexible**: agregar una nueva relacion (p.ej. `SIGUE_A` para
   recomendaciones tipo Twitter) no requiere migraciones de tablas.
5. **Propiedades en aristas**: la puntuacion de una calificacion vive en
   la propia relacion `CALIFICO`, lo que evita una tabla auxiliar.

---

## 6. Estructura del repositorio

```
Segundo Proyecto/
|-- docker-compose.yml
|-- README.md
|-- data-generator/        # Imagen Python que genera CSVs y carga Neo4j
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- main.py
|   |-- generator.py
|   `-- loader.py
|-- schema/
|   |-- 01_schema.cypher
|   `-- 02_load_data.cypher
|-- queries/               # Consultas y analisis de redes
|   `-- ... (10 archivos .cypher)
|-- data/                  # CSVs generados (volumen de Neo4j para LOAD CSV)
|-- scripts/               # Helpers shell
|   |-- run.sh
|   |-- reset.sh
|   `-- run_query.sh
`-- docs/
    |-- Documentacion_Tecnica.md
    `-- Manual_Usuario.md
```
