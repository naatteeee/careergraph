import pandas as pd, json, re, html

df = pd.read_csv("data/archive/postings.csv",
                 usecols=["job_id", "title", "company_name", "description", "location"])

df = df.dropna(subset=["description"])
df = df[df["description"].str.len().between(1500, 6000)]   # annotatable length
df = df.drop_duplicates(subset=["description"])

sample = df.sample(n=120, random_state=42)   # 120 = 100 target + 20 spare

def clean(t):
    t = html.unescape(str(t))
    return re.sub(r"\s+", " ", t).strip()

with open("data/sample_120.jsonl", "w", encoding="utf-8") as f:
    for _, r in sample.iterrows():
        f.write(json.dumps({
            "id": str(r["job_id"]),
            "title": clean(r["title"]),
            "company": clean(r["company_name"]),
            "text": clean(r["description"]),
        }, ensure_ascii=False) + "\n")

print("wrote", len(sample), "ads")
print("mean length:", int(sample["description"].str.len().mean()))
