def low_confidence_flags(tokens, conf, threshold=0.7, pred_text=None):
    cells = [l.split("\t") for l in pred_text.split("\n")] if pred_text is not None else None
    flags = []
    line = col = 0
    cell = []

    def flush():
        if cell and min(c for _, _, c in cell) < threshold:
            idx, _, c = min(cell, key=lambda x: x[2])
            text = " ".join(t for _, t, _ in cell)
            if cells is not None and line < len(cells) and col < len(cells[line]):
                text = cells[line][col]          # the cell as it appears in the prediction
            flags.append({"issue": "low_confidence_token", "line": line, "column": col,
                          "token": text, "token_index": idx, "confidence": float(c)})

    for i, (tok, c) in enumerate(zip(tokens, conf)):
        if tok == "<t>":
            flush(); cell = []; col += 1
        elif tok == "<b>":
            flush(); cell = []; line += 1; col = 0
        else:
            cell.append((i, tok, c))
    flush()
    return flags