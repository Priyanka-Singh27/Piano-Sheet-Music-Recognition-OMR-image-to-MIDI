from music21 import converter

# Parse the **kern file
score = converter.parse("test_sample.krn")

# Confirm it parsed correctly
print("Parsed OK. Number of parts:", len(score.parts))
score.show('text')  # prints a readable breakdown of notes

# Export to MusicXML
score.write('musicxml', fp="test_sample.musicxml")
print("Wrote test_sample.musicxml")

# Export to MIDI
score.write('midi', fp="test_sample.mid")
print("Wrote test_sample.mid")