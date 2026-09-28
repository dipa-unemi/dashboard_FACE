# Dashboard FACE

Dashboard académico de la Facultad de Educación y Ciencias de la Educación (FACE).

**🔗 Ver el dashboard en vivo:** https://dipa-unemi.github.io/dashboard_FACE/docs/index.html

## Estructura

```
data/      Fuentes de datos en formato Excel (privadas, fuera del repositorio)
scripts/   Agregación para el tablero
docs/      Dashboard web (HTML/CSS/JS), publicado con GitHub Pages
```

## Pestañas

| Pestaña | Qué responde | Archivo | Estado |
|---|---|---|---|
| Docentes | Quién enseña en la facultad | `docs/docentes.html` | Publicada |
| Seguimiento a Graduados | Dónde termina el estudiante después de titularse | — | Pendiente |

**Seguimiento a Graduados todavía no está.** El módulo necesita cruzar la
encuesta con la base de estudiantes de la facultad para traer sexo, etnia,
grupo socioeconómico, edad de ingreso y cohorte, y para tener el universo de
titulados que sirve de denominador a la tasa de respuesta. Esa base aún no
está disponible para FACE, así que el módulo queda para una segunda etapa en
vez de publicarse con seis de sus nueve dimensiones vacías.

## Manejo de los datos fuente

**Los archivos de origen nunca entran al repositorio.** Contienen microdatos
de personas identificables. Viven solo en la carpeta local `data/`, que está
excluida por `.gitignore`, y se comparten por los canales internos de la
facultad, no por GitHub.

Esto vale también para el historial: un archivo borrado en un commit
posterior sigue siendo descargable desde los commits anteriores. Si alguna
vez se sube uno por error, no basta con borrarlo en un commit nuevo — avisa
antes de seguir trabajando.

Como salvaguarda, `.gitignore` bloquea `data/` y cualquier `.xlsx` o `.xls`
en todo el repositorio.

## Cómo se alimenta la pestaña de Docentes

```bash
python scripts/agregar_docentes.py
```

El script lee `data/data_docente.xlsx` y reescribe el bloque de datos dentro
de `docs/docentes.html`. El tablero es un único archivo autocontenido, así que
volver a correrlo reemplaza el bloque anterior sin tocar nada más.

Lo que se publica son **conteos por combinación de atributos**, no registros de
personas: el identificador del docente se usa para contar personas distintas y
no llega al archivo publicado.

### Criterios que aplica el script

| Regla | Por qué |
|---|---|
| Las grafías de una carrera se unifican quitando tildes | La misma carrera aparece con y sin tilde en el distributivo; sin esto abriría dos barras en el gráfico |
| Los tramos de edad arrancan en 20 años | Cuatro docentes tienen la edad registrada como 2, 3 o 4 años (error de captura); caen en «SIN REGISTRO» |
| La discapacidad se publica como sí/no | El tipo concreto solo aparece en el perfil agregado del periodo vigente |
| Las categorías con menos de 10 docentes se agrupan en el perfil del periodo vigente | Con ~180 docentes, publicar «INDÍGENA: 2» del semestre en curso señala a una persona concreta |
| Las filas sin identificador de docente se conservan | Son asignaciones reales; descartarlas cambiaría el total de la facultad |

El script verifica en cada corrida que los cuatro grupos agregados sumen
exactamente las asignaciones y los cupos de estudiante del archivo fuente.

### Procedencia del script

El generador de esta pestaña no quedó versionado en el repositorio de
FACSECYD, así que se reconstruyó a partir del tablero ya publicado. La
reconstrucción reproduce sus 5.798 filas agregadas sin una sola diferencia, de
modo que las dos facultades se leen con el mismo criterio.

## Clonar

```bash
git clone https://github.com/dipa-unemi/dashboard_FACE.git
```
