# Revisión de las bases de FACE (extractos del SGA, octubre 2026)

Revisión previa a la construcción del dashboard. Solo conteos agregados: ningún
identificador. Cifras de los extractos `Result_*_2.xlsx` del 2026-10-12.

## Veredicto

Las bases están **completas y consistentes** para construir el tablero. No se encontró
nada que impida publicar. Hay novedades menores, ya tratadas por el pipeline o sin efecto
en los indicadores, y **cuatro decisiones que debe confirmar la Dirección** (al final).

## Cobertura

| Base | Filas | Periodos | Observación |
|---|---:|---|---|
| Estudiantes | 796.294 | 1S-2021 a 1S-2026 (11) | **Completa**: bajo el límite de filas de Excel (1.048.575), no es provisional |
| Distributivo docente | 15.303 | 11 | Docentes por periodo idénticos a `Indicadores_Docentes_FACE` (script R) en los 11 periodos |
| Desempeño docente | 2.699 | 11 | |
| Tutorías | 238.050 | 11 | |
| Becas | 14.678 | 11 | |
| Producción científica | 2.346 | años 2021 a 2026 | 1.384 artículos únicos |
| Vinculación | 343 | proyectos desde 2012 | 197 proyectos únicos |
| Satisfacción estudiantil | 335.677 | 1S-2025, 2S-2025, 1S-2026 | Los 11 servicios que usa el tablero están presentes |
| Satisfacción docente | 978 | solo 1S-2026 | 153 docentes |
| Seguimiento a graduados | 264.151 | encuestas 2017 a 2026 | 99,7 % de las encuestas cruzan con un titulado de la base de estudiantes |

El periodo remedial que FACSECYD excluye (ABRIL- MAYO 2021) **no aparece** en FACE: su
1S-2021 es el semestre regular MAYO A SEPTIEMBRE 2021.

## Catálogo de carreras (11 vigentes)

| Modalidad | Carreras |
|---|---|
| En línea | Educación Básica · Educación Inicial · Pedagogía de los Idiomas Nacionales y Extranjeros |
| Presencial | Educación (Extensión Daule) · Educación 2019 · Educación Especial · Pedagogía de la Actividad Física y Deporte 2019 · Pedagogía de la Lengua y la Literatura · Pedagogía de los Idiomas Nacionales y Extranjeros 2019 |
| Semipresencial | Educación Inicial 2019 · Pedagogía de las Ciencias Experimentales |

Quedan fuera, por no vigentes, las licenciaturas en Ciencias de la Educación (menciones
Educación Básica, Inicial, Cultura Física, Educadores de Párvulos) e Informática y
Programación. Pesan poco en las bases académicas (293 filas de estudiantes) pero mucho en
graduados (60.729 respuestas, casi todas de encuestas 2017–2022) y en vinculación (162 de
343 filas).

## Novedades encontradas y cómo se tratan

| # | Base | Novedad | Tratamiento |
|---|---|---|---|
| 1 | Estudiantes | Inglés VI y VII (General English), Educación Básica e Inicial en línea, 2024: 6.685 registros; traen 82 de los 88 casos de asignatura registrada dos veces en el periodo | Se excluyen, como en FACSECYD. Deja fuera 41 matrículas que solo tenían esa asignatura en el periodo. **Confirmar** |
| 2 | Estudiantes | 6 casos más de asignatura registrada dos veces (2S-2023 y 1S-2023) | Sin archivo de decisión: se dejan las dos filas (efecto despreciable) |
| 3 | Estudiantes | 2 filas duplicadas exactas | Se eliminan |
| 4 | Estudiantes | 2 inscripciones de Educación Inicial 2019 registradas como PRESENCIAL (la carrera es semipresencial) | Se conservan en su carrera; el paso 01 lo informa |
| 5 | Estudiantes | Edad de ingreso imposible (−5 a 1 año, o 14) en 46 inscripciones | Van a «Sin dato válido» en el perfil |
| 6 | Estudiantes | 3 notas de 101 (1S-2026) y 27 asistencias de hasta 105 % (2S-2021) | Se dejan; en los histogramas caen en la banda 95–100. Efecto en promedios < 0,01 |
| 7 | Estudiantes | 169 asignaturas «EN CURSO» en periodos ya cerrados (sobre todo Idiomas en línea 1S-2021) | No son evaluaciones válidas: no entran en el rendimiento |
| 8 | Estudiantes | 125 REPROBADO con nota ≥ 70 | No es error: todas tienen asistencia bajo el mínimo (presencial y semipresencial) |
| 9 | Estudiantes | 1.684 titulados con fecha de agosto–septiembre 2026 (código 2S-2026, posterior al último periodo de la base) | Correcto: cuentan en los titulados de 2026 (año parcial) |
| 10 | Distributivo | El mismo docente aparece 2–3 veces en el mismo paralelo (TEORÍA + VIRTUAL, PRÁCTICA + TEORÍA…) con el mismo total de estudiantes: 2.449 paralelos | **Cambio frente a FACSECYD**: la carga estudiantil cuenta cada paralelo una vez por docente (si no, duplicaría estudiantes). FACSECYD podría tener el mismo efecto |
| 11 | Distributivo | Edad docente de 2, 3 o 4 años (174 filas) | «Sin dato válido» (ya documentado en el README) |
| 12 | Distributivo | 2 asignaciones sin docente | Se conservan; no cuentan como docente |
| 13 | Desempeño | La escala cambia en 2025: el promedio baja de ~4,8 a ~4,1 | Mismo umbral que FACSECYD (4,0); el tablero ya avisa «nueva escala desde 2025». El % satisfactorio cae de forma artificial |
| 14 | Tutorías | 1.301 duplicados exactos | Se eliminan |
| 15 | Tutorías | Fechas de tutoría con año 0203 o 2011 (19) y 9.959 sin fecha (solicitudes) | Sin efecto: los indicadores usan estado y asistencia, no la fecha |
| 16 | Graduados | 5.147 duplicados exactos y 4 respuestas contradictorias (2 graduados) | Se eliminan |
| 17 | Satisfacción est. | 470 respuestas repetidas (persona, periodo, pregunta) | Cuenta la última |
| 18 | Estudiantes | Países sin código de mapa (Emiratos Árabes Unidos, Camboya, Irán, Ucrania) | Agregados al catálogo de países |

## Decisiones pendientes de la Dirección de FACE

1. **Inglés VI y VII** (novedad 1): se aplicó el criterio de FACSECYD.
2. **Educación (Extensión Daule)**: abrió en 1S-2026 con 59 estudiantes; se publica como
   carrera, igual que Administración Daule en FACSECYD.
3. **Duración de las carreras** (`DURACION_NIVELES` en `comun.py`): hoy se usa lo
   observado (9 niveles en las carreras en línea; 8 en las demás). Afecta la graduación
   oportuna y la deserción a mitad de carrera.
4. **Los 6 casos de asignatura repetida** (novedad 2): para resolverlos como en
   FACSECYD, poner `Revision_asignaturas_registradas_dos_veces.xlsx` junto a los extractos.
