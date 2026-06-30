# Asset Report — Icon Specification

> The **canonical reference for icon generation** in *Asset Report* — building
> type badges, resource icons, and UI/action icons. The *what*; the *how*
> (silhouette, light, edge, palette discipline) is owned by
> [`StyleGuides/Fantasy-Strategy-v1.md`](../../StyleGuides/Fantasy-Strategy-v1.md),
> especially its **Icon Language** section. Read that and
> [`GameArtBible.md`](GameArtBible.md) first.

## Icon tiers

The game uses three tiers of icon. Each has a fixed frame so the player learns
the grammar once.

| Tier | What it is | Frame | Where it appears |
| --- | --- | --- | --- |
| **Map-node** | A whole building scene | Gold **Base Ring** + Top Badge + rim light | The map (see [`Buildings.md`](Buildings.md)) |
| **Type badge** | A node's type identifier | Small **circular gold-rim** badge, **or** **red heraldic banner-shield** | Top-center of each node; legends |
| **Resource / UI icon** | One concept (a good, an action, a status) | **Circular gold-rim** badge (resources) or framed/unframed glyph (UI) | Resource bar, buttons, tooltips |

## The two canonical badge frames

Frame shape is **meaningful** — it encodes category before color does.

1. **Circular gold-rim badge** — the default. A dark, slightly domed fill ringed
   in warm engraved gold. Used for **resources, civic, economy, research, and
   divine** types. This is the same gold language as the Base Ring, so badges and
   nodes read as one family.
2. **Heraldic banner-shield badge** — a red banner/shield silhouette with a gold
   edge. Used for **military and defense** types (Barracks, Archer Tower, Wall).
   Seeing the red shield, the player knows "military" before reading the icon
   inside it.

> Keep both frames pixel-consistent across the whole set: same gold rim weight,
> same dark fill, same size, same warm rim light. Only the glyph inside changes.

## Type-badge glyph library (from the references)

Each building carries one simple, silhouette-first glyph:

| Building | Glyph | Frame |
| --- | --- | --- |
| Lumber Camp | Hammer | Circular gold |
| Quarry | Cut stone | Circular gold |
| Farmland | Wheat sheaf | Circular gold |
| Iron Mine | Ore gem | Circular gold |
| Gold Mine | Gold nugget | Circular gold |
| Academy | Open book | Circular gold |
| Forge | Chalice / crafting emblem | Circular gold |
| Market | Scales | Circular gold |
| Temple | Radiant star | Circular gold (emissive glyph) |
| Barracks | Crossed swords | **Red heraldic shield** |
| Archer Tower | Bow | **Red heraldic shield** |
| Wall | Shield | **Red heraldic shield** |
| Home Keep / Settlement / Citadel | Faction sigil / star on banner | Pennant / civic mark |

When adding a new building, choose a glyph that is (a) a single object, (b) an
unmistakable silhouette, and (c) not already in use. Tools imply resources;
weapons imply military; civic symbols (book, scales, star) imply civic/economy/
divine.

## How icons communicate meaning

- **Hierarchy:** node > type badge > resource/UI icon, by size and frame richness.
  Never let a UI pip compete visually with a building node.
- **Badge placement:** type badges sit **centered at the top of the node**,
  slightly overlapping the Base Ring. Status badges (wax seals) sit at corners.
- **Color coding** (style-guide keys): **blue+gold** civic/Order, **red**
  military/defense, **gold-neutral** resource/economy, **warm radiant** divine.
  Color reinforces the frame; it never carries meaning alone — every icon also
  reads in grayscale.
- **Silhouette first:** identifiable as a black shape at ~32px. Test small before
  detailing. Interior detail only where it aids recognition.
- **Scale:** one concept per icon, generous even padding, composed in a centered
  square-safe area so icons align on a grid.

## UI / action icons

Beyond buildings and resources, the game needs the icons of **bureaucracy** —
these are part of its identity and should be drawn as fantasy-medieval office
objects, not modern symbols:

- **Stamp** (approve/deny), **wax seal**, **quill**, **ledger/clipboard**,
  **scroll/writ**, **abacus**, **coin (gp)**, **quest scroll**, **inkwell**,
  **filing tray ("IN"/"PENDING")**, **audit notice**.
- Status stamps are a sub-set with strong color meaning: **APPROVED** (green
  wax/ink), **DENIED** (red), **PENDING** (neutral), **OVERDUE** (warning).
  These may carry the only baked-in text the game uses *inside the diegetic UI*,
  but icon assets themselves stay text-free per the style guide.

## Consistency checklist for an icon

- [ ] Correct tier and frame (circular gold vs. red heraldic vs. UI glyph).
- [ ] Single concept; unmistakable silhouette at 32px; reads in grayscale.
- [ ] Color key matches category and only reinforces the frame.
- [ ] Gold-rim weight, dark fill, and rim light match the rest of the set.
- [ ] Only divine/arcane glyphs (e.g. the Temple star, Faith) emit light.
- [ ] No baked-in text on the asset (status-stamp lettering is a UI decision, not
      an icon asset).
