"""
ReservaDB - Script de Carga Masiva de Datos
Genera usuarios, espacios y al menos 100,000 reservas utilizando Batch Writes.
Utiliza la libreria Faker para generar datos realistas y cassandra-driver
para la conexion y carga al cluster.
"""

import uuid
import random
import time
import sys
from datetime import date, timedelta, time as dt_time

from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, ConsistencyLevel
from faker import Faker

# Semilla para reproducibilidad
random.seed(42)
fake = Faker('es_MX')
Faker.seed(42)

# ============================================================
# PARAMETROS DE CONFIGURACION
# ============================================================
CASSANDRA_HOSTS = ['127.0.0.1']
CASSANDRA_PORT = 9042
KEYSPACE = 'reserva_db'

NUM_USUARIOS = 500
NUM_ESPACIOS = 50
NUM_RESERVAS = 100000
BATCH_SIZE = 5  # Reservas por batch (cada una inserta en 3 tablas = 15 statements)

# Datos para generacion de espacios
TIPOS_ESPACIO = ['sala_conferencia', 'escritorio', 'auditorio']
UBICACIONES = [
    'Edificio A - Nivel 1', 'Edificio A - Nivel 2', 'Edificio A - Nivel 3',
    'Edificio B - Nivel 1', 'Edificio B - Nivel 2',
    'Edificio C - Nivel 1', 'Edificio C - Nivel 2', 'Edificio C - Nivel 3',
    'Torre Norte - Nivel 1', 'Torre Norte - Nivel 2',
    'Torre Sur - Nivel 1', 'Torre Sur - Nivel 2'
]

# Estados posibles de una reserva
ESTADOS_RESERVA = ['confirmada', 'pendiente', 'cancelada', 'completada']

# Horarios disponibles: de 7:00 a 21:00 en bloques de 1 hora
HORAS_DISPONIBLES = [dt_time(h, 0) for h in range(7, 21)]
DURACIONES_HORAS = [1, 2, 3]  # Duracion posible en horas

# Rango de fechas para las reservas generadas
FECHA_INICIO = date(2025, 1, 1)
FECHA_FIN = date(2026, 6, 30)
DIAS_RANGO = (FECHA_FIN - FECHA_INICIO).days


def conectar_cluster():
    """Establece la conexion con el cluster de Cassandra."""
    print("Conectando al cluster de Cassandra...")
    try:
        cluster = Cluster(CASSANDRA_HOSTS, port=CASSANDRA_PORT,
                          connect_timeout=30)
        session = cluster.connect(KEYSPACE)
        session.default_consistency_level = ConsistencyLevel.QUORUM
        print("Conexion establecida correctamente.")
        return cluster, session
    except Exception as e:
        print(f"Error al conectar con el cluster: {e}")
        sys.exit(1)


