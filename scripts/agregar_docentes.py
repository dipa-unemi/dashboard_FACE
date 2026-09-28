# -*- coding: utf-8 -*-
"""
Agregacion del modulo de Docentes (FACE).

Lee el distributivo docente y escribe el bloque de datos que consume la pestana
Docentes, inyectandolo dentro de docs/docentes.html. El tablero queda como un
unico archivo autocontenido, igual que en FACSECYD.

Lo que sale del script NO contiene datos personales: cada fila publicada es un
conteo para una combinacion de atributos, nunca un docente identificado. El
docente_id se usa solo para contar personas distintas y no se publica.

Entrada : data/data_docente.xlsx   (privado, fuera del repositorio)
Salida  : docs/docentes.html       (bloque "const RAW = {...};" reescrito)

Uso:  python scripts/agregar_docentes.py

Nota de reproducibilidad: este script se reconstruyo a partir del tablero ya
publicado de FACSECYD, cuyo generador no quedo versionado, y reproduce sus
5.798 filas agregadas sin una sola diferencia. Las dos facultades se leen, por
tanto, con el mismo criterio.
"""

import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent
XLSX = RAIZ / "data" / "data_docente.xlsx"
HTML = RAIZ / "docs" / "docentes.html"

NULO_SQL = chr(92) + "N"       # el nulo de MySQL, exportado como texto
SIN_REGISTRO = "SIN REGISTRO"
NO_REGISTRA = "NO REGISTRA"

# Umbral de agrupacion del perfil demografico del periodo vigente. Con ~180
# docentes en la facultad, publicar "INDIGENA: 2" del semestre en curso senala
# a una persona concreta; por debajo del umbral las categorias se funden.
UMBRAL = 10

_TIL = str.maketrans("ÁÉÍÓÚÜÑáéíóúüñ", "AEIOUUNaeiouun")

# Atributos que describen a la PERSONA. Lo que describe a la asignatura
# (nivel, paralelo, asignatura) no entra: el tablero nunca desglosa por materia.
DEMO = ["docente_sexo", "docente_etnia", "docente_discapacidad_bin", "docente_edad_rango"]
BASE = ["docente_dedicacion", "docente_categoria", "docente_nivel_academico"] + DEMO


def sin_tildes(x):
    return str(x).translate(_TIL)


def norm_carrera(x):
    """Une las grafias de una misma carrera. En el distributivo de FACE la misma
    carrera aparece con y sin tildes (EDUCACION INICIAL y EDUCACIoN INICIAL);
    sin esto cada grafia abriria su propia barra en el grafico."""
    return re.sub(r"\s+", " ", sin_tildes(x).upper()).strip()


def rango_edad(e):
    """Los tramos arrancan en 20 a proposito: hay docentes con edad registrada
    como 2, 3 o 4 anios (error de captura evidente). Caen en SIN REGISTRO en vez
    de inventar un tramo de profesores nino."""
    try:
        e = int(e)
    except (TypeError, ValueError):
        return SIN_REGISTRO
    if e < 20:
        return SIN_REGISTRO
    if e < 30:
        return "MENOS DE 30"
    if e < 40:
        return "30 A 39"
    if e < 50:
        return "40 A 49"
    if e < 60:
        return "50 A 59"
    return "60 O MAS"


def periodo_key(c):
    m = re.match(r"^([12])S-(\d{4})$", str(c) or "")
    return int(m.group(2)) * 10 + int(m.group(1)) if m else -1


def preparar(ruta):
    df = pd.read_excel(ruta, sheet_name="Hoja1")
    # El nulo de MySQL solo se traduce en los atributos de perfil. docente_id se
    # deja tal cual a proposito: las filas sin identificador son asignaciones
    # reales y descartarlas cambiaria el total de la facultad.
    for c in ["docente_dedicacion", "docente_categoria", "docente_nivel_academico",
              "docente_sexo", "docente_etnia"]:
        df[c] = df[c].map(lambda v: None if str(v).strip() == NULO_SQL else v)
    for c in ["docente_dedicacion", "docente_categoria", "docente_nivel_academico"]:
        df[c] = df[c].fillna(SIN_REGISTRO)
    for c in ["docente_sexo", "docente_etnia"]:
        df[c] = df[c].fillna(NO_REGISTRA)
    df["carrera_asignatura"] = df.carrera_asignatura.map(norm_carrera)
    # El tablero filtra por si hay discapacidad registrada, no por cual: el tipo
    # concreto solo aparece en el perfil agregado del periodo vigente.
    df["docente_discapacidad_bin"] = df.docente_discapacidad.map(
        lambda v: "SIN DISCAPACIDAD" if str(v).strip().upper() == "SIN DISCAPACIDAD"
        else "CON DISCAPACIDAD REGISTRADA")
    df["docente_edad_rango"] = df.docente_edad.map(rango_edad)
    df["total_estudiantes"] = pd.to_numeric(df.total_estudiantes, errors="coerce").fillna(0)
    return df


