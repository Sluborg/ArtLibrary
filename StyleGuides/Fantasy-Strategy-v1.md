# Fantasy Strategy — Style Guide v1

> **Status:** Canonical. This is the production-ready style guide Lubot loads
> before generating Fantasy Strategy visuals. It is the single source of creative
> truth for this style: every image, illustration, and icon must obey it.
>
> **How to use this file:** Read it top to bottom before generating. The
> [Prompt Patterns](#prompt-patterns) and
> [Negative Prompt Patterns](#negative-prompt-patterns) sections are
> copy-ready; the [Consistency Rules](#consistency-rules),
> [Style Constraints](#style-constraints), and [Creative DNA](#creative-dna)
> sections are the checklist a finished visual is judged against.

---

## Vision

Fantasy Strategy is a world of **kingdoms, banners, and hard choices**, seen from
the calm distance of a commander's map table. The art should feel like the
illustrated plates of a beautiful strategy game manual: confident, legible, and
timeless — never noisy, never grimdark, never cartoonish. A player glancing at
any visual should instantly read **what it is, which faction it belongs to, and
whether it matters**, before they read a single word of text.

The emotional target is **measured wonder**: a grounded, hand-crafted fantasy
that takes itself seriously without becoming bleak. Heroic but not gaudy.
Magical but not garish. Old-world craft, rendered clean.

## Visual Identity

- **Genre:** high fantasy, tactical/strategy framing — castles, units, terrain,
  resources, banners, sigils.
- **Format range:** UI **icons**, unit and building **illustrations**, terrain
  and resource tiles, faction crests, and full **wallpapers** / key art.
- **Overall feel:** semi-stylized painterly realism. Forms are simplified and
  readable like an icon set, but surfaces are painted with believable material
  and light. Think "illustrated board-game plate," not photoreal render and not
  flat vector.
- **Signature traits:** strong silhouettes, warm parchment neutrals, a single
  confident light source, restrained palettes, and a faint hand-crafted edge as
  if engraved or hand-painted.

## Shape Language

- **Silhouette first.** Every visual must be recognizable as a black silhouette
  alone. If the silhouette is ambiguous, the shape is wrong.
- **Primary forms are big and simple; detail is earned.** Read the big shape,
  then a few medium shapes, then sparse fine detail. No uniform detail noise.
- **Faction shape cues:**
  - *Order / human kingdoms* — vertical, symmetrical, architectural; squared
    bases, banners, clean arches.
  - *Wild / beast clans* — diagonal, asymmetrical, organic; claws, horns,
    tusk-and-bone angles.
  - *Arcane / mystic* — floating, concentric, crystalline; circles, runes,
    levitating elements.
- **Corners:** gently softened, not razor-sharp and not rounded-cute. A slight
  hand-tooled bevel.
- **Scale logic:** heroes and key buildings get more silhouette complexity;
  common units and resources stay simple so the map reads at a glance.

## Color Philosophy

- **Parchment-grounded.** The neutral world is warm: aged paper, weathered
  stone, oiled wood. Color sits on top of this warm base, never replaces it.
- **Restrained palettes.** Each visual uses **one dominant hue + one accent +
  warm neutrals**. No rainbow. Saturation is muted overall, with a single
  saturated accent allowed for the thing that matters most.
- **Faction color keys** (use for tint, banners, glows, and rim accents):
  - *Order* — royal blue + warm gold.
  - *Wild* — moss/forest green + bone/ochre.
  - *Arcane* — violet/indigo + cyan glow.
  - *Neutral / resource* — desaturated earth tones, copper, slate.
- **Accent discipline.** The accent color marks the focal point (a glowing rune,
  a banner, a gem). Everything else recedes toward the warm neutral base.
- **Avoid:** pure black, pure white, neon, and high-saturation primaries spread
  across the whole image.

## Lighting

- **One key light, warm, upper-left.** A single dominant light source, warm in
  temperature, coming from the upper-left at roughly 45°. Consistent across the
  whole set so nothing looks pasted in.
- **Cool, soft fill.** A gentle cool fill (sky bounce) lifts the shadows so they
  never go muddy or pure black. Shadow tone is a desaturated cool, not gray.
- **Rim light for separation.** A subtle warm or faction-tinted rim on the upper
  edges lifts the subject off its background. Used sparingly, only where
  separation is needed.
- **Magic emits; nothing else does.** Only arcane elements (runes, spells,
  enchanted gear) are self-illuminating, and that glow is the brightest thing in
  frame. Mundane materials never glow.

## Materials

Render a small, consistent material vocabulary so the world feels unified:

- **Stone** — matte, chalky, weathered; soft micro-pitting, no mirror highlights.
- **Wood** — oiled, mid-roughness, visible but calm grain.
- **Metal** — brushed/forged, low-gloss; controlled specular, gold reads warm,
  steel reads cool-neutral. No chrome.
- **Cloth / banners** — soft matte with gentle folds; faction color lives here.
- **Leather / hide** — supple matte, subtle grain.
- **Crystal / arcane** — semi-translucent, internally lit, the only glossy /
  emissive material allowed.
- **Earth / foliage** — broken-up matte, never a flat fill.

Surfaces show **honest wear** — chips, patina, scuffs — but stay clean and
deliberate. Weathering tells a story; it never becomes grime or clutter.

## Composition

- **Centered and self-contained** for icons, units, and resources: one clear
  subject, generous padding, no cropping of the key silhouette.
- **Strong figure/ground separation.** The subject never fights its background.
  Backgrounds for icons are simple — a soft parchment vignette or a faint tonal
  field — so the silhouette stays clean.
- **Rule of thirds / heroic framing** for illustrations and wallpapers; lead the
  eye to the focal accent.
- **One focal point per visual.** Secondary elements support, they do not
  compete. If two things shout, mute one.
- **Breathing room.** Negative space is a feature; crowding is a failure.

## Perspective

- **Icons & resources:** front-on or slight 3/4, eye-level. Flat enough to read
  instantly at small sizes.
- **Units & buildings:** **3/4 view from slightly above** (a gentle
  bird's-eye / isometric-leaning angle), matching the map-table camera. This is
  the default for anything that sits "on the board."
- **Terrain tiles:** consistent top-down-leaning isometric so tiles stitch
  together cleanly.
- **Key art / wallpapers:** cinematic eye-level or low-hero angle is allowed for
  drama.
- Keep perspective **consistent within a set** so pieces share one world.

## Rendering

- **Painterly-clean.** Soft, deliberate brushwork that resolves to crisp,
  readable forms. Visible craft, not visible noise.
- **Edges:** confident, slightly hand-tooled outlines or form-edges — like an
  engraved plate — without a heavy uniform cartoon outline.
- **Gradients are smooth and few.** Form is described by light and material, not
  by busy texture.
- **Resolution-aware detail.** Detail density is tuned to display size: icons
  read at 32–64px; illustrations and wallpapers carry more.
- **Clean alpha.** Icons and units render on transparent or trivially removable
  backgrounds, with tidy anti-aliased edges — no halos, no fringing.

## Icon Language

- **Built for small sizes.** An icon must stay legible down to ~32px. Test the
  silhouette small before anything else.
- **One concept per icon.** Each icon communicates a single idea (a resource, an
  action, a unit type). No compound scenes.
- **Consistent visual weight.** Icons in a set share line weight, padding, corner
  treatment, and lighting so they read as a family.
- **Bold silhouette, minimal interior detail.** Interior detail only where it
  aids recognition at size.
- **Color-coded by function** using the faction/resource color keys, but
  legible in grayscale too — never rely on hue alone.
- **Square-safe.** Compose within a centered safe area with even padding so icons
  align on a grid.

## Prompt Patterns

Copy-ready scaffolds. Fill the `{...}` slots. Always append the shared style
suffix and pair with the [Negative Prompt Patterns](#negative-prompt-patterns).

**Shared style suffix (append to every prompt):**

```
semi-stylized painterly fantasy strategy game art, strong readable silhouette,
single warm key light from upper-left with soft cool fill, restrained muted
palette grounded in warm parchment neutrals with one {faction} accent,
hand-crafted engraved-plate finish, clean edges, centered, generous padding,
consistent material rendering, high craft, no text, no watermark
```

**Icon:**

```
A {subject} icon for a fantasy strategy game, {faction} faction,
front-on, bold simple silhouette legible at 32px, single concept,
flat parchment-tone background, [shared style suffix]
```

**Unit / character:**

```
A {unit} of the {faction} faction, 3/4 view from slightly above,
heroic readable pose, faction colors {color key} on cloth and banner,
believable {materials}, honest wear, soft parchment vignette background,
[shared style suffix]
```

**Building / structure:**

```
A {building} for the {faction} faction, 3/4 isometric-leaning view from above,
architectural silhouette, {materials}, banners in faction color,
sits on a simple terrain base, [shared style suffix]
```

**Terrain / resource tile:**

```
A {terrain/resource} tile, top-down isometric, seamless-friendly,
muted earth tones, matte materials, simple readable forms, [shared style suffix]
```

**Wallpaper / key art:**

```
Key art of {scene} in the Fantasy Strategy world, cinematic {eye-level/low-hero}
framing, one clear focal point lit by the warm key light, atmospheric depth,
restrained palette with a single saturated {faction} accent, [shared style suffix]
```

## Negative Prompt Patterns

Append to every generation. Tune the bracketed extras per visual type.

**Base negative (always):**

```
photorealistic, photo, 3D render look, plastic, chrome, glossy CGI,
flat vector, hard cartoon outline, cel shading, anime, sticker,
neon colors, oversaturated, rainbow palette, pure black shadows, blown highlights,
busy background, cluttered, visual noise, grime, gore, grimdark,
text, letters, words, numbers, watermark, signature, logo, UI frames,
extra limbs, deformed, blurry, low detail, jpeg artifacts
```

**Add for icons / units (clean cutout):**

```
background scenery, cropped silhouette, multiple subjects, drop shadow halo,
edge fringing, color fringing
```

**Add for non-arcane subjects:**

```
glowing, emissive, magical glow, light beams
```

## Consistency Rules

A new visual must sit beside the existing library and look like the same hand
made it. Enforce:

1. **Same light, always.** Warm key from upper-left, cool soft fill, magic-only
   emission. No exceptions across a set.
2. **Same palette discipline.** Warm parchment base + one dominant hue + one
   accent, keyed to faction. No new colors invented per visual.
3. **Same material vocabulary.** Use the [Materials](#materials) list; don't
   introduce chrome, neon plastic, or photoreal surfaces.
4. **Same perspective per category.** Icons front-on; units/buildings 3/4 from
   above; terrain isometric. Match the category, not your mood.
5. **Same edge & finish.** Hand-tooled engraved-plate edges, painterly-clean
   rendering, no heavy uniform outline.
6. **Faction legibility.** Shape cue + color key together must identify the
   faction at a glance, and still read in grayscale.
7. **Search before adding.** If the library already has a close match, reuse it.
   New visuals exist to fill genuine gaps, not to duplicate.
8. **Set cohesion.** Within an icon set or unit roster, share line weight,
   padding, and scale logic so the family reads as one.

## Style Constraints

Hard limits. A visual that breaks any of these is rejected, not tweaked:

- **No text, numbers, watermarks, or signatures** baked into the image.
- **No photorealism and no 3D-render look.** Painterly-stylized only.
- **No flat vector and no hard cartoon/cel outline.** Painted craft only.
- **No neon, no rainbow, no oversaturation.** Muted, parchment-grounded palette.
- **No glow on mundane objects.** Only arcane elements emit light.
- **No pure black or pure white** as large fields; shadows and highlights stay
  toned.
- **No clutter, gore, or grimdark tone.** Clean, measured, heroic.
- **Icons stay single-concept and legible at 32px.** No miniature scenes.
- **Backgrounds for icons/units stay simple** and trivially removable.

## Creative DNA

If everything else is forgotten, keep these. This is the irreducible essence of
Fantasy Strategy art:

- **Silhouette is king.** Readability beats detail, every time.
- **Measured wonder.** Heroic, grounded, hand-crafted — never gaudy, never bleak.
- **Warm parchment world, one confident light.** The whole world shares one warm
  key light and a warm neutral base.
- **Restraint is the style.** One dominant hue, one accent, muted everything
  else. The accent marks what matters.
- **Only magic glows.** Emission is reserved; it always means "arcane."
- **One subject, one focal point, room to breathe.**
- **Same hand made all of it.** Consistency across the set is the brand.
