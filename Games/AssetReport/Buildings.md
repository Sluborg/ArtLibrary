# Asset Report — Buildings (roster + art worklist)

> The **building roster as a checklist that doubles as the needed-vs-done worklist**
> for *Asset Report* map nodes. Read [`GameArtBible.md`](GameArtBible.md) first for
> the node-construction system and the shared vocabulary; rendering rules live in
> [`StyleGuides/AssetReport-v1.md`](../../StyleGuides/AssetReport-v1.md). The roster
> is seeded from the committed reference plate
> [`node-design-sheet.png`](../../Illustrations/AssetReport/node-design-sheet.png).
>
> **Terminology:** the **"Art status"** column tracks whether the *visual* exists in
> the DAM (`needed` / `done`) — it is **not** an "Asset status" (see the Glossary in
> the bible: *asset* is a game concept; *visual* is a DAM file).

## Roster / worklist

`raw_url` is **blank until the visual is uploaded** and appears in `asset-index.json`
(it then becomes `https://raw.githubusercontent.com/Sluborg/ArtLibrary/main/<Target filename>`).
All 15 building nodes are currently **needed** — none are in the index yet.

> This roster is a **proposed art backlog** derived from the reference sheet —
> candidate nodes, **not approved game design**. Stefan's sign-off at generation
> time gates what actually gets made; rows here imply no commitment to include a
> building in the game.

| Stable ID (slug) | Display name | Category | Top-badge icon | Gameplay role | Art status (needed/done) | Target filename | raw_url (blank until uploaded) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `home-keep` | Home Keep | `PLAYER_BASE` | Blue pennant (star) | Player base / starting capital | needed | `Illustrations/AssetReport/node-home-keep.png` | |
| `grand-citadel` | Grand Citadel | `LANDMARK` | Blue pennant | Max-tier civic landmark | needed | `Illustrations/AssetReport/node-grand-citadel.png` | |
| `settlement` | Settlement | `CIVIC` | Blue pennant | Village / watchpost expansion | needed | `Illustrations/AssetReport/node-settlement.png` | |
| `lumber-camp` | Lumber Camp | `RESOURCE` | Hammer | Produces **wood** | needed | `Illustrations/AssetReport/node-lumber-camp.png` | |
| `quarry` | Quarry | `RESOURCE` | Stone block | Produces **stone** | needed | `Illustrations/AssetReport/node-quarry.png` | |
| `farmland` | Farmland | `RESOURCE` | Wheat sheaf | Produces **food/grain** | needed | `Illustrations/AssetReport/node-farmland.png` | |
| `iron-mine` | Iron Mine | `RESOURCE` | Ore gem (blue) | Produces **iron/ore** | needed | `Illustrations/AssetReport/node-iron-mine.png` | |
| `gold-mine` | Gold Mine | `RESOURCE` | Gold nuggets | Produces **gold (gp)** | needed | `Illustrations/AssetReport/node-gold-mine.png` | |
| `academy` | Academy | `RESEARCH` | Open book | Research / **knowledge** | needed | `Illustrations/AssetReport/node-academy.png` | |
| `forge` | Forge | `CRAFTING` | Crafting emblem (shield/chalice) | Crafts equipment | needed | `Illustrations/AssetReport/node-forge.png` | |
| `barracks` | Barracks | `MILITARY` | Crossed swords (red shield) | Trains military units | needed | `Illustrations/AssetReport/node-barracks.png` | |
| `archer-tower` | Archer Tower | `DEFENSE` | Bow (red shield) | Ranged defense | needed | `Illustrations/AssetReport/node-archer-tower.png` | |
| `wall` | Wall | `DEFENSE` | Shield (red) | Fortification / defense | needed | `Illustrations/AssetReport/node-wall.png` | |
| `temple` | Temple | `DIVINE` | Radiant star | **Faith** / divine (the emissive node) | needed | `Illustrations/AssetReport/node-temple.png` | |
| `market` | Market | `ECONOMY` | Scales (balance) | Trade / economy | needed | `Illustrations/AssetReport/node-market.png` | |

> **Roster status summary:** 15 building nodes — **15 needed, 0 done.** Update a
> row's **Art status** to `done` and paste its `raw_url` once the node visual is
> uploaded and appears in `asset-index.json`. (The two committed visuals so far are
> the **title screen** and this **node design sheet**, not building nodes.)

---

## Building families (design notes)

Design every new building into one of these families. The family fixes its roof
color, banner, badge frame, and the props in its scene. (Node anatomy — Base Ring +
Themed Scene + Top Badge + Rim Light — is canonical; see
[`GameArtBible.md`](GameArtBible.md).)

