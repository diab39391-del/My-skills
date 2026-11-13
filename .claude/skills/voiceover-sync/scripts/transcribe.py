"""Word-level transcription of a voiceover with faster-whisper.

usage: python3 transcribe.py vo.wav words.json [--prompt "names, brand words, ..."] [--model MODEL]
Writes [{start,end,text,words:[{w,s,e}]}] and prints one line per segment plus word times.

Audio is decoded with ffmpeg (not PyAV) because some PyAV builds reject the
`metadata_errors` argument faster-whisper passes.
"""
import argparse, json, subprocess, time
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('audio'); ap.add_argument('out')
ap.add_argument('--prompt', default='')
ap.add_argument('--lang', default='ar')
ap.add_argument('--model', default='mobiuslabsgmbh/faster-whisper-large-v3-turbo')
a = ap.parse_args()

from faster_whisper import WhisperModel

raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', a.audio, '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(raw, np.float32).copy()
t = time.time()
m = WhisperModel(a.model, device='cpu', compute_type='int8', cpu_threads=4)
segs, _ = m.transcribe(audio, language=a.lang, word_timestamps=True, beam_size=5, vad_filter=False,
                       initial_prompt=a.prompt or None)
out = []
for s in segs:
    ws = [{'w': w.word.strip(), 's': round(w.start, 2), 'e': round(w.end, 2)} for w in s.words]
    out.append({'start': round(s.start, 2), 'end': round(s.end, 2), 'text': s.text.strip(), 'words': ws})
    print(f'[{s.start:6.2f}-{s.end:6.2f}] {s.text.strip()}')
    print('    ' + ' | '.join(f"{w['w']} {w['s']:.2f}" for w in ws))
json.dump(out, open(a.out, 'w'), ensure_ascii=False, indent=1)
print(f'done in {time.time() - t:.0f}s, audio {len(audio) / 16000:.2f}s')
