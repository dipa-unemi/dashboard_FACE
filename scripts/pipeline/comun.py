"""
Piezas comunes del pipeline de datos del dashboard FACE.

Es la adaptación a FACE del pipeline del dashboard FACSECYD (misma estructura,
mismos indicadores y mismas reglas). Todo criterio que cambie una cifra
publicada vive aquí: el catálogo de carreras, las exclusiones, el periodo que
se descarta y los umbrales de protección de datos.

Rutas:
  DATOS   carpeta con los extractos del SGA (Result_*.xlsx). Se toma, en este
          orden: la variable de entorno FACE_DATA_DIR; ../Base de datos FACE,
          al lado de la carpeta del repo, si existe; o la propia carpeta del
          repo, donde .gitignore bloquea todo .xlsx y .parquet.
  PROC    DATOS/_procesado: bases ya filtradas, en .parquet (con microdatos:
          nunca entran al repositorio).
  SALIDA  docs/data: lo único que se publica, solo agregados.
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[2]
if os.environ.get("FACE_DATA_DIR"):
    DATOS = Path(os.environ["FACE_DATA_DIR"])
elif (RAIZ.parent / "Base de datos FACE").is_dir():
    DATOS = RAIZ.parent / "Base de datos FACE"
else:
    DATOS = RAIZ
PROC = DATOS / "_procesado"
SALIDA = RAIZ / "docs" / "data"

# --------------------------------------------------------------- carreras
# Mismo criterio que FACSECYD: las carreras NO se unifican; la versión de malla
# y la modalidad distinguen programas distintos. En los extractos de FACE cada
# nombre del SGA corresponde a una sola modalidad (salvo 2 inscripciones de
# EDUCACION INICIAL 2019 registradas como PRESENCIAL, que el paso 01 informa),
# así que el nombre basta como clave.
FACULTAD = "FACE"
CARRERAS = [
    # clave,   nombre en el SGA,                                           nombre visible,                                                  modalidad
    ("BAS_L",  "EDUCACION BASICA",                                         "Educación Básica (en línea)",                                   "EN LÍNEA"),
    ("INI_L",  "EDUCACION INICIAL",                                        "Educación Inicial (en línea)",                                  "EN LÍNEA"),
    ("IDI_L",  "PEDAGOGIA DE LOS IDIOMAS NACIONALES Y EXTRANJEROS",        "Pedagogía de los Idiomas Nacionales y Extranjeros (en línea)",  "EN LÍNEA"),
    # Extensión Daule: abrió en 1S-2026 (por eso tiene pocos estudiantes). Se mantiene con el mismo
    # criterio que Administración de Empresas (Daule) en FACSECYD; pendiente de confirmar por la Dirección de FACE.
    ("EDU",    "EDUCACION",                                                "Educación (Daule)",                                             "PRESENCIAL"),
    ("EDU19",  "EDUCACION 2019",                                           "Educación 2019",                                                "PRESENCIAL"),
    ("ESP",    "EDUCACION ESPECIAL",                                       "Educación Especial",                                            "PRESENCIAL"),
    ("PAF19",  "PEDAGOGIA DE LA ACTIVIDAD FISICA Y DEPORTE 2019",          "Pedagogía de la Actividad Física y Deporte 2019",               "PRESENCIAL"),
    ("LEN",    "PEDAGOGIA DE LA LENGUA Y LA LITERATURA",                   "Pedagogía de la Lengua y la Literatura",                        "PRESENCIAL"),
    ("IDI19",  "PEDAGOGIA DE LOS IDIOMAS NACIONALES Y EXTRANJEROS 2019",   "Pedagogía de los Idiomas Nacionales y Extranjeros 2019",        "PRESENCIAL"),
    ("INI19",  "EDUCACION INICIAL 2019",                                   "Educación Inicial 2019 (semipresencial)",                       "SEMIPRESENCIAL"),
    ("CEX",    "PEDAGOGIA DE LAS CIENCIAS EXPERIMENTALES",                 "Pedagogía de las Ciencias Experimentales (semipresencial)",     "SEMIPRESENCIAL"),
]
# Carreras de FACE que aparecen en los extractos pero ya no están vigentes (el SGA las marca
# carrera_vigente = NO o solo tienen registros históricos). Quedan fuera por no estar en el
# catálogo; la lista sirve para que el paso 06 compruebe que ningún nombre se publique.
CARRERAS_NO_VIGENTES = {
    "LICENCIATURA EN CIENCIAS DE LA EDUCACION", "LICENCIATURA EN CIENCIAS DE LA EDUCACION MENCION CULTURA FISICA",
    "LICENCIATURA EN CIENCIAS DE LA EDUCACION MENCION EDUCACION BASICA",
    "LICENCIATURA EN CIENCIAS DE LA EDUCACION MENCION EDUCACION BASICA 2019",
    "LICENCIATURA EN CIENCIAS DE LA EDUCACION MENCION EDUCACION INICIAL",
    "LICENCIATURA EN CIENCIAS DE LA EDUCACION MENCION EDUCACION INICIAL 2019",
    "LICENCIATURA EN CIENCIAS DE LA EDUCACION MENCION EDUCADORES DE PARVULOS",
    "LICENCIATURA EN EDUCACION INICIAL", "INFORMATICA Y PROGRAMACION", "PEDAGOGIA DE LA ACTIVIDAD FISICA Y DEPORTE",
}
# Duración de cada carrera en niveles (semestres), según su malla. Se usa para
# la graduación oportuna y la deserción a mitad de carrera. Una carrera que no
# esté aquí toma el nivel más alto observado en la base, con un mínimo de
# DURACION_MINIMA (las carreras nuevas aún no tienen estudiantes en los últimos
# niveles). FACE: POR CONFIRMAR con la Dirección. Lo observado: 9 niveles en las
# tres carreras en línea; 8 en las demás (Educación Daule solo tiene 1.er nivel).
DURACION_NIVELES = {}
DURACION_MINIMA = 8
CLAVE_DE = {sga: k for k, sga, _, _ in CARRERAS}
SGA_DE = {k: sga for k, sga, _, _ in CARRERAS}
CARRERAS_K = [k for k, *_ in CARRERAS]

# Agregados: la facultad y cada modalidad (suma de sus carreras). Se calculan
# igual que la facultad: una persona que está en dos carreras cuenta una vez.
MODALIDADES = {"MOD_LIN": ("EN LÍNEA", "En línea"), "MOD_PRE": ("PRESENCIAL", "Presencial"),
               "MOD_SEM": ("SEMIPRESENCIAL", "Semipresencial")}
AGREGADOS = [FACULTAD] + list(MODALIDADES)
CLAVES = AGREGADOS + CARRERAS_K


def miembros(k):
    """Carreras que forman una clave (la facultad, una modalidad o una carrera)."""
    if k == FACULTAD:
        return CARRERAS_K
    if k in MODALIDADES:
        return [c for c, _, _, mod in CARRERAS if mod == MODALIDADES[k][0]]
    return [k]


def es_agregado(k):
    return k in AGREGADOS


def filtro(df, k, col="clave"):
    return df if k == FACULTAD else df[df[col].isin(miembros(k))]


# Nombre corto para las etiquetas de los gráficos
CORTO = {"BAS_L": "Ed. Básica (L)", "INI_L": "Ed. Inicial (L)", "IDI_L": "Idiomas (L)",
         "EDU": "Educación Daule", "EDU19": "Educación 2019", "ESP": "Ed. Especial", "PAF19": "Actividad Física 2019",
         "LEN": "Lengua y Literatura", "IDI19": "Idiomas 2019", "INI19": "Ed. Inicial 2019", "CEX": "Ciencias Experimentales"}


def catalogo_carreras():
    """Lo que el tablero necesita saber de cada carrera (sin colores: los pone el tablero)."""
    return [{"k": k, "sga": sga, "nom": nom, "corto": CORTO.get(k, nom), "mod": mod,
             "sede": "Extensión Daule" if k == "EDU" else "Milagro"}
            for k, sga, nom, mod in CARRERAS]


def catalogo_modalidades():
    return [{"k": k, "mod": mod, "nom": nom, "carreras": miembros(k)} for k, (mod, nom) in MODALIDADES.items()]


# ------------------------------------------------- exclusiones (Dirección)
# Combinaciones carrera + PRESENCIAL no vigentes. En FACSECYD la misma carrera sigue
# vigente en otra modalidad y se excluye por combinación; en los extractos de FACE no
# hay ese caso (las carreras no vigentes tienen nombre propio y salen por no estar en
# el catálogo), así que el conjunto queda vacío.
EXCLUIR_PRESENCIAL = set()
# Periodo que se descarta: el remedial de abril - mayo 2021 (en FACSECYD el SGA lo codifica
# como 1S-2021). Los extractos de FACE no lo traen: su 1S-2021 es el semestre regular
# MAYO A SEPTIEMBRE 2021. La regla se conserva y quita 0 filas.
PERIODO_EXCLUIDO = ("1S-2021", "ABRIL- MAYO 2021")

# Asignaturas que se excluyen de toda la base de estudiantes: Inglés VI y VII de General
# English (carreras en línea, 2024). En FACSECYD lo decidió la Dirección el 2026-10-07; en FACE
# son las mismas asignaturas (Educación Básica e Inicial en línea, 1S y 2S-2024: 6.685 registros)
# y traen 82 de los 88 casos de asignatura registrada dos veces en el periodo. Se aplica el mismo
# criterio; PENDIENTE de confirmar por la Dirección de FACE.
ASIGNATURAS_EXCLUIDAS = {1691: "INGLES VI (GENERAL ENGLISH)", 2070: "INGLES VII (GENERAL ENGLISH)"}

# Asignaturas registradas dos veces en el mismo periodo (misma inscripción, periodo y asignatura,
# con distinto número de matrícula o nota): la Dirección eligió qué fila conservar en cada caso
# (2026-10-07). La decisión vive en la hoja «Detalle» de este Excel, fuera del repositorio porque
# lleva identificadores de estudiantes: una fila por caso = la fila que se conserva.
DECISION_REPETIDAS = (DATOS / "Revision_asignaturas_registradas_dos_veces.xlsx", "Detalle (2 filas por caso)")

# ----------------------------------------------- protección de datos
MIN_BASE = 10   # grupos con menos personas no se publican
K_ANON = 5      # categorías con menos casos se agrupan en «Otras categorías (pocos casos)»
OTRAS = "Otras categorías (pocos casos)"

# ----------------------------------------------------------- periodos
MESES = {"ENERO": "Ene", "FEBRERO": "Feb", "MARZO": "Mar", "ABRIL": "Abr", "MAYO": "May",
         "JUNIO": "Jun", "JULIO": "Jul", "AGOSTO": "Ago", "SEPTIEMBRE": "Sep",
         "OCTUBRE": "Oct", "NOVIEMBRE": "Nov", "DICIEMBRE": "Dic"}


def etiqueta_periodo(nombre: str) -> str:
    """'NOVIEMBRE 2021 MARZO 2022' -> 'Nov 2021 – Mar 2022'; 'ABRIL - JULIO 2026' -> 'Abr – Jul 2026'."""
    toks = re.findall(r"[A-ZÁÉÍÓÚ]+|\d{4}", nombre.upper())
    partes, mes = [], None
    for t in toks:
        if t in MESES:
            if mes:
                partes.append([mes, None])
            mes = MESES[t]
        elif t.isdigit() and mes:
            partes.append([mes, t]); mes = None
    if mes:
        partes.append([mes, None])
    if len(partes) >= 2:
        (m1, a1), (m2, a2) = partes[0], partes[-1]
        a1 = a1 or a2
        return f"{m1} – {m2} {a2}" if a1 == a2 else f"{m1} {a1} – {m2} {a2}"
    return nombre.title()


def orden_periodo(cod: str) -> tuple:
    s, a = cod.split("-")
    return int(a), int(s[0])


def siguiente(cod: str, n: int = 1) -> str:
    """Código del semestre n posiciones después: 1S-2021 + 1 = 2S-2021."""
    a, s = orden_periodo(cod)
    i = a * 2 + (s - 1) + n
    return f"{i % 2 + 1}S-{i // 2}"


# ----------------------------------------------------------- utilidades
def pct(num, den, dec=1):
    return None if not den else round(100.0 * num / den, dec)


def r(x, dec=2):
    return None if x is None or pd.isna(x) else round(float(x), dec)


def por_carrera(df, col="clave"):
    """Itera (clave, subconjunto) para la facultad, cada modalidad y cada carrera."""
    for k in CLAVES:
        yield k, filtro(df, k, col)


def leer(nombre, columnas=None):
    ruta = PROC / f"{nombre}.parquet"
    if not ruta.exists():
        sys.exit(f"No existe {ruta}. Corre primero: python scripts/pipeline/01_preparar_bases.py")
    return pd.read_parquet(ruta, columns=columnas)


def estado():
    """Bitácora del paso 01 (qué bases se usaron y si alguna es provisional)."""
    ruta = PROC / "bitacora.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def agrupar_pocos(conteos, k=K_ANON):
    """[(categoría, n), ...] -> las de menos de k casos se suman en OTRAS."""
    filas, otras = [], 0
    for cat, n in conteos:
        if n < k:
            otras += n
        else:
            filas.append([cat, int(n)])
    if otras:
        filas.append([OTRAS, int(otras)])
    return filas


PROVINCIAS = ["Azuay", "Bolívar", "Cañar", "Carchi", "Chimborazo", "Cotopaxi", "El Oro", "Esmeraldas",
              "Galápagos", "Guayas", "Imbabura", "Loja", "Los Ríos", "Manabí", "Morona Santiago", "Napo",
              "Orellana", "Pastaza", "Pichincha", "Santa Elena", "Santo Domingo de los Tsáchilas",
              "Sucumbíos", "Tungurahua", "Zamora Chinchipe"]
_SIN_TILDE = str.maketrans("ÁÉÍÓÚáéíóú", "AEIOUaeiou")
_PROV = {p.upper().translate(_SIN_TILDE): p for p in PROVINCIAS}


def provincia(prov, pais=None):
    """Nombre oficial de la provincia (el que usa el mapa); 'Exterior' si el país no es Ecuador."""
    if pais is not None and isinstance(pais, str) and pais.strip() and pais.strip().upper() != "ECUADOR":
        return "Exterior"
    if not isinstance(prov, str) or not prov.strip():
        return "No registra"
    # Con país Ecuador, una provincia que no existe en el país se trata como dato no registrado.
    return _PROV.get(prov.strip().upper().translate(_SIN_TILDE), "No registra" if pais is not None else "Exterior")


# País de procedencia: nombre del SGA (sin tildes ni espacios) -> (nombre visible, código ISO3 del mapa mundial).
_PAISES = {
    "ECUADOR": ("Ecuador", "ECU"), "ESTADOS UNIDOS": ("Estados Unidos", "USA"),
    "ESTADOS UNIDOS DE AMERICA": ("Estados Unidos", "USA"), "ESPANA": ("España", "ESP"), "CHILE": ("Chile", "CHL"),
    "COLOMBIA": ("Colombia", "COL"), "ITALIA": ("Italia", "ITA"), "PERU": ("Perú", "PER"),
    "ARGENTINA": ("Argentina", "ARG"), "MEXICO": ("México", "MEX"), "ALEMANIA": ("Alemania", "DEU"),
    "REINO UNIDO DE GRANBRETANA E IRLANDA DEL NORTE": ("Reino Unido", "GBR"), "BRASIL": ("Brasil", "BRA"),
    "VENEZUELA": ("Venezuela", "VEN"), "FRANCIA": ("Francia", "FRA"), "RUSIA": ("Rusia", "RUS"),
    "AUSTRALIA": ("Australia", "AUS"), "CANADA": ("Canadá", "CAN"), "CUBA": ("Cuba", "CUB"),
    "ARUBA": ("Aruba", "ABW"), "SUIZA": ("Suiza", "CHE"), "QATAR": ("Catar", "QAT"), "PANAMA": ("Panamá", "PAN"),
    "PAISES BAJOS": ("Países Bajos", "NLD"), "ISRAEL": ("Israel", "ISR"), "BOLIVIA": ("Bolivia", "BOL"),
    "BAHAMAS": ("Bahamas", "BHS"), "CHINA": ("China", "CHN"), "COSTA RICA": ("Costa Rica", "CRI"),
    "HONDURAS": ("Honduras", "HND"), "EL SALVADOR": ("El Salvador", "SLV"), "EGIPTO": ("Egipto", "EGY"),
    "POLONIA": ("Polonia", "POL"), "PUERTO RICO": ("Puerto Rico", "PRI"),
    "REPUBLICA DOMINICANA": ("República Dominicana", "DOM"), "TURQUIA": ("Turquía", "TUR"),
    "URUGUAY": ("Uruguay", "URY"), "PARAGUAY": ("Paraguay", "PRY"), "GUATEMALA": ("Guatemala", "GTM"),
    "NICARAGUA": ("Nicaragua", "NIC"), "PORTUGAL": ("Portugal", "PRT"), "JAPON": ("Japón", "JPN"),
    # FACE
    "EMIRATOS ARABES UNIDOS": ("Emiratos Árabes Unidos", "ARE"), "CAMBOYA": ("Camboya", "KHM"),
    "IRAN": ("Irán", "IRN"), "UCRANIA": ("Ucrania", "UKR"),
}
_PAISES_SIN_ESPACIO = {k.replace(" ", ""): v for k, v in _PAISES.items()}


def pais(p):
    """Nombre visible del país ('No registra' si falta). Un país nuevo sin equivalencia queda en tipo oración."""
    if not isinstance(p, str) or not p.strip() or p.strip().upper() in ("NO REGISTRA", "\\N"):
        return "No registra"
    k = p.strip().upper().translate(_SIN_TILDE).replace("Ñ", "N")
    v = _PAISES.get(k) or _PAISES_SIN_ESPACIO.get(k.replace(" ", ""))
    return v[0] if v else p.strip().capitalize()


ISO_PAIS = {nom: iso for nom, iso in _PAISES.values()}


def tipo_oracion(s):
    """'MESTIZO/A' -> 'Mestizo/a'; 'TIEMPO COMPLETO' -> 'Tiempo completo'."""
    return s if not isinstance(s, str) else s.strip().capitalize()


def escribir_js(archivo, variable, obj, origen, descripcion):
    SALIDA.mkdir(parents=True, exist_ok=True)
    obj = {"generado": date.today().isoformat(), **obj}
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
                     default=lambda o: o.item() if hasattr(o, "item") else str(o))
    (SALIDA / archivo).write_text(
        f"/* Generado por scripts/pipeline/{origen} — no editar a mano. {descripcion} */\n"
        f"window.{variable}={txt};\n", encoding="utf-8")
    print(f"Escrito docs/data/{archivo} ({len(txt) / 1024:.0f} KB)")
