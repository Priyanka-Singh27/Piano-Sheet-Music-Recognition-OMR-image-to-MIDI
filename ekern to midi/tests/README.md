# Stage 2 — Symbolic Cleanup & MIDI Conversion (Owner: Person2)

Goal: **kern sequence -> clean, expressive MIDI file.
Full task list: see Detailed_Project_Plan_Tools_Tasks.pdf, Section 7.

## Subfolders
- `correction_rules/` — measure-duration check, key-signature plausibility check (music21)
- `conversion/` — **kern -> MusicXML -> MIDI conversion code
- `dynamics_pedal/` — dynamics/pedal-to-MIDI mapping (built/tested on MuseScore sample files)
- `confidence_flagging/` — flags low-confidence tokens from Person1's output for Person4's correction UI
- `evaluation/` — note-level Precision/Recall/F1 scripts
- `outputs/` — generated .musicxml / .mid files (hand off point for Person3/Person4)
