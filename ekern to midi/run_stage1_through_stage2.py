import inspect, json, os, sys, tempfile
from collections import Counter
from music21 import converter

from conversion import convert_from_ekern
from correction_rules import measure_duration_check
from eval_stage1_preds import ekern_to_score
from f1_eval import extract_notes, prf1


def structure_report(pred_text):
    """Heuristic column check on predicted eKern: follows *^ (split) and *v (merge)."""
    lines = pred_text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    ends_ok = bool(lines) and all(c == "*-" for c in lines[-1].split("\t"))
    expected = None
    for i, line in enumerate(lines):
        cells = line.split("\t")
        if expected is not None and len(cells) != expected:
            return {"ends_with_terminator": ends_ok, "first_bad_line": i,
                    "found_cols": len(cells), "expected_cols": expected, "line": line[:70]}
        splits = sum(1 for c in cells if c == "*^")
        merges, run = 0, 0
        for c in cells + [None]:
            if c == "*v":
                run += 1
            else:
                merges += max(run - 1, 0)
                run = 0
        expected = len(cells) + splits - merges
    return {"ends_with_terminator": ends_ok, "first_bad_line": None}


def flag_table(conv, test, label):
    flagged = [r for r in conv if test(r)]
    wrong = [r for r in conv if r["f1"] < 1.0]
    both = [r for r in flagged if r["f1"] < 1.0]
    prec = len(both) / len(flagged) if flagged else float("nan")
    rec = len(both) / len(wrong) if wrong else float("nan")
    print(f"  {label:36s} flagged {len(flagged):4d}   wrong|flagged {prec:.2f}   flagged|wrong {rec:.2f}")


def main(preds_path, out_dir):
    if "tokens" not in inspect.signature(convert_from_ekern).parameters:
        sys.exit("convert_from_ekern has no tokens/conf parameters yet: apply the conversion.py edit first")
    data = json.load(open(preds_path, encoding="utf-8"))
    os.makedirs(out_dir, exist_ok=True)
    rows, failures = [], []

    with tempfile.TemporaryDirectory() as tmp:
        for k, rec in enumerate(data):
            try:
                gt_score = ekern_to_score(rec["ref"], tmp, f"ref_{k}")
            except Exception:
                continue                                   # unusable reference
            gt_notes = extract_notes(gt_score)
            gt_dur = len(measure_duration_check(gt_score))
            row = {"idx": rec["idx"], "n_gt": sum(gt_notes.values()), "converted": False,
                   "tp": 0, "n_pred": 0, "f1": 0.0, "dur_pred": 0, "dur_ref": gt_dur,
                   "key": 0, "lowconf": 0, "repeats": 0}
            pid = f"s{rec['idx']:05d}"
            try:
                _, _, flag_path = convert_from_ekern(rec["pred"], pid, output_dir=out_dir,
                                                     tokens=rec["tokens"], conf=rec["conf"])
                flags = json.load(open(flag_path, encoding="utf-8"))
                pred_score = converter.parse(os.path.join(out_dir, f"{pid}.krn"), forceSource=True)
                pred_notes = extract_notes(pred_score)
                _, _, f1 = prf1(pred_notes, gt_notes)
                c = Counter(fl["issue"] for fl in flags)
                row.update(converted=True, tp=sum((pred_notes & gt_notes).values()),
                           n_pred=sum(pred_notes.values()), f1=f1,
                           dur_pred=c["duration_mismatch"],
                           key=c["accidental_outside_key_signature"],
                           lowconf=c["low_confidence_token"],
                           repeats=c["malformed_repeats_stripped_for_midi"])
            except Exception as e:
                failures.append({"idx": rec["idx"], "spine_ok": rec.get("spine_ok"),
                                 "n_tokens": len(rec["tokens"]),
                                 "error": f"{type(e).__name__}: {str(e)[:150]}",
                                 "structure": structure_report(rec["pred"])})
            rows.append(row)

    n = len(rows)
    conv = [r for r in rows if r["converted"]]
    print(f"\n{preds_path}")
    print(f"scored {n}   converted {len(conv)}   failed {len(failures)}")

    # micro vs macro F1 (failed systems contribute misses, no predicted notes)
    tp, npred, ngt = (sum(r[k] for r in rows) for k in ("tp", "n_pred", "n_gt"))
    P = tp / npred if npred else 0.0
    R = tp / ngt if ngt else 0.0
    print(f"\nmicro  P {P:.4f}  R {R:.4f}  F1 {2*P*R/(P+R) if P+R else 0:.4f}")
    print(f"macro  F1 {sum(r['f1'] for r in rows)/n:.4f}   (failed systems count as 0)")

    # F1 by system size (reference note count), quartiles
    sizes = sorted(r["n_gt"] for r in rows)
    cuts = [sizes[n * i // 4] for i in (1, 2, 3)]
    print(f"\nF1 by size (reference notes; quartile cuts {cuts})")
    for b in range(4):
        grp = [r for r in rows if sum(r["n_gt"] >= c for c in cuts) == b]
        if grp:
            print(f"  Q{b+1}: {len(grp):4d} systems  mean F1 {sum(r['f1'] for r in grp)/len(grp):.4f}"
                  f"  exact {sum(1 for r in grp if r['f1']==1.0):4d}"
                  f"  failed {sum(1 for r in grp if not r['converted'])}")

    # do the flags land in the systems that are actually wrong?
    wrong = sum(1 for r in conv if r["f1"] < 1.0)
    print(f"\nflags vs errors, converted systems only (wrong = F1 < 1: {wrong}/{len(conv)} = {wrong/len(conv):.2f})")
    flag_table(conv, lambda r: r["dur_pred"] > 0, "duration_mismatch (any)")
    flag_table(conv, lambda r: r["dur_pred"] > r["dur_ref"], "duration_mismatch (more than ref)")
    flag_table(conv, lambda r: r["key"] > 0, "accidental_outside_key_signature")
    flag_table(conv, lambda r: r["lowconf"] > 0, "low_confidence_token (< 0.7)")
    flag_table(conv, lambda r: r["repeats"] > 0, "malformed_repeats_stripped")

    print("\nfailed predictions")
    for fl in failures:
        print(" ", fl["idx"], "spine_ok", fl["spine_ok"], "tokens", fl["n_tokens"])
        print("     ", fl["error"])
        print("     ", fl["structure"])

    tag = os.path.basename(preds_path).replace(".json", "")
    json.dump({"rows": rows, "failures": failures},
              open(os.path.join(out_dir, f"summary_{tag}.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])