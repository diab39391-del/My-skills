---
name: egyptian-arabic-copy
description: >-
  Write video and ad copy in natural Egyptian Arabic (عامية مصرية): voiceover
  scripts ready for ElevenLabs or Azure ar-EG voices, on-screen text, hooks,
  CTAs and captions, with the pronunciation fixes TTS needs (diacritics,
  numbers written as words, pause punctuation). Use for any Arabic script,
  "اكتبلي سكريبت", "فويس أوفر بالمصري", "برومت لإيليفن لابس", a reel or ad
  for an Egyptian audience, or when another skill produces English copy that
  must become Egyptian Arabic.
---

# Egyptian Arabic copy (voice + screen)

## Two texts, never one
Every video has a **spoken** text and an **on-screen** text. Write both.
| | Spoken (VO) | On screen |
|---|---|---|
| Register | Real Egyptian speech: بتدوّر، دلوقتي، قدّام، عشان، إزاي، هيتعلّم | Short, readable, can lean slightly formal: عصائر، أمام، ناحية |
| Length | Full sentence | The 2-6 words that carry the sentence |
| Numbers | Written as words: "ميّة سبعة وعشرين", phone digit by digit "صفر واحد اتنين…" | Digits: 127, 01208070248 |
| Names | As said ("ميس منى") | As written (منى الذهبي) |

## Rules for natural Egyptian
- Use spoken forms, not فصحى dressed up: "عاوز" not "أريد", "بيعمل" not "يقوم بـ", "مش" not "ليس", "كده" not "هكذا", "دلوقتي" not "الآن".
- Short sentences, one idea each. A question hook works: «بتدوّر على مكان يأسّس ابنك صح؟».
- Speak to one person: «ابنك», «إنتَ», «سجّل».
- No corporate filler ("نقدم لكم أفضل الخدمات المتميزة"). Name the concrete thing.
- English words Egyptians say as English stay as they are: ماث، كورس، أونلاين.

## TTS pronunciation kit (ElevenLabs, Azure ar-EG)
- **Diacritics only where the voice will guess wrong**: إنتَ (not إنتِ), حَر, يأسّس, بتدوّر, متميّز. Don't vowel the whole line.
- **Pauses**: "…" = a breath inside a sentence; a blank line = a pause between sentences (and a scene cut). Commas between list items make each item land separately (useful for word-synced cards).
- **Numbers and phone numbers** in words, grouped the way the screen groups them.
- Keep names exactly as the client spells them; if the voice mangles one, add diacritics to that word only and regenerate that sentence.
- ElevenLabs settings to hand over: Eleven v3 (fallback Multilingual v2), Stability 40-50 %, Similarity 75 %, Style 20-30 %, Speed 1.0 (1.05 if too long). Pick a voice whose description says Egyptian Arabic. Ask for **one file** with the blank lines kept.
- Pace: ~2.2-2.6 spoken words per second. 40 s holds about 90-100 words; a long list (services, phone) eats time, so warn the user when the brief does not fit the length.

## Honesty
- No invented facts: ratings, years, numbers of students, prices, awards, "the best in Egypt". Only what the client gave.
- A method/brand name (e.g. a teaching method) describes what it covers, not everything.
- Illustrative data on screen gets "مثال توضيحي".

## Output format for a script request
1. A table: time | visuals | VO line.
2. The ElevenLabs block (spoken text only, in a code block, blank lines between sentences).
3. Settings and a one-line note on what to send back.
4. Assumptions marked (افتراض، أكّد) when the brief was missing something.
