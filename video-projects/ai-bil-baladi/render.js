// usage: node render.js probe out/sheet.png t1 t2 ...   |  node render.js chunk startSec endSec out/part.mp4  |  node render.js cues out/cues.json
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const URL_ = 'http://127.0.0.1:8765/' + (process.env.PAGE || 'index.html');
const FPS = 30;

async function open() {
  const b = await chromium.launch({ args: ['--font-render-hinting=none', '--force-color-profile=srgb', '--disable-checker-imaging'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  p.on('pageerror', e => console.error('PAGEERR', e.message));
  await p.goto(URL_);
  await p.waitForFunction('window.ready === true', null, { timeout: 60000 });
  return { b, p };
}
async function shot(p, t, type = 'jpeg') {
  await p.evaluate(t => { seek(t); return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))); }, t);
  return p.screenshot(type === 'jpeg' ? { type: 'jpeg', quality: 93 } : { type: 'png' });
}
(async () => {
  const [mode, ...a] = process.argv.slice(2);
  const { b, p } = await open();
  if (mode === 'cues') { fs.writeFileSync(a[0], JSON.stringify(await p.evaluate('CUES'))); }
  if (mode === 'probe') {
    const out = a[0], ts = a.slice(1).map(Number); fs.mkdirSync('out/probe', { recursive: true });
    const files = [];
    for (const t of ts) { const f = `out/probe/${t.toFixed(2)}.png`; fs.writeFileSync(f, await shot(p, t, 'png')); files.push(f); }
    const cols = Math.min(4, files.length), rows = Math.ceil(files.length / cols);
    const args = ['-y']; files.forEach(f => args.push('-i', f));
    let fc = files.map((_, i) => `[${i}:v]scale=640:-1,drawtext=text='${ts[i].toFixed(1)}':x=10:y=10:fontsize=28:fontcolor=white:box=1:boxcolor=black[v${i}]`).join(';');
    for (let i = files.length; i < cols * rows; i++) { fc += `;color=black:s=640x360:d=1[v${i}]`; }
    const n = cols * rows; const layout = Array.from({ length: n }, (_, i) => `${(i % cols) * 640}_${Math.floor(i / cols) * 360}`).join('|');
    fc += ';' + Array.from({ length: n }, (_, i) => `[v${i}]`).join('') + `xstack=inputs=${n}:layout=${layout}`;
    if (n === 1) fc = fc.replace(/;\[v0\]xstack.*$/, '');
    args.push('-filter_complex', fc, '-frames:v', '1', out);
    await new Promise(r => spawn('ffmpeg', args, { stdio: 'ignore' }).on('close', r));
  }
  if (mode === 'chunk') {
    const s = +a[0], e = +a[1], out = a[2]; const f0 = Math.round(s * FPS), f1 = Math.round(e * FPS);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-color_range', 'tv', '-colorspace', 'bt709', '-vf', 'scale=in_range=pc:out_range=tv:out_color_matrix=bt709', out], { stdio: ['pipe', 'ignore', 'inherit'] });
    const t0 = Date.now();
    for (let f = f0; f < f1; f++) {
      const buf = await shot(p, f / FPS);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 300 === 0) console.log(`${out} frame ${f}/${f1} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await b.close();
})();
