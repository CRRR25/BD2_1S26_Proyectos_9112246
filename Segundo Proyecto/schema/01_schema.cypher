// =====================================================================
// Schema: constraints e indices para el sistema de recomendacion
// =====================================================================

// --- Unicidad por identificador natural ---
CREATE CONSTRAINT usuario_id_unique IF NOT EXISTS
FOR (u:Usuario) REQUIRE u.id IS UNIQUE;

CREATE CONSTRAINT pelicula_id_unique IF NOT EXISTS
FOR (p:Pelicula) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT genero_nombre_unique IF NOT EXISTS
FOR (g:Genero) REQUIRE g.nombre IS UNIQUE;

CREATE CONSTRAINT actor_id_unique IF NOT EXISTS
FOR (a:Actor) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT director_id_unique IF NOT EXISTS
FOR (d:Director) REQUIRE d.id IS UNIQUE;

// --- Indices auxiliares para filtrado y ordenamiento ---
CREATE INDEX usuario_email IF NOT EXISTS
FOR (u:Usuario) ON (u.email);

CREATE INDEX pelicula_titulo IF NOT EXISTS
FOR (p:Pelicula) ON (p.titulo);

CREATE INDEX pelicula_anio IF NOT EXISTS
FOR (p:Pelicula) ON (p.anio);
