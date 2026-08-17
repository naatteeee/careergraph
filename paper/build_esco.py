import pandas as pd, json, os

path = "data/esco/skills_en.csv"
print("Using:", path)

df = pd.read_csv(path)
print("Columns:", list(df.columns))

def find_col(*names):
    for n in names:
        for c in df.columns:
            if c.strip().lower() == n.lower():
                return c
    return None

col_pref = find_col("preferredLabel", "preferred_label")
col_alt  = find_col("altLabels", "alternative_labels", "altLabel")
col_uri  = find_col("conceptUri", "concept_uri", "uri")
print("Detected ->", col_pref, "|", col_alt, "|", col_uri)

taxonomy = {}
for _, row in df.iterrows():
    pref = str(row[col_pref]).strip().lower()
    if not pref or pref == "nan":
        continue
    forms = {pref}
    if col_alt and pd.notna(row[col_alt]):
        for a in str(row[col_alt]).replace("|", "\n").split("\n"):
            a = a.strip().lower()
            if len(a) > 2:
                forms.add(a)
    taxonomy[pref] = {
        "uri": str(row[col_uri]) if col_uri else "",
        "forms": sorted(f for f in forms if len(f) > 2),
    }

os.makedirs("data", exist_ok=True)
json.dump(taxonomy, open("data/esco_taxonomy.json", "w", encoding="utf-8"),
          ensure_ascii=False)
print("Skills:", len(taxonomy))
print("Surface forms:", sum(len(v["forms"]) for v in taxonomy.values()))