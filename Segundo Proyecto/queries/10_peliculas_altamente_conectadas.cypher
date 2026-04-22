// =====================================================================
// Analisis de redes 2
// Peliculas altamente conectadas: aquellas con mayor cantidad de
// actores/directores reconocidos.
//
// Se considera "reconocido" a todo actor o director que ha trabajado
// en mas de 3 peliculas en el grafo.  El score combina la cantidad
// total de actores y directores reconocidos vinculados a la pelicula.
// =====================================================================
MATCH (a:Actor)-[:ACTUO_EN]->(:Pelicula)
WITH a, count(*) AS apariciones
WHERE apariciones > 3
WITH collect(a) AS actoresReconocidos

MATCH (d:Director)-[:DIRIGIO]->(:Pelicula)
WITH actoresReconocidos, d, count(*) AS dirigidas
WHERE dirigidas > 3
WITH actoresReconocidos, collect(d) AS directoresReconocidos

MATCH (p:Pelicula)
OPTIONAL MATCH (p)<-[:ACTUO_EN]-(a:Actor) WHERE a IN actoresReconocidos
WITH p, directoresReconocidos, count(DISTINCT a) AS actoresFamosos
OPTIONAL MATCH (p)<-[:DIRIGIO]-(d:Director) WHERE d IN directoresReconocidos
WITH p, actoresFamosos, count(DISTINCT d) AS directoresFamosos
RETURN p.titulo                                  AS pelicula,
       p.anio                                    AS anio,
       actoresFamosos,
       directoresFamosos,
       (actoresFamosos + directoresFamosos)      AS scoreConectividad
ORDER BY scoreConectividad DESC, pelicula
LIMIT 15;
