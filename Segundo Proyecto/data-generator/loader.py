"""
Aplica el esquema y carga las relaciones contra Neo4j usando el driver
oficial.  Lee los archivos .cypher de /app/schema y los ejecuta uno a
uno separando por sentencia (delimitador `;`).

La carga masiva (LOAD CSV) la ejecuta Neo4j directamente usando los
archivos puestos en /var/lib/neo4j/import (volumen ./data del compose).
"""

import os
import time
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "movies12345")


def _split_statements(script: str) -> list[str]:
    """Divide un script Cypher por ; (ignorando lineas en blanco/comentarios)."""
    stmts = []
    buff = []
    for line in script.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        buff.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(buff).rstrip(";").strip()
            if stmt:
                stmts.append(stmt)
            buff = []
    if buff:
        stmt = "\n".join(buff).strip()
        if stmt:
            stmts.append(stmt)
    return stmts


def _wait_for_neo4j(driver, retries: int = 30, delay: float = 2.0) -> None:
    for i in range(retries):
        try:
            with driver.session() as s:
                s.run("RETURN 1").consume()
            return
        except Exception as e:
            print(f"  Esperando a Neo4j... intento {i+1}/{retries} ({e})")
            time.sleep(delay)
    raise RuntimeError("Neo4j no respondio a tiempo")


def run_script(script_path: str) -> None:
    print(f"Ejecutando script: {script_path}")
    with open(script_path, encoding="utf-8") as f:
        script = f.read()
    statements = _split_statements(script)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    _wait_for_neo4j(driver)
    try:
        with driver.session() as session:
            for i, stmt in enumerate(statements, 1):
                preview = stmt.splitlines()[0][:80]
                print(f"  [{i}/{len(statements)}] {preview} ...")
                session.run(stmt).consume()
        print("Script ejecutado correctamente.")
    finally:
        driver.close()


def load_schema():
    run_script("/app/schema/01_schema.cypher")


def load_data():
    run_script("/app/schema/02_load_data.cypher")


def reset_db():
    """Borra todos los nodos y relaciones (cuidado en produccion)."""
    print("Reseteando base de datos...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    _wait_for_neo4j(driver)
    try:
        with driver.session() as s:
            s.run("MATCH (n) DETACH DELETE n").consume()
        print("Base de datos vacia.")
    finally:
        driver.close()


def stats():
    """Imprime el conteo de nodos y relaciones cargadas."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    _wait_for_neo4j(driver)
    queries = {
        "Usuarios":            "MATCH (n:Usuario)   RETURN count(n) AS c",
        "Peliculas":           "MATCH (n:Pelicula)  RETURN count(n) AS c",
        "Generos":             "MATCH (n:Genero)    RETURN count(n) AS c",
        "Actores":             "MATCH (n:Actor)     RETURN count(n) AS c",
        "Directores":          "MATCH (n:Director)  RETURN count(n) AS c",
        "Rel CALIFICO":        "MATCH ()-[r:CALIFICO]->()    RETURN count(r) AS c",
        "Rel VIO":             "MATCH ()-[r:VIO]->()         RETURN count(r) AS c",
        "Rel ES_AMIGO_DE":     "MATCH ()-[r:ES_AMIGO_DE]->() RETURN count(r) AS c",
        "Rel PERTENECE_A":     "MATCH ()-[r:PERTENECE_A]->() RETURN count(r) AS c",
        "Rel ACTUO_EN":        "MATCH ()-[r:ACTUO_EN]->()    RETURN count(r) AS c",
        "Rel DIRIGIO":         "MATCH ()-[r:DIRIGIO]->()     RETURN count(r) AS c",
        "Rel LE_GUSTA":        "MATCH ()-[r:LE_GUSTA]->()    RETURN count(r) AS c",
    }
    print("Conteos en la base de datos:")
    try:
        with driver.session() as s:
            for label, q in queries.items():
                c = s.run(q).single()["c"]
                print(f"  {label:<20} {c}")
    finally:
        driver.close()
