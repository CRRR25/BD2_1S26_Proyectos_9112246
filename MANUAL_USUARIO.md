# Manual de Usuario — Ruta Más Corta Entre Ciudades

## 1. Introducción

Este sistema permite encontrar la **ruta más corta** entre dos ciudades de una
red de transporte interdepartamental. El motor de razonamiento está
implementado en **Prolog** y la aplicación se utiliza desde un navegador web a
través de una interfaz gráfica sencilla e intuitiva.

Con la aplicación usted puede:

- Consultar la ruta más corta entre una ciudad de origen y una de destino.
- Visualizar **todas las rutas posibles** ordenadas de menor a mayor distancia.
- Agregar nuevas ciudades a la base de conocimiento.
- Agregar nuevas conexiones (carreteras) entre ciudades.
- Consultar la tabla de conexiones registradas.

## 2. Requisitos previos

Antes de ejecutar el sistema debe tener instalado:

- **SWI-Prolog** (https://www.swi-prolog.org)
- **Python 3.11 o superior**
- Un **navegador web** actualizado

## 3. Instalación

1. Clonar el repositorio:

   ```bash
   git clone <url-del-repositorio>
   cd "[IA1]_VACASJUN2026_Carlos-Rangell_9112246"
   ```

2. Crear y activar un entorno virtual (recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate        # Linux / macOS
   venv\Scripts\activate           # Windows
   ```

3. Instalar las dependencias del backend:

   ```bash
   pip install -r backend/requirements.txt
   ```

## 4. Ejecución

Desde la carpeta `backend` ejecute:

```bash
cd backend
python run.py
```

Cuando el servidor inicie verá un mensaje indicando que está disponible en:

```
http://localhost:8000
```

Abra esa dirección en su navegador para usar la aplicación.

## 5. Uso del sistema

### 5.1 Consultar la ruta más corta

1. Seleccione la **ciudad de origen** en la primera lista desplegable.
2. Seleccione la **ciudad de destino** en la segunda lista desplegable.
3. Presione el botón **Ruta más corta**.
4. En la sección *Resultados* se mostrará la ruta recomendada (resaltada) junto
   con la **distancia total** recorrida.

### 5.2 Ver todas las rutas posibles

1. Seleccione origen y destino.
2. Presione el botón **Todas las rutas**.
3. Se mostrarán todas las rutas posibles, **ordenadas de menor a mayor
   distancia**. La primera aparece marcada como *Más corta*.

### 5.3 Limpiar la búsqueda

Presione el botón **Limpiar** para borrar los resultados de la pantalla.

### 5.4 Agregar una ciudad

1. En la sección *Administrar base de conocimiento*, escriba el nombre de la
   ciudad en el campo **Nombre de la ciudad**.
2. Presione **Agregar**.
3. La nueva ciudad quedará disponible en todas las listas desplegables.

### 5.5 Agregar una conexión

1. Seleccione la ciudad de **Origen** y la de **Destino**.
2. Ingrese la **Distancia (km)**.
3. Presione **Agregar**.
4. La nueva conexión aparecerá en la tabla *Conexiones registradas* y podrá
   utilizarse de inmediato en las búsquedas de rutas.

## 6. Mensajes del sistema

El sistema valida la información ingresada y muestra mensajes claros, por
ejemplo:

- *"La ciudad 'x' no existe en la base de conocimiento."*
- *"No existe una ruta disponible entre 'a' y 'b'."*
- *"La ciudad de origen y destino deben ser diferentes."*
- *"La distancia debe ser un valor positivo."*

## 7. Notas importantes

- Las ciudades y conexiones agregadas durante la ejecución se mantienen
  mientras el servidor esté encendido. Al reiniciarlo, la base vuelve a su
  estado inicial definido en el archivo `prolog/rutas.pl`.
- El sistema **no utiliza bases de datos**; todo el conocimiento reside en
  Prolog.
