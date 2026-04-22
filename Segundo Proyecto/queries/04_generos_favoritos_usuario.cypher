// =====================================================================
// Consulta 4
// Generos favoritos de un usuario basandose en sus calificaciones.
// Se calcula el promedio de las puntuaciones que ha dado a las
// peliculas de cada genero y la cantidad de peliculas calificadas.
// =====================================================================
MATCH (u:Usuario {id: 1})-[c:CALIFICO]->(p:Pelicula)-[:PERTENECE_A]->(g:Genero)
RETURN g.nombre                       AS genero,
       round(avg(c.puntuacion), 2)    AS promedio,
       count(DISTINCT p)              AS peliculasCalificadas
ORDER BY promedio DESC, peliculasCalificadas DESC
LIMIT 5;
