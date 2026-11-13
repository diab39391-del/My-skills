"""Synthesized music bed + SFX placed on the film's cue list (out/cues.json). Writes out/mix_raw.wav."""
import json, wave
import numpy as np, os, subprocess
E=os.environ.get

SR, DUR = 44100, float(E('DUR', '480'))
N = int(SR * DUR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR

def lp(x, k):  # cheap low-pass: moving average
    if k <= 1: return x
    return np.convolve(x, np.ones(k) / k, mode='same')

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

# ---------------- music ----------------
BPM = float(E('BPM', '88')); BEAT = 60 / BPM; BAR = 4 * BEAT
music = np.zeros((2, N), np.float32)
# A minor: Am F C G  (two bars each)
CH = [[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]]
ROOT = [45, 41, 48, 43]
if E('KEY') == 'major':
    CH = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]; ROOT = [48, 43, 45, 41]
seg = 2 * BAR
nseg = int(np.ceil(DUR / seg))

def tone(f, n, harm=(1, .25, .1), detune=0.0):
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for h, a in enumerate(harm, 1):
        out += a * np.sin(2 * np.pi * f * h * (1 + detune) * tt + h)
    return out

for s in range(nseg):
    i0 = int(s * seg * SR); n = min(int(seg * SR) + int(1.5 * SR), N - i0)
    if n <= 0: break
    c = CH[s % 4]
    env = np.minimum(1, np.arange(n) / (1.2 * SR)) * np.clip((seg * SR + 1.5 * SR - np.arange(n)) / (1.5 * SR), 0, 1)
    pad = np.zeros((2, n))
    for k, m in enumerate(c):
        f = mtof(m)
        pad[0] += tone(f, n, detune=-0.003) * .5
        pad[1] += tone(f, n, detune=0.003) * .5
    pad *= env * 0.05
    music[:, i0:i0 + n] += pad
    # bass plucks on beats 1 and 3 (from 30 s on)
    if s * seg >= float(E('BASS_FROM', '30')):
        for b in (0, 2, 4, 6):
            j0 = i0 + int(b * BEAT * SR); m = int(1.2 * SR)
            if j0 + m > N: continue
            tt = np.arange(m) / SR
            bs = np.sin(2 * np.pi * mtof(ROOT[s % 4]) * tt) * np.exp(-tt * 3.5) * 0.11
            music[:, j0:j0 + m] += bs
    # soft arp 8ths (from 60 s on, chapters)
    if s * seg >= float(E('ARP_FROM', '60')):
        notes = [c[0] + 12, c[1] + 12, c[2] + 12, c[1] + 12]
        for q in range(16):
            j0 = i0 + int(q * BEAT / 2 * SR); m = int(.5 * SR)
            if j0 + m > N: continue
            tt = np.arange(m) / SR
            ar = np.sin(2 * np.pi * mtof(notes[q % 4]) * tt) * np.exp(-tt * 9) * 0.035
            pan = .35 if q % 2 else -.35
            music[0, j0:j0 + m] += ar * (1 - pan); music[1, j0:j0 + m] += ar * (1 + pan)
    # hats (from 30 s)
    if s * seg >= float(E('BASS_FROM', '30')):
        for q in range(16):
            j0 = i0 + int((q + .5) * BEAT / 2 * SR) if False else i0 + int(q * BEAT / 2 * SR)
            m = int(.05 * SR)
            if j0 + m > N or q % 2 == 0: continue
            nz = rng.standard_normal(m); nz = nz - lp(nz, 6)
            music[:, j0:j0 + m] += nz * np.exp(-np.arange(m) / SR * 80) * 0.02
# fade in/out
fi = np.minimum(1, t_all / 3.0); fo = np.clip((DUR - t_all) / 4.0, 0, 1)
music *= (fi * fo)

# ---------------- sfx ----------------
def env_exp(n, k): return np.exp(-np.arange(n) / SR * k)
def noise(n): return rng.standard_normal(n)