def generar_usuarios(session):
    """Genera y carga los usuarios en la tabla correspondiente."""
    usuarios = []

    insert_stmt = session.prepare(
        "INSERT INTO usuarios (usuario_id, nombre, email, dpi, telefono, nit) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )

    print(f"Generando {NUM_USUARIOS} usuarios...")

    for i in range(NUM_USUARIOS):
        uid = uuid.uuid4()
        nombre = fake.name()
        email = fake.email()
        dpi = fake.numerify('#############')   # 13 digitos, formato DPI Guatemala
        telefono = fake.numerify('########')   # 8 digitos
        # 70% tienen NIT, 30% son CF (consumidor final)
        nit = fake.numerify('#######') + '-' + str(random.randint(0, 9)) if random.random() > 0.3 else 'CF'

        session.execute(insert_stmt, (uid, nombre, email, dpi, telefono, nit))
        usuarios.append({'id': uid, 'nombre': nombre})

        if (i + 1) % 100 == 0:
            print(f"  Usuarios insertados: {i + 1}/{NUM_USUARIOS}")

    print(f"  Total usuarios cargados: {len(usuarios)}")
    return usuarios


def generar_espacios(session):
    """Genera y carga los espacios en la tabla correspondiente."""
    espacios = []

    insert_stmt = session.prepare(
        "INSERT INTO espacios (espacio_id, nombre, tipo, capacidad_maxima, ubicacion) "
        "VALUES (?, ?, ?, ?, ?)"
    )

    # Definir los espacios del sistema de coworking
    lista_espacios = []

    # 20 salas de conferencia con capacidad de 5 a 20 personas
    for i in range(20):
        lista_espacios.append({
            'nombre': f'Sala {chr(65 + i)}',
            'tipo': 'sala_conferencia',
            'capacidad': random.randint(5, 20)
        })

    # 20 escritorios individuales o compartidos con capacidad de 1 a 4
    for i in range(20):
        lista_espacios.append({
            'nombre': f'Escritorio {i + 1}',
            'tipo': 'escritorio',
            'capacidad': random.randint(1, 4)
        })

    # 10 auditorios con capacidad de 30 a 100 personas
    for i in range(10):
        lista_espacios.append({
            'nombre': f'Auditorio {i + 1}',
            'tipo': 'auditorio',
            'capacidad': random.randint(30, 100)
        })

    print(f"Generando {len(lista_espacios)} espacios...")

    for esp in lista_espacios:
        eid = uuid.uuid4()
        ubicacion = random.choice(UBICACIONES)

        session.execute(insert_stmt, (
            eid, esp['nombre'], esp['tipo'], esp['capacidad'], ubicacion
        ))
        espacios.append({'id': eid, 'nombre': esp['nombre']})

    print(f"  Total espacios cargados: {len(espacios)}")
    return espacios


def generar_reservas(session, usuarios, espacios):
    """
    Genera al menos 100,000 reservas y las inserta en las 3 tablas
    denormalizadas utilizando Batch Writes.
    Cada batch agrupa las inserciones de varias reservas para optimizar
    la comunicacion con el cluster.
    """

    # Prepared statements para cada tabla denormalizada
    insert_espacio_fecha = session.prepare(
        "INSERT INTO reservas_por_espacio_fecha "
        "(espacio_id, fecha, hora_inicio, reserva_id, hora_fin, "
        "usuario_id, usuario_nombre, espacio_nombre, estado) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )

    insert_usuario = session.prepare(
        "INSERT INTO reservas_por_usuario "
        "(usuario_id, fecha, hora_inicio, reserva_id, hora_fin, "
        "espacio_id, espacio_nombre, usuario_nombre, estado) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )

    insert_ocupacion = session.prepare(
        "INSERT INTO ocupacion_por_espacio_rango "
        "(espacio_id, fecha, hora_inicio, reserva_id, hora_fin, "
        "usuario_id, usuario_nombre, espacio_nombre, estado) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )

    print(f"Generando {NUM_RESERVAS} reservas con Batch Writes...")
    print(f"  Tamano de batch: {BATCH_SIZE} reservas ({BATCH_SIZE * 3} statements por batch)")

    inicio_total = time.time()
    batch = BatchStatement(consistency_level=ConsistencyLevel.QUORUM)
    reservas_en_batch = 0
    batches_ejecutados = 0

    for i in range(NUM_RESERVAS):
        reserva_id = uuid.uuid4()
        usuario = random.choice(usuarios)
        espacio = random.choice(espacios)

        # Generar fecha aleatoria dentro del rango definido
        dias_offset = random.randint(0, DIAS_RANGO)
        fecha = FECHA_INICIO + timedelta(days=dias_offset)

        # Generar horario de la reserva
        hora_inicio = random.choice(HORAS_DISPONIBLES)
        duracion = random.choice(DURACIONES_HORAS)
        hora_fin_h = min(hora_inicio.hour + duracion, 22)
        hora_fin = dt_time(hora_fin_h, 0)

        # Asignar estado de la reserva
        estado = random.choice(ESTADOS_RESERVA)

        # Insertar en tabla Q1: reservas_por_espacio_fecha
        batch.add(insert_espacio_fecha, (
            espacio['id'], fecha, hora_inicio, reserva_id, hora_fin,
            usuario['id'], usuario['nombre'], espacio['nombre'], estado
        ))

        # Insertar en tabla Q2: reservas_por_usuario
        batch.add(insert_usuario, (
            usuario['id'], fecha, hora_inicio, reserva_id, hora_fin,
            espacio['id'], espacio['nombre'], usuario['nombre'], estado
        ))

        # Insertar en tabla Q3: ocupacion_por_espacio_rango
        batch.add(insert_ocupacion, (
            espacio['id'], fecha, hora_inicio, reserva_id, hora_fin,
            usuario['id'], usuario['nombre'], espacio['nombre'], estado
        ))

        reservas_en_batch += 1

        # Ejecutar batch cuando se alcanza el tamano definido
        if reservas_en_batch >= BATCH_SIZE:
            session.execute(batch)
            batch = BatchStatement(consistency_level=ConsistencyLevel.QUORUM)
            batches_ejecutados += 1
            reservas_en_batch = 0

        # Reporte de progreso cada 5,000 reservas
        if (i + 1) % 5000 == 0:
            transcurrido = time.time() - inicio_total
            velocidad = (i + 1) / transcurrido
            print(f"  Reservas insertadas: {i + 1:>7}/{NUM_RESERVAS} "
                  f"| {velocidad:>6.0f} reservas/seg "
                  f"| Batches ejecutados: {batches_ejecutados}")

    # Ejecutar el batch final si quedan reservas pendientes
    if reservas_en_batch > 0:
        session.execute(batch)
        batches_ejecutados += 1

    tiempo_total = time.time() - inicio_total
    velocidad_promedio = NUM_RESERVAS / tiempo_total

    print(f"\n  Carga completada exitosamente:")
    print(f"    Reservas insertadas:  {NUM_RESERVAS:,}")
    print(f"    Batches ejecutados:   {batches_ejecutados:,}")
    print(f"    Tiempo total:         {tiempo_total:.1f} segundos")
    print(f"    Velocidad promedio:   {velocidad_promedio:.0f} reservas/segundo")


def verificar_carga(session):
    """Verifica la cantidad de registros en cada tabla despues de la carga."""
    print("\nVerificando integridad de la carga...")

    tablas = [
        'usuarios', 'espacios',
        'reservas_por_espacio_fecha',
        'reservas_por_usuario',
        'ocupacion_por_espacio_rango'
    ]

    for tabla in tablas:
        rows = session.execute(f"SELECT COUNT(*) as total FROM {tabla}")
        total = rows.one().total
        print(f"  {tabla}: {total:,} registros")


def main():
    print("=" * 65)
    print("  RESERVADB - CARGA MASIVA DE DATOS")
    print("  Sistema Distribuido de Gestion de Espacios Compartidos")
    print("=" * 65)

    cluster, session = conectar_cluster()

    try:
        print("\n[FASE 1/4] Generando usuarios...")
        print("-" * 40)
        usuarios = generar_usuarios(session)

        print("\n[FASE 2/4] Generando espacios...")
        print("-" * 40)
        espacios = generar_espacios(session)

        print("\n[FASE 3/4] Carga masiva de reservas...")
        print("-" * 40)
        generar_reservas(session, usuarios, espacios)

        print("\n[FASE 4/4] Verificacion de datos...")
        print("-" * 40)
        verificar_carga(session)

        print("\n" + "=" * 65)
        print("  CARGA MASIVA FINALIZADA EXITOSAMENTE")
        print("=" * 65)

    finally:
        cluster.shutdown()


if __name__ == '__main__':
    main()
