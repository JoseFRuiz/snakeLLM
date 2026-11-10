"""
Analiza un archivo de resultados de matching.py.

Uso: python analisis_resultados.py [results_<modelo>_<version>.csv]
"""
import re
import sys
import pandas as pd

CSV = sys.argv[1] if len(sys.argv) > 1 else "results_claude-haiku-5-5_es_v2.csv"
UNKNOWN = "Sin identificar"

d = pd.read_csv(CSV, encoding="utf-8-sig")
d["ref"] = d["reference"].str.replace("_reference.PNG", "", regex=False)
d["is_match"] = d["is_match"].astype(str).str.lower().eq("true")
known = d[d["species"] != UNKNOWN].copy()
known["same"] = known["species"] == known["ref"]
known["correct"] = known["is_match"] == known["same"]

def pct(x):
    return f"{100 * x:.0f}%"

print(f"Archivo: {CSV}  ({len(d)} comparaciones, {d['query_image'].nunique()} fotos)\n")

# 1. Matriz: % de fotos de cada grupo que el modelo considera compatibles con cada especie
print("1. % de fotos de cada grupo juzgadas COINCIDE con cada especie de referencia")
matrix = d.pivot_table(index="species", columns="ref", values="is_match", aggfunc="mean")
print(matrix.map(pct).to_string(), "\n")

# 2. Sensibilidad, especificidad y exactitud
print("2. Desempeño por especie (solo fotos identificadas)")
rows = []
for sp in sorted(known["ref"].unique()):
    pos = known[(known["ref"] == sp) & known["same"]]
    neg = known[(known["ref"] == sp) & ~known["same"]]
    rows.append({
        "especie": sp,
        "sensibilidad": pct(pos["is_match"].mean()),
        "especificidad": pct((~neg["is_match"]).mean()),
        "exactitud": pct(known[known["ref"] == sp]["correct"].mean()),
    })
print(pd.DataFrame(rows).to_string(index=False))
pos = known[known["same"]]
neg = known[~known["same"]]
print(f"Global: sensibilidad {pct(pos['is_match'].mean())}, especificidad "
      f"{pct((~neg['is_match']).mean())}, exactitud {pct(known['correct'].mean())}\n")

# 3. Por foto: con cuántas especies coincide
print("3. Número de especies con las que coincide cada foto")
per_photo = d.groupby(["species", "query_image"]).agg(
    n_match=("is_match", "sum"),
    matched=("ref", lambda s: ", ".join(sorted(s[d.loc[s.index, "is_match"]]))),
).reset_index()
print(per_photo.pivot_table(index="species", columns="n_match", values="query_image",
                            aggfunc="count", fill_value=0).to_string())
kp = per_photo[per_photo["species"] != UNKNOWN]
correct_in = kp.apply(lambda r: r["species"] in r["matched"].split(", "), axis=1)
unique_ok = correct_in & (kp["n_match"] == 1)
print(f"Fotos identificadas: {len(kp)}. Incluyen la especie correcta: {correct_in.sum()} "
      f"({pct(correct_in.mean())}). Solo la especie correcta: {unique_ok.sum()} ({pct(unique_ok.mean())}). "
      f"Promedio de especies por foto: {kp['n_match'].mean():.1f}\n")

# 4. Pares de especies confundidos (falsos positivos)
print("4. Confusiones: fotos de la especie X juzgadas compatibles con la especie Y")
fp = known[~known["same"] & known["is_match"]]
conf = fp.groupby(["species", "ref"]).size().rename("fotos").reset_index()
totals = known.groupby("species")["query_image"].nunique()
conf["% del grupo"] = conf.apply(lambda r: pct(r["fotos"] / totals[r["species"]]), axis=1)
print(conf.sort_values("fotos", ascending=False).to_string(index=False), "\n")

# 5. Fotos sin identificar
print("5. Fotos sin identificar: especies compatibles")
up = per_photo[per_photo["species"] == UNKNOWN]
print(up["n_match"].value_counts().sort_index().rename("fotos").to_string())
print("Fotos compatibles con una sola especie:")
print(up[up["n_match"] == 1]["matched"].value_counts().to_string(), "\n")

# 6. Indicadores en las justificaciones
print("6. Indicadores en las justificaciones (fotos identificadas)")
patterns = {
    "rasgo no verificable": r"no se (?:aprecia|observa|distingue|ve|puede)|no (?:es|son) visible|no puedo (?:confirmar|verificar)|no se pueden? (?:verificar|valorar|evaluar)",
    "confianza limitada": r"no es concluyente|no concluyente|moderad|limitad|dudos|incierto|ambig",
    "ejemplar conservado": r"conservad|preservad|preservaci",
}
# (Los autores citados no sirven como indicador: el modelo cita exactamente
# a los autores de la descripción de la especie de referencia.)
text = known["result_text"].str.lower()
ind = []
for name, pat in patterns.items():
    has = text.str.contains(pat, regex=True)
    ind.append({
        "indicador": name,
        "en aciertos": pct(has[known["correct"]].mean()),
        "en errores": pct(has[~known["correct"]].mean()),
    })
print(pd.DataFrame(ind).to_string(index=False), "\n")

# 7. Rasgos citados en las justificaciones: aciertos vs errores, por especie de referencia
print("7. Rasgos citados: % de justificaciones que los mencionan (aciertos / errores)")
features = {
    "media luna": r"media luna",
    "zigzag": r"zig ?zag",
    "línea media / dividida": r"l[ií]nea media|dividid",
    "franja": r"franja",
    "banda": r"banda",
    "nuca / occipital": r"nuca|nucal|occipital",
    "parietales": r"parietal",
    "manchas fusionadas": r"fusionad",
    "color uniforme / sin marcas": r"uniforme|sin marcas|carece de marcas",
    "moteado": r"motead",
}
rows = []
for sp in sorted(known["ref"].unique()):
    sub = known[known["ref"] == sp]
    t = sub["result_text"].str.lower()
    row = {"especie": sp}
    for name, pat in features.items():
        has = t.str.contains(pat, regex=True)
        row[name] = f"{pct(has[sub['correct']].mean())} / {pct(has[~sub['correct']].mean())}"
    rows.append(row)
print(pd.DataFrame(rows).set_index("especie").T.to_string())
