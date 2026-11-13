---
name: vertical-local-ad
description: >-
  Build a 30-60 s vertical (9:16, 1080x1920) Arabic motion-graphics ad for a
  local business (nursery, clinic, gym, shop, centre) from a ready HTML
  template: viewer searches, the business card appears as the result, a tap
  dives into the logo, then services, team, values, map with address, and a
  CTA end card with the phone number lit digit by digit, all synced to a
  voiceover. Use for "اعمل إعلان لـ…", "فيديو موشن لحضانة/عيادة/محل",
  "ريلز إعلان", a business logo plus a voiceover, or a reference ad in the
  "search, then result, then inside" style.
---

# Vertical local-business ad (Arabic, 9:16)

A working template, not a blank page. `assets/template.html` is a full film engine
(pure `window.seek(t)`, RTL Arabic, Cairo font, 3D icons) with neutral `[placeholders]`.
A new ad = fill the `BRAND` block + the timeline + the logo, then render. Never ship a
frame that still shows a `[placeholder]`.

## The story (keep the chain, it is what makes it work)
| Scene (`type`) | What happens | Typical length |
|---|---|---|
| `search` | Hook question, a search bar types the query on an Arabic keyboard, tap "بحث" | 4-6 s |
| `result` | Search bar moves up, the business card rises (logo, two-colour name, gold badge, slogan, address, call/directions/save), tap on the logo, a navy circle floods out of it | 2-4 s |
| `highlight` | "Inside" on the brand colour: 4 tiles pop, then `BRAND.highlight.word` builds from its own letters and glows, then one line (the business's main strength) | 5-6 s |
| `services` | Grid of service cards with 3D icons (up to 8), each popping on the word that names it | 6-9 s |
| `team` | Team line with 3 people icons (`BRAND.teamIcons`) | 4-5 s |
| `values` | Two big value cards joined by "+", then a line | 5-6 s |
| `address` | Schematic map draws, pin drops, landmarks pop, address card (labelled "خريطة توضيحية") | 5-6 s |
| `end` | Logo draws itself, name, badge, slogan, manager, CTA button, phone number lighting up group by group | 8-15 s |

Drop or reorder scenes in the `sc(...)` list at the bottom; every scene is self-contained.

## Workflow
1. **Brief** (ask only what is missing): business name (two parts for the two colours), logo image, colours, the gold badge text (main strength), the highlight word, slogan, services, team line, address + 2-3 landmarks, manager name (optional), phone, CTA. Never invent ratings, prices, years, numbers of students or awards: no facts, no claim.
2. **Script + VO text**: use the `egyptian-arabic-copy` skill. The user usually records the voice in ElevenLabs and sends it back.
3. **Copy the template** into a work folder: `assets/template.html` (rename), `assets/render.js`, `assets/audio.py`, `assets/fonts/`, `assets/icons/`.
4. **Fill `BRAND`** at the top of the HTML (replace every `[...]`; pick service icons from `assets/icons/`). Accent syntax inside text: `_x_` accent 1 (navy), `*x*` accent 2 (magenta), `^x^` gold.
5. **Colours**: change the CSS tokens in `:root` (`--navy --mag --gold --blue --red --cream`). Sample them from the logo: `ffmpeg -i logo.png -f rawvideo -pix_fmt rgb24 -` then count saturated pixels (see "Colour sampling" below).
6. **Logo**: `logo()` holds a placeholder mark. If the client logo is small or a screenshot, redraw it as SVG inside `logo()` keeping the class names `lg-o lg-i lg-k1 lg-k2 lg-st lg-bk` (the end card animates them: rings draw, book rises, figures pop, star spins). If a high-res PNG exists, put `<image href="brand/logo.png" x="20" y="20" width="160" height="160"/>` inside the circle instead. Tell the user when the logo is a redraw and ask for the original file.
7. **Sync to the voice**: use the `voiceover-sync` skill to get `words.json`. Then set every `sc(t0, t1, ...)` boundary to sentence starts, `SUBT` (one entry per service) to the word starts of each service (seconds from the scene start, minus ~0.08), `DG` in the end scene to when each phone group is spoken, and the per-line `la` arrays (team, values) to their words. Set `DUR` = VO length + 1-1.5 s hold.
8. **Check stills before rendering** (vertical contact sheet): `VW=1080 VH=1920 PAGE=ad.html node render.js probe out/s.png 2 6 12 20 30 45`. Read the PNG. Fix overlaps, empty halves, text at the edges (keep text inside y 200-1750).
9. **Render** in 4 parallel chunks, then mux (below). Verify: frame count = DUR x 30, loudness -14 LUFS.

## Commands
```bash
python3 -m http.server 8765 --bind 127.0.0.1 &           # serve the work folder
export VW=1080 VH=1920 PAGE=ad.html
node render.js cues out/cues.json                        # SFX cue list from the timeline
DUR=53 KEY=major BPM=100 BASS_FROM=0 ARP_FROM=6 CUES=out/cues.json \
  VO=vo.wav MUSIC_GAIN=0.7 SFX_GAIN=0.7 OUT=out/raw.wav python3 audio.py   # music + SFX + ducked VO
# two-pass loudnorm to -14 LUFS: measure with print_format=json, then apply with linear=true
for i in 0 1 2 3; do node render.js chunk $((i*D/4)) $(((i+1)*D/4)) out/p$i.mp4 & done; wait
ffmpeg -f concat -safe 0 -i list.txt -i out/mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart final.mp4
```
- `render.js` needs `VW/VH` env for vertical; Playwright is preinstalled; the local server dies between sessions, restart it if `ERR_CONNECTION_REFUSED`.
- `audio.py`: synthesized music bed + SFX on the cue list; `KEY=major` for kids/happy brands; `VO=` mixes the voice on top and ducks the bed under it.
- Speed: ~3 fps per chunk on 4 CPUs, so a 50 s film takes ~6 min.

## Colour sampling
```bash
ffmpeg -v error -i logo.png -f rawvideo -pix_fmt rgb24 - | python3 -c "
import sys;from collections import Counter;d=sys.stdin.buffer.read();c=Counter()
for i in range(0,len(d),3):
  r,g,b=d[i:i+3]
  if max(r,g,b)-min(r,g,b)>70:c[(r//8*8,g//8*8,b//8*8)]+=1
[print('#%02x%02x%02x'%k,v) for k,v in c.most_common(10)]"
```

## Assets
- `assets/fonts/`: Cairo 400/700/900, Arabic + Latin subsets (SIL Open Font License).
- `assets/icons/`: 69 Microsoft Fluent Emoji 3D icons (MIT) named by meaning (`abacus abc alarm backpack balloon book books bulb chat child crayon heart mosque numbers openbook palette pencil phone pin puzzle sparkles star teacher tm tw writing`, and more). More icons: `npm pack @lobehub/fluent-emoji-3d` (assets named by codepoint, e.g. `1f9ee.webp`).

## Rules learned on the real job
- Never copy a real search engine's logo or exact UI: the search bar is generic (magnifier + rounded bar).
- No fake stars or reviews on the result card. The map is schematic: keep the "خريطة توضيحية" label.
- One line on screen = what the voice says, condensed. If the VO adds an item (e.g. a service), add its card; if the screen claims something the VO and the brief do not (e.g. "everything with method X"), remove it.
- Don't commit a client's phone number or personal names to a public repo without asking.
- Phone numbers: write them as words in the VO script (see `egyptian-arabic-copy`), show them as digits on screen, light each group as it is spoken.
