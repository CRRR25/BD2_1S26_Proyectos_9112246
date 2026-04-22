// =====================================================================
// Consulta 1
// Todas las peliculas calificadas por un usuario especifico con
// puntuacion mayor a 4 (es decir 5 estrellas, ya que la escala es 1-5).
// Cambiar el id del usuario segun se requiera.
// =====================================================================
MATCH (u:Usuario {id: 1})-[c:CALIFICO]->(p:Pelicula)
WHERE c.puntuacion > 4
RETURN u.nombre   AS usuario,
       p.titulo   AS pelicula,
       p.anio     AS anio,
       c.puntuacion AS puntuacion,
       c.fecha    AS fecha
ORDER BY c.puntuacion DESC, p.titulo;
