# create_test_ekern.py

# Each line is a list: [treble spine value, bass spine value]
# (or single-value lines for header/global tokens)
lines = [
    ("**ekern_1.0", "**ekern_1.0"),
    ("*clefF4", "*clefG2"),
    ("*k[b-e-]", "*k[b-e-]"),
    ("*M2/4", "*M2/4"),
    ("=-", "=-"),
    ("4·GGG 4·GG", "4·g"),
    ("8·r", "8·r"),
    ("24·FF·LL", "24·f·LL"),
    ("24·GG", "24·g"),
    ("24·AA·JJ", "24·a·JJ"),
    ("=:|!", "=:|!"),
    ("16·GGG 16·GG", "16·g·LL"),
    ("16·GG·LL", "16·d"),
    ("16·BB·-", "16·g"),
    ("16·D·JJ", "16·b·-·JJ"),
    ("4·G·[", "16·dd·LL"),
    (".", "16·ee·-"),
    (".", "16·dd"),
    (".", "16·cc·JJ"),
    ("=", "="),
    ("*-", "*-"),
]

# Join each pair with a REAL tab character, and lines with a real newline
ekern_text = "\n".join("\t".join(pair) for pair in lines)

with open("grandstaff_test.ekrn", "w", encoding="utf-8") as f:
    f.write(ekern_text)

# Verify the tabs are actually there before moving on
with open("grandstaff_test.ekrn", encoding="utf-8") as f:
    content = f.read()
print(repr(content[:60]))