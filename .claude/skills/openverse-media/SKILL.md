---
name: openverse-media
description: >-
  Find free, openly licensed sound effects, music and images on Openverse
  (WordPress's search engine over Freesound, Jamendo, Wikimedia, Flickr and
  more), filter by licence (CC0, CC BY) and commercial use, download the
  picks and write the credits file. Use when a video, ad or site needs a
  whoosh, click, pop, ambience, music bed or a photo/illustration that is
  free and legal to use, "مؤثرات صوتية مجانية", "صوت مرخص", "صور مجانية",
  or when real-sfx / real-sound need a library to pick from.
---

# Openverse media: free sounds and images, with credits

Openverse is not a skill or an app to install: it is a public API over hundreds of millions of
openly licensed works. This skill searches it, downloads what you pick, and keeps the credits.

## Licence rules (read before using anything)
| Licence | Commercial ad? | Credit needed? |
|---|---|---|
| `cc0`, `pdm` (public domain) | yes | no (kind to add) |
| `by` | yes | **yes**, in the description or end card |
| `by-sa` | yes, but derivatives share-alike | yes |
| `by-nc*`, `nc-*` | **no** (non-commercial only) | yes |
| `*-nd` | no edits allowed: not for sound design | yes |

For client ads use `--license cc0` or `--license cc0,by --commercial`. Always check the result's
licence again before shipping; Openverse reports what the source says.

## Commands
```bash
python3 -I scripts/openverse.py search audio "whoosh" --license cc0 --max-sec 2
python3 -I scripts/openverse.py search audio "kids playground ambience" --license cc0,by --commercial
python3 -I scripts/openverse.py search images "colorful classroom" --license cc0
python3 -I scripts/openverse.py get audio <ID> <ID> --out work/sfx      # files + work/sfx/CREDITS.md + credits.json
```
- Query in English (sources are tagged in English): whoosh, swoosh, pop, click, ding, chime, riser, impact, keyboard typing, paper, ambience.
- Pick short takes for UI moments (`--max-sec 1-2`), then verify them with the `earshot` skill (`describe`, `match`) since you cannot hear.
- Hand the folder to `real-sfx` / `real-sound` as a library, or place the files with `vertical-local-ad/assets/audio.py`.
- Put `CREDITS.md` lines for every `by` file in the video description or the end card.

## Network
Needs `api.openverse.org` plus the file's own host (shown in each result's source: e.g. `cdn.freesound.org`,
`mp3d.jamendo.com`, `upload.wikimedia.org`). In a cloud session, ask to allow those exact hosts. The anonymous API is
rate-limited: search a few times, not in loops.
