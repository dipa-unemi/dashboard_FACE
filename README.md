# Dashboard FACE

Dashboard académico de la Facultad de Educación y Ciencias de la Educación (FACE).

**🔗 Ver el dashboard en vivo:** https://dipa-unemi.github.io/dashboard_FACE/docs/index.html

## Estructura

Desde octubre 2026 el tablero sigue la estructura y la metodología del dashboard de
FACSECYD: siete vistas (estudiantes, grupos de interés, cuerpo docente, investigación,
vinculación y servicios de apoyo), las 11 carreras vigentes agrupadas por modalidad.

```
docs/              Dashboard web publicado con GitHub Pages
  index.html         página del tablero
  js/app.js          código del tablero (el mismo de FACSECYD)
  css/tablero.css    estilos
  data/              datos agregados (sin información de personas) que lee el tablero
  img/               logos institucionales
scripts/pipeline/  Proceso que genera docs/data/ a partir de los extractos del SGA
```

- Los datos se regeneran con `py scripts/pipeline/procesar_todo.py` y el tablero en un
  solo archivo, para abrir sin servidor, con `py scripts/pipeline/07_html_local.py`
  (ver `scripts/pipeline/README.md`).
- La revisión de las bases y las decisiones pendientes: `scripts/pipeline/REVISION_BASES.md`.
- La versión anterior (pestaña Docentes: `docs/docentes.html`, `nav.js`, `styles.css` y
  `scripts/agregar_docentes.py`) queda en el repositorio, ya sin enlazar.

## Manejo de los datos fuente

**Este repositorio es público: no guarda ningún extracto del SGA.** Los Excel
(`Result_*_2.xlsx`) y las bases depuradas (`_procesado/`) contienen microdatos
de personas identificables y se quedan fuera de git; `.gitignore` bloquea
`*.xlsx`, `*.xls`, `*.parquet`, `*.csv` y `_procesado/`. El pipeline los busca
fuera del repositorio (ver `scripts/pipeline/README.md`).

Lo que se publica en `docs/data/` son solo agregados: conteos y porcentajes por
carrera y periodo, sin identificadores, con grupos de menos de 10 personas
ocultos y categorías de menos de 5 casos agrupadas. `06_verificar.py` lo
comprueba en cada corrida.

## Clonar

```bash
git clone https://github.com/dipa-unemi/dashboard_FACE.git
```
