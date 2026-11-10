"""
Paso 5c · Indicadores con la metodología de los informes del SGA -> docs/data/informes-data.js (FACS_INF).

Lee las salidas de las consultas que replican los informes del SGA (comun.INFORMES; consultas en
Dashboard_Academico_Perfil/consultas/Consultas_nuevas). Cada consulta reproduce el cálculo del informe
y este paso solo cuenta, para que el tablero dé las mismas cifras que el SGA:

  R02 permanencia (FR0087)  PE1 = nuevos de primer nivel del periodo anterior que pasan a segundo nivel
                            / nuevos de primer nivel del periodo anterior. Una fila por estudiante.
  R16 deserción (FR0122)    TD = desertores en Ai+δ / cohorte Ai; δ = niveles / 2 redondeado arriba.
  R19 titulación (FR0125)   TT = titulados hasta el fin de Ai + niveles + 2 / cohorte Ai.
  R11 afinidad (FR0108)     APA = asignaturas con afinidad > 0 en el campo detallado / asignaturas de los
                            ejes 3 y 43, con la corrección de campos equivalentes del 04-11-2026.
  R22 proyectos (FR0127)    proyectos de investigación con algún integrante en el distributivo de la carrera.
  R23 producción (FR0128)   artículos (impacto mundial y regional), libros, capítulos, ponencias y
                            proceedings; el autor debe constar en el distributivo de la carrera el año de
                            la publicación.

Las tasas se truncan a dos decimales como en los informes (55/178 = 30,89), no se redondean.

Facultad y modalidades: una persona (o un producto, o un proyecto) que está en dos carreras cuenta una
vez. Los datos de estudiantes se desglosan por sexo y nivel socioeconómico como el resto de la
trayectoria; los grupos con menos de MIN_BASE estudiantes no se publican y se aplica supresión
complementaria (si solo una parte de un total queda oculta, se oculta también la parte publicada más
pequeña, para que no se deduzca restando). La producción y los proyectos no son datos de personas: se
publican sin umbral y sin nombres de autores ni de integrantes.
"""
import json
import re
from collections import defaultdict

import pandas as pd

from comun import (AGREGADOS, CARRERAS_K, CARRERAS_NO_VIGENTES, CLAVE_DE, FACULTAD, INFORMES, MIN_BASE, MODALIDADES,
                   SALIDA, escribir_js, etiqueta_periodo, miembros, orden_periodo)

TILDES = str.maketrans("ÁÉÍÓÚáéíóú", "AEIOUaeiou")
CATALOGO = {k.translate(TILDES): v for k, v in CLAVE_DE.items()}
NO_VIGENTES = {x.translate(TILDES) for x in CARRERAS_NO_VIGENTES}
GSE = ["BAJO", "MEDIO BAJO", "MEDIO TÍPICO", "MEDIO ALTO", "ALTO"]
# Periodos que aún no terminan (su matrícula y su planta pueden cambiar): AGOSTO - DICIEMBRE 2026 (479).
EN_CURSO = {"2S-2026"}


# Otros nombres con que se guardaron los resultados (el primero que exista gana, en este orden).
ALIAS = {"R11_afinidad_CACES_FACE": ["R11_afinidad_CACES_FACE", "R11_afinidad_CACES"],
         "R23_produccion_FACE": ["R23_produccion_v2", "R23_produccion_FACE"]}


def buscar(nombre):
    return next((INFORMES / f"{n}{ext}" for n in ALIAS.get(nombre, [nombre]) for ext in (".xlsx", ".csv")
                 if (INFORMES / f"{n}{ext}").exists()), None)


def leer(nombre):
    ruta = buscar(nombre)
    if ruta is None:
        raise SystemExit(f"No existe {INFORMES / nombre}.xlsx ni .csv (variable FACE_INFORMES_DIR)")
    df = (pd.read_excel(ruta) if ruta.suffix == ".xlsx"
          else pd.read_csv(ruta, keep_default_na=False, na_values=[r"\N"]))
    nom = df.carrera.astype(str).str.strip().str.upper().str.translate(TILDES)
    fuera = set(nom[~nom.isin(CATALOGO)]) - NO_VIGENTES
    assert not fuera, f"{ruta.name}: carreras que no están en el catálogo ni en las no vigentes: {fuera}"
    df["clave"] = nom.map(CATALOGO)
    print(f"{ruta.name}: {len(df):,} filas; fuera del catálogo (no vigentes): {int(df.clave.isna().sum()):,}")
    return df[df.clave.notna()].copy()


