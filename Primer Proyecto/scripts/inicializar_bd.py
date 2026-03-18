"""
ReservaDB - Inicializacion de la Base de Datos
Crea el keyspace y todas las tablas definidas en el modelo de datos.
Debe ejecutarse despues de que el cluster de Cassandra este activo.

Uso:
    python inicializar_bd.py
"""

import sys
import time

from cassandra.cluster import Cluster
from cassandra.query import ConsistencyLevel, SimpleStatement

CASSANDRA_HOSTS = ['127.0.0.1']
CASSANDRA_PORT = 9042


def esperar_cluster():
    """Espera a que el cluster de Cassandra este disponible."""
    print("Esperando a que el cluster de Cassandra este disponible...")
    intentos = 0
    max_intentos = 30

    while intentos < max_intentos:
        try:
            cluster = Cluster(
                CASSANDRA_HOSTS,
                port=CASSANDRA_PORT,
                connect_timeout=30
            )
            session = cluster.connect()
            print("Cluster disponible.")
            return cluster, session
        except Exception as e:
            intentos += 1
            print(f"  Intento {intentos}/{max_intentos} - {e}")
            print(f"  Reintentando en 10 segundos...")
            try:
                cluster.shutdown()
            except Exception:
                pass
            time.sleep(10)

    print("No se pudo conectar al cluster despues de multiples intentos.")
    sys.exit(1)


def ejecutar_ddl(session):
    """Ejecuta las sentencias DDL para crear el keyspace y las tablas."""

    sentencias = [
        # Keyspace
        (
            "Creando keyspace reserva_db...",
            """
            CREATE KEYSPACE IF NOT EXISTS reserva_db
            WITH replication = {
                'class': 'SimpleStrategy',
                'replication_factor': 3
            }
            """
        ),

        # Tabla de usuarios
        (
            "Creando tabla usuarios...",
            """
            CREATE TABLE IF NOT EXISTS reserva_db.usuarios (
                usuario_id UUID,
                nombre TEXT,
                email TEXT,
                dpi TEXT,
                telefono TEXT,
                nit TEXT,
                PRIMARY KEY (usuario_id)
            )
            """
        ),

        # Tabla de espacios
        (
            "Creando tabla espacios...",
            """
            CREATE TABLE IF NOT EXISTS reserva_db.espacios (
                espacio_id UUID,
                nombre TEXT,
                tipo TEXT,
                capacidad_maxima INT,
                ubicacion TEXT,
                PRIMARY KEY (espacio_id)
            )
            """
        ),

        # Tabla Q1: reservas_por_espacio_fecha
        (
            "Creando tabla reservas_por_espacio_fecha (Q1: disponibilidad)...",
            """
            CREATE TABLE IF NOT EXISTS reserva_db.reservas_por_espacio_fecha (
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
            AND default_time_to_live = 31536000
            """
        ),

        # Tabla Q2: reservas_por_usuario
        (
            "Creando tabla reservas_por_usuario (Q2: historial)...",
            """
            CREATE TABLE IF NOT EXISTS reserva_db.reservas_por_usuario (
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
            AND compaction = {'class': 'LeveledCompactionStrategy'}
            """
        ),

        # Tabla Q3: ocupacion_por_espacio_rango
        (
            "Creando tabla ocupacion_por_espacio_rango (Q3: ocupacion)...",
            """
            CREATE TABLE IF NOT EXISTS reserva_db.ocupacion_por_espacio_rango (
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
            AND compaction = {'class': 'SizeTieredCompactionStrategy'}
            """
        ),
    ]

    for mensaje, sentencia in sentencias:
        print(f"  {mensaje}")
        try:
            stmt = SimpleStatement(sentencia, consistency_level=ConsistencyLevel.ONE)
            session.execute(stmt, timeout=60)
            print(f"    [OK]")
            time.sleep(3)  # Esperar a que el esquema se propague entre nodos
        except Exception as e:
            print(f"    [ERROR] {e}")
            sys.exit(1)


def verificar_tablas(session):
    """Verifica que todas las tablas se crearon correctamente."""
    print("\nVerificando tablas creadas...")

    session.set_keyspace('reserva_db')
    rows = session.execute(
        "SELECT table_name FROM system_schema.tables WHERE keyspace_name = 'reserva_db'"
    )
    tablas = [row.table_name for row in rows]

    tablas_esperadas = [
        'usuarios', 'espacios',
        'reservas_por_espacio_fecha',
        'reservas_por_usuario',
        'ocupacion_por_espacio_rango'
    ]

    for tabla in tablas_esperadas:
        if tabla in tablas:
            print(f"  [OK] {tabla}")
        else:
            print(f"  [FALTA] {tabla}")

    return all(t in tablas for t in tablas_esperadas)


def main():
    print("=" * 65)
    print("  RESERVADB - INICIALIZACION DE BASE DE DATOS")
    print("=" * 65)

    cluster, session = esperar_cluster()

    try:
        print("\nCreando keyspace y tablas...")
        print("-" * 40)
        ejecutar_ddl(session)

        print()
        if verificar_tablas(session):
            print("\n  Todas las tablas fueron creadas exitosamente.")
            print("\n  Siguiente paso: ejecutar carga_datos.py para insertar datos.")
        else:
            print("\n  Algunas tablas no se crearon. Revisar los errores anteriores.")

    finally:
        cluster.shutdown()

    print("\n" + "=" * 65)
    print("  INICIALIZACION COMPLETADA")
    print("=" * 65)


if __name__ == '__main__':
    main()
