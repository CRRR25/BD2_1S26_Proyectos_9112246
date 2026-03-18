-- ============================================================
-- ReservaDB: Sistema Distribuido de Gestion de Espacios Compartidos
-- Definicion de Keyspace y Tablas (DDL)
-- ============================================================

-- Creacion del keyspace con SimpleStrategy y factor de replicacion 3.
-- Justificacion:
--   Se utiliza SimpleStrategy porque el cluster se despliega en un unico
--   datacenter (entorno local con Docker). Con un factor de replicacion
--   de 3, cada dato se replica en los 3 nodos del cluster, lo que permite
--   mantener disponibilidad incluso si uno o dos nodos fallan (dependiendo
--   del Consistency Level utilizado). Para un entorno de produccion con
--   multiples datacenters, se recomienda NetworkTopologyStrategy.

CREATE KEYSPACE IF NOT EXISTS reserva_db
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 3
};

USE reserva_db;

-- ============================================================
-- TABLAS DE ENTIDADES BASE
-- ============================================================

-- Tabla de usuarios del sistema de coworking.
-- Permite buscar la informacion de un usuario por su ID.
CREATE TABLE IF NOT EXISTS usuarios (
    usuario_id UUID,
    nombre TEXT,
    email TEXT,
    dpi TEXT,
    telefono TEXT,
    nit TEXT,
    PRIMARY KEY (usuario_id)
);

-- Tabla de espacios disponibles para reservar.
-- Permite buscar la informacion de un espacio por su ID.
CREATE TABLE IF NOT EXISTS espacios (
    espacio_id UUID,
    nombre TEXT,
    tipo TEXT,
    capacidad_maxima INT,
    ubicacion TEXT,
    PRIMARY KEY (espacio_id)
);

-- ============================================================
-- TABLAS DENORMALIZADAS - DISENO BASADO EN QUERIES
-- (Query-Driven Modeling)
--
-- Cada tabla esta disenada para responder una consulta especifica
-- del negocio de forma eficiente, sin necesidad de JOINs ni
-- ALLOW FILTERING. Los datos se duplican intencionalmente en
-- multiples tablas para optimizar los patrones de acceso.
-- ============================================================

-- ============================================================
-- TABLA Q1: reservas_por_espacio_fecha
-- ============================================================
-- Consulta que satisface:
--   "Consultar la disponibilidad de un espacio en una fecha especifica"
--   SELECT * FROM reservas_por_espacio_fecha
--   WHERE espacio_id = ? AND fecha = ?;
--
-- Justificacion de claves:
--   Partition Key: (espacio_id, fecha)
--     Se agrupa por espacio y fecha para que todas las reservas de un
--     espacio en un dia especifico esten en la misma particion. Esto
--     permite leer la disponibilidad de un dia completo con una sola
--     lectura de particion, minimizando la latencia.
--
--   Clustering Key: hora_inicio ASC, reserva_id ASC
--     Se ordena por hora de inicio para visualizar cronologicamente las
--     reservas del dia. El reserva_id garantiza unicidad en caso de
--     reservas que inicien al mismo tiempo.
--
-- Estrategia de compactacion: LeveledCompactionStrategy
--   Optimizada para lecturas frecuentes con pocas escrituras por
--   particion, ideal para consultas de disponibilidad que se ejecutan
--   repetidamente sobre los mismos datos.
--
-- TTL: 31536000 segundos (365 dias)
--   Las reservas se eliminan automaticamente despues de un anio,
--   evitando el crecimiento indefinido de la tabla.

CREATE TABLE IF NOT EXISTS reservas_por_espacio_fecha (
    espacio_id UUID,
    fecha DATE,
    hora_inicio TIME,
    reserva_id UUID,
    hora_fin TIME,
    usuario_id UUID,
    usuario_nombre TEXT,
    espacio_nombre TEXT,
    estado TEXT,
    PRIMARY KEY ((espacio_id, fecha), hora_inicio, reserva_id)
) WITH CLUSTERING ORDER BY (hora_inicio ASC, reserva_id ASC)
AND compaction = {'class': 'LeveledCompactionStrategy'}
AND default_time_to_live = 31536000;

