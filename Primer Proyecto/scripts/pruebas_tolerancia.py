"""
ReservaDB - Pruebas de Tolerancia a Fallos y Analisis de Niveles de Consistencia

Este script ejecuta pruebas para verificar como se comporta el sistema
cuando se caen nodos del cluster. Se prueban los 3 niveles de consistencia
(ONE, QUORUM, ALL) y se comparan sus tiempos de respuesta.

Pasos para realizar las pruebas:
    1. Levantar el cluster completo (3 nodos):
       docker-compose up -d

    2. Correr las pruebas con todos los nodos funcionando:
       python pruebas_tolerancia.py

    3. Apagar un nodo para simular una falla:
       docker stop cassandra-node3

    4. Correr las pruebas de nuevo y comparar:
       python pruebas_tolerancia.py

    5. Apagar un segundo nodo:
       docker stop cassandra-node2

    6. Correr las pruebas una ultima vez:
       python pruebas_tolerancia.py

    7. Volver a encender los nodos:
       docker start cassandra-node2
       docker start cassandra-node3

Que se espera en cada escenario:
    - Con RF=3 y 3 nodos, cada dato se guarda en los 3 nodos.
    - ONE: funciona si al menos 1 nodo esta encendido.
    - QUORUM: funciona si al menos 2 de 3 nodos estan encendidos.
    - ALL: solo funciona si los 3 nodos estan encendidos.
"""

import time
import sys
import uuid
from datetime import date, timedelta, time as dt_time

from cassandra.cluster import Cluster, NoHostAvailable
from cassandra.query import SimpleStatement, ConsistencyLevel
from cassandra import Unavailable, ReadTimeout, WriteTimeout

# ============================================================
# CONFIGURACION
# ============================================================
CASSANDRA_HOSTS = ['127.0.0.1']
CASSANDRA_PORT = 9042
KEYSPACE = 'reserva_db'
NUM_ITERACIONES = 10

# Niveles de consistencia que se van a probar
CONSISTENCY_LEVELS = {
    'ONE': ConsistencyLevel.ONE,
    'QUORUM': ConsistencyLevel.QUORUM,
    'ALL': ConsistencyLevel.ALL
}


def conectar():
    """Se conecta al cluster de Cassandra."""
    try:
        cluster = Cluster(CASSANDRA_HOSTS, port=CASSANDRA_PORT,
                          connect_timeout=30)
        session = cluster.connect(KEYSPACE)
        return cluster, session
    except Exception as e:
        print(f"No se pudo conectar al cluster: {e}")
        print("Hay que verificar que al menos un nodo este encendido.")
        sys.exit(1)


def obtener_estado_cluster(session):
    """Muestra cuantos nodos estan activos en el cluster."""
    print("\nEstado del cluster:")
    print("-" * 50)

    try:
        rows = session.execute(
            "SELECT peer, data_center, rack, release_version "
            "FROM system.peers"
        )
        peers = list(rows)

        local = session.execute(
            "SELECT listen_address, data_center, rack, release_version "
            "FROM system.local"
        ).one()

        print(f"  Nodo principal: {local.listen_address} "
              f"(Centro de datos: {local.data_center}, Rack: {local.rack}, "
              f"Version: {local.release_version})")

        for peer in peers:
            print(f"  Nodo replica:   {peer.peer} "
                  f"(Centro de datos: {peer.data_center}, Rack: {peer.rack}, "
                  f"Version: {peer.release_version})")

        total_nodos = 1 + len(peers)
        print(f"\n  Nodos detectados en total: {total_nodos}")
        return total_nodos

    except Exception as e:
        print(f"  No se pudo consultar el estado: {e}")
        return 0


def obtener_datos_prueba(session):
    """Busca datos reales en la base de datos para usarlos en las pruebas."""
    try:
        row = session.execute(
            "SELECT espacio_id, fecha FROM ocupacion_por_espacio_rango LIMIT 1"
        ).one()
        if not row:
            print("La base de datos esta vacia. Primero hay que correr carga_datos.py")
            sys.exit(1)

        row_usr = session.execute(
            "SELECT usuario_id FROM reservas_por_usuario LIMIT 1"
        ).one()

        # Convertir la fecha de Cassandra a fecha nativa de Python
        fecha_nativa = date.fromisoformat(str(row.fecha))
        return row.espacio_id, fecha_nativa, row_usr.usuario_id

    except Exception as e:
        print(f"Error al buscar datos de prueba: {e}")
        sys.exit(1)


