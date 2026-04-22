// =====================================================================
// Consulta 5
// Ruta mas corta de amistad entre dos usuarios (grados de separacion).
// Se utiliza shortestPath ignorando la direccion de ES_AMIGO_DE.
// Cambiar los ids segun se requiera.
// =====================================================================
MATCH (a:Usuario {id: 1}), (b:Usuario {id: 250}),
      ruta = shortestPath((a)-[:ES_AMIGO_DE*..6]-(b))
RETURN a.nombre              AS origen,
       b.nombre              AS destino,
       length(ruta)          AS gradosDeSeparacion,
       [n IN nodes(ruta) | n.nombre] AS cadenaDeAmigos;
