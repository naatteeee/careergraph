"""
Evaluation: concept-level P/R/F1 under exact and relaxed matching,
plus hybrid union and McNemar significance tests.

Relaxed matching counts a prediction as correct if it exactly matches a gold
skill OR if one string contains the other OR token-level Jaccard >= 0.6.
This mirrors the Exact/Relaxed F1 protocol used in comparable extraction work
and avoids penalising trivial wording differences
("apa accreditation" vs "apa accredited program").
"""
import json, re, csv, os
from itertools import combinations
from collections import Counter

os.makedirs("results", exist_ok=True)

STOP = {"a", "an", "the", "of", "in", "and", "to", "for", "with", "on"}


def norm(s):
    s = str(s).strip().lower()
    s = re.sub(r"^oov:\s*", "", s)
    s = re.sub(r"[^a-z0-9+#. ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def toks(s):
    return {t for t in norm(s).split() if t not in STOP and len(t) > 1}


def load(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        d[str(r["id"])] = sorted({norm(s) for s in r["skills"] if norm(s)})
    return d


def relaxed_match(p, g):
    if p == g:
        return True
    if len(p) > 4 and len(g) > 4 and (p in g or g in p):
        return True
    tp, tg = toks(p), toks(g)
    if not tp or not tg:
        return False
    j = len(tp & tg) / len(tp | tg)
    return j >= 0.6


def score(gold, pred, relaxed):
    TP = FP = FN = 0
    matched_detail = {}
    for aid, gs in gold.items():
        ps = pred.get(aid, [])
        g_left = list(gs)
        hits = []
        for p in ps:
            found = None
            for g in g_left:
                if (relaxed_match(p, g) if relaxed else p == g):
                    found = g
                    break
            if found:
                hits.append((p, found))
                g_left.remove(found)
            else:
                FP += 1
        TP += len(hits)
        FN += len(g_left)
        matched_detail[aid] = (hits, g_left, ps)
    P = TP / (TP + FP) if TP + FP else 0.0
    R = TP / (TP + FN) if TP + FN else 0.0
    F = 2 * P * R / (P + R) if P + R else 0.0
    return dict(TP=TP, FP=FP, FN=FN, P=round(P, 3), R=round(R, 3), F1=round(F, 3))


def found_set(gold, pred, relaxed):
    """For each (ad, gold skill) instance, did this system find it?"""
    out = {}
    for aid, gs in gold.items():
        ps = pred.get(aid, [])
        for g in gs:
            hit = any((relaxed_match(p, g) if relaxed else p == g) for p in ps)
            out[(aid, g)] = hit
    return out


def mcnemar(a, b):
    only_a = sum(1 for k in a if a[k] and not b[k])
    only_b = sum(1 for k in a if b[k] and not a[k])
    n = only_a + only_b
    if n == 0:
        return dict(b=only_a, c=only_b, chi2=0.0, p=1.0)
    chi2 = (abs(only_a - only_b) - 1) ** 2 / n
    try:
        from scipy.stats import chi2 as chi2dist
        p = float(1 - chi2dist.cdf(chi2, 1))
    except ImportError:
        p = None
    return dict(b=only_a, c=only_b, chi2=round(chi2, 2),
                p=(f"{p:.2e}" if p is not None and p < 1e-4 else
                   (round(p, 5) if p is not None else "scipy missing")))


def main():
    gold = load("data/gold.jsonl")
    lex = load("data/preds_lexicon.jsonl")
    llm = load("data/preds_llm.jsonl")
    union = {aid: sorted(set(lex.get(aid, [])) | set(llm.get(aid, []))) for aid in gold}

    systems = {"Lexicon (ESCO)": lex, "LLM (zero-shot)": llm, "Union (hybrid)": union}

    n = len(gold)
    gtot = sum(len(v) for v in gold.values())
    print("=" * 66)
    print(f"Ads: {n} | gold skills: {gtot} (mean {gtot/n:.1f}/ad)")
    for name, s in systems.items():
        t = sum(len(v) for v in s.values())
        print(f"  {name:18s} predicted {t:4d} (mean {t/n:.1f}/ad)")
    print("=" * 66)

    rows = []
    for relaxed in (False, True):
        label = "RELAXED" if relaxed else "EXACT"
        print(f"\n--- {label} MATCH ---")
        print(f"{'System':20s} {'P':>6s} {'R':>6s} {'F1':>6s}   {'TP':>4s} {'FP':>4s} {'FN':>4s}")
        for name, s in systems.items():
            r = score(gold, s, relaxed)
            r["System"] = name
            r["Match"] = label
            rows.append(r)
            print(f"{name:20s} {r['P']:6.3f} {r['R']:6.3f} {r['F1']:6.3f}   "
                  f"{r['TP']:4d} {r['FP']:4d} {r['FN']:4d}")

        print(f"\n  McNemar ({label}):")
        fs = {k: found_set(gold, v, relaxed) for k, v in systems.items()}
        for a, b in combinations(systems, 2):
            t = mcnemar(fs[a], fs[b])
            print(f"    {a} vs {b}: only-first={t['b']} only-second={t['c']} "
                  f"chi2={t['chi2']} p={t['p']}")

    with open("results/main_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Match", "System", "P", "R", "F1", "TP", "FP", "FN"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})

    # ---- false-positive offenders (lexicon) ----
    fp_counter = Counter()
    for aid, gs in gold.items():
        for p in lex.get(aid, []):
            if not any(relaxed_match(p, g) for g in gs):
                fp_counter[p] += 1
    print("\n--- top lexicon false positives (relaxed) ---")
    for k, v in fp_counter.most_common(15):
        print(f"  {v:2d}x  {k}")
    total_fp = sum(fp_counter.values())
    top5 = sum(v for _, v in fp_counter.most_common(5))
    print(f"  top-5 concepts account for {top5}/{total_fp} = {top5/max(total_fp,1):.0%} of FPs")

    with open("results/lexicon_false_positives.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["concept", "count"])
        for k, v in fp_counter.most_common():
            w.writerow([k, v])

    # ---- per-ad recall, to show variance ----
    with open("results/per_ad.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ad_id", "gold_n", "lex_n", "llm_n", "lex_recall", "llm_recall"])
        for aid, gs in gold.items():
            lr = sum(1 for g in gs if any(relaxed_match(p, g) for p in lex.get(aid, [])))
            mr = sum(1 for g in gs if any(relaxed_match(p, g) for p in llm.get(aid, [])))
            w.writerow([aid, len(gs), len(lex.get(aid, [])), len(llm.get(aid, [])),
                        round(lr/max(len(gs),1), 3), round(mr/max(len(gs),1), 3)])

    zero_lex = sum(1 for aid, gs in gold.items()
                   if not any(any(relaxed_match(p, g) for p in lex.get(aid, [])) for g in gs))
    print(f"\nAds where lexicon found ZERO gold skills: {zero_lex}/{n}")

    json.dump({"n_ads": n, "gold_skills": gtot, "results": rows},
              open("results/summary.json", "w"), indent=2)
    print("\nwrote results/main_table.csv, lexicon_false_positives.csv, per_ad.csv")


if __name__ == "__main__":
    main()