def ejecutar_prueba_lectura(session, nombre, query_str, params, cl):
    """
    Ejecuta una consulta de lectura varias veces con un nivel de consistencia
    y mide cuanto tarda cada vez.
    """
    query = SimpleStatement(query_str, consistency_level=cl)

    latencias = []
    errores = 0
    filas = []

    for _ in range(NUM_ITERACIONES):
        try:
            inicio = time.time()
            filas = list(session.execute(query, params))
            fin = time.time()
            latencias.append((fin - inicio) * 1000)
        except (Unavailable, ReadTimeout, NoHostAvailable):
            errores += 1
        except Exception:
            errores += 1

    if latencias:
        return {
            'nombre': nombre,
            'exitosas': len(latencias),
            'errores': errores,
            'promedio': sum(latencias) / len(latencias),
            'minima': min(latencias),
            'maxima': max(latencias),
            'num_filas': len(filas)
        }
    else:
        return {
            'nombre': nombre,
            'exitosas': 0,
            'errores': errores,
            'promedio': 0,
            'minima': 0,
            'maxima': 0,
            'num_filas': 0
        }


def ejecutar_prueba_escritura(session, cl):
    """
    Inserta registros de prueba con un nivel de consistencia
    y mide cuanto tarda cada insercion.
    """
    query = SimpleStatement(
        "INSERT INTO reservas_por_espacio_fecha "
        "(espacio_id, fecha, hora_inicio, reserva_id, hora_fin, "
        "usuario_id, usuario_nombre, espacio_nombre, estado) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        consistency_level=cl
    )

    latencias = []
    errores = 0

    for _ in range(NUM_ITERACIONES):
        try:
            params = (
                uuid.uuid4(), date(2099, 12, 31), dt_time(12, 0),
                uuid.uuid4(), dt_time(13, 0),
                uuid.uuid4(), 'Prueba Tolerancia', 'Espacio Prueba', 'pendiente'
            )
            inicio = time.time()
            session.execute(query, params)
            fin = time.time()
            latencias.append((fin - inicio) * 1000)
        except (Unavailable, WriteTimeout, NoHostAvailable):
            errores += 1
        except Exception:
            errores += 1

    if latencias:
        return {
            'exitosas': len(latencias),
            'errores': errores,
            'promedio': sum(latencias) / len(latencias),
            'minima': min(latencias),
            'maxima': max(latencias)
        }
    else:
        return {
            'exitosas': 0,
            'errores': errores,
            'promedio': 0,
            'minima': 0,
            'maxima': 0
        }


def ejecutar_pruebas_por_cl(session, espacio_id, fecha, usuario_id, cl_nombre, cl):
    """Ejecuta todas las pruebas para un nivel de consistencia."""

    print(f"\n  Nivel de consistencia: {cl_nombre}")
    print(f"  {'─' * 55}")

    # Lectura Q1: Disponibilidad por espacio y fecha
    r1 = ejecutar_prueba_lectura(
        session, "Q1: Disponibilidad espacio/fecha",
        "SELECT hora_inicio, hora_fin, usuario_nombre, estado "
        "FROM reservas_por_espacio_fecha WHERE espacio_id = %s AND fecha = %s",
        (espacio_id, fecha), cl
    )

    # Lectura Q2: Historial de reservas por usuario
    r2 = ejecutar_prueba_lectura(
        session, "Q2: Historial reservas/usuario",
        "SELECT fecha, hora_inicio, hora_fin, espacio_nombre, estado "
        "FROM reservas_por_usuario WHERE usuario_id = %s",
        (usuario_id,), cl
    )

    # Lectura Q3: Ocupacion por rango de fechas
    fecha_fin = fecha + timedelta(days=30)
    r3 = ejecutar_prueba_lectura(
        session, "Q3: Ocupacion espacio/rango",
        "SELECT fecha, hora_inicio, hora_fin, usuario_nombre, estado "
        "FROM ocupacion_por_espacio_rango "
        "WHERE espacio_id = %s AND fecha >= %s AND fecha <= %s",
        (espacio_id, fecha, fecha_fin), cl
    )

    # Prueba de escritura
    w = ejecutar_prueba_escritura(session, cl)

    # Mostrar tabla de resultados
    print(f"\n  {'Operacion':<40} {'Bien':<6} {'Mal':<6} {'Prom(ms)':<10} {'Min(ms)':<10} {'Max(ms)':<10}")
    print(f"  {'─' * 82}")

    for r in [r1, r2, r3]:
        if r['exitosas'] > 0:
            print(f"  {r['nombre']:<40} {r['exitosas']:<6} {r['errores']:<6} "
                  f"{r['promedio']:<10.2f} {r['minima']:<10.2f} {r['maxima']:<10.2f}")
        else:
            print(f"  {r['nombre']:<40} {r['exitosas']:<6} {r['errores']:<6} "
                  f"{'FALLO':<10} {'─':<10} {'─':<10}")

    if w['exitosas'] > 0:
        print(f"  {'Escritura (INSERT)':<40} {w['exitosas']:<6} {w['errores']:<6} "
              f"{w['promedio']:<10.2f} {w['minima']:<10.2f} {w['maxima']:<10.2f}")
    else:
        print(f"  {'Escritura (INSERT)':<40} {w['exitosas']:<6} {w['errores']:<6} "
              f"{'FALLO':<10} {'─':<10} {'─':<10}")

    return {
        'cl': cl_nombre,
        'lecturas': [r1, r2, r3],
        'escritura': w
    }


