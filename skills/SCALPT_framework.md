# SCALPT — Prompt Framework untuk LoRA Portrait (dari boss, 29Ogo2026)

> Formula boss untuk prompt LoRA face yang HIDUP — guna UNTUK SEMUA prompt Aura/Ana-Art.
> S.C.A.L.P.T = Subject, Context, Action, Lighting, Perspective, Technical Style.

## Prinsip utama
- JANGAN asyik guna: `looking at camera` / `standing` / `smiling` → nampak macam model pose untuk kamera, bukan lifestyle.
- GUNA action natural + environment + Malaysian context → LoRA face nampak macam gambar lifestyle sebenar.
- Prompt lama kita kuat kat S + P, LEMAH kat C + A + storytelling + Malaysia-specific elements.

## Templat universal
```
[SUBJECT] ana_girl, 27-year-old Malaysian Malay woman, neat beige hijab,
[CONTEXT] location, environment, Malaysian setting (lokasi spesifik)
[ACTION]  what the person is doing naturally (satu action bermakna)
[LIGHTING] type of light, time of day
[PERSPECTIVE] camera angle, focal length (35/50/85mm), framing
[STYLE]   professional photography style
[QUALITY] photorealistic, high detail, realistic skin, sharp focus, cinematic grading, RAW
```

## Action bank (pilih SATU, jangan standing-looking-at-camera)
- reviewing a menu
- checking phone while waiting for Grab
- walking toward KLCC
- buying coffee at Zus Coffee
- looking at rainfall from café window
- waiting for MRT train
- crossing Bukit Bintang intersection
- taking photos near River of Life
- working on laptop inside coworking space
- glancing away toward city skyline, one hand on railing
- turning back over shoulder as if someone called her
- looking down at a drink just bought from 7-Eleven
- adjusting hijab while looking at car side mirror

## Location bank (Malaysia-specific)
- KLCC / Petronas Twin Towers skyline
- TRX Kuala Lumpur (corporate, office tower)
- Jalan Alor (street food, neon, wet pavement)
- Mid Valley Megamall (7-Eleven ground floor, skylight)
- Bukit Bintang intersection
- River of Life
- Putrajaya (government/civic)
- Penang heritage street
- Langkawi resort
- rooftop restaurant KL (golden hour, skyline view)
- luxury hotel lobby KL (marble, chandelier)

## Contoh siap-pakai (contoh boss, dengan <lora> diganti ana_girl)

**Indoor — café KL:**
```
ana_girl, 27-year-old Malaysian Malay woman, neat beige hijab,
sitting at a modern café in Kuala Lumpur,
holding a cup of coffee while looking outside the glass window,
Petronas Twin Towers visible in distant background,
warm ambient café lighting, golden hour sunlight entering through large windows,
medium shot, 85mm lens, shallow depth of field, candid moment,
professional lifestyle photography, natural skin texture, realistic eyes,
highly detailed, soft bokeh, cinematic color grading, RAW photo
```

**Outdoor — Jalan Alor dusk:**
```
ana_girl, 27-year-old Malaysian Malay woman, neat beige hijab,
walking along Jalan Alor Kuala Lumpur at dusk,
surrounded by neon signs and local food stalls,
casually looking at street vendors, busy Malaysian city atmosphere,
wet pavement after rain, cinematic evening lighting, street photography,
50mm lens, full body shot, natural pose, photorealistic,
realistic skin texture, high detail, bokeh lights, Kodak Portra color tone
```

**Corporate — TRX:**
```
ana_girl, 27-year-old Malaysian Malay woman, neat beige hijab,
standing in a modern office at TRX Kuala Lumpur,
reviewing documents beside floor-to-ceiling windows,
Kuala Lumpur skyline visible outside, professional business attire,
soft daylight, corporate photography, 85mm lens, eye-level angle,
clean office environment, premium executive portrait, photorealistic,
ultra realistic, high detail, professional color grading
```

**Luxury hotel:**
```
ana_girl, 27-year-old Malaysian Malay woman, neat beige hijab,
inside a luxury hotel lobby in Kuala Lumpur,
walking through marble flooring and elegant interior,
holding a designer handbag, warm chandelier lighting, luxury atmosphere,
full body shot, 85mm lens, cinematic composition, high-end fashion photography,
photorealistic, realistic skin texture, soft shadows, premium magazine style
```

**Upgraded hotel restaurant (contoh boss naikkan versi):**
```
ana_girl, 27-year-old Malaysian Malay woman, neat beige hijab,
inside an upscale Kuala Lumpur hotel restaurant,
standing beside a table while glancing over shoulder,
elegant modest outfit, warm luxury interior, soft amber lighting from wall lamps,
premium dining atmosphere, polished wooden furniture, subtle candlelight reflections,
85mm lens, eye-level perspective, medium full-body portrait, shallow depth of field,
professional lifestyle photography, cinematic color grading, natural skin texture,
realistic facial details, highly detailed, soft bokeh, RAW photo, masterpiece, photorealistic
```

## Nota
- `ana_girl` gantikan `<lora:your_face:1>` — trigger LoRA kita.
- Semua prompt tetap perlu anchor proporsi (guardrail) + skin texture + `no beauty filter, no plastic skin`.
- 1 angle + 1 action + 1 scene + 1 lighting per prompt — jangan campur.
