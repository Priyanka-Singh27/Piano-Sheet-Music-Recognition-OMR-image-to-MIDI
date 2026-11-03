#Batch scaling — 200 pieces, with a real summary
#converion.py (from ekern: grandstaff to midi) is working on 20 pieces, now lets check on more pieces to get a more meaningful sense of how often issues/repeat-stripping actually occur.
#Rather than just a pass/fail count, this version tracks what kinds of flags show up and how often — useful both for debugging and for actual numbers you can cite in your paper's write-up later.

# batch_test.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import json
from datasets import load_dataset
from conversion import convert_from_ekern

dataset = load_dataset("PRAIG/camera-grandstaff")
train = dataset["train"]

N = 200
results = []

for i in range(N):
    piece_id = f"batch_{i:04d}"
    try:
        musicxml_file, midi_file, flagged_file = convert_from_ekern(
            train[i]["transcription"], piece_id=piece_id
        )
        with open(flagged_file, encoding="utf-8") as f:
            flags = json.load(f)
        results.append({"piece_id": piece_id, "status": "ok", "flags": flags})
    except Exception as e:
        results.append({"piece_id": piece_id, "status": "error", "error": str(e)})

ok = [r for r in results if r["status"] == "ok"]
errors = [r for r in results if r["status"] == "error"]

print(f"\n=== Summary over {N} pieces ===")
print(f"Succeeded: {len(ok)}/{N}")
print(f"Failed:    {len(errors)}/{N}")

# Break down flags by issue type across all successful conversions
issue_counts = {}
pieces_with_any_flag = 0

for r in ok:
    if r["flags"]:
        pieces_with_any_flag += 1
    for flag in r["flags"]:
        issue = flag.get("issue", "unknown")
        issue_counts[issue] = issue_counts.get(issue, 0) + 1

print(f"\nPieces with at least one flag: {pieces_with_any_flag}/{len(ok)}")
print("Flag counts by type:")
for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
    print(f"  {issue}: {count}")

if errors:
    print("\n=== Errors ===")
    for r in errors:
        print(f"{r['piece_id']}: {r['error']}")

# Save full results for later reference
with open("batch_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("\nFull results saved to batch_results.json")