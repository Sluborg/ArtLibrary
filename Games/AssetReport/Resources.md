# Asset Report — Resources

> The visual language for **resource icons** in *Asset Report*. The *what* of the
> economy; rendering rules live in
> [`StyleGuides/Fantasy-Strategy-v1.md`](../../StyleGuides/Fantasy-Strategy-v1.md).
> Pairs with [`Icons.md`](Icons.md) (the icon spec) and
> [`GameArtBible.md`](GameArtBible.md).

## The economy at a glance

*Asset Report* runs a tangible, medieval, **gold-denominated** economy. Resources
are raw materials extracted from the map, refined goods, and two meta-resources
that are unique to this game: **Faith** (the only emissive resource) and
**Approval/Influence** (the bureaucratic currency of stamps and signatures).

Every resource has a single, instantly readable hero object, shown in a circular
gold badge, and must survive shrinking to a resource-bar pip and reading in
grayscale (silhouette + value, never hue alone).

## Resource set

| Resource | Hero object | Source | Color key | Notes |
| --- | --- | --- | --- | --- |
| **Wood** | Stacked oiled logs / cut timber | Lumber Camp | warm brown | Oiled wood material, calm grain |
| **Stone** | Cut grey ashlar block(s) | Quarry | slate grey | Matte, chalky, soft pitting |
| **Food / Grain** | Wheat sheaf | Farmland | golden ochre | The harvest; windmill output |
| **Iron / Ore** | Raw ore chunk → ingot | Iron Mine | cool blue-grey | Low-gloss forged metal |
| **Gold (gp)** | Coin stack / nugget | Gold Mine, Market | warm gold | The currency; the ledger's lifeblood |
| **Knowledge** | Open tome / scroll | Academy | royal blue + gold | Research progress |
| **Faith** | Radiant star / holy light | Temple | warm radiant | **Emissive** — the one glowing resource |
| **Approval / Influence** | Wax seal / stamp / signed writ | Civil service | red wax + gold | The bureaucratic meta-currency |

## Visual rules for resource icons

- **One object, dead center, generous padding.** A resource icon is a single
  concept (style guide: *one concept per icon*). No scenes, no compound props.
- **Circular gold badge frame** by default — the same gold-rim language as the
  building Top Badge, so resources and node badges read as one family. (See
  [`Icons.md`](Icons.md) for the frame spec.)
- **Material is the storyteller.** Wood reads as oiled timber, stone as chalky
  ashlar, gold as warm low-gloss metal, ore as cool forged metal — per the style
  guide's material vocabulary. The material alone should half-identify the
  resource before the shape resolves.
- **Gold is the connective tissue.** Currency, badge rims, and the warm key light
  all share the gold register. Gold pieces (gp) appear throughout the UI, quest
  payouts, and the treasury — keep the coin look consistent everywhere it shows.
- **Faith is the only one that glows.** Its radiant star is self-illuminating and
  is the brightest thing in its badge; every other resource is honest,
  non-emissive material.
- **Approval/Influence is the game's signature resource.** Render it as the
  physical objects of bureaucracy — a **red wax seal**, a **stamp**, a **signed
  writ** — not an abstract symbol. It ties the economy back to the player's desk.
- **Quantity is conveyed by the bar, not the icon.** The icon is the *type*; the
  count lives in the resource bar beside it (see [`UI.md`](UI.md)). Don't draw
  "more logs" to mean "more wood."

## Refined / derived goods

When refined goods are needed (e.g. planks from wood, tools from iron, bread from
grain), keep the **same color key as the raw resource** and show the worked form
(plank vs. log, ingot vs. ore, loaf vs. sheaf). Lineage reads through shared hue;
processing reads through the changed object.

## Consistency checklist for a resource icon

- [ ] Single hero object, centered, even padding, legible at ~32px.
- [ ] Circular gold badge frame matching the node-badge family.
- [ ] Correct color key from the table; muted, parchment-grounded.
- [ ] Material identifies the resource; reads in grayscale too.
- [ ] Only Faith emits light; all others are non-emissive.
- [ ] Gold/currency look matches the gp used across the UI and payouts.

## Resource-icon worklist

Standalone resource icons, drawn as their own pieces (derived from the top-badge
icons on the node design sheet, whose look is approved). Placeholders for now. This
set is **proposed**, pending ResourceType ratification.

| Stable ID | Display name | Description/role | Art status | Target filename | raw_url |
| --- | --- | --- | --- | --- | --- |
| `icon-resource-wood` | Wood | Stacked oiled logs / cut timber (Lumber Camp) | needed (placeholder) | `Icons/AssetReport/icon-resource-wood.png` | |
| `icon-resource-stone` | Stone | Cut grey ashlar block (Quarry) | needed (placeholder) | `Icons/AssetReport/icon-resource-stone.png` | |
| `icon-resource-food` | Food / Grain | Wheat sheaf; the harvest (Farmland) | needed (placeholder) | `Icons/AssetReport/icon-resource-food.png` | |
| `icon-resource-iron` | Iron / Ore | Raw ore → ingot (Iron Mine) | needed (placeholder) | `Icons/AssetReport/icon-resource-iron.png` | |
| `icon-resource-gold` | Gold (gp) | Coin stack / nugget; the currency (Gold Mine, Market) | needed (placeholder) | `Icons/AssetReport/icon-resource-gold.png` | |
| `icon-resource-knowledge` | Knowledge | Open tome / scroll; research (Academy) | needed (placeholder) | `Icons/AssetReport/icon-resource-knowledge.png` | |
| `icon-resource-faith` | Faith | Radiant star / holy light — the emissive resource (Temple) | needed (placeholder) | `Icons/AssetReport/icon-resource-faith.png` | |
| `icon-resource-approval` | Approval / Influence | Wax seal / stamp / signed writ; bureaucratic currency (Civil service) | needed (placeholder) | `Icons/AssetReport/icon-resource-approval.png` | |
