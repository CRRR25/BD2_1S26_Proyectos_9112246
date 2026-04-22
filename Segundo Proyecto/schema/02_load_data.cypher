// =====================================================================
// Carga masiva de datos con LOAD CSV
// Los CSV se leen desde la carpeta de import de Neo4j (montada en
// /var/lib/neo4j/import segun docker-compose.yml).
// =====================================================================

// ---------- Generos ----------
LOAD CSV WITH HEADERS FROM 'file:///generos.csv' AS row
MERGE (g:Genero {nombre: row.nombre})
SET g.descripcion = row.descripcion;

// ---------- Usuarios ----------
LOAD CSV WITH HEADERS FROM 'file:///usuarios.csv' AS row
MERGE (u:Usuario {id: toInteger(row.id)})
SET u.nombre = row.nombre,
    u.email  = row.email,
    u.edad   = toInteger(row.edad),
    u.pais   = row.pais;

// ---------- Peliculas ----------
LOAD CSV WITH HEADERS FROM 'file:///peliculas.csv' AS row
MERGE (p:Pelicula {id: toInteger(row.id)})
SET p.titulo   = row.titulo,
    p.anio     = toInteger(row.anio),
    p.duracion = toInteger(row.duracion),
    p.sinopsis = row.sinopsis;

// ---------- Actores ----------
LOAD CSV WITH HEADERS FROM 'file:///actores.csv' AS row
MERGE (a:Actor {id: toInteger(row.id)})
SET a.nombre            = row.nombre,
    a.fechaNacimiento   = date(row.fechaNacimiento),
    a.nacionalidad      = row.nacionalidad;

// ---------- Directores ----------
LOAD CSV WITH HEADERS FROM 'file:///directores.csv' AS row
MERGE (d:Director {id: toInteger(row.id)})
SET d.nombre            = row.nombre,
    d.fechaNacimiento   = date(row.fechaNacimiento),
    d.nacionalidad      = row.nacionalidad;

// ---------- Relaciones PERTENECE_A (Pelicula -> Genero) ----------
LOAD CSV WITH HEADERS FROM 'file:///pelicula_genero.csv' AS row
MATCH (p:Pelicula {id: toInteger(row.peliculaId)})
MATCH (g:Genero   {nombre: row.genero})
MERGE (p)-[:PERTENECE_A]->(g);

// ---------- Relaciones DIRIGIO (Director -> Pelicula) ----------
LOAD CSV WITH HEADERS FROM 'file:///director_pelicula.csv' AS row
MATCH (d:Director {id: toInteger(row.directorId)})
MATCH (p:Pelicula {id: toInteger(row.peliculaId)})
MERGE (d)-[:DIRIGIO]->(p);

// ---------- Relaciones ACTUO_EN (Actor -> Pelicula) ----------
// Una pelicula no puede tener al mismo actor con el mismo personaje mas
// de una vez: la unicidad esta dada por (actor, pelicula, personaje)
LOAD CSV WITH HEADERS FROM 'file:///actor_pelicula.csv' AS row
MATCH (a:Actor    {id: toInteger(row.actorId)})
MATCH (p:Pelicula {id: toInteger(row.peliculaId)})
MERGE (a)-[r:ACTUO_EN {personaje: row.personaje}]->(p);

// ---------- Relaciones LE_GUSTA (Usuario -> Genero) ----------
LOAD CSV WITH HEADERS FROM 'file:///usuario_genero.csv' AS row
MATCH (u:Usuario {id: toInteger(row.usuarioId)})
MATCH (g:Genero  {nombre: row.genero})
MERGE (u)-[r:LE_GUSTA]->(g)
SET r.nivelInteres = toInteger(row.nivelInteres);

// ---------- Relaciones VIO (Usuario -> Pelicula) ----------
LOAD CSV WITH HEADERS FROM 'file:///vio.csv' AS row
MATCH (u:Usuario  {id: toInteger(row.usuarioId)})
MATCH (p:Pelicula {id: toInteger(row.peliculaId)})
MERGE (u)-[r:VIO]->(p)
SET r.fechaVisualizacion = date(row.fechaVisualizacion),
    r.completo           = (toLower(row.completo) = 'true');

// ---------- Relaciones CALIFICO (Usuario -> Pelicula) ----------
LOAD CSV WITH HEADERS FROM 'file:///califico.csv' AS row
MATCH (u:Usuario  {id: toInteger(row.usuarioId)})
MATCH (p:Pelicula {id: toInteger(row.peliculaId)})
MERGE (u)-[r:CALIFICO]->(p)
SET r.puntuacion = toInteger(row.puntuacion),
    r.fecha      = date(row.fecha),
    r.comentario = row.comentario;

// ---------- Relaciones ES_AMIGO_DE (Usuario <-> Usuario) ----------
// Bidireccional: se guarda una sola arista; las consultas la tratan
// sin direccion con MATCH (a)-[:ES_AMIGO_DE]-(b)
LOAD CSV WITH HEADERS FROM 'file:///amistades.csv' AS row
MATCH (u1:Usuario {id: toInteger(row.usuario1Id)})
MATCH (u2:Usuario {id: toInteger(row.usuario2Id)})
MERGE (u1)-[r:ES_AMIGO_DE]->(u2)
SET r.fechaAmistad = date(row.fechaAmistad);
