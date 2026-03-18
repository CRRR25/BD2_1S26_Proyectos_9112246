"""
ReservaDB - Ejecucion de Consultas CQL con Medicion de Latencia
Ejecuta las 3 consultas principales del negocio, mide su latencia
y muestra los resultados en formato tabular.

Uso:
    python consultas.py
"""

import time
import sys
from datetime import date, timedelta

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, ConsistencyLevel

# ============================================================
# CONFIGURACION
# ============================================================
CASSANDRA_HOSTS = ['127.0.0.1']
CASSANDRA_PORT = 9042
KEYSPACE = 'reserva_db'
NUM_EJECUCIONES = 5  # Veces que se ejecuta cada consulta para promediar latencia


def conectar():
    """Establece conexion con el cluster."""
    try:
        cluster = Cluster(CASSANDRA_HOSTS, port=CASSANDRA_PORT,
                          connect_timeout=30)
        session = cluster.connect(KEYSPACE)
        print("Conexion al cluster establecida.\n")
        return cluster, session
    except Exception as e:
        print(f"Error de conexion: {e}")
        sys.exit(1)


def obtener_ids_muestra(session):
    """
    Obtiene IDs reales de la base de datos para usar en las consultas.
    Se toman de las tablas existentes para garantizar que las consultas
    retornen resultados.
    """
    print("Obteniendo datos de muestra para las consultas...")

    # Obtener un usuario con reservas
    rows = session.execute("SELECT usuario_id FROM reservas_por_usuario LIMIT 1")
    row = rows.one()
    if not row:
        print("No se encontraron datos. Ejecutar primero carga_datos.py")
        sys.exit(1)
    usuario_id = row.usuario_id

    # Obtener un espacio con reservas y su fecha
    rows = session.execute(
        "SELECT espacio_id, fecha FROM ocupacion_por_espacio_rango LIMIT 1"
    )
    row = rows.one()
    espacio_id = row.espacio_id
    fecha_muestra = row.fecha

    # Obtener nombre del usuario y del espacio
    row_usr = session.execute(
        "SELECT nombre FROM usuarios WHERE usuario_id = %s", (usuario_id,)
    ).one()
    nombre_usuario = row_usr.nombre if row_usr else "Desconocido"

    row_esp = session.execute(
        "SELECT nombre FROM espacios WHERE espacio_id = %s", (espacio_id,)
    ).one()
    nombre_espacio = row_esp.nombre if row_esp else "Desconocido"

    print(f"  Usuario de prueba: {nombre_usuario} ({usuario_id})")
    print(f"  Espacio de prueba: {nombre_espacio} ({espacio_id})")
    print(f"  Fecha de prueba:   {fecha_muestra}")

    return usuario_id, espacio_id, fecha_muestra


def medir_latencia(session, query, params, num_ejecuciones=NUM_EJECUCIONES):
    """
    Ejecuta una consulta varias veces y calcula la latencia promedio,
    minima y maxima en milisegundos.
    """
    latencias = []

    for _ in range(num_ejecuciones):
        inicio = time.time()
        resultado = session.execute(query, params)
        fin = time.time()
        latencias.append((fin - inicio) * 1000)  # Convertir a ms
        filas = list(resultado)

    promedio = sum(latencias) / len(latencias)
    minima = min(latencias)
    maxima = max(latencias)

    return {
        'promedio': promedio,
        'minima': minima,
        'maxima': maxima,
        'filas': filas,
        'num_resultados': len(filas)
    }


def consulta_disponibilidad(session, espacio_id, fecha):
    """
    Q1: Consultar disponibilidad de un espacio en una fecha.
    Tabla: reservas_por_espacio_fecha
    Partition Key: (espacio_id, fecha)
    """
    print("\n" + "=" * 65)
    print("Q1: DISPONIBILIDAD DE ESPACIO POR FECHA")
    print("=" * 65)
    print(f"Tabla: reservas_por_espacio_fecha")
    print(f"Query: SELECT ... WHERE espacio_id = ? AND fecha = ?")
    print(f"Parametros: espacio_id={espacio_id}, fecha={fecha}")

    query = SimpleStatement(
        "SELECT hora_inicio, hora_fin, usuario_nombre, estado "
        "FROM reservas_por_espacio_fecha "
        "WHERE espacio_id = %s AND fecha = %s",
        consistency_level=ConsistencyLevel.QUORUM
    )

    resultado = medir_latencia(session, query, (espacio_id, fecha))

    print(f"\nResultados: {resultado['num_resultados']} reservas encontradas")
    print(f"Latencia promedio: {resultado['promedio']:.2f} ms")
    print(f"Latencia minima:   {resultado['minima']:.2f} ms")
    print(f"Latencia maxima:   {resultado['maxima']:.2f} ms")

    if resultado['filas']:
        print(f"\n{'Hora Inicio':<14} {'Hora Fin':<14} {'Usuario':<30} {'Estado':<15}")
        print("-" * 73)
        for fila in resultado['filas'][:15]:  # Mostrar maximo 15
            print(f"{str(fila.hora_inicio):<14} {str(fila.hora_fin):<14} "
                  f"{fila.usuario_nombre:<30} {fila.estado:<15}")
        if resultado['num_resultados'] > 15:
            print(f"  ... y {resultado['num_resultados'] - 15} reservas mas.")

    return resultado


