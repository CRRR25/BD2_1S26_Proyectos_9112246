// =====================================================================
// Consulta 3
// Promedio de calificaciones de una pelicula especifica, junto con la
// cantidad de calificaciones recibidas.
// Cambiar el id de la pelicula segun se requiera.
// =====================================================================
MATCH (p:Pelicula {id: 1})<-[c:CALIFICO]-(:Usuario)
RETURN p.titulo               AS pelicula,
       round(avg(c.puntuacion), 2) AS promedio,
       count(c)               AS totalCalificaciones,
       min(c.puntuacion)      AS minimo,
       max(c.puntuacion)      AS maximo;
