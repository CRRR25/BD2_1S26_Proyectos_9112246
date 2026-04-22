"""
Genera los archivos CSV con datos sinteticos para el sistema de
recomendacion de peliculas en Neo4j.

Cantidades minimas (ver enunciado):
  - 500 usuarios
  - 200 peliculas
  - 100 actores
  -  50 directores
  -  15 generos

Las relaciones se generan respetando las reglas de negocio:
  - calificacion en [1, 5]
  - una pelicula no puede tener al mismo actor en el mismo personaje
    mas de una vez
  - amistad bidireccional (se almacena un solo registro por pareja)
"""

import csv
import os
import random
from datetime import date, timedelta
from faker import Faker

faker = Faker("es_ES")
Faker.seed(42)
random.seed(42)

NUM_USUARIOS = 500
NUM_PELICULAS = 200
NUM_ACTORES = 100
NUM_DIRECTORES = 50

GENEROS = [
    ("Accion",      "Peliculas con secuencias de alta intensidad y persecuciones"),
    ("Aventura",    "Viajes, descubrimientos y exploracion"),
    ("Comedia",     "Peliculas con tono humoristico"),
    ("Drama",       "Conflictos emocionales y desarrollo de personajes"),
    ("Terror",      "Pretende provocar miedo o tension"),
    ("Romance",     "Centradas en relaciones amorosas"),
    ("Ciencia Ficcion", "Tecnologia, ciencia y futurismo"),
    ("Fantasia",    "Mundos imaginarios y elementos magicos"),
    ("Thriller",    "Suspenso y giros inesperados"),
    ("Documental",  "Temas reales con enfoque informativo"),
    ("Animacion",   "Hechas con tecnicas de animacion"),
    ("Misterio",    "Resolucion de enigmas y crimenes"),
    ("Crimen",      "Sobre el mundo del delito"),
    ("Historico",   "Ambientadas en hechos del pasado"),
    ("Musical",     "La musica es parte central del relato"),
]

PAISES = [
    "Guatemala", "Mexico", "Estados Unidos", "Espana", "Argentina",
    "Colombia", "Chile", "Peru", "Brasil", "Canada", "Reino Unido",
    "Francia", "Alemania", "Italia", "Japon", "Corea del Sur",
]

NACIONALIDADES = PAISES + ["Australia", "India", "Suecia", "Irlanda"]

PERSONAJES = [
    "Protagonista", "Antagonista", "Mejor Amigo", "Mentor", "Interes Romantico",
    "Hermano", "Hermana", "Padre", "Madre", "Companero",
    "Detective", "Cientifico", "Soldado", "Mago", "Heroe Secundario",
    "Villano Secundario", "Doctor", "Profesor", "Capitan", "Reportero",
]

PALABRAS_TITULO = [
    "Sombras", "Estrellas", "Eternidad", "Reino", "Verdad", "Olvido",
    "Memoria", "Tormenta", "Camino", "Silencio", "Cielo", "Promesa",
    "Codigo", "Origen", "Destino", "Amanecer", "Crepusculo", "Imperio",
    "Leyenda", "Secreto", "Ultimo", "Primera", "Caza", "Refugio",
]


def random_date(start_year: int, end_year: int) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def write_csv(path: str, header: list[str], rows: list[list]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  -> {path} ({len(rows)} filas)")


def gen_generos(out_dir: str):
    rows = [[nombre, desc] for nombre, desc in GENEROS]
    write_csv(os.path.join(out_dir, "generos.csv"),
              ["nombre", "descripcion"], rows)


def gen_usuarios(out_dir: str) -> list[int]:
    rows = []
    ids = []
    seen_emails = set()
    for i in range(1, NUM_USUARIOS + 1):
        nombre = faker.name()
        email = f"user{i}@" + faker.free_email_domain()
        while email in seen_emails:
            email = f"user{i}.{random.randint(1,9999)}@" + faker.free_email_domain()
        seen_emails.add(email)
        edad = random.randint(15, 75)
        pais = random.choice(PAISES)
        rows.append([i, nombre, email, edad, pais])
        ids.append(i)
    write_csv(os.path.join(out_dir, "usuarios.csv"),
              ["id", "nombre", "email", "edad", "pais"], rows)
    return ids


def gen_peliculas(out_dir: str) -> list[int]:
    rows = []
    ids = []
    for i in range(1, NUM_PELICULAS + 1):
        titulo = f"{random.choice(PALABRAS_TITULO)} {random.choice(PALABRAS_TITULO)}"
        if random.random() < 0.3:
            titulo += f" {random.choice(['I','II','III','del Tiempo','Final'])}"
        anio = random.randint(1970, 2024)
        duracion = random.randint(80, 200)
        sinopsis = faker.paragraph(nb_sentences=2).replace("\n", " ").replace('"', "'")
        rows.append([i, titulo, anio, duracion, sinopsis])
        ids.append(i)
    write_csv(os.path.join(out_dir, "peliculas.csv"),
              ["id", "titulo", "anio", "duracion", "sinopsis"], rows)
    return ids


def gen_actores(out_dir: str) -> list[int]:
    rows = []
    ids = []
    for i in range(1, NUM_ACTORES + 1):
        nombre = faker.name()
        fnac = random_date(1940, 2000).isoformat()
        nac = random.choice(NACIONALIDADES)
        rows.append([i, nombre, fnac, nac])
        ids.append(i)
    write_csv(os.path.join(out_dir, "actores.csv"),
              ["id", "nombre", "fechaNacimiento", "nacionalidad"], rows)
    return ids


def gen_directores(out_dir: str) -> list[int]:
    rows = []
    ids = []
    for i in range(1, NUM_DIRECTORES + 1):
        nombre = faker.name()
        fnac = random_date(1935, 1995).isoformat()
        nac = random.choice(NACIONALIDADES)
        rows.append([i, nombre, fnac, nac])
        ids.append(i)
    write_csv(os.path.join(out_dir, "directores.csv"),
              ["id", "nombre", "fechaNacimiento", "nacionalidad"], rows)
    return ids


def gen_pelicula_genero(out_dir: str, peliculas: list[int]):
    nombres = [g[0] for g in GENEROS]
    rows = []
    for pid in peliculas:
        # cada pelicula tiene entre 1 y 3 generos distintos
        k = random.randint(1, 3)
        for g in random.sample(nombres, k):
            rows.append([pid, g])
    write_csv(os.path.join(out_dir, "pelicula_genero.csv"),
              ["peliculaId", "genero"], rows)


def gen_director_pelicula(out_dir: str, directores: list[int],
                          peliculas: list[int]):
    rows = []
    # cada pelicula es dirigida por exactamente un director
    for pid in peliculas:
        did = random.choice(directores)
        rows.append([did, pid])
    write_csv(os.path.join(out_dir, "director_pelicula.csv"),
              ["directorId", "peliculaId"], rows)


def gen_actor_pelicula(out_dir: str, actores: list[int],
                       peliculas: list[int]):
    rows = []
    for pid in peliculas:
        # 3 a 8 actores por pelicula
        k = random.randint(3, 8)
        for aid in random.sample(actores, k):
            personaje = random.choice(PERSONAJES)
            # garantizar (actor, pelicula, personaje) unico
            rows.append([aid, pid, personaje])
    # quitar duplicados exactos
    seen = set()
    unique = []
    for r in rows:
        key = (r[0], r[1], r[2])
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)
    write_csv(os.path.join(out_dir, "actor_pelicula.csv"),
              ["actorId", "peliculaId", "personaje"], unique)


