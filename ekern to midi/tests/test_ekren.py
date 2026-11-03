# test_ekren.py

from music21 import converter, bar
from kernpy import get_kern_from_ekern


def safe_write_midi(score, midi_path):
    """
    Writes MIDI, falling back to stripping malformed repeat barlines
    if music21's repeat-expansion fails (common with real/toy eKern
    data that has incomplete repeat structures).
    """
    try:
        score.write('midi', fp=midi_path)
        return False  # no stripping needed
    except Exception:
        for m in score.recurse().getElementsByClass('Measure'):
            if isinstance(m.leftBarline, bar.Repeat):
                m.leftBarline = bar.Barline('regular')
            if isinstance(m.rightBarline, bar.Repeat):
                m.rightBarline = bar.Barline('regular')
        score.write('midi', fp=midi_path)
        return True  # repeats were stripped


# 1. Load the test eKern file
with open("twinkle.ekrn", encoding="utf-8") as f:
    ekern_text = f.read()

print("=== Raw eKern (first 300 chars) ===")
print(ekern_text[:300])
print()

# 2. Convert eKern -> kern using kernpy
kern_text = get_kern_from_ekern(ekern_text)
kern_text = kern_text.replace("**kern_1.0", "**kern")  # music21 needs the bare header

print("=== Converted kern (first 300 chars) ===")
print(kern_text[:300])
print()

# 3. Write it to a file and parse with music21
with open("your_test_file_converted.krn", "w", encoding="utf-8") as f:
    f.write(kern_text)

score = converter.parse("your_test_file_converted.krn")

# 4. THE KEY CHECK: did it actually find parts?
print("Number of parts found:", len(score.parts))
if len(score.parts) == 0:
    print("!!! ZERO PARTS — conversion silently failed, check the header/content above !!!")
else:
    score.show('text')  # readable note-by-note breakdown

# 5. Write MusicXML
score.write('musicxml', fp="your_test_file.musicxml")
print("Wrote MusicXML OK")

# 6. Write MIDI, with automatic fallback for malformed repeats
repeats_stripped = safe_write_midi(score, "your_test_file.mid")
print("Wrote MIDI OK" + (" (had to strip malformed repeats)" if repeats_stripped else ""))