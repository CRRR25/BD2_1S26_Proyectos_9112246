// =====================================================================
// Consulta 6
// Peliculas mas populares (con mas visualizaciones) de un genero
// especifico.  Cambiar el nombre del genero segun se requiera.
// =====================================================================
MATCH (g:Genero {nombre: 'Accion'})<-[:PERTENECE_A]-(p:Pelicula)
OPTIONAL MATCH (p)<-[v:VIO]-(:Usuario)
RETURN p.titulo               AS pelicula,
       p.anio                 AS anio,
       count(v)               AS visualizaciones
ORDER BY visualizaciones DESC, pelicula
LIMIT 10;
