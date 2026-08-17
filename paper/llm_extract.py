import json, os, re, time, sys
from dotenv import load_dotenv

load_dotenv()

MODEL     = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")
BASE_URL  = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
API_KEY   = os.environ.get("OPENAI_API_KEY", "")
MAX_CHARS = 6000
SLEEP     = 1.0

PROMPT = """You are extracting skills from a job advertisement.

List every skill, tool, technology, programming language, certification, or
professional competence that the advertisement states as a requirement,
preference, or responsibility of the role.

Rules:
- Only list skills the advertisement actually states. Do not infer skills.
- Do not list the job title itself.
- Ignore skills mentioned only in equal-opportunity statements, benefits
  sections, or legal disclaimers.
- Use short skill names (1-4 words), lowercase.

Return ONLY a JSON array of strings. No explanation, no markdown.

Job advertisement:
\"\"\"{text}\"\"\""""


def parse(raw):
    s = raw.strip()
    s = re.sub(r"^```(?:json)?", "", s).strip()
    s = re.sub(r"```$", "", s).strip()
    try:
        val = json.loads(s)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", s, re.S)
        if not m:
            return None
        try:
            val = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(val, list):
        return None
    return [str(x).strip().lower() for x in val if str(x).strip()]


def call_llm(text):
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.format(text=text[:MAX_CHARS])}],
        temperature=0,
    )
    raw = resp.choices[0].message.content.strip()
    usage = {"in": getattr(resp.usage, "prompt_tokens", 0),
             "out": getattr(resp.usage, "completion_tokens", 0)}
    return parse(raw), usage, raw


def main():
    if not API_KEY:
        sys.exit("OPENAI_API_KEY missing from .env")

    ads = {}
    for line in open("data/sample_120.jsonl", encoding="utf-8"):
        a = json.loads(line)
        ads[a["id"]] = a

    if os.path.exists("data/gold.jsonl"):
        ids = [json.loads(l)["id"] for l in open("data/gold.jsonl", encoding="utf-8")]
        print(f"Processing {len(ids)} annotated ads")
    else:
        ids = list(ads)[:5]
        print("gold.jsonl not found - DRY RUN on 5 ads")

    out = []
    log = {"model": MODEL, "n": 0, "parse_failures": 0, "retries": 0,
           "tokens_in": 0, "tokens_out": 0, "seconds": 0.0}

    t0 = time.time()
    for i, aid in enumerate(ids, 1):
        ad = ads.get(aid)
        if ad is None:
            print(f"  !! id {aid} not found, skipping")
            continue
        skills, usage, raw = call_llm(ad["text"])
        if skills is None:
            log["retries"] += 1
            time.sleep(2)
            skills, u2, raw = call_llm(ad["text"])
            usage["in"] += u2["in"]; usage["out"] += u2["out"]
            if skills is None:
                log["parse_failures"] += 1
                skills = []
        out.append({"id": aid, "skills": skills, "raw": raw})
        log["tokens_in"] += usage["in"]; log["tokens_out"] += usage["out"]
        log["n"] += 1
        print(f"[{i}/{len(ids)}] {ad['title'][:45]:45s} -> {len(skills)} skills")
        time.sleep(SLEEP)

    log["seconds"] = round(time.time() - t0, 1)
    log["seconds_per_ad"] = round(log["seconds"] / max(log["n"], 1), 2)

    with open("data/preds_llm.jsonl", "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(log, open("data/llm_run_log.json", "w"), indent=2)

    print("\n--- run log ---")
    print(json.dumps(log, indent=2))


if __name__ == "__main__":
    main()