def consulta_historial_usuario(session, usuario_id):
    """
    Q2: Ver historial de reservas de un usuario.
    Tabla: reservas_por_usuario
    Partition Key: usuario_id
    """
    print("\n" + "=" * 65)
    print("Q2: HISTORIAL DE RESERVAS POR USUARIO")
    print("=" * 65)
    print(f"Tabla: reservas_por_usuario")
    print(f"Query: SELECT ... WHERE usuario_id = ?")
    print(f"Parametros: usuario_id={usuario_id}")

    query = SimpleStatement(
        "SELECT fecha, hora_inicio, hora_fin, espacio_nombre, estado "
        "FROM reservas_por_usuario "
        "WHERE usuario_id = %s",
        consistency_level=ConsistencyLevel.QUORUM
    )

    resultado = medir_latencia(session, query, (usuario_id,))

    print(f"\nResultados: {resultado['num_resultados']} reservas en historial")
    print(f"Latencia promedio: {resultado['promedio']:.2f} ms")
    print(f"Latencia minima:   {resultado['minima']:.2f} ms")
    print(f"Latencia maxima:   {resultado['maxima']:.2f} ms")

    if resultado['filas']:
        print(f"\n{'Fecha':<14} {'Hora Inicio':<14} {'Hora Fin':<14} {'Espacio':<20} {'Estado':<15}")
        print("-" * 77)
        for fila in resultado['filas'][:15]:
            print(f"{str(fila.fecha):<14} {str(fila.hora_inicio):<14} "
                  f"{str(fila.hora_fin):<14} {fila.espacio_nombre:<20} {fila.estado:<15}")
        if resultado['num_resultados'] > 15:
            print(f"  ... y {resultado['num_resultados'] - 15} reservas mas.")

    return resultado


def consulta_ocupacion_rango(session, espacio_id, fecha_inicio, fecha_fin):
    """
    Q3: Obtener ocupacion de un espacio en un rango de fechas.
    Tabla: ocupacion_por_espacio_rango
    Partition Key: espacio_id
    """
    print("\n" + "=" * 65)
    print("Q3: OCUPACION DE ESPACIO POR RANGO DE FECHAS")
    print("=" * 65)
    print(f"Tabla: ocupacion_por_espacio_rango")
    print(f"Query: SELECT ... WHERE espacio_id = ? AND fecha >= ? AND fecha <= ?")
    print(f"Parametros: espacio_id={espacio_id}, "
          f"fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}")

    query = SimpleStatement(
        "SELECT fecha, hora_inicio, hora_fin, usuario_nombre, estado "
        "FROM ocupacion_por_espacio_rango "
        "WHERE espacio_id = %s AND fecha >= %s AND fecha <= %s",
        consistency_level=ConsistencyLevel.QUORUM
    )

    resultado = medir_latencia(session, query, (espacio_id, fecha_inicio, fecha_fin))

    print(f"\nResultados: {resultado['num_resultados']} reservas en el rango")
    print(f"Latencia promedio: {resultado['promedio']:.2f} ms")
    print(f"Latencia minima:   {resultado['minima']:.2f} ms")
    print(f"Latencia maxima:   {resultado['maxima']:.2f} ms")

    if resultado['filas']:
        print(f"\n{'Fecha':<14} {'Hora Inicio':<14} {'Hora Fin':<14} {'Usuario':<30} {'Estado':<15}")
        print("-" * 87)
        for fila in resultado['filas'][:15]:
            print(f"{str(fila.fecha):<14} {str(fila.hora_inicio):<14} "
                  f"{str(fila.hora_fin):<14} {fila.usuario_nombre:<30} {fila.estado:<15}")
        if resultado['num_resultados'] > 15:
            print(f"  ... y {resultado['num_resultados'] - 15} reservas mas.")

    return resultado


def main():
    print("=" * 65)
    print("  RESERVADB - EJECUCION Y MEDICION DE CONSULTAS CQL")
    print("=" * 65)

    cluster, session = conectar()

    try:
        # Obtener datos reales de la BD para las consultas
        usuario_id, espacio_id, fecha_muestra = obtener_ids_muestra(session)

        # Q1: Disponibilidad de espacio por fecha
        r1 = consulta_disponibilidad(session, espacio_id, fecha_muestra)

        # Q2: Historial de reservas por usuario
        r2 = consulta_historial_usuario(session, usuario_id)

        # Q3: Ocupacion por rango de fechas (rango de 30 dias a partir de la fecha muestra)
        fecha_inicio_rango = date.fromisoformat(str(fecha_muestra))
        fecha_fin_rango = fecha_inicio_rango + timedelta(days=30)
        r3 = consulta_ocupacion_rango(session, espacio_id, fecha_inicio_rango, fecha_fin_rango)

        # Resumen comparativo de latencias
        print("\n" + "=" * 65)
        print("  RESUMEN COMPARATIVO DE LATENCIAS")
        print("=" * 65)
        print(f"\n{'Consulta':<45} {'Promedio (ms)':<15} {'Min (ms)':<12} {'Max (ms)':<12} {'Filas':<8}")
        print("-" * 92)
        print(f"{'Q1: Disponibilidad espacio/fecha':<45} "
              f"{r1['promedio']:<15.2f} {r1['minima']:<12.2f} {r1['maxima']:<12.2f} {r1['num_resultados']:<8}")
        print(f"{'Q2: Historial reservas/usuario':<45} "
              f"{r2['promedio']:<15.2f} {r2['minima']:<12.2f} {r2['maxima']:<12.2f} {r2['num_resultados']:<8}")
        print(f"{'Q3: Ocupacion espacio/rango fechas':<45} "
              f"{r3['promedio']:<15.2f} {r3['minima']:<12.2f} {r3['maxima']:<12.2f} {r3['num_resultados']:<8}")

        print(f"\nNota: cada consulta se ejecuto {NUM_EJECUCIONES} veces para calcular promedios.")
        print("Consistency Level utilizado: QUORUM")

    finally:
        cluster.shutdown()


if __name__ == '__main__':
    main()
