---
name: voiceover-sync
description: >-
  Sync a motion-graphics video to a recorded voiceover (ElevenLabs or any
  recording): transcribe it with Whisper to get every word's timestamp,
  compare what was said with the script and add or remove on-screen content
  to match, retime each scene and each pop to its word, then mix the voice
  over a ducked music bed. Also covers making an Egyptian Arabic TTS voice
  (edge-tts ar-EG). Use when the user sends a voice file ("ظبط ده مع
  المحتوى", "سنكرن الصوت", "زود المحتوى الناقص حسب الصوت"), wants a
  voiceover made, or a video's text and animation must land on the spoken
  words.
---

# Voiceover sync

Goal: every word, card and icon appears on the frame its word is spoken, and what is on
screen matches what is said (nothing missing, nothing claimed that the voice and brief do not say).

## 1. Look at the file
```bash
ffprobe -v error -show_entries format=duration:stream=sample_rate,channels -of default=nw=1 vo.wav
ffmpeg -i vo.wav -af silencedetect=noise=-38dB:d=0.25 -f null - 2>&1 | grep -oE "silence_(start|end): [0-9.]+"
```
The video length = VO length + a 1-1.5 s hold on the end card. If the VO is longer than the
length the user asked for, stretch the video to the voice; never cut the voice.

## 2. Transcribe with word timestamps (preferred)
```bash
pip install -q faster-whisper
python3 scripts/transcribe.py vo.wav words.json --prompt "brand name, product words, people's names"
```
- Model `mobiuslabsgmbh/faster-whisper-large-v3-turbo`, int8 on CPU: ~90 s to load the first time, ~20 s for a 1-minute VO. Arabic (including Egyptian) comes out clean.
- The `--prompt` with the brand and names fixes spelling of proper nouns.
- **Network**: the model download needs these hosts allowed in the cloud environment: `huggingface.co`, `us.aws.cdn.hf.co`, `cdn.hf.co`, `cdn-lfs.hf.co`, `cdn-lfs-us-1.hf.co`, `cas-bridge.xethub.hf.co`. Set `HF_HUB_DISABLE_XET=1` and `REQUESTS_CA_BUNDLE=SSL_CERT_FILE=/root/.ccr/ca-bundle.crt` behind the agent proxy. Once cached, `HF_HUB_OFFLINE=1`.
- Whisper writes Egyptian pronunciation (e.g. "مونة الدهبي" for منى الذهبي, "عصاير" for عصائر, "ومحفظين"): put the correct written form on screen, keep the timing.

## 3. Diff the voice against the script and the screen
Read the transcript line by line next to the scene list:
- **Said but not on screen** (an extra service, an honorific like "ميس", "رقم التواصل" before the number): add it (a card, a label, a word).
- **On screen but not said and not in the brief**: remove it.
- Report the changes to the user in one short list.

## 4. Retime
- Scene boundaries = sentence starts (segment `start`, or the first word's `s`).
- A pop/card/highlight starts ~0.05-0.1 s **before** its word (`s - 0.08`): the eye leads the ear.
- Multi-line text: give each line its own start (the word that opens it) instead of one stagger.
- Phone numbers: light each digit group when its group is spoken.
- Then render 6-8 check frames at word times and look at them before the full render.

## 5. Fallback without a recognizer (no Hugging Face)
1. Make a reference read of the script, one wav per sentence, with edge-tts (below).
2. `python3 scripts/align_dtw.py vo.wav ref_00.wav ref_01.wav ... > bounds.json`: MFCC + DTW alignment, snapped to real pauses. Gives sentence starts only (words inside a sentence are then paced by estimate: say so to the user).

## 6. Make an Egyptian voice when the user has none
```bash
pip install -q edge-tts
SSL_CERT_FILE=/root/.ccr/ca-bundle.crt edge-tts --proxy "$HTTPS_PROXY" --voice ar-EG-ShakirNeural --rate=+6% --text "..." --write-media line.mp3
```
- Voices: `ar-EG-ShakirNeural` (male), `ar-EG-SalmaNeural` (female). Needs host `speech.platform.bing.com`; `--proxy` is required (aiohttp ignores the proxy env).
- In loops, run ffmpeg with `-nostdin` or it eats the loop's stdin.
- Quality is fine for drafts and references; for the final, the user's ElevenLabs voice is better. Settings to give them: Eleven v3 (or Multilingual v2), Stability 40-50 %, Similarity 75 %, Style 20-30 %, one file with blank lines between sentences.

## 7. Mix
Voice on top, music and SFX ducked under it, two-pass loudnorm to -14 LUFS, peak <= -1 dBTP.
The `audio.py` in `vertical-local-ad/assets/` does this with `VO=vo.wav MUSIC_GAIN=0.6-0.7 SFX_GAIN=0.7`.
