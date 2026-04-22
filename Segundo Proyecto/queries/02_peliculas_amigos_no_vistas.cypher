// =====================================================================
// Consulta 2
// Peliculas que los amigos del usuario vieron pero el usuario aun no
// ha visto.  La amistad es bidireccional, por eso se ignora la
// direccion de la relacion ES_AMIGO_DE.
// =====================================================================
MATCH (u:Usuario {id: 1})-[:ES_AMIGO_DE]-(amigo:Usuario)-[:VIO]->(p:Pelicula)
WHERE NOT (u)-[:VIO]->(p)
RETURN p.titulo                AS pelicula,
       p.anio                  AS anio,
       count(DISTINCT amigo)   AS amigosQueLaVieron,
       collect(DISTINCT amigo.nombre) AS amigos
ORDER BY amigosQueLaVieron DESC, pelicula
LIMIT 25;
