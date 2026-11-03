import json, os, shutil, sys, tempfile
from conversion import convert_from_ekern


def main(preds_path, out_dir, dest_dir, limit=20):
    data = {r["idx"]: r for r in json.load(open(preds_path, encoding="utf-8"))}
    tag = os.path.basename(preds_path).replace(".json", "")
    summary = json.load(open(os.path.join(out_dir, f"summary_{tag}.json")))

    # converted systems whose notes differ from the reference, worst first
    wrong = [r for r in summary["rows"] if r["converted"] and r["f1"] < 1.0]
    wrong.sort(key=lambda r: r["f1"])
    if limit:
        wrong = wrong[:limit]

    os.makedirs(dest_dir, exist_ok=True)
    made = 0
    with tempfile.TemporaryDirectory() as tmp:
        for rank, r in enumerate(wrong, 1):
            pid = f"s{r['idx']:05d}"
            pred_mid = os.path.join(out_dir, f"{pid}.mid")
            if not os.path.exists(pred_mid):
                print("skip", pid, "- prediction MIDI not found")
                continue
            try:
                _, ref_mid, _ = convert_from_ekern(data[r["idx"]]["ref"], pid + "_ref", output_dir=tmp)
            except Exception as e:
                print("skip", pid, "- reference failed:", type(e).__name__, str(e)[:80])
                continue
            stem = f"{rank:02d}_{pid}_F{r['f1']:.2f}"
            shutil.copy(pred_mid, os.path.join(dest_dir, f"{stem}_pred.mid"))
            shutil.copy(ref_mid, os.path.join(dest_dir, f"{stem}_ref.mid"))
            made += 1
    print(f"wrote {made} pairs to {dest_dir}  (of {len(wrong)} selected, "
          f"{sum(1 for r in summary['rows'] if r['converted'] and r['f1'] < 1.0)} wrong systems in total)")


if __name__ == "__main__":
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else 20
    main(sys.argv[1], sys.argv[2], sys.argv[3], limit)