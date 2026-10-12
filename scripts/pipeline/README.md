# Pipeline de datos del dashboard FACE

Convierte los extractos del SGA en los archivos agregados que lee el tablero
(`docs/data/*.js`), con la misma estructura, indicadores y reglas que el dashboard
de FACSECYD (que a su vez sigue el de FACS).

```
py scripts/pipeline/procesar_todo.py            # todo, de 01 a 06
py scripts/pipeline/procesar_todo.py --desde 2  # reutiliza las bases ya preparadas
py scripts/pipeline/07_html_local.py            # tablero en UN archivo: ../Dashboard_FACE_local.html
```

Requiere Python 3 con `pandas`, `pyarrow` y `python-calamine`:
`py -m pip install pandas pyarrow python-calamine`.

| Paso | Qué hace | Salida |
|---|---|---|
| `01_preparar_bases.py` | Lee los Excel, aplica los filtros y limpia | `_procesado/*.parquet` + `bitacora.json` |
| `02_agregar_indicadores.py` | Satisfacción (estudiantes, docentes, graduados), investigación, vinculación, tutorías y becas | `docs/data/face-data.js` |
| `03_agregar_docentes.py` | Planta, nivel académico, dedicación, evaluación, capacitación, perfil | `docs/data/docentes-data.js` |
| `04_agregar_graduados.py` | Empleabilidad, condiciones del empleo, competencias, cobertura | `docs/data/graduados-data.js` |
| `05_agregar_estudiantes.py` | Trayectoria, perfil sociodemográfico y rendimiento | `trayectoria-`, `perfil-`, `rendimiento-data.js` |
| `06_verificar.py` | Sin identificadores, sin carreras excluidas, umbrales aplicados, cifras que cuadran | resumen por carrera |
| `07_html_local.py` | Empaqueta `docs/` en un solo `.html` para abrir con doble clic | `../Dashboard_FACE_local.html` |

La revisión de las bases que precedió al tablero, con las novedades encontradas y las
decisiones pendientes, está en [`REVISION_BASES.md`](REVISION_BASES.md).

## Dónde están los datos

Los extractos (`Result_*_2.xlsx`) se buscan, en este orden: en la carpeta que indique la
variable `FACE_DATA_DIR`; en `../Base de datos FACE`, al lado del repositorio, si existe;
o en la propia carpeta del repositorio. **Nunca entran a git**: `.gitignore` bloquea
`*.xlsx`, `*.parquet` y `_procesado/`. Las bases depuradas (`_procesado/`) contienen
microdatos y quedan junto a los extractos.

## Criterios que cambian cifras (todos en `comun.py`)

- **Carreras:** 11 vigentes, sin unificar versiones de malla ni modalidades (`CARRERAS`).
  Las licenciaturas en Ciencias de la Educación e Informática y Programación quedan fuera
  por no vigentes (`CARRERAS_NO_VIGENTES`).
- **Asignaturas excluidas:** Inglés VI y VII de General English (mismo criterio que
  FACSECYD; pendiente de confirmar en FACE).
- **Duración de las carreras** (`DURACION_NIVELES`): por confirmar; mientras tanto,
  el nivel más alto observado, con un mínimo de 8.
- **Carga estudiantil del docente:** cada paralelo cuenta una vez por docente aunque el
  distributivo lo repita por componente (teoría, práctica, virtual). Es la única regla
  que difiere de FACSECYD (ver `03_agregar_docentes.py`).
- **Protección de datos:** grupos de menos de 10 personas no se publican; categorías
  de menos de 5 casos se agrupan.
