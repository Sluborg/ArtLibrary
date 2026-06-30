# Asset Report — Style Guide v1

> **Status:** Canonical, game-specific. This is the generation-ready style guide
> Lubot **pins per visual** when generating *Asset Report* art. It is **derived from
> the title screen** — the master theme anchor:
> `Wallpapers/AssetReport/title-screen.jpg`
> ([raw_url](https://raw.githubusercontent.com/Sluborg/ArtLibrary/main/Wallpapers/AssetReport/title-screen.jpg)).
>
> It refines the library's broader parent guide,
> [`Fantasy-Strategy-v1.md`](Fantasy-Strategy-v1.md), for this game. Where they
> overlap, the parent's hard limits still hold; this guide tightens palette,
> lighting, and tone to the title screen. Read the *what* in
> [`Games/AssetReport/GameArtBible.md`](../Games/AssetReport/GameArtBible.md).
>
> **How to use:** load top-to-bottom before generating. The
> [Palette](#palette-sampled-from-the-title-screen),
> [Prompt scaffolds](#prompt-scaffolds) and [Negative prompts](#negative-prompts) are
> copy-ready; the [Do / Don't](#do--dont) list is the checklist a visual is judged
> against.

---

## Creative DNA (the irreducible essence)

- **Epic glory clashed with mundane bureaucracy.** Heroes, gods, and dragons drawn
  with total sincerity; the comedy comes from *framing* them against ledgers, stamps,
  and a weary clerk — never from making the fantasy look silly.
- **Warm gold world, one divine light.** A perpetual golden late-afternoon; a single
  warm key, brightest at the divine burst. Dark vignette hugs the edges.
- **Painterly, illustrative, ornately framed.** Confident brushwork resolving to
  crisp forms; engraved gold metalwork and wax seals frame the UI.
- **Only magic glows.** The divine/arcane emit light; mundane stone, wood, and
  parchment never do (firelight from a forge is an allowed hot mundane source).
- **Measured, warm, never grimdark.** Prosperous, dignified, dry-witted.

## Palette (sampled from the title screen)

> **Approximate — eyeball-sampled** from the title screen; treat as targets, not
> exact specs. One dominant hue (gold) + one accent (blue gem) + warm parchment
> neutrals, grounded by a dark vignette.

| Role | Hex (approx.) | Use |
| --- | --- | --- |
| **Gold — highlight** | `#EAC76B` | Title metal highlights, finials, coins, rim accents |
| **Gold — mid** | `#C9A24B` | Dominant gold; rings, trim, sun-warmed stone |
| **Gold/bronze — deep** | `#8A6A2F` | Engraved shadow in metalwork, ornament depth |
| **Divine cream light** | `#FBF4D8` | God-rays, the brightest divine emission |
| **Warm sky glow** | `#E0A24F` | Mid sky, atmospheric warmth behind heroes |
| **Blue gem — accent** | `#3FA6DE` | The accent: inset title gems, magic sparks, glints |
| **Royal banner blue** | `#2C3E73` | Civic/Order banners, conical roofs, shields |
| **Red wax / seal** | `#9B2D24` | Wax seals, the DENIED stamp, military heraldry |
| **Parchment** | `#D9C7A0` | Forms, ledgers, scrolls, the neutral working world |
| **Ink / line dark** | `#2A2018` | Linework, ink, deepest readable shadow |
| **Vignette near-black (warm)** | `#161009` | Corner falloff, node backdrop |

**Discipline:** muted overall saturation; the **one saturated accent** is the
**blue gem** (or a divine glow), reserved for what matters most. No rainbow, no neon.

## Lighting

- **One warm key, brightest at the divine source.** A dominant warm light reads as if
  cast by the radiant sky-god / sun behind the heroes; for nodes and icons, a warm
  key from the **upper-left ~45°** (matching the parent guide) keeps the set
  consistent.
- **God-rays & atmosphere.** Volumetric light beams and dust in the air on key art;
  long warm shadows.
- **Dark vignette.** Corners and edges fall to warm near-black, concentrating the eye
  — strongest on the title plate and node backdrops.
- **Value = reverence.** The glorious background is warm and bright; the
  foreground desk/paperwork is cooler and more muted. Brightness marks importance.
- **Emission rule.** Only divine/arcane elements self-illuminate (the glow is the
  brightest thing in frame). Forge firelight is an allowed hot mundane source;
  ordinary stone/wood/cloth never glow.
- **Warm rim light** lifts subjects (and every map node) off the dark background.

## Brush, line & finish

- **Painterly-illustrative, semi-realistic.** Soft, deliberate brushwork that
  resolves to crisp, readable forms. Visible craft, not visible noise.
- **Confident, slightly hand-tooled edges** — like an engraved plate — without a
  heavy uniform cartoon outline.
- **Ornate engraved framing.** Gold metalwork with filigree, gem inlays, and red wax
  seals is the signature UI/badge treatment (the title plate is the north star).
- **Honest wear.** Chips, patina, ink-stains, scuffs — deliberate, never grime or
  clutter.
- **Material vocabulary** (from the parent guide): matte chalky **stone**; oiled
  mid-roughness **wood**; low-gloss forged **metal** (gold warm, steel cool-neutral,
  no chrome); soft matte **cloth/banners**; semi-translucent internally-lit
  **crystal/arcane** (the only glossy/emissive material).

## Perspective (per category)

- **Map nodes / buildings:** 3/4 isometric from slightly above (map-table camera),
  composed into the Base Ring. (See the node system in the bible.)
- **Icons / badges / resources:** front-on or slight 3/4, legible at ~32px.
- **Key art / splash:** cinematic eye-level or low-hero framing for drama (the title
  screen).

## Do / Don't

**Do**
- Hold **both halves** in key art — epic background, bureaucratic foreground.
- Ground everything in **warm gold + parchment**; spend the **blue-gem accent** on
  the one focal point.
- Keep the **node furniture identical** (gold Base Ring, laurel foliage, warm rim
  light, top badge); change only the building and its badge.
- Render the fantasy **straight and sincere**; let the **comedy live in the framing**
  (a DENIED stamp, an abacus, "ITEMIZE EVERYTHING").
- Use **fantasy-medieval** bureaucratic props: quills, wax seals, ledgers, scrolls,
  clipboards, abacus, stamps.
- Maintain **strong silhouettes** legible in grayscale and at small sizes.

**Don't**
- No **grimdark, gore, horror, or bleakness**; no cruelty.
- No **zany cartoon / slapstick / rubber-hose / meme** rendering; no goofy
  proportions.
- No **modern office** clichés (staplers, fluorescent light, cubicles, sticky notes,
  printers).
- No **sci-fi, steampunk, clockwork, or gunpowder**.
- No **neon, rainbow, oversaturation**; no **photoreal or 3D-render** look; no flat
  vector or hard cel outline.
- No **glowing mundane objects** (only divine/arcane emit; forge fire excepted).
- No **baked-in text, numbers, watermarks, or signatures** in the artwork.
- No **clutter** that buries the focal point; keep one clear subject with room to
  breathe.

## Prompt scaffolds

Fill the `{...}` slots; always append the **shared suffix** and pair with the
[negative prompts](#negative-prompts).

**Shared style suffix (append to every prompt):**
```
Asset Report style: painterly illustrative high-fantasy meets medieval bureaucracy,
warm gold palette with divine cream light and a single blue-gem accent, dark warm
vignette, one warm key light, ornate engraved gold framing, matte stone and oiled
wood, honest wear, strong readable silhouette, high craft, no text, no watermark
```

**Building map node:**
```
A {building} map node for Asset Report, {family} family, 3/4 isometric from slightly
above, sitting inside a consistent gold Base Ring it slightly overlaps, small rounded
terrain base with green laurel foliage, warm epic rim light, deep near-black warm
background, {roof color} roofs and {banner color} banners, [shared style suffix]
```

**Type badge / resource / UI icon:**
```
A {subject} icon for Asset Report, {circular gold-rimmed badge | red heraldic
banner-shield}, single concept, bold silhouette legible at 32px, warm gold and
parchment with one blue-gem accent, flat dark background, [shared style suffix]
```

**Character (hero or civil servant):**
```
A {hero/clerk/official} for Asset Report, 3/4 view, sincere heroic or wry
bureaucratic pose, royal-blue-and-gold cloth, believable {materials}, ink-stains and
honest wear, soft warm vignette background, [shared style suffix]
```

**Key art / splash:**
```
Key art for Asset Report: {epic scene — heroes, radiant sky-god, dragon} glowing in
the background while {a weary fantasy clerk at an ink-stained desk with ledgers,
stamps, abacus} works in the foreground, cinematic low-hero framing, god-rays, warm
gold with a single blue-gem accent, dark vignette, [shared style suffix]
```

## Negative prompts

**Base negative (always):**
```
photorealistic, photo, 3D render look, plastic, chrome, glossy CGI, flat vector,
hard cartoon outline, cel shading, anime, sticker, neon colors, oversaturated,
rainbow palette, pure black shadows, blown highlights, busy background, cluttered,
visual noise, grime, gore, grimdark, slapstick, goofy proportions, meme,
modern office, stapler, fluorescent light, cubicle, sticky note, printer, computer,
sci-fi, steampunk, clockwork, gunpowder, text, letters, words, numbers, watermark,
signature, logo, UI frames, extra limbs, deformed, blurry, low detail, jpeg artifacts
```

**Add for icons / badges / nodes (clean, single-concept):**
```
multiple subjects, cropped silhouette, drop shadow halo, edge fringing,
color fringing, inconsistent ring, off-center badge
```

**Add for non-divine subjects (no stray glow):**
```
glowing, emissive, magical glow, light beams, halo
```

## Consistency rules

1. **Same light, always** — one warm key, divine-only emission, dark vignette.
2. **Same palette discipline** — warm gold + parchment base, one blue-gem accent;
   no new colors invented per visual.
3. **Same node furniture** — identical Base Ring, foliage, rim light, and badge
   frame across the whole set; only the building/icon changes.
4. **Same perspective per category** — nodes 3/4 iso-from-above; icons front-on;
   key art cinematic.
5. **Same finish** — painterly-clean, engraved-plate edges, ornate gold framing.
6. **Fantasy drawn straight; comedy in the framing.**
7. **Search ArtLibrary first** (filter `collection == "AssetReport"`); reuse before
   generating a near-duplicate.
