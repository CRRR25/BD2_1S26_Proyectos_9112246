"""
ReservaDB - Verificacion de Distribucion de Datos entre Nodos

Verifica que los datos estan distribuidos correctamente entre los 3 nodos
del cluster, mostrando informacion sobre las particiones y la carga de
cada nodo.

Uso:
    python verificar_distribucion.py
"""

import sys
import subprocess
from cassandra.cluster import Cluster
from cassandra.query import ConsistencyLevel

CASSANDRA_HOSTS = ['127.0.0.1']
CASSANDRA_PORT = 9042
KEYSPACE = 'reserva_db'


def conectar():
    """Establece conexion con el cluster."""
    try:
        cluster = Cluster(CASSANDRA_HOSTS, port=CASSANDRA_PORT,
                          connect_timeout=30)
        session = cluster.connect(KEYSPACE)
        return cluster, session
    except Exception as e:
        print(f"Error de conexion: {e}")
        sys.exit(1)


def mostrar_info_cluster(session):
    """Muestra informacion general del cluster."""
    print("=" * 65)
    print("  INFORMACION DEL CLUSTER")
    print("=" * 65)

    # Nodo local
    local = session.execute(
        "SELECT cluster_name, listen_address, data_center, rack, "
        "release_version, partitioner FROM system.local"
    ).one()

    print(f"\n  Nombre del cluster:  {local.cluster_name}")
    print(f"  Partitioner:         {local.partitioner}")
    print(f"  Version Cassandra:   {local.release_version}")

    # Nodos del cluster
    print(f"\n  Nodos del cluster:")
    print(f"  {'─' * 55}")
    print(f"  Nodo local:  {local.listen_address} "
          f"(DC: {local.data_center}, Rack: {local.rack})")

    peers = session.execute(
        "SELECT peer, data_center, rack, release_version FROM system.peers"
    )
    for peer in peers:
        print(f"  Nodo peer:   {peer.peer} "
              f"(DC: {peer.data_center}, Rack: {peer.rack})")


def verificar_conteo_tablas(session):
    """Muestra el conteo de registros por tabla."""
    print(f"\n{'=' * 65}")
    print(f"  CONTEO DE REGISTROS POR TABLA")
    print(f"{'=' * 65}")

    tablas = {
        'usuarios': 'Tabla de usuarios',
        'espacios': 'Tabla de espacios',
        'reservas_por_espacio_fecha': 'Q1: Disponibilidad por espacio y fecha',
        'reservas_por_usuario': 'Q2: Historial por usuario',
        'ocupacion_por_espacio_rango': 'Q3: Ocupacion por rango de fechas'
    }

    print(f"\n  {'Tabla':<35} {'Registros':<15} {'Proposito'}")
    print(f"  {'─' * 90}")

    for tabla, descripcion in tablas.items():
        try:
            rows = session.execute(f"SELECT COUNT(*) as total FROM {tabla}")
            total = rows.one().total
            print(f"  {tabla:<35} {total:>10,}     {descripcion}")
        except Exception as e:
            print(f"  {tabla:<35} {'ERROR':<15} {e}")


def verificar_keyspace(session):
    """Muestra la configuracion del keyspace."""
    print(f"\n{'=' * 65}")
    print(f"  CONFIGURACION DEL KEYSPACE")
    print(f"{'=' * 65}")

    rows = session.execute(
        "SELECT keyspace_name, replication FROM system_schema.keyspaces "
        "WHERE keyspace_name = 'reserva_db'"
    )
    row = rows.one()

    if row:
        print(f"\n  Keyspace:     {row.keyspace_name}")
        print(f"  Replicacion:  {row.replication}")

        replication = row.replication
        strategy = replication.get('class', 'N/A')
        rf = replication.get('replication_factor', 'N/A')

        print(f"\n  Estrategia:          {strategy}")
        print(f"  Replication Factor:  {rf}")

        if str(rf) == '3':
            print(f"\n  [OK] RF=3 es correcto para un cluster de 3 nodos.")
            print(f"       Cada dato se replica en los 3 nodos del cluster.")
        else:
            print(f"\n  [ADVERTENCIA] RF={rf} podria no ser optimo para 3 nodos.")


def verificar_distribucion_nodetool():
    """
    Intenta ejecutar nodetool para mostrar la distribucion de datos.
    Se ejecuta dentro del contenedor Docker de Cassandra.
    """
    print(f"\n{'=' * 65}")
    print(f"  DISTRIBUCION DE DATOS ENTRE NODOS (nodetool)")
    print(f"{'=' * 65}")

    try:
        # Ejecutar nodetool status dentro del contenedor
        resultado = subprocess.run(
            ['docker', 'exec', 'cassandra-node1', 'nodetool', 'status'],
            capture_output=True, text=True, timeout=30
        )
        if resultado.returncode == 0:
            print(f"\n{resultado.stdout}")
        else:
            print(f"\n  No se pudo ejecutar nodetool: {resultado.stderr}")
            print(f"  Ejecutar manualmente: docker exec cassandra-node1 nodetool status")

    except FileNotFoundError:
        print("\n  Docker no disponible desde este entorno.")
        print("  Para verificar la distribucion, ejecutar manualmente:")
        print("    docker exec cassandra-node1 nodetool status")
        print("    docker exec cassandra-node1 nodetool ring reserva_db")

    try:
        # Tambien mostrar el detalle del tablespace
        resultado = subprocess.run(
            ['docker', 'exec', 'cassandra-node1', 'nodetool', 'tablestats', 'reserva_db'],
            capture_output=True, text=True, timeout=30
        )
        if resultado.returncode == 0:
            # Mostrar solo las lineas relevantes
            lineas = resultado.stdout.split('\n')
            for linea in lineas:
                if any(k in linea.lower() for k in ['table:', 'space used', 'number of', 'read count', 'write count']):
                    print(f"  {linea.strip()}")

    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def main():
    print("=" * 65)
    print("  RESERVADB - VERIFICACION DE DISTRIBUCION DE DATOS")
    print("=" * 65)

    cluster, session = conectar()

    try:
        mostrar_info_cluster(session)
        verificar_keyspace(session)
        verificar_conteo_tablas(session)
        verificar_distribucion_nodetool()

        print(f"\n{'=' * 65}")
        print(f"  VERIFICACION COMPLETADA")
        print(f"{'=' * 65}")

    finally:
        cluster.shutdown()


if __name__ == '__main__':
    main()