-- ============================================================
-- TABLA Q2: reservas_por_usuario
-- ============================================================
-- Consulta que satisface:
--   "Ver el historial completo de reservas de un usuario"
--   SELECT * FROM reservas_por_usuario WHERE usuario_id = ?;
--
--   Tambien soporta filtro por rango de fechas:
--   SELECT * FROM reservas_por_usuario
--   WHERE usuario_id = ? AND fecha >= ? AND fecha <= ?;
--
-- Justificacion de claves:
--   Partition Key: usuario_id
--     Se agrupa por usuario para que todo el historial de un usuario
--     este en una sola particion, permitiendo obtenerlo con una unica
--     lectura eficiente.
--
--   Clustering Key: fecha DESC, hora_inicio DESC, reserva_id ASC
--     Se ordena de forma descendente por fecha y hora para mostrar
--     las reservas mas recientes primero, que es el patron de acceso
--     mas comun al consultar un historial.
--
-- Estrategia de compactacion: LeveledCompactionStrategy
--   Optimizada para lecturas de historial que son frecuentes.

CREATE TABLE IF NOT EXISTS reservas_por_usuario (
    usuario_id UUID,
    fecha DATE,
    hora_inicio TIME,
    reserva_id UUID,
    hora_fin TIME,
    espacio_id UUID,
    espacio_nombre TEXT,
    usuario_nombre TEXT,
    estado TEXT,
    PRIMARY KEY (usuario_id, fecha, hora_inicio, reserva_id)
) WITH CLUSTERING ORDER BY (fecha DESC, hora_inicio DESC, reserva_id ASC)
AND compaction = {'class': 'LeveledCompactionStrategy'};

-- ============================================================
-- TABLA Q3: ocupacion_por_espacio_rango
-- ============================================================
-- Consulta que satisface:
--   "Obtener la ocupacion de un espacio en un rango de fechas"
--   SELECT * FROM ocupacion_por_espacio_rango
--   WHERE espacio_id = ? AND fecha >= ? AND fecha <= ?;
--
-- Justificacion de claves:
--   Partition Key: espacio_id
--     Se agrupa por espacio para que todas las reservas historicas
--     de un espacio esten en la misma particion. Esto permite hacer
--     range scans eficientes sobre la columna fecha.
--
--   Clustering Key: fecha ASC, hora_inicio ASC, reserva_id ASC
--     Se ordena ascendentemente por fecha y hora para recorrer
--     la ocupacion cronologicamente dentro del rango solicitado.
--
--   Diferencia con la tabla Q1:
--     En Q1, la fecha es parte de la Partition Key, lo que limita
--     la consulta a una fecha especifica. Aqui, la fecha es parte
--     del Clustering Key, lo que permite hacer rangos de fechas
--     dentro de una misma particion (por espacio).
--
-- Estrategia de compactacion: SizeTieredCompactionStrategy
--   Adecuada para tablas con alta carga de escrituras, ya que
--   esta tabla acumula todo el historial de cada espacio.

CREATE TABLE IF NOT EXISTS ocupacion_por_espacio_rango (
    espacio_id UUID,
    fecha DATE,
    hora_inicio TIME,
    reserva_id UUID,
    hora_fin TIME,
    usuario_id UUID,
    usuario_nombre TEXT,
    espacio_nombre TEXT,
    estado TEXT,
    PRIMARY KEY (espacio_id, fecha, hora_inicio, reserva_id)
) WITH CLUSTERING ORDER BY (fecha ASC, hora_inicio ASC, reserva_id ASC)
AND compaction = {'class': 'SizeTieredCompactionStrategy'};
