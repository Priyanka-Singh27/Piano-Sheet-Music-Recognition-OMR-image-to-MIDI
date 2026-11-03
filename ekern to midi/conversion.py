import json
import os
from music21 import converter, bar
import kernpy as kp

from correction_rules import measure_duration_check, key_signature_check
from confidence_flags import low_confidence_flags

def _safe_write_midi(score, midi_path):
    """
    Writes MIDI, falling back to stripping malformed repeat barlines
    if music21's repeat-expansion fails (common on real transcription data).
    """
    try:
        score.write('midi', fp=midi_path)
        return False
    except Exception:
        for m in score.recurse().getElementsByClass('Measure'):
            if isinstance(m.leftBarline, bar.Repeat):
                m.leftBarline = bar.Barline('regular')
            if isinstance(m.rightBarline, bar.Repeat):
                m.rightBarline = bar.Barline('regular')
        score.write('midi', fp=midi_path)
        return True


def convert(kern_text, piece_id, output_dir="outputs", tokens=None, conf=None):
    os.makedirs(output_dir, exist_ok=True)

    temp_krn_path = os.path.join(output_dir, f"{piece_id}.krn")
    with open(temp_krn_path, "w", encoding="utf-8") as f:
        f.write(kern_text)

    score = converter.parse(temp_krn_path)

    if len(score.parts) == 0:
        raise ValueError(f"[{piece_id}] parsed to zero parts — likely a malformed **kern header or separator issue")

    duration_flags = measure_duration_check(score)
    key_flags = key_signature_check(score)
    all_flags = duration_flags + key_flags

    # new: Stage 1 confidence flags, only when Stage 1 supplied them
    if tokens is not None and conf is not None:
        all_flags += low_confidence_flags(tokens, conf)

    musicxml_path = os.path.join(output_dir, f"{piece_id}.musicxml")
    midi_path = os.path.join(output_dir, f"{piece_id}.mid")
    flagged_path = os.path.join(output_dir, f"{piece_id}_flagged_tokens.json")

    score.write('musicxml', fp=musicxml_path)

    repeats_stripped = _safe_write_midi(score, midi_path)
    if repeats_stripped:
        all_flags.append({"issue": "malformed_repeats_stripped_for_midi"})

    with open(flagged_path, "w", encoding="utf-8") as f:
        json.dump(all_flags, f, indent=2)

    return musicxml_path, midi_path, flagged_path


def convert_from_ekern(ekern_text, piece_id, output_dir="outputs", tokens=None, conf=None):
    kern_text = kp.get_kern_from_ekern(ekern_text)
    kern_text = kern_text.replace("**kern_1.0", "**kern")
    return convert(kern_text, piece_id=piece_id, output_dir=output_dir,
                   tokens=tokens, conf=conf)


if __name__ == "__main__":
    from datasets import load_dataset

    dataset = load_dataset("PRAIG/camera-grandstaff")
    train = dataset["train"]

    N = 20
    results = []

    for i in range(N):
        piece_id = f"real_{i:04d}"
        try:
            musicxml_file, midi_file, flagged_file = convert_from_ekern(
                train[i]["transcription"], piece_id=piece_id
            )
            with open(flagged_file, encoding="utf-8") as f:
                flags = json.load(f)
            results.append({"piece_id": piece_id, "status": "ok", "num_flags": len(flags)})
        except Exception as e:
            results.append({"piece_id": piece_id, "status": "error", "error": str(e)})

    ok = [r for r in results if r["status"] == "ok"]
    errors = [r for r in results if r["status"] == "error"]

    print(f"\n{len(ok)}/{N} converted successfully")
    print(f"{len(errors)}/{N} failed")

    for r in errors:
        print(r["piece_id"], "->", r["error"])