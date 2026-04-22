// =====================================================================
// Consulta 7 (cubierta en la rubrica de evaluacion)
// Actores que han trabajado con un director especifico, junto con la
// cantidad de peliculas en las que coincidieron.
// =====================================================================
MATCH (d:Director {id: 1})-[:DIRIGIO]->(p:Pelicula)<-[:ACTUO_EN]-(a:Actor)
RETURN d.nombre                AS director,
       a.nombre                AS actor,
       count(DISTINCT p)       AS peliculasJuntos,
       collect(DISTINCT p.titulo) AS peliculas
ORDER BY peliculasJuntos DESC, actor;