def main():
    print("=" * 65)
    print("  RESERVADB - PRUEBAS DE TOLERANCIA A FALLOS")
    print("  Comparacion de Niveles de Consistencia")
    print("=" * 65)

    cluster, session = conectar()

    try:
        # Ver cuantos nodos estan activos
        num_nodos = obtener_estado_cluster(session)

        # Buscar datos reales para las pruebas
        espacio_id, fecha, usuario_id = obtener_datos_prueba(session)
        print(f"\nDatos que se usaran para las pruebas:")
        print(f"  ID del espacio:  {espacio_id}")
        print(f"  Fecha:           {fecha}")
        print(f"  ID del usuario:  {usuario_id}")

        # Correr las pruebas con cada nivel de consistencia
        print(f"\nEjecutando pruebas ({NUM_ITERACIONES} veces cada consulta)...")
        print("=" * 65)

        resultados = {}
        for cl_nombre, cl in CONSISTENCY_LEVELS.items():
            resultados[cl_nombre] = ejecutar_pruebas_por_cl(
                session, espacio_id, fecha, usuario_id, cl_nombre, cl
            )

        # Tabla resumen
        print("\n" + "=" * 65)
        print("  TABLA RESUMEN DE RESULTADOS")
        print("=" * 65)

        print(f"\n  Nodos activos: {num_nodos}")
        print(f"  Factor de replicacion: 3")
        print(f"  Repeticiones por prueba: {NUM_ITERACIONES}")

        print(f"\n  {'Nivel':<10} {'Lecturas OK':<14} {'Lecturas Mal':<14} "
              f"{'Tiempo Prom.':<14} {'Escritura OK':<14} {'Escritura Mal':<14}")
        print(f"  {'─' * 80}")

        for cl_nombre in CONSISTENCY_LEVELS:
            r = resultados[cl_nombre]
            total_ok = sum(l['exitosas'] for l in r['lecturas'])
            total_err = sum(l['errores'] for l in r['lecturas'])
            proms = [l['promedio'] for l in r['lecturas'] if l['exitosas'] > 0]
            prom_general = sum(proms) / len(proms) if proms else 0

            print(f"  {cl_nombre:<10} {total_ok:<14} {total_err:<14} "
                  f"{prom_general:<14.2f} {r['escritura']['exitosas']:<14} "
                  f"{r['escritura']['errores']:<14}")

        # Analisis de lo que paso
        print(f"\n  QUE PASO EN CADA NIVEL:")
        print(f"  {'─' * 55}")

        todos_ok = all(
            all(l['exitosas'] == NUM_ITERACIONES for l in r['lecturas'])
            and r['escritura']['exitosas'] == NUM_ITERACIONES
            for r in resultados.values()
        )

        if todos_ok:
            print("  Todos los niveles funcionaron bien, lo que significa")
            print("  que los 3 nodos del cluster estan activos y respondiendo.")
        else:
            for cl_nombre in CONSISTENCY_LEVELS:
                r = resultados[cl_nombre]
                tiene_errores = (
                    any(l['errores'] > 0 for l in r['lecturas'])
                    or r['escritura']['errores'] > 0
                )
                if tiene_errores:
                    print(f"  {cl_nombre}: Tuvo errores en algunas consultas.")
                    if cl_nombre == 'ALL':
                        print(f"    Esto es normal cuando hay nodos apagados, porque")
                        print(f"    ALL necesita que TODOS los nodos respondan.")
                    elif cl_nombre == 'QUORUM':
                        print(f"    Esto pasa cuando hay 2 o mas nodos apagados,")
                        print(f"    porque QUORUM necesita que al menos 2 de 3 respondan.")
                    elif cl_nombre == 'ONE':
                        print(f"    Esto significa que todos los nodos estan caidos")
                        print(f"    o hay un problema de conexion serio.")
                else:
                    print(f"  {cl_nombre}: Funciono sin problemas.")

        # Conclusiones
        print(f"\n  CONCLUSIONES:")
        print(f"  {'─' * 55}")
        print(f"  - ONE es el mas rapido pero el menos seguro en cuanto a")
        print(f"    consistencia. Solo necesita que 1 nodo responda, asi que")
        print(f"    aguanta que se caigan hasta 2 nodos.")
        print(f"  - QUORUM es el balance ideal: necesita que 2 de 3 nodos")
        print(f"    respondan, dando buena consistencia y aguantando la")
        print(f"    caida de 1 nodo.")
        print(f"  - ALL es el mas lento porque espera a que los 3 nodos")
        print(f"    respondan. Si se cae cualquier nodo, las consultas fallan.")
        print(f"  - Para el sistema de reservas, QUORUM es la mejor opcion")
        print(f"    porque ofrece datos confiables sin sacrificar demasiado")
        print(f"    la velocidad, y tolera la caida de 1 nodo sin problemas.")

    finally:
        cluster.shutdown()


if __name__ == '__main__':
    main()
