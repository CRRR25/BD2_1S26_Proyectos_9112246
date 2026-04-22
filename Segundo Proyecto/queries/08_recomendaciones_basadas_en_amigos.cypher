// =====================================================================
// Consulta 8 (cubierta en la rubrica de evaluacion)
// Recomendaciones de peliculas para un usuario, basadas en las
// calificaciones altas (>= 4) que dieron sus amigos a peliculas que el
// usuario aun no ha visto.  Se priorizan ademas las peliculas cuyos
// generos coinciden con los gustos del usuario.
// =====================================================================
MATCH (u:Usuario {id: 1})-[:ES_AMIGO_DE]-(amigo:Usuario)-[c:CALIFICO]->(p:Pelicula)
WHERE c.puntuacion >= 4
  AND NOT (u)-[:VIO]->(p)
OPTIONAL MATCH (p)-[:PERTENECE_A]->(g:Genero)<-[gusto:LE_GUSTA]-(u)
WITH p,
     count(DISTINCT amigo)            AS amigosQueRecomiendan,
     avg(c.puntuacion)                AS promedioAmigos,
     coalesce(sum(gusto.nivelInteres), 0) AS afinidadGenero
RETURN p.titulo                       AS pelicula,
       p.anio                         AS anio,
       amigosQueRecomiendan,
       round(promedioAmigos, 2)       AS promedioAmigos,
       afinidadGenero,
       round(promedioAmigos * amigosQueRecomiendan + afinidadGenero, 2) AS scoreRecomendacion
ORDER BY scoreRecomendacion DESC
LIMIT 10;
