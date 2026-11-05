# Pipeline de datos del dashboard FACE

Convierte los extractos del SGA en los archivos agregados que lee el tablero
(`docs/data/*.js`), con la misma estructura, indicadores y reglas que el dashboard
de FACSECYD (que a su vez sigue el de FACS).

```
py scripts/pipeline/procesar_todo.py            # todo, de 01 a 06 (con 05b)
py scripts/pipeline/procesar_todo.py --desde 2  # reutiliza las bases ya preparadas
py scripts/pipeline/07_html_local.py            # tablero en UN archivo: ../Dashboard_FACE_local.html
```

Requiere Python 3 con `pandas` 3 o superior, `pyarrow` y `python-calamine`:
`py -m pip install "pandas>=3" pyarrow python-calamine`. Con pandas 2 los pasos 03 y 05
fallan (los textos vacíos se leen como `pd.NA`).

| Paso | Qué hace | Salida |
|---|---|---|
| `01_preparar_bases.py` | Lee los Excel, aplica los filtros y limpia | `_procesado/*.parquet` + `bitacora.json` |
| `02_agregar_indicadores.py` | Satisfacción (estudiantes, docentes, graduados), investigación, vinculación, tutorías y becas | `docs/data/face-data.js` |
| `03_agregar_docentes.py` | Planta, nivel académico, dedicación, evaluación, capacitación, perfil | `docs/data/docentes-data.js` |
| `04_agregar_graduados.py` | Empleabilidad, condiciones del empleo, competencias, cobertura | `docs/data/graduados-data.js` |
| `05_agregar_estudiantes.py` | Trayectoria, perfil sociodemográfico y rendimiento | `trayectoria-`, `perfil-`, `rendimiento-data.js` |
| `05c_informes_sga.py` | Permanencia, deserción, titulación, afinidad docente, producción científica (cinco tipos) y proyectos de investigación con el cálculo de los informes del SGA (FR0087, FR0122, FR0125, FR0108, FR0128, FR0127), a partir de las consultas R02, R16, R19, R11, R23 y R22 | `docs/data/informes-data.js` |
| `05b_proteger.py` | Supresión complementaria: oculta además lo necesario para que ninguna cifra suprimida se deduzca restando | reescribe `docs/data/*.js` (solo quita cifras) |
| `06_verificar.py` | Sin identificadores, sin carreras excluidas, umbrales aplicados, nada deducible por resta, cifras que cuadran | resumen por carrera |
| `07_html_local.py` | Empaqueta `docs/` en un solo `.html` para abrir con doble clic | `../Dashboard_FACE_local.html` |

La revisión de las bases que precedió al tablero, con las novedades encontradas y las
decisiones pendientes, está en [`REVISION_BASES.md`](REVISION_BASES.md).

## Dónde están los datos

Los extractos (`Result_*_2.xlsx`) se buscan, en este orden: en la carpeta que indique la
variable `FACE_DATA_DIR`; en `../Base de datos FACE`, al lado del repositorio, si existe;
o en la propia carpeta del repositorio. **Nunca entran a git**: `.gitignore` bloquea
`*.xlsx`, `*.parquet` y `_procesado/`. Las bases depuradas (`_procesado/`) contienen
microdatos y quedan junto a los extractos.

Esto vale también para el historial: un archivo borrado en un commit posterior sigue
siendo descargable desde los commits anteriores. Si alguna vez se sube uno por error, no
basta con borrarlo en un commit nuevo: avisa antes de seguir trabajando.

## Indicadores de los informes del SGA (paso 05c)

Las consultas que replican los informes del SGA están en `Dashboard_Academico_Perfil/consultas/Consultas_nuevas`
(una por informe, solo FACE). Sus resultados (`R02_permanencia_FACE.xlsx`, `R16_desercion_FACE.xlsx`,
`R19_titulacion_FACE.xlsx`, `R11_afinidad_FACE_CORREGIDO.csv`, `R22_corregido.csv`, `R23_produccion_FACE.xlsx`)
se buscan en la variable `FACE_INFORMES_DIR` o en `<datos>/datas_nuevas`, y tampoco entran a git. El SGA decide
la cohorte, quién deserta o se titula, qué asignatura es afín y qué producto o proyecto es de la carrera; el paso
solo cuenta, trunca las tasas a dos decimales como los informes e imprime un control contra los PDF de Educación 2019.
En el tablero, estos datos reemplazan a la deserción y la titulación del paso 05 y a la producción del paso 02.

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
  de menos de 5 casos se agrupan. Además, `05b_proteger.py` aplica supresión
  complementaria: si el total y todas las categorías menos una están publicados (o la
  modalidad y todas sus carreras menos una, o el año y todos sus momentos de encuesta
  menos uno), oculta también la categoría publicada más pequeña. El Perfil
  sociodemográfico no aplica umbral (decisión de la Dirección).
