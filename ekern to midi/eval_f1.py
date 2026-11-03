import sys, os, json
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datasets import load_dataset
from music21 import converter
from conversion import convert_from_ekern
from f1_eval import extract_notes, prf1

N = 100
OUT = os.path.join(os.path.dirname(__file__), "eval_outputs")

test = load_dataset("PRAIG/camera-grandstaff")["test"]

rows, errors = [], []
for i in range(N):
    piece_id = f"eval_{i:04d}"
    try:
        musicxml_path, _, _ = convert_from_ekern(
            test[i]["transcription"], piece_id, output_dir=OUT)
        gt_score = converter.parse(os.path.join(OUT, f"{piece_id}.krn"))
        pred_score = converter.parse(musicxml_path)
        p, r, f = prf1(extract_notes(pred_score), extract_notes(gt_score))
        rows.append({"piece_id": piece_id, "precision": p, "recall": r, "f1": f})
    except Exception as e:
        errors.append((piece_id, str(e)))

n = len(rows)
print(f"Evaluated {n}/{N} pieces ({len(errors)} errors)")
print(f"Mean precision: {sum(r['precision'] for r in rows)/n:.4f}")
print(f"Mean recall:    {sum(r['recall'] for r in rows)/n:.4f}")
print(f"Mean F1:        {sum(r['f1'] for r in rows)/n:.4f}")

imperfect = [r for r in rows if r["f1"] < 1.0]
print(f"Pieces with F1 < 1.0: {len(imperfect)}")
for r in imperfect[:10]:
    print("  ", r["piece_id"], round(r["f1"], 4))
for e in errors:
    print("ERROR", e)

with open(os.path.join(OUT, "f1_results.json"), "w") as f:
    json.dump(rows, f, indent=2)