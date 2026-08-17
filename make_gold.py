import csv, json

rows = list(csv.DictReader(open("data/annotation_done.csv", encoding="utf-8-sig")))

n = 0
with open("data/gold.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        raw = r.get("final_skills", "").strip()
        if not raw:
            continue  # skip rows you didn't annotate
        skills = [s.strip().lower() for s in raw.split(";") if s.strip()]
        skills = [s[4:].strip() if s.startswith("oov:") else s for s in skills]
        f.write(json.dumps({"id": r["id"], "skills": sorted(set(skills))},
                           ensure_ascii=False) + "\n")
        n += 1

print("wrote", n, "annotated ads to data/gold.jsonl")