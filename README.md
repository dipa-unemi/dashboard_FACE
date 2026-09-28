# Dashboard FACE

Dashboard académico de la Facultad de Educación y Ciencias de la Educación (FACE).

**🔗 Ver el dashboard en vivo:** https://dipa-unemi.github.io/dashboard_FACE/docs/index.html

## Estructura

```
data/      Fuentes de datos en formato Excel (versionadas: este repo es privado)
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

**Este repositorio es privado, y por eso guarda sus Excel de origen en
`data/`.** Es una diferencia deliberada con el repositorio de FACSECYD, que es
público y por tanto nunca los versiona. La idea es que el equipo trabaje sobre
el mismo material sin pasarlo por correo.

Los archivos contienen microdatos de personas identificables. De ahí se
derivan tres reglas que no son opcionales:

1. **El repositorio no puede hacerse público.** El historial de git es
   permanente: cambiar la visibilidad expondría los Excel en todos los commits
   anteriores, no solo en el último. Borrarlos en un commit nuevo no los borra.
2. **GitHub Pages publica en abierto aunque el repositorio sea privado.** Si se
   activa, el tablero queda accesible para cualquiera con el enlace. Eso está
   bien para `docs/`, que solo contiene agregados — pero es una decisión que se
   toma a conciencia, no de paso.
3. **Quien tenga acceso al repositorio puede descargar los microdatos.** La
   lista de colaboradores es, en la práctica, la lista de quién puede ver los
   datos personales de la facultad.

Como salvaguarda, `.gitignore` sigue bloqueando cualquier `.xlsx` o `.xls`
fuera de `data/`, y dentro de `data/` los habilita **uno por uno**: un archivo
nuevo que aparezca ahí no se sube solo, alguien tiene que decidirlo.

Lo que se publica en `docs/` nunca son microdatos: son conteos por combinación
de atributos, y el identificador del docente no llega al archivo publicado.

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
