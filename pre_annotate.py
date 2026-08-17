import json, re, csv

taxonomy = json.load(open("data/esco_taxonomy.json", encoding="utf-8"))

# surface form -> canonical skill
index, maxlen = {}, 1
for skill, v in taxonomy.items():
    for f in v["forms"]:
        index[f] = skill
        maxlen = max(maxlen, len(f.split()))
maxlen = min(maxlen, 6)
print("index size:", len(index), "| max n-gram:", maxlen)

token_re = re.compile(r"[a-z0-9+#.]+")

def extract(text):
    toks = token_re.findall(text.lower())
    found = set()
    for i in range(len(toks)):
        for n in range(1, maxlen + 1):
            if i + n > len(toks):
                break
            hit = index.get(" ".join(toks[i:i+n]))
            if hit:
                found.add(hit)
    return sorted(found)

ads = [json.loads(l) for l in open("data/sample_120.jsonl", encoding="utf-8")]

with open("data/annotation_sheet.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "title", "company", "predicted_skills", "final_skills", "notes", "text"])
    for a in ads:
        preds = extract(a["text"])
        w.writerow([a["id"], a["title"], a["company"],
                    "; ".join(preds), "; ".join(preds), "", a["text"]])

print("wrote data/annotation_sheet.csv")
print("mean predicted skills/ad:",
      round(sum(len(extract(a['text'])) for a in ads) / len(ads), 1))