def sfx(kind):
    if kind == 'swish':
        n = int(.28 * SR); e = np.sin(np.linspace(0, np.pi, n)) ** 2
        x = noise(n); x = x - lp(x, 40); return lp(x, 3) * e * .5
    if kind == 'whoosh':
        n = int(.6 * SR); e = np.sin(np.linspace(0, np.pi, n)) ** 3
        return lp(noise(n), 12) * e * 1.4
    if kind == 'rise':
        n = int(.7 * SR); tt = np.arange(n) / SR; f = 180 + 700 * (tt / tt[-1]) ** 2
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * .3 + lp(noise(n), 8) * .5) * (tt / tt[-1]) ** 2
    if kind == 'hit':
        n = int(.9 * SR); tt = np.arange(n) / SR; f = 90 * np.exp(-tt * 6) + 45
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 5) * 1.2 + lp(noise(n), 4) * env_exp(n, 40) * .4
    if kind == 'pop':
        n = int(.12 * SR); tt = np.arange(n) / SR; f = 380 + 900 * tt / tt[-1]
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 35) * .8
    if kind == 'tick':
        n = int(.03 * SR); return (np.sin(2 * np.pi * 2300 * np.arange(n) / SR) * .5 + noise(n) * .3) * env_exp(n, 220)
    if kind == 'ding':
        n = int(1.2 * SR); tt = np.arange(n) / SR
        return (np.sin(2 * np.pi * 1318.5 * tt) + .5 * np.sin(2 * np.pi * 1975.5 * tt)) * env_exp(n, 4.5) * .35
    if kind == 'scratch':
        n = int(.35 * SR); x = noise(n); x = x - lp(x, 10); e = np.minimum(1, np.arange(n) / (.03 * SR)) * env_exp(n, 9)
        return x * e * .6
    if kind == 'stamp':
        n = int(.7 * SR); tt = np.arange(n) / SR; f = 120 * np.exp(-tt * 10) + 55
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 7) * 1.3 + lp(noise(n), 3) * env_exp(n, 30) * .7
    if kind == 'glitch':
        n = int(.25 * SR); x = np.sign(np.repeat(noise(n // 40 + 1), 40)[:n]) * .25
        return x * (np.sin(2 * np.pi * 37 * np.arange(n) / SR) > 0) * np.linspace(1, .4, n)
    if kind == 'buzz':
        n = int(.35 * SR); tt = np.arange(n) / SR
        return lp(np.sign(np.sin(2 * np.pi * 110 * tt)), 20) * np.minimum(1, (n - np.arange(n)) / (.05 * SR)) * .25
    raise ValueError(kind)

fx = np.zeros((2, N), np.float32)
cues = json.load(open(E('CUES', 'out/cues.json')))
for t, kind, g in cues:
    s = sfx(kind) * g * 0.5 * float(E('SFX_GAIN', '1'))
    i0 = int(t * SR); i1 = min(N, i0 + len(s))
    pan = 0.0 if kind in ('hit', 'stamp', 'rise') else float(rng.uniform(-.25, .25))
    fx[0, i0:i1] += s[:i1 - i0] * (1 - pan); fx[1, i0:i1] += s[:i1 - i0] * (1 + pan)

mix = music * float(E('MUSIC_GAIN', '1')) + fx
if E('VO'):
    raw = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', E('VO'), '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
    vo = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    vo = vo / (np.abs(vo).max() + 1e-9) * 0.9
    v = np.zeros(N, np.float32); v[:min(N, len(vo))] = vo[:N]
    # duck music+sfx bed under the voice (smoothed envelope)
    env = np.convolve(np.abs(v), np.ones(int(.25 * SR)) / int(.25 * SR), 'same'); env = np.clip(env / (env.max() + 1e-9) * 3, 0, 1)
    mix = mix * (1 - 0.45 * env) * 0.55 + v
mix /= max(1e-9, np.abs(mix).max()) / 0.9
pcm = (mix.T * 32767).astype(np.int16)
with wave.open(E('OUT', 'out/mix_raw.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('cues', len(cues), 'ok')
