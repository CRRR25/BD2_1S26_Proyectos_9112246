-- ============================================================
-- ReservaDB - Consultas CQL del Negocio
-- Cada consulta esta disenada para ejecutarse sobre su tabla
-- especializada, sin necesidad de JOINs ni ALLOW FILTERING.
-- ============================================================

USE reserva_db;

-- ============================================================
-- Q1: DISPONIBILIDAD DE UN ESPACIO EN UNA FECHA ESPECIFICA
-- ============================================================
-- Tabla utilizada: reservas_por_espacio_fecha
-- Partition Key: (espacio_id, fecha)
-- Patron de acceso: dado un espacio y una fecha, obtener todas
-- las reservas existentes para identificar horarios libres.
--
-- Para ejecutar esta consulta, reemplazar los valores de ejemplo
-- con un espacio_id y fecha reales del sistema.

-- Ejemplo: ver todas las reservas de un espacio el 15 de marzo 2025
SELECT hora_inicio, hora_fin, usuario_nombre, estado
FROM reservas_por_espacio_fecha
WHERE espacio_id = 550e8400-e29b-41d4-a716-446655440000
  AND fecha = '2025-03-15';

-- Ejemplo: filtrar solo reservas confirmadas en esa fecha
SELECT hora_inicio, hora_fin, usuario_nombre
FROM reservas_por_espacio_fecha
WHERE espacio_id = 550e8400-e29b-41d4-a716-446655440000
  AND fecha = '2025-03-15'
  AND hora_inicio >= '08:00:00'
  AND hora_inicio <= '18:00:00';


-- ============================================================
-- Q2: HISTORIAL DE RESERVAS DE UN USUARIO
-- ============================================================
-- Tabla utilizada: reservas_por_usuario
-- Partition Key: usuario_id
-- Patron de acceso: dado un usuario, obtener todas sus reservas
-- ordenadas de la mas reciente a la mas antigua.

-- Ejemplo: ver todo el historial de un usuario
SELECT fecha, hora_inicio, hora_fin, espacio_nombre, estado
FROM reservas_por_usuario
WHERE usuario_id = 550e8400-e29b-41d4-a716-446655440001;

-- Ejemplo: ver reservas de un usuario en un rango de fechas especifico
SELECT fecha, hora_inicio, hora_fin, espacio_nombre, estado
FROM reservas_por_usuario
WHERE usuario_id = 550e8400-e29b-41d4-a716-446655440001
  AND fecha >= '2025-03-01'
  AND fecha <= '2025-03-31';

-- Ejemplo: ver solo las reservas confirmadas recientes (ultimos 7 dias)
SELECT fecha, hora_inicio, hora_fin, espacio_nombre, estado
FROM reservas_por_usuario
WHERE usuario_id = 550e8400-e29b-41d4-a716-446655440001
  AND fecha >= '2025-03-08'
  AND fecha <= '2025-03-15';


-- ============================================================
-- Q3: OCUPACION DE ESPACIOS POR RANGO DE FECHAS
-- ============================================================
-- Tabla utilizada: ocupacion_por_espacio_rango
-- Partition Key: espacio_id
-- Patron de acceso: dado un espacio, obtener todas las reservas
-- en un rango de fechas para analizar su ocupacion.

-- Ejemplo: ocupacion de un espacio durante todo marzo 2025
SELECT fecha, hora_inicio, hora_fin, usuario_nombre, estado
FROM ocupacion_por_espacio_rango
WHERE espacio_id = 550e8400-e29b-41d4-a716-446655440000
  AND fecha >= '2025-03-01'
  AND fecha <= '2025-03-31';

-- Ejemplo: ocupacion del primer trimestre 2025
SELECT fecha, hora_inicio, hora_fin, usuario_nombre, estado
FROM ocupacion_por_espacio_rango
WHERE espacio_id = 550e8400-e29b-41d4-a716-446655440000
  AND fecha >= '2025-01-01'
  AND fecha <= '2025-03-31';

-- Ejemplo: contar reservas por espacio en un rango
SELECT COUNT(*) as total_reservas
FROM ocupacion_por_espacio_rango
WHERE espacio_id = 550e8400-e29b-41d4-a716-446655440000
  AND fecha >= '2025-01-01'
  AND fecha <= '2025-06-30';


-- ============================================================
-- CONSULTAS ADICIONALES UTILES
-- ============================================================

-- Consultar informacion de un usuario
SELECT * FROM usuarios WHERE usuario_id = 550e8400-e29b-41d4-a716-446655440001;

-- Consultar informacion de un espacio
SELECT * FROM espacios WHERE espacio_id = 550e8400-e29b-41d4-a716-446655440000;

-- Modificar el estado de una reserva (cancelar antes de la fecha de uso)
-- Se debe actualizar en las 3 tablas denormalizadas para mantener consistencia:
UPDATE reservas_por_espacio_fecha
SET estado = 'cancelada'
WHERE espacio_id = 550e8400-e29b-41d4-a716-446655440000
  AND fecha = '2025-03-15'
  AND hora_inicio = '09:00:00'
  AND reserva_id = 550e8400-e29b-41d4-a716-446655440099;

UPDATE reservas_por_usuario
SET estado = 'cancelada'
WHERE usuario_id = 550e8400-e29b-41d4-a716-446655440001
  AND fecha = '2025-03-15'
  AND hora_inicio = '09:00:00'
  AND reserva_id = 550e8400-e29b-41d4-a716-446655440099;

UPDATE ocupacion_por_espacio_rango
SET estado = 'cancelada'
WHERE espacio_id = 550e8400-e29b-41d4-a716-446655440000
  AND fecha = '2025-03-15'
  AND hora_inicio = '09:00:00'
  AND reserva_id = 550e8400-e29b-41d4-a716-446655440099;


-- ============================================================
-- VERIFICACION DE DISTRIBUCION DE DATOS
-- ============================================================
-- Verificar la cantidad total de registros en cada tabla
SELECT COUNT(*) FROM reservas_por_espacio_fecha;
SELECT COUNT(*) FROM reservas_por_usuario;
SELECT COUNT(*) FROM ocupacion_por_espacio_rango;
SELECT COUNT(*) FROM usuarios;
SELECT COUNT(*) FROM espacios;
