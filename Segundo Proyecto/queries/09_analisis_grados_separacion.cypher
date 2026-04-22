// =====================================================================
// Analisis de redes 1
// Distribucion de grados de separacion entre un usuario semilla y el
// resto de la red de amistades.  Util para visualizar que tan
// "conectado" esta cada usuario.
//
// Usa shortestPath y limita a 6 saltos (teoria de los seis grados).
// =====================================================================
MATCH (origen:Usuario {id: 1}), (otro:Usuario)
WHERE otro <> origen
OPTIONAL MATCH ruta = shortestPath((origen)-[:ES_AMIGO_DE*..6]-(otro))
WITH otro, ruta
RETURN
  CASE
    WHEN ruta IS NULL THEN 'No alcanzable'
    ELSE toString(length(ruta))
  END                          AS gradosDeSeparacion,
  count(otro)                  AS cantidadDeUsuarios
ORDER BY gradosDeSeparacion;