def trunc2(k, n):
    return None if not n else int(k * 10000 // n) / 100


def claves_de(df):
    """(clave, subconjunto) para la facultad, cada modalidad y cada carrera."""
    for k in AGREGADOS + CARRERAS_K:
        yield k, df[df.clave.isin(miembros(k))]


def dims(df):
    yield "", df
    for g in GSE:
        yield f"|{g}", df[df.grupo_socioeconomico == g]
    for s in ["HOMBRE", "MUJER"]:
        yield f"|sexo:{s}", df[df.sexo == s]


# ------------------------------------------------------------ protección de datos
def proteger(crudo):
    """crudo[clave][periodo] = [base, numerador]. Devuelve solo lo publicable: base >= MIN_BASE y, además,
    supresión complementaria en tres particiones (sexo, nivel socioeconómico y carreras de una modalidad /
    modalidades de la facultad): si una sola parte de un total publicado queda oculta, se oculta también la
    parte publicada más pequeña."""
    pub = {(k, p) for k, per in crudo.items() for p, f in per.items() if f[0] >= MIN_BASE}
    bases = {k.split("|")[0] for k in crudo}
    sufs = {("|" + k.split("|", 1)[1]) if "|" in k else "" for k in crudo}
    particiones = []
    for b in bases:
        particiones.append((b, [f"{b}|sexo:HOMBRE", f"{b}|sexo:MUJER"]))
        particiones.append((b, [f"{b}|{g}" for g in GSE]))
    for s in sufs:
        for m in MODALIDADES:
            particiones.append((m + s, [c + s for c in miembros(m)]))
        particiones.append((FACULTAD + s, [m + s for m in MODALIDADES]))
    periodos = {p for per in crudo.values() for p in per}
    cambio = True
    while cambio:
        cambio = False
        for padre, hijos in particiones:
            for p in periodos:
                if (padre, p) not in pub:
                    continue
                con_datos = [h for h in hijos if p in crudo.get(h, {}) and crudo[h][p][0] > 0]
                ocultos = [h for h in con_datos if (h, p) not in pub]
                visibles = [h for h in con_datos if (h, p) in pub]
                if len(ocultos) == 1 and visibles:
                    menor = min(visibles, key=lambda h: crudo[h][p][0])
                    pub.discard((menor, p))
                    cambio = True
    out = defaultdict(dict)
    for k, per in crudo.items():
        for p, f in per.items():
            if (k, p) in pub:
                out[k][p] = f
    return dict(out), sum(len(v) for v in crudo.values()) - len(pub)


etiquetas = {}

# ===================================================== R02 · permanencia estudiantil
r02 = leer("R02_permanencia_FACE")
etiquetas.update({c: etiqueta_periodo(n) for c, n in zip(r02.periodo, r02.periodo_en_curso)})
perm = {}
for k, sub in claves_de(r02):
    for suf, x in dims(sub):
        x = x.drop_duplicates(["periodo", "inscripcion_id"])
        per = {p: [int(len(g)), int((g.segunda_matricula == "SI").sum())] for p, g in x.groupby("periodo")}
        if per:
            perm[k + suf] = per
perm, oc_perm = proteger(perm)

# ===================================================== R16 · deserción a mitad de carrera
r16 = leer("R16_desercion_FACE")
etiquetas.update({c: etiqueta_periodo(n) for c, n in zip(r16.cohorte, r16.ai)})
des, delta = {}, {}
for k, sub in claves_de(r16):
    # Una persona en dos carreras de la misma cohorte cuenta una vez: deserta solo si deserta en todas.
    u = (sub.assign(d=(sub.desertor == "SI").astype(int))
         .groupby(["cohorte", "persona_id"], as_index=False)
         .agg(d=("d", "min"), sexo=("sexo", "first"), grupo_socioeconomico=("grupo_socioeconomico", "first")))
    for suf, x in dims(u):
        per = {c: [int(len(g)), int(g.d.sum())] for c, g in x.groupby("cohorte")}
        if per:
            des[k + suf] = per
for k, g in r16.groupby("clave"):
    delta[k] = int(g.delta.iloc[0])
des, oc_des = proteger(des)

# ===================================================== R19 · titulación
r19 = leer("R19_titulacion_FACE")
etiquetas.update({c: etiqueta_periodo(n) for c, n in zip(r19.cohorte, r19.ai)})
tit_c = {}
for k, sub in claves_de(r19):
    u = (sub.assign(t=(sub.titulado_en_ventana == "SI").astype(int), g=sub.fechagraduado.notna().astype(int))
         .groupby(["cohorte", "persona_id"], as_index=False)
         .agg(t=("t", "max"), g=("g", "max"), sexo=("sexo", "first"), grupo_socioeconomico=("grupo_socioeconomico", "first")))
    for suf, x in dims(u):
        per = {c: [int(len(g)), int(g.t.sum()), int(g.g.sum())] for c, g in x.groupby("cohorte")}
        if per:
            tit_c[k + suf] = per
tit_c, oc_tit = proteger(tit_c)

# ===================================================== R11 · afinidad del personal académico
# Con la consulta según el CACES (R11_afinidad_CACES_FACE): cada paralelo vale 1 si su docente es afín y 0 si no, la
# asignatura vale el promedio de sus paralelos y TAAF es la suma de esos promedios (Modelo genérico, indicador 8).
# Sin ella, se usa la del reporte del SGA (afín si el promedio 0/33/67/100 es mayor que 0).
CACES = buscar("R11_afinidad_CACES_FACE") is not None
r11 = leer("R11_afinidad_CACES_FACE" if CACES else "R11_afinidad_FACE_CORREGIDO")
etiquetas.update({c: etiqueta_periodo(n) for c, n in zip(r11.periodo, r11.periodo_nombre)})
if CACES:
    r11["valor"] = pd.to_numeric(r11.afinidad_asignatura).astype(float)
    r11["pct"] = r11.valor * 100
else:
    r11["valor"] = (r11.asignatura_afin_apa == "SI").astype(float)
    r11["pct"] = r11.porcentaje_afinidad_cd
afin, afin_det = {}, {}
for k, sub in claves_de(r11):
    per = {p: [int(len(g)), round(float(g.valor.sum()), 4)] for p, g in sub.groupby("periodo")}
    if per:
        afin[k] = per
limpio = lambda s: " ".join(str(s).split()) if isinstance(s, str) else ""
for k, sub in r11.groupby("clave"):
    afin_det[k] = {p: [[a, n, limpio(cd), round(float(v), 2), int(f > 0), int(par), int(pdoc)]
                       for a, n, cd, v, f, par, pdoc in zip(g.asignatura, g.nivel, g.campo_detallado, g.pct, g.valor,
                                                           g.paralelos, g.paralelos_con_docente)]
                   for p, g in sub.sort_values(["periodo", "nivel", "asignatura"]).groupby("periodo")}

# ===================================================== R23 · producción científica
r23 = leer("R23_produccion_FACE")
TIPO = {"ARTICULO IMPACTO MUNDIAL": "AM", "ARTICULO IMPACTO REGIONAL": "AR", "LIBRO": "LI",
        "CAPITULO DE LIBRO": "CA", "PONENCIA": "PO", "PROCEEDING": "PR"}
assert set(r23.tipo_produccion) <= set(TIPO), set(r23.tipo_produccion) - set(TIPO)
r23["tipo"] = r23.tipo_produccion.map(TIPO)
r23["uid"] = r23.clase + ":" + r23.producto_id.astype(str)
txt = lambda s: "" if pd.isna(s) else " ".join(str(s).split())
productos = r23.drop_duplicates("uid").set_index("uid")
car_de = r23.groupby("uid").clave.apply(lambda s: "+".join(sorted(set(s), key=CARRERAS_K.index)))
# Docentes autores de cada producto en cada carrera, modalidad y facultad (distintos: el que está en dos carreras
# cuenta una vez en la modalidad y en la facultad). Sale de las filas de la consulta (una por docente del
# distributivo), no de autores_registrados del SGA, que viene vacío en parte de los productos.
doc_de = defaultdict(dict)
for k, sub in claves_de(r23):
    for uid, n in sub.groupby("uid").docente_id.nunique().items():
        doc_de[uid][k] = int(n)
items = []
for uid, p in productos.iterrows():
    # Sin nombres de editores: el libro no lleva editorial (a veces es una persona) y el capítulo, solo el título del libro.
    medio = "" if p.tipo == "LI" else txt(p.medio).rsplit(" - ", 1)[0] if p.tipo == "CA" else txt(p.medio)
    items.append([p.tipo, int(p.anio), txt(p.titulo), medio, txt(p.bases_indexadas), txt(p.doi_o_isbn),
                  txt(p.linea), int(p.proviene_proyecto == "SI"), txt(p.grupo_investigacion), txt(p.nivel_nombre),
                  txt(p.cuartil), int(pd.to_numeric(p.autores_estudiantes, errors="coerce") > 0 if p.clase == "articulo" else 0),
                  int(p.acceso_abierto == "SI"), car_de[uid], doc_de[uid]])
ANIOS_PROD = sorted(int(a) for a in r23.anio.unique())

# Planta docente del año por carrera: denominador de «docentes con producción» (lo calcula el paso 02).
fd = (SALIDA / "face-data.js").read_text(encoding="utf-8")
planta = {k: {p["p"]: p.get("n") for p in pts}
          for k, pts in json.loads(fd[fd.index("=") + 1:].strip().rstrip(";"))["ind"]["doc_prod"].items()}

SUB_TIPOS = {"art": ["AM", "AR"], "lib": ["LI", "CA"], "pon": ["PO"], "proc": ["PR"]}   # apartados del tablero
prod = {}
for k, sub in claves_de(r23):
    u = sub.drop_duplicates("uid")
    porA = {}
    for a in ANIOS_PROD:
        x, xs = u[u.anio == a], sub[sub.anio == a]
        art = x[x.clase == "articulo"]
        aut_art = xs[xs.clase == "articulo"].docente_id.nunique()
        n_pl = planta.get(k, {}).get(str(a))
        porA[str(a)] = {
            "t": {t: int((x.tipo == t).sum()) for t in TIPO.values()},
            "total": int(len(x)), "aut": int(xs.docente_id.nunique()), "autArt": int(aut_art), "planta": n_pl,
            "id": int((x.doi_o_isbn.fillna("").astype(str).str.strip() != "").sum()),
            "proy": int((x.proviene_proyecto == "SI").sum()),
            "grupo": int((x.grupo_investigacion.fillna("").astype(str).str.strip() != "").sum()),
            "art": {"n": int(len(art)), "est": int((pd.to_numeric(art.autores_estudiantes, errors="coerce") > 0).sum()),
                    "aa": int((art.acceso_abierto == "SI").sum()), "proy": int((art.proviene_proyecto == "SI").sum()),
                    "cuartil": {q: int((art.cuartil == q).sum()) for q in ["Q1", "Q2", "Q3", "Q4", "WOS", "WOS-ESCI", "SIN CUARTIL", "PROCEEDING"]},
                    "nivel": {nv: int((art.nivel_nombre == nv).sum()) for nv in art.nivel_nombre.dropna().unique()}},
        }
    # Docentes distintos con al menos un producto de cada apartado: [hasta el año, solo en el año].
    aut_sub = {}
    for s, tipos in SUB_TIPOS.items():
        xs = sub[sub.tipo.isin(tipos)]
        aut_sub[s] = {str(a): [int(xs[xs.anio <= a].docente_id.nunique()), int(xs[xs.anio == a].docente_id.nunique())]
                      for a in ANIOS_PROD}
    prod[k] = {"anios": porA, "autRango": int(sub.docente_id.nunique()), "totalRango": int(u.uid.nunique()),
               "autSub": aut_sub}

# ===================================================== R22 · proyectos de investigación
r22 = leer("R22_corregido")
r22["uid"] = r22.origen + ":" + r22.proyecto_id.astype(str)
nombres = lambda s: {re.sub(r"\s*\(.*\)$", "", x).strip() for x in str(s).split("; ") if x.strip()} if isinstance(s, str) else set()
r22["prof"] = r22.profesores.map(nombres)
proy = {}
for k, sub in claves_de(r22):
    porA = {}
    for a, g in sub.groupby("anio"):
        u = g.drop_duplicates("uid")
        porA[str(int(a))] = {"total": int(len(u)), "ini": int((u.iniciado_en_el_anio == "SI").sum()),
                             "ej": int((u.estado != "FINALIZADO").sum()), "fin": int((u.estado == "FINALIZADO").sum()),
                             "prof": len(set().union(*g.prof))}
    ult = sub[sub.anio == sub.anio.max()].drop_duplicates("uid")
    u = sub.drop_duplicates("uid")
    desde = int(sub.anio.min())
    proy[k] = {"anios": porA, "rango": {
        "total": int(len(u)), "ini": int((pd.to_datetime(u.fecha_inicio).dt.year >= desde).sum()),
        "ej": int((ult.estado != "FINALIZADO").sum()),
        "fin": int(sub[sub.estado == "FINALIZADO"].uid.nunique()), "prof": len(set().union(*sub.prof))}}
pcar = r22.groupby("uid").clave.apply(lambda s: "+".join(sorted(set(s), key=CARRERAS_K.index)))
# Docentes que integran cada proyecto en cada carrera, modalidad y facultad (en todo su periodo de ejecución).
pdoc = defaultdict(dict)
for k, sub in claves_de(r22):
    for uid, g in sub.groupby("uid"):
        pdoc[uid][k] = len(set().union(*g.prof))
pitems = []
for uid, g in r22.groupby("uid"):
    p = g.iloc[0]
    est_anio = {str(int(a)): int(h.estado.iloc[0] == "FINALIZADO") for a, h in g.groupby("anio")}
    pitems.append([p.origen, txt(p.titulo), txt(p.linea), txt(p.grupo), txt(p.financiamiento),
                   str(p.fecha_inicio)[:10], str(p.fecha_fin)[:10], est_anio, pcar[uid], pdoc[uid]])
RANGO_PROY = [int(r22.anio.min()), int(r22.anio.max())]

escribir_js("informes-data.js", "FACS_INF", {
    "minBase": MIN_BASE, "enCurso": sorted(EN_CURSO), "etiquetas": etiquetas,
    "perm": perm, "des": des, "delta": delta, "tit": tit_c,
    "afin": afin, "afinDet": afin_det, "afinMetodo": "CACES" if CACES else "SGA",
    "prod": prod, "prodItems": items, "prodAnios": ANIOS_PROD,
    "proy": proy, "proyItems": pitems, "proyRango": RANGO_PROY,
}, "05c_informes_sga.py", "Indicadores con la metodología de los informes del SGA (R02, R11, R16, R19, R22, R23). "
   "Solo agregados; sin nombres de personas.")
print(f"Supresión (umbral + complementaria): permanencia {oc_perm}, deserción {oc_des}, titulación {oc_tit} celdas")

# --------------------------------------------- control contra los PDF de Educación 2019 (carrera 156)
def chk(nombre, real, esperado):
    print(f"  {'OK ' if real == esperado else 'DIF'} {nombre}: {real}" + ("" if real == esperado else f" (informe {esperado})"))


print("Control Educación 2019 frente a los informes del SGA:")
chk("permanencia 1S-2026 [NE1, NE2]", perm["EDU19"].get("1S-2026"), [213, 183])
chk("deserción 1S-2024 [NEG Ai, desertores]", des["EDU19"].get("1S-2024"), [182, 65])
chk("titulación 1S-2021 [TE, NET]", tit_c["EDU19"].get("1S-2021", [None, None])[:2], [286, 175])
if not CACES:   # el informe FR0108 del SGA; con el cálculo del CACES las cifras cambian a propósito
    chk("afinidad 1S-2026 [TA, TAAF]", afin["EDU19"].get("1S-2026"), [25, 24])
print("Afinidad:", "cálculo del CACES (R11_afinidad_CACES_FACE)" if CACES else "cálculo del reporte del SGA (R11_afinidad_FACE_CORREGIDO)")
chk("proyectos rango [total, profesores]", [proy["EDU19"]["rango"]["total"], proy["EDU19"]["rango"]["prof"]], [32, 27])
