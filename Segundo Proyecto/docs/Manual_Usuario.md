# Manual de Usuario
## Sistema de Recomendacion de Peliculas con Neo4j

---

## 1. Requisitos previos

Solo se necesita Docker.  Todo lo demas (Neo4j, Python, Faker,
neo4j-driver, APOC) se levanta automaticamente desde imagenes oficiales.

- Docker Engine 24+ con Docker Compose v2 (`docker compose ...`).
- Puertos libres: `7474` (HTTP de Neo4j Browser) y `7687` (Bolt).

> No se requiere instalar Neo4j Desktop, Python ni librerias en la
> maquina anfitriona.

---

## 2. Como levantar el proyecto

Desde la carpeta `Segundo Proyecto/` ejecuta:

```bash
docker compose up -d neo4j
```

Esto descarga la imagen `neo4j:5.20-community`, instala el plugin APOC y
expone el Browser en http://localhost:7474.

> Credenciales por defecto: usuario `neo4j`, contrasena `movies12345`
> (definidas en `docker-compose.yml`).

Una vez que Neo4j este listo (el healthcheck tarda ~15 s), genera los
CSV, aplica el esquema y carga los datos:

```bash
docker compose run --rm data-generator python main.py --all
```

Esto:

1. Genera todos los CSV bajo `data/` (~500 usuarios, 200 peliculas, etc.).
2. Aplica `schema/01_schema.cypher` (constraints e indices).
3. Ejecuta `schema/02_load_data.cypher` con todos los `LOAD CSV`.
4. Imprime el conteo final de nodos y relaciones.

Salida esperada (los conteos varian un poco por aleatoriedad):

```
Conteos en la base de datos:
  Usuarios             500
  Peliculas            200
  Generos              15
  Actores              100
  Directores           50
  Rel CALIFICO         ~4500
  Rel VIO              ~7500
  Rel ES_AMIGO_DE      1500
  Rel PERTENECE_A      ~400
  Rel ACTUO_EN         ~1100
  Rel DIRIGIO          200
  Rel LE_GUSTA         ~1750
```

---

## 3. Como verificar que todo funciona

### Opcion A - Neo4j Browser (recomendado)

1. Abre http://localhost:7474 en tu navegador.
2. Conecta con:
   - Connect URL: `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: `movies12345`
3. Ejecuta:

   ```cypher
   MATCH (n) RETURN labels(n)[0] AS tipo, count(*) AS cantidad
   ORDER BY cantidad DESC;
   ```

   Debes ver al menos los conteos minimos del enunciado.

4. Para visualizar una porcion del grafo:

   ```cypher
   MATCH (u:Usuario {id:1})-[r]-(x)
   RETURN u, r, x
   LIMIT 50;
   ```

### Opcion B - Linea de comandos (cypher-shell del contenedor)

```bash
docker exec -it movies_neo4j cypher-shell -u neo4j -p movies12345 \
  "MATCH (u:Usuario) RETURN count(u) AS usuarios;"
```

### Opcion C - Helper incluido

```bash
./scripts/run_query.sh queries/01_calificaciones_usuario_mayor_4.cypher
```

---

## 4. Como ejecutar cada consulta

Todas las consultas estan en `queries/` con un id que las identifica.
Para ejecutarlas:

```bash
# Desde la carpeta del proyecto
docker exec -i movies_neo4j cypher-shell -u neo4j -p movies12345 \
  < queries/01_calificaciones_usuario_mayor_4.cypher
```

O bien copiando el contenido del archivo en Neo4j Browser.

### 4.1 Ejemplos practicos

**Consulta 1 - Calificaciones > 4 de un usuario**
```cypher
MATCH (u:Usuario {id: 1})-[c:CALIFICO]->(p:Pelicula)
WHERE c.puntuacion > 4
RETURN u.nombre, p.titulo, c.puntuacion, c.fecha
ORDER BY c.puntuacion DESC, p.titulo;
```
Resultado: lista de peliculas con puntuacion 5 (la unica > 4 en la
escala 1-5).  Cambia el `id` del usuario para probar con otros.

**Consulta 2 - Peliculas que vieron mis amigos y yo no**
```cypher
MATCH (u:Usuario {id: 1})-[:ES_AMIGO_DE]-(amigo)-[:VIO]->(p:Pelicula)
WHERE NOT (u)-[:VIO]->(p)
RETURN p.titulo, count(DISTINCT amigo) AS recomendadores
ORDER BY recomendadores DESC LIMIT 25;
```
Interpretacion: las primeras filas son las peliculas con mas amigos que
ya las vieron, candidatas naturales para recomendar.

**Consulta 5 - Ruta mas corta entre dos usuarios**
```cypher
MATCH (a:Usuario {id:1}), (b:Usuario {id:250}),
      ruta = shortestPath((a)-[:ES_AMIGO_DE*..6]-(b))
RETURN length(ruta) AS grados,
       [n IN nodes(ruta) | n.nombre] AS cadena;
```
Devuelve `null` si los dos usuarios no estan conectados (puede pasar con
ids que cayeron en una "isla" del grafo - probar con otros ids).

**Consulta 8 - Recomendaciones basadas en amigos**
```cypher
MATCH (u:Usuario {id:1})-[:ES_AMIGO_DE]-(a)-[c:CALIFICO]->(p:Pelicula)
WHERE c.puntuacion >= 4 AND NOT (u)-[:VIO]->(p)
OPTIONAL MATCH (p)-[:PERTENECE_A]->(g)<-[gusto:LE_GUSTA]-(u)
RETURN p.titulo,
       count(DISTINCT a) AS amigos,
       round(avg(c.puntuacion),2) AS prom,
       coalesce(sum(gusto.nivelInteres),0) AS afinidad
ORDER BY prom * amigos + coalesce(sum(gusto.nivelInteres),0) DESC
LIMIT 10;
```

---

## 5. Resolucion de problemas

| Sintoma | Causa probable | Solucion |
|---------|----------------|----------|
| `docker compose up` falla con "port is already in use" | Otro proceso usa 7474/7687 | Detener Neo4j Desktop / cambiar `ports` en `docker-compose.yml` |
| `Connection refused` desde Browser | Neo4j aun no termina de arrancar | Esperar 15-30 s, revisar `docker logs movies_neo4j` |
| `Neo.ClientError.Schema.ConstraintValidationFailed` al cargar | Datos duplicados | `docker compose run --rm data-generator python main.py --reset --all` |
| `Couldn't load the external resource at: file:///...` | El CSV no esta en la carpeta `data/` | Volver a ejecutar `--generate` |
| La consulta 5 devuelve `null` | Los dos usuarios estan en componentes distintos | Probar con otro par de ids |

### Vaciar y recargar todo

```bash
docker compose run --rm data-generator python main.py --reset --all
```

### Detener todo

```bash
docker compose down            # detiene contenedores, conserva el volumen
docker compose down -v         # ademas borra el volumen de Neo4j
```

---

## 6. Acceso a archivos generados

Los CSV producidos por el generador quedan en
`Segundo Proyecto/data/` en el host (gracias al bind mount), por lo que
se pueden abrir con cualquier editor o subir al repositorio si se
desea.
