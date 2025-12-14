import os
import json
import whisper
from pathlib import Path

# === SETTINGS ===
AUDIO_FOLDER = Path(r"C:\Users\wsd3\OneDrive\Desktop\Audio")  # change to your folder
OUTPUT_JSON = AUDIO_FOLDER / "transcriptions.json"
MODEL_SIZE = "base"  # tiny, base, small, medium, large

# === INITIALIZE MODEL ===
model = whisper.load_model(MODEL_SIZE)
results = {}

# === TRANSCRIBE LOOP ===
for audio_file in AUDIO_FOLDER.glob("*"):
    if audio_file.suffix.lower() in [".mp3", ".wav", ".m4a", ".flac"]:
        print(f"🎧 Transcribing: {audio_file.name}")
        try:
            result = model.transcribe(str(audio_file))
            text = result["text"].strip()

            # Save per-file transcript
            txt_out = audio_file.with_suffix(".txt")
            txt_out.write_text(text, encoding="utf-8")

            # Add to combined JSON
            results[audio_file.name] = text

        except Exception as e:
            print(f"⚠️ Error with {audio_file.name}: {e}")

# === SAVE COMBINED JSON ===
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n✅ All done. Transcriptions saved in:\n{OUTPUT_JSON}")