def gen_usuario_genero(out_dir: str, usuarios: list[int]):
    nombres = [g[0] for g in GENEROS]
    rows = []
    for uid in usuarios:
        k = random.randint(2, 5)
        for g in random.sample(nombres, k):
            nivel = random.randint(1, 5)
            rows.append([uid, g, nivel])
    write_csv(os.path.join(out_dir, "usuario_genero.csv"),
              ["usuarioId", "genero", "nivelInteres"], rows)


def gen_amistades(out_dir: str, usuarios: list[int]):
    rows = []
    seen = set()
    # promedio ~6 amistades por usuario -> ~3000 aristas
    target = NUM_USUARIOS * 3
    while len(rows) < target:
        a, b = random.sample(usuarios, 2)
        if a == b:
            continue
        key = tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        fecha = random_date(2018, 2024).isoformat()
        rows.append([key[0], key[1], fecha])
    write_csv(os.path.join(out_dir, "amistades.csv"),
              ["usuario1Id", "usuario2Id", "fechaAmistad"], rows)


def gen_vio_y_califico(out_dir: str, usuarios: list[int],
                       peliculas: list[int]):
    vio_rows = []
    cal_rows = []
    seen_vio = set()
    seen_cal = set()
    # cada usuario ve entre 5 y 25 peliculas
    for uid in usuarios:
        k = random.randint(5, 25)
        for pid in random.sample(peliculas, k):
            if (uid, pid) in seen_vio:
                continue
            seen_vio.add((uid, pid))
            fecha_vis = random_date(2022, 2024).isoformat()
            completo = random.random() < 0.85
            vio_rows.append([uid, pid, fecha_vis, str(completo).lower()])
            # si la vio completa, hay 70% de probabilidad de que la califique
            if completo and random.random() < 0.7 and (uid, pid) not in seen_cal:
                seen_cal.add((uid, pid))
                punt = random.randint(1, 5)
                fecha_cal = fecha_vis
                comentario = faker.sentence(nb_words=8).replace('"', "'")
                cal_rows.append([uid, pid, punt, fecha_cal, comentario])
    write_csv(os.path.join(out_dir, "vio.csv"),
              ["usuarioId", "peliculaId", "fechaVisualizacion", "completo"],
              vio_rows)
    write_csv(os.path.join(out_dir, "califico.csv"),
              ["usuarioId", "peliculaId", "puntuacion", "fecha", "comentario"],
              cal_rows)


def generate_all(out_dir: str = "/app/data") -> None:
    print(f"Generando CSVs en: {out_dir}")
    gen_generos(out_dir)
    usuarios = gen_usuarios(out_dir)
    peliculas = gen_peliculas(out_dir)
    actores = gen_actores(out_dir)
    directores = gen_directores(out_dir)
    gen_pelicula_genero(out_dir, peliculas)
    gen_director_pelicula(out_dir, directores, peliculas)
    gen_actor_pelicula(out_dir, actores, peliculas)
    gen_usuario_genero(out_dir, usuarios)
    gen_amistades(out_dir, usuarios)
    gen_vio_y_califico(out_dir, usuarios, peliculas)
    print("Generacion de CSVs completada.")
