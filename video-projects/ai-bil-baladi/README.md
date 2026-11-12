# AI bil-baladi: 8-minute motion graphics video

Motion graphics for the Egyptian-Arabic YouTube script about AI. Every frame is computed from time in `index.html` (`window.seek(t)`), captured with Playwright and encoded with ffmpeg.

```bash
python3 -m http.server 8765 --bind 127.0.0.1 &
node render.js cues out/cues.json                # SFX cue list from the timeline
node render.js probe out/sheet.png 0 30 60       # contact sheet of chosen seconds
node render.js chunk 0 120 out/part0.mp4         # render a range (run 4 in parallel)
python3 audio.py                                  # synthesized music + SFX -> out/mix_raw.wav
```
Then loudnorm to -14 LUFS, concat parts and mux the audio. Preview in a browser: Space = play/pause, arrow keys = +/-1 s.

Fonts: Cairo (SIL Open Font License), from @fontsource/cairo.