### 1. Civic / Player core — *blue & gold* (`PLAYER_BASE`, `LANDMARK`, `CIVIC`)
The player's identity and seat of power. Pale ashlar stone, **crenellated** towers,
**blue conical spires and domes with gold finials**, blue-and-gold banners and
pennants (often a gold star or sigil on blue).
- **Home Keep** — *Player base.* A single sturdy crenellated keep, one blue banner.
  The humble starting point.
- **Grand Citadel** — *Landmark.* The grand form: multiple blue-domed towers, many
  banners, gold trim — maximum civic splendor. The silhouette others aspire to.
- **Settlement** — *Village / Watchpost.* A modest church-like hall and tower with a
  blue flag; the spreading edge of the realm.

### 2. Resource extraction — *working timber & stone* (`RESOURCE`)
Honest, busy, tool-laden. Timber-and-plaster, scaffolding, cranes, carts, and the
**raw material visibly on show**. Plain roofs. Badge tells you the output.
- **Lumber Camp** — timber lodge, a crane, stacked logs. *(Badge: hammer.)*
- **Quarry** — cut-stone pit, a hoist/crane, grey blocks. *(Badge: stone.)*
- **Farmland** — windmill, tilled fields, a farmhouse, sheaves. *(Badge: wheat.)*
- **Iron Mine** — mine mouth in rock, cart rails, ore glint. *(Badge: ore gem.)*
- **Gold Mine** — mine mouth with gold seams and nuggets. *(Badge: gold nugget.)*

### 3. Research & Craft — *scholarship vs. industry* (`RESEARCH`, `CRAFTING`)
- **Academy** — *Research.* A **classical blue-and-gold dome**, columns, learning.
  *(Badge: open book.)*
- **Forge** — *Crafting.* A workshop with a tall **chimney venting fire-glow**, an
  anvil, a kiln. The fire is firelight (a hot mundane source), handled per the style
  guide. *(Badge: crafting emblem — chalice/shield.)*

### 4. Military & Defense — *red banners, fortified* (`MILITARY`, `DEFENSE`)
Drilled, hard-edged, **red heraldic banners**, red-tile or grey battlements. These
nodes use the **heraldic banner-shield badge** (red) instead of the circular gold
badge — frame shape itself signals "military".
- **Barracks** — *Military.* Red-tiled hall, weapon racks, training ground. *(Badge:
  crossed swords on red.)*
- **Archer Tower** — *Defense.* A tall stone tower with a red banner. *(Badge: bow on
  red.)*
- **Wall** — *Defense.* Crenellated curtain wall and gate, red banners. *(Badge:
  shield.)*

### 5. Economy — *commerce & color* (`ECONOMY`)
- **Market** — *Economy.* **Striped (red-and-white) awnings**, laden stalls, crates
  of goods, coin. The most colorful, bustling node. *(Badge: scales.)*

### 6. Divine — *the only building that glows* (`DIVINE`)
- **Temple** — *Divine.* A shrine with a **radiant figure / holy light** between two
  banner-hung pillars. Per the style guide, this is the one building family that is
  **emissive** — holy light is the brightest thing in frame. *(Badge: radiant star.)*

## Designing a new building

1. **Place it in a family** (above) → fixes roof color, banner color, badge frame,
   scene props. Assign its `Category`.
2. **Give it a slug** (kebab-case) and target filename `node-<slug>.png` under
   `Illustrations/AssetReport/`; add a row to the worklist with Art status `needed`.
3. **Pick the right node-type badge** — circular gold for
   civic/resource/economy/research/divine, heraldic red shield for military/defense.
4. **Build the silhouette first.** It must read as a black shape, identifiable from
   its neighbors at node size. Civic = vertical towers + domes; resource = low
   working structures + tools; military = hard battlements; economy = awnings +
   stalls; divine = symmetrical shrine + light.
5. **Render the scene** per the style guide: 3/4 isometric from slightly above, warm
   upper-left key light, the node's warm rim light, matte stone / oiled wood / red
   tile, honest wear, small terrain base with laurel foliage.
6. **Compose into the Base Ring**, breaking the top edge, Top Badge centered above.
   Keep the ring, badge frame, foliage, and rim light **identical to every other
   node** — only the building changes.
7. **Signal progression** through mass and ornament, not new colors: more towers,
   more banners, more gold, taller silhouette = more advanced.

## Consistency checklist for a building node

- [ ] Correct family roof color, banner, and badge frame.
- [ ] Identical Base Ring, foliage, and rim light to the rest of the set.
- [ ] Top Badge centered, gold-rimmed (or red heraldic for military/defense).
- [ ] Silhouette unmistakable at node size and in grayscale.
- [ ] Only the Temple (and any divine/arcane element) emits light.
- [ ] Warm parchment-grounded palette; one dominant hue + the family accent.
- [ ] 3/4 isometric-from-above perspective matching the map-table camera.
- [ ] Slug, `node-<slug>.png` filename, `collection: AssetReport`, and required
      `kind: illustration` set so it indexes and validates.