def agregar(df, claves):
    """Una fila por combinacion exacta de claves. 'docentes' cuenta personas
    distintas y 'asignaciones' cuenta filas del distributivo: un mismo docente
    con tres materias es 1 docente y 3 asignaciones."""
    filas = []
    for k, g in df.groupby(claves, sort=False, dropna=False):
        k = k if isinstance(k, tuple) else (k,)
        nd = g.docente_id.nunique()
        na = len(g)
        ne = int(g.total_estudiantes.sum())
        tipos = [{"tipo": t, "docentes": int(gg.docente_id.nunique()),
                  "asignaciones": int(len(gg))}
                 for t, gg in g.groupby("tipo_docente", sort=False)]
        tipos.sort(key=lambda r: (-r["docentes"], r["tipo"]))
        filas.append(dict(zip(claves, k)) | {
            "docentes": int(nd), "asignaciones": int(na), "estudiantes_total": ne,
            "carga_promedio": round(ne / nd, 1),
            "asignaciones_por_docente": round(na / nd, 2),
            "por_tipo": tipos})
    cols = claves + ["docentes", "asignaciones", "estudiantes_total",
                     "carga_promedio", "asignaciones_por_docente", "por_tipo"]
    # Formato columnar: el tablero lo recompone con zip() al cargar.
    return {c: [f[c] for f in filas] for c in cols}


def perfil(df, ult):
    g = df[df.periodo_codigo == ult]
    per = g.drop_duplicates("docente_id")

    def reparto(col, agrupar=True):
        vc = per[col].value_counts()
        if not agrupar:
            return [{"categoria": k, "docentes": int(v)} for k, v in vc.items()]
        altos = [{"categoria": k, "docentes": int(v)} for k, v in vc.items() if v >= UMBRAL]
        resto = int(vc[vc < UMBRAL].sum())
        if resto:
            altos.append({"categoria": "Otro / pocos casos", "docentes": resto})
        return altos

    con_disc = per[per.docente_discapacidad_bin != "SIN DISCAPACIDAD"]
    det = con_disc.docente_discapacidad.value_counts()
    return {
        "periodo_codigo": ult, "periodo": g.periodo.iloc[0],
        "total_docentes": int(per.docente_id.nunique()), "umbral_agrupacion": UMBRAL,
        "sexo": reparto("docente_sexo"), "etnia": reparto("docente_etnia"),
        # La discapacidad es binaria: agrupar su categoria minoritaria la borraria.
        "discapacidad": reparto("docente_discapacidad_bin", agrupar=False),
        "discapacidad_detalle": [{"categoria": k, "docentes": int(v)} for k, v in det.items()],
    }


def construir(df):
    ult = max(df.periodo_codigo.unique(), key=periodo_key)
    return {
        "docentes_general": agregar(df, BASE),
        "docentes_periodo": agregar(df, ["periodo_codigo", "periodo"] + BASE),
        "docentes_modalidad": agregar(df, ["periodo_codigo", "periodo", "modalidad"] + BASE),
        "docentes_carrera": agregar(df, ["periodo_codigo", "periodo", "facultad",
                                         "carrera_asignatura", "modalidad"] + BASE),
        "docentes_perfil_demografico": perfil(df, ult),
        "docentes_opciones": {
            "carrera": sorted(df.carrera_asignatura.unique()),
            "modalidad": sorted(df.modalidad.unique()),
            "dedicacion": sorted(df.docente_dedicacion.unique()),
            "categoria": sorted(df.docente_categoria.unique()),
            "nivel_academico": sorted(df.docente_nivel_academico.unique()),
            "sexo": sorted(df.docente_sexo.unique()),
            "etnia": sorted(df.docente_etnia.unique()),
            "discapacidad": sorted(df.docente_discapacidad_bin.unique()),
            "periodo": sorted(df.periodo_codigo.unique(), key=periodo_key)},
        "docentes_meta": {"latest_periodo": ult,
                          "generado": datetime.now().strftime("%Y-%m-%d %H:%M")},
    }


def inyectar(raw):
    """Reescribe la linea 'const RAW = {...};' de docs/docentes.html. El tablero
    se mantiene como un solo archivo, asi que el script es idempotente: correrlo
    de nuevo reemplaza el bloque anterior."""
    texto = HTML.read_text(encoding="utf-8")
    bloque = "const RAW = " + json.dumps(raw, ensure_ascii=False) + ";"
    nuevo, n = re.subn(r"^const RAW = .*;$", lambda _: bloque, texto,
                       count=1, flags=re.MULTILINE)
    if n != 1:
        raise SystemExit("No se encontro el bloque const RAW en " + str(HTML))
    HTML.write_text(nuevo, encoding="utf-8")


def main():
    if not XLSX.exists():
        raise SystemExit("Falta " + str(XLSX) + " · el Excel de origen vive solo en local.")
    print("=" * 70)
    print("AGREGACION · DOCENTES FACE")
    print("=" * 70)
    df = preparar(XLSX)
    print("Fuente: {:,} asignaciones · {:,} docentes · {:,} cupos de estudiante"
          .format(len(df), df.docente_id.nunique(), int(df.total_estudiantes.sum()))
          .replace(",", "."))

    raw = construir(df)
    total_est = int(df.total_estudiantes.sum())
    for g in ["docentes_general", "docentes_periodo", "docentes_modalidad", "docentes_carrera"]:
        t = raw[g]
        # Control: cada grupo reparte el total de la facultad, sin perder ni duplicar.
        assert sum(t["asignaciones"]) == len(df), g + " no cuadra con el origen"
        assert sum(t["estudiantes_total"]) == total_est, g + " no cuadra con el origen"
        print("  {:22s} {:5d} combinaciones publicadas".format(g, len(t["docentes"])))

    inyectar(raw)
    print()
    print("Escrito: " + str(HTML.relative_to(RAIZ)))
    print("Periodo mas reciente: " + raw["docentes_meta"]["latest_periodo"])


if __name__ == "__main__":
    main()
