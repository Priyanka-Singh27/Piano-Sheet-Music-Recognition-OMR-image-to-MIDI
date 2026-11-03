from collections import Counter


def extract_notes(score):
    notes = Counter()
    for n in score.flatten().notes:
        start = round(float(n.offset), 4)
        dur = round(float(n.duration.quarterLength), 4)
        for p in n.pitches:
            notes[(p.midi, start, dur)] += 1
    return notes


def prf1(pred, gt):
    tp = sum((pred & gt).values())
    n_pred = sum(pred.values())
    n_gt = sum(gt.values())
    precision = tp / n_pred if n_pred else 0.0
    recall = tp / n_gt if n_gt else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1