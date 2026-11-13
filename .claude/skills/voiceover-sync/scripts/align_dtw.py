"""Sentence boundaries WITHOUT a speech recognizer (fallback when Hugging Face is blocked).

Idea: synthesize a reference read of the same sentences (one wav per sentence, e.g. with
edge-tts ar-EG voices), concatenate them, align the reference to the real voiceover with
MFCC + DTW, map the reference sentence boundaries through the path, then snap each one to
the nearest real pause in the voiceover.

usage: python3 align_dtw.py vo.wav ref_00.wav ref_01.wav ... > bounds.json
Prints the start time of sentences 2..N in the voiceover (sentence 1 starts at 0).
"""
import json, re, subprocess, sys
import numpy as np

SR = 16000

def pcm(path):
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

def dur(path):
    return len(pcm(path)) / SR

def feats(x):
    x = np.append(x[0], x[1:] - .97 * x[:-1])
    n, h = 400, 160; N = 1 + (len(x) - n) // h
    fr = np.lib.stride_tricks.as_strided(x, (N, n), (x.strides[0] * h, x.strides[0])).copy() * np.hanning(n).astype(np.float32)
    P = np.abs(np.fft.rfft(fr, 512)) ** 2
    mel = lambda f: 2595 * np.log10(1 + f / 700); imel = lambda m: 700 * (10 ** (m / 2595) - 1)
    bins = np.floor(513 * imel(np.linspace(mel(80), mel(7600), 42)) / SR).astype(int)
    fb = np.zeros((40, 257), np.float32)
    for m in range(1, 41):
        a, b, c = bins[m - 1], bins[m], bins[m + 1]
        fb[m - 1, a:b] = (np.arange(a, b) - a) / max(1, b - a); fb[m - 1, b:c] = (c - np.arange(b, c)) / max(1, c - b)
    L = np.log(P @ fb.T + 1e-6)
    D = np.cos(np.pi / 40 * (np.arange(40)[None, :] + .5) * np.arange(20)[:, None])
    M = (L @ D.T)[:, 1:]; M = (M - M.mean(0)) / (M.std(0) + 1e-6)
    F = np.hstack([M, np.gradient(M, axis=0) * .5])
    return F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-6)

vo, refs = sys.argv[1], sys.argv[2:]
ref = np.concatenate([pcm(r) for r in refs]); A, B = feats(ref), feats(pcm(vo))
na, nb = len(A), len(B); C = 1 - A @ B.T
inf = np.float32(1e9); Dm = np.full((na + 1, nb + 1), inf, np.float32); Dm[0, 0] = 0; band = int(max(na, nb) * .25)
for i in range(1, na + 1):
    c, prev = C[i - 1], Dm[i - 1]; row = np.full(nb + 1, inf, np.float32)
    lo = max(1, int(i * nb / na) - band); hi = min(nb, int(i * nb / na) + band)
    row[lo:hi + 1] = c[lo - 1:hi] + np.minimum(prev[lo - 1:hi], prev[lo:hi + 1])
    for j in range(lo + 1, hi + 1):
        v = row[j - 1] + c[j - 1]
        if v < row[j]: row[j] = v
    Dm[i] = row
i, j, path = na, nb, []
while i > 0 and j > 0:
    path.append((i - 1, j - 1)); k = np.argmin([Dm[i - 1, j - 1], Dm[i - 1, j], Dm[i, j - 1]])
    i, j = (i - 1, j - 1) if k == 0 else (i - 1, j) if k == 1 else (i, j - 1)
path = np.array(path[::-1])
cb = np.cumsum([dur(r) for r in refs])[:-1]
est = [float(path[path[:, 0] == min(int(b * 100), na - 1)][:, 1].mean()) / 100 for b in cb]
o = subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-i', vo, '-af', 'silencedetect=noise=-38dB:d=0.1', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
gaps = list(zip(map(float, re.findall(r'silence_start: ([0-9.]+)', o)), map(float, re.findall(r'silence_end: ([0-9.]+)', o))))
res = []
for b in est:
    g = min(gaps, key=lambda g: abs((g[0] + g[1]) / 2 - b)) if gaps else None
    res.append(round(g[1] - .05, 2) if g and abs((g[0] + g[1]) / 2 - b) < .7 else round(b, 2))
print(json.dumps(res))
