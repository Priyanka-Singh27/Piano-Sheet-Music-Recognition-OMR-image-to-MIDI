import json, sys
from eval_stage1_preds import evaluate
from confidence_flags import low_confidence_flags

path = sys.argv[1]
rows = evaluate(path)
data = {r["idx"]: r for r in json.load(open(path, encoding="utf-8"))}

bad = [r for r in rows if not r["parsed"]]
print("\nunparsable (idx, spine_ok):", [(r["idx"], r["spine_ok"]) for r in bad])
print("spine_ok False but still parsed:",
      sum(1 for r in rows if r["parsed"] and r["spine_ok"] is False))

n_flags = {r["idx"]: len(low_confidence_flags(data[r["idx"]]["tokens"],
                                              data[r["idx"]]["conf"])) for r in rows}
perfect = [r for r in rows if r["f1"] == 1.0]
wrong = [r for r in rows if r["f1"] < 1.0]
mean = lambda xs: sum(xs) / len(xs) if xs else 0.0
print("\nflags per system (conf < 0.7):")
print("  exact-match systems :", round(mean([n_flags[r['idx']] for r in perfect]), 3))
print("  systems with errors :", round(mean([n_flags[r['idx']] for r in wrong]), 3))
print("  % of error systems with >= 1 flag:",
      round(100 * mean([1 if n_flags[r['idx']] else 0 for r in wrong]), 1))
print("  % of exact systems with >= 1 flag:",
      round(100 * mean([1 if n_flags[r['idx']] else 0 for r in perfect]), 1))