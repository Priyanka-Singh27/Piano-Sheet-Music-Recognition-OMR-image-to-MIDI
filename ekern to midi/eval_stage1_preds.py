import json, os, sys, tempfile
from kernpy import get_kern_from_ekern
from music21 import converter
from f1_eval import extract_notes, prf1


def ekern_to_score(text, tmpdir, tag):
    kern = get_kern_from_ekern(text).replace("**kern_1.0", "**kern")
    path = os.path.join(tmpdir, f"{tag}.krn")
    with open(path, "w", encoding="utf-8") as f:
        f.write(kern)
    score = converter.parse(path, forceSource=True)
    if len(score.parts) == 0:
        raise ValueError("zero parts after parsing")
    return score


def evaluate(preds_path):
    with open(preds_path, encoding="utf-8") as f:
        data = json.load(f)

    rows, ref_failed, pred_failed = [], 0, 0
    with tempfile.TemporaryDirectory() as tmp:
        for k, rec in enumerate(data):
            try:
                gt = extract_notes(ekern_to_score(rec["ref"], tmp, f"ref_{k}"))
            except Exception:
                ref_failed += 1          # can't score without a usable reference
                continue
            try:
                pred = extract_notes(ekern_to_score(rec["pred"], tmp, f"pred_{k}"))
                p, r, f1 = prf1(pred, gt)
                parsed = True
            except Exception:
                p = r = f1 = 0.0         # unparsable prediction counts as total miss
                parsed = False
                pred_failed += 1
            rows.append({"idx": rec["idx"], "precision": p, "recall": r, "f1": f1,
                         "parsed": parsed, "spine_ok": rec.get("spine_ok")})

    n = len(rows)
    ok = [r for r in rows if r["parsed"]]
    print(f"{preds_path}")
    print(f"  scored: {n}/{len(data)}  (reference unparsable: {ref_failed})")
    print(f"  prediction unparsable (scored 0): {pred_failed}")
    print(f"  mean F1, all scored:        {sum(r['f1'] for r in rows)/n:.4f}")
    if ok:
        print(f"  mean F1, parsable only:     {sum(r['f1'] for r in ok)/len(ok):.4f}")
        print(f"  mean precision / recall:    {sum(r['precision'] for r in ok)/len(ok):.4f} / "
              f"{sum(r['recall'] for r in ok)/len(ok):.4f}")
    print(f"  exact-note matches (F1=1):  {sum(1 for r in rows if r['f1']==1.0)}/{n}")
    return rows


if __name__ == "__main__":
    evaluate(sys.argv[1])