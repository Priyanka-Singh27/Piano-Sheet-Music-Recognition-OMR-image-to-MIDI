import json
d = {r["idx"]: r for r in json.load(open("stage1_preds/preds_runC_val1000.json", encoding="utf-8"))}
for i in (1237, 3464, 3500, 2371, 2710, 4301):
    r = d[i]
    print(i, "n_tokens:", len(r["tokens"]), "spine_ok:", r["spine_ok"], "tail:", r["tokens"][-6:])