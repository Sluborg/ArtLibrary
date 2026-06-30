# Asset Report — Buildings

> Describes the **architectural system** of *Asset Report* and how to design new
> buildings so they belong. This is the *what*; rendering rules (light,
> material, edge, palette) live in
> [`StyleGuides/Fantasy-Strategy-v1.md`](../../StyleGuides/Fantasy-Strategy-v1.md).
> Read [`GameArtBible.md`](GameArtBible.md) first.

## What a building is in this game

Every building is delivered as a **map node**: a painterly, isometric building
scene presented inside a consistent furniture of ring + badge + light. Buildings
are how the realm is built, and the map-node set is the largest art collection in
the game.

### Map-node anatomy (canonical — never vary the furniture)

The reference "Base Ring" sheet defines four fixed parts. Reproduce them exactly
on every building node:

1. **Base Ring** — a circular **gold ring**, identical on every node. It is the
   shared frame that makes the whole map read as one system. Render with the
   style guide's warm key light and engraved-plate finish. *Consistent for all.*
2. **Themed Scene** — the building itself, a 3/4 isometric-from-above scene that
   **sits inside and slightly overlaps the ring**, breaking the top edge so it
   feels three-dimensional. The building stands on a small rounded terrain base
   with a sprig of green **laurel/foliage** at the foot of the ring.
3. **Top Badge** — a small **circular, gold-rimmed badge** centered at the top of
   the ring, carrying the **node-type identifier** icon (hammer, stone, wheat,
   tome, scales, etc.). See [`Icons.md`](Icons.md).
4. **Rim Light** — a warm, "epic" rim light along the building's upper edges,
   lifting it off the dark background. *Epic warm theme*, consistent across all
   nodes.

> Background for the node set is a deep near-black warm field so the gold ring
> and rim light pop. The building never fights the ring; the ring never fights
> the badge.

## Building families

Design every new building into one of these families. The family fixes its roof
color, banner, badge frame, and the props in its scene.

### 1. Civic / Player Core — *blue & gold*
The player's identity and seat of power. Pale ashlar stone, **crenellated**
towers, **blue conical spires and domes with gold finials**, blue-and-gold
banners and pennants (often a gold star or sigil on blue).
- **Home Keep** — *Player base.* A single sturdy crenellated keep, one blue
  banner. The humble starting point.
- **Grand Citadel** — *Landmark.* The grand form: multiple blue-domed towers,
  many banners, gold trim — maximum civic splendor. This is the silhouette other
  buildings aspire to.
- **Settlement** — *Village / Watchpost.* A modest church-like hall and tower
  with a blue flag; the spreading edge of the realm.

### 2. Resource Extraction — *working timber & stone*
Honest, busy, tool-laden. Timber-and-plaster, scaffolding, cranes, carts, and the
**raw material visibly on show**. Plain roofs. Badge tells you the output.
- **Lumber Camp** — timber lodge, a crane, stacked logs. *(Badge: hammer.)*
- **Quarry** — cut-stone pit, a hoist/crane, grey blocks. *(Badge: stone.)*
- **Farmland** — windmill, tilled fields, a farmhouse, sheaves. *(Badge: wheat.)*
- **Iron Mine** — mine mouth in rock, cart rails, ore glint. *(Badge: ore gem.)*
- **Gold Mine** — mine mouth with gold seams and nuggets. *(Badge: gold nugget.)*

### 3. Research & Craft — *scholarship vs. industry*
- **Academy** — *Research.* A **classical blue-and-gold dome**, columns, learning.
  *(Badge: open book.)*
- **Forge** — *Crafting.* A workshop with a tall **chimney venting fire-glow**, an
  anvil, a kiln. The fire is firelight (hot mundane source), handled per the
  style guide. *(Badge: crafting emblem — chalice/shield.)*

### 4. Military & Defense — *red banners, fortified*
Drilled, hard-edged, **red heraldic banners**, red-tile or grey battlements. These
nodes use the **heraldic banner-shield badge** (red) instead of the circular gold
badge — frame shape itself signals "military."
- **Barracks** — *Military.* Red-tiled hall, weapon racks, training ground.
  *(Badge: crossed swords on red.)*
- **Archer Tower** — *Defense.* A tall stone tower with a red banner.
  *(Badge: bow on red.)*
- **Wall** — *Defense.* Crenellated curtain wall and gate, red banners.
  *(Badge: shield.)*

### 5. Economy — *commerce & color*
- **Market** — *Economy.* **Striped (red-and-white) awnings**, laden stalls,
  crates of goods, coin. The most colorful, bustling node. *(Badge: scales.)*

### 6. Divine — *the only building that glows*
- **Temple** — *Divine.* A shrine with a **radiant figure / holy light** between
  two banner-hung pillars. Per the style guide, this is the one building family
  that is **emissive** — holy light is the brightest thing in frame.
  *(Badge: radiant star.)*

## Designing a new building

1. **Place it in a family** (above). The family decides roof color, banner color,
   badge frame, and scene props.
2. **Pick the right node-type badge** (see [`Icons.md`](Icons.md)) — circular gold
   for civic/resource/economy/research/divine, heraldic red shield for
   military/defense.
3. **Build the silhouette first.** It must read as a black shape and be
   identifiable from its neighbors at node size. Civic = vertical towers + domes;
   resource = low working structures + tools; military = hard battlements;
   economy = awnings + stalls; divine = symmetrical shrine + light.
4. **Render the scene** per the style guide: 3/4 isometric from slightly above,
   warm upper-left key light, the node's warm rim light, matte stone / oiled wood
   / red tile, honest wear, small terrain base with laurel foliage.
5. **Compose into the Base Ring**, breaking the top edge, with the Top Badge
   centered above. Keep the ring, badge frame, foliage, and rim light **identical
   to every other node** — only the building changes.
6. **Signal progression** through mass and ornament, not new colors: more towers,
   more banners, more gold, taller silhouette = more advanced. Within an upgrade
   line (e.g. Settlement → Town → Citadel) keep the family's roof and banner so
   the lineage is obvious.

## Consistency checklist for a building node

- [ ] Correct family roof color, banner, and badge frame.
- [ ] Identical Base Ring, foliage, and rim light to the rest of the set.
- [ ] Top Badge centered, gold-rimmed (or red heraldic for military/defense).
- [ ] Silhouette unmistakable at node size and in grayscale.
- [ ] Only the Temple (and any divine/arcane element) emits light.
- [ ] Warm parchment-grounded palette; one dominant hue + the family accent.
- [ ] 3/4 isometric-from-above perspective matching the map-table camera.
