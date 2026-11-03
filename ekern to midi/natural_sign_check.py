import os, re, tempfile
from collections import Counter
from kernpy import get_kern_from_ekern
from music21 import converter

NATURAL = re.compile(r"·n(?=[\s·]|$)", re.M)      # an explicit natural sign piece in eKern


def parse_label(text, tmp, tag):
    kern = get_kern_from_ekern(text).replace("**kern_1.0", "**kern")
    path = os.path.join(tmp, f"{tag}.krn")
    with open(path, "w", encoding="utf-8") as f:
        f.write(kern)
    score = converter.parse(path, forceSource=True)
    if len(score.parts) == 0:
        raise ValueError("zero parts")
    return score


def pitch_multiset(score):
    return Counter((round(float(n.offset), 4), p.midi)
                   for n in score.flatten().notes for p in n.pitches)


def compare(labels):
    n_labels = n_notes = n_changed_notes = n_changed_labels = n_naturals = n_failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for k, text in enumerate(labels):
            stripped = NATURAL.sub("", text)
            try:
                a = parse_label(text, tmp, f"with_{k}")
                b = parse_label(stripped, tmp, f"without_{k}")
            except Exception:
                n_failed += 1
                continue
            pa, pb = pitch_multiset(a), pitch_multiset(b)
            changed = sum((pa - pb).values())            # notes whose pitch differs
            n_labels += 1
            n_notes += sum(pa.values())
            n_naturals += len(NATURAL.findall(text))
            n_changed_notes += changed
            n_changed_labels += 1 if changed else 0
    print(f"labels compared: {n_labels}  (failed to parse: {n_failed})")
    print(f"natural-sign pieces removed: {n_naturals}   notes in these labels: {n_notes}")
    print(f"notes whose MIDI pitch changed: {n_changed_notes}   labels with any change: {n_changed_labels}")


if __name__ == "__main__":
    from datasets import load_dataset
    test = load_dataset("PRAIG/camera-grandstaff")["test"]
    texts = test["transcription"]                       # labels only, no images, no model output
    chosen = [t for t in texts if NATURAL.search(t)][:30]
    print(f"first 30 test labels containing ·n (scanned {len(texts)} labels, "
          f"{sum(1 for t in texts if NATURAL.search(t))} contain it)")
    compare(chosen)
    