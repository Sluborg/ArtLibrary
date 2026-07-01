# Asset Report — UI Visual Language

> The visual language for the game's **UI**: panels, borders, windows, fonts,
> decorations, interaction style, and mood. This describes *what the UI is made
> of*, not how to build it — no implementation. Rendering rules live in
> [`StyleGuides/Fantasy-Strategy-v1.md`](../../StyleGuides/Fantasy-Strategy-v1.md);
> read [`GameArtBible.md`](GameArtBible.md) first.

## Concept: the screen is a clerk's desk

The UI of *Asset Report* is not a frame **around** the game — it **is** the game.
The player's job is administration, so the interface is the desk, the ledger, the
clipboard, and the stamp. Every UI surface should feel like a real, slightly worn
object of a fantasy-medieval civil service: warm, official, hand-made, tactile.

The gold-engraved **title plate** of the splash art ("ASSET REPORT") is the north
star for the UI's most important moments; the **torn-parchment subtitle banner**
is the north star for its quieter ones.

## Panels

- **Parchment & ledger pages.** Primary panels are warm aged paper — ledger
  sheets with faint ruled lines, columns, and ink. Lists (quests, resources,
  buildings) look like entries in a ledger.
- **Clipboards & document trays.** Modal content sits on a clipboard or in a
  filing tray. The "IN", "PENDING", and "DENIED" trays are a recurring motif.
- **Slate-and-gold plates.** Headline panels (titles, results, victory) use the
  dark slate background with a heavy gold engraved frame, like the title plate.
- **Layering reads as a desk:** papers overlap, pinned notes sit at the edges,
  a wax seal anchors a corner. Depth comes from stacked documents, not glass and
  blur.

## Borders & frames

- **Gold engraved filigree** for important frames — symmetrical, ornamented
  corners, blue gem accents at the cardinal points (per the title plate). Heroic
  but legible; never so busy it competes with content.
- **Torn / deckled parchment edges** for soft banners and minor headers.
- **Heraldic banners** (blue+gold civic, red military) as section markers and
  faction tags.
- **Pinned-note framing** — tape, pins, and curled corners — for tips, reminders,
  and flavor ("REMEMBER: ITEMIZE EVERYTHING").

## Windows

- Treat each window as a **document on the desk**: an open ledger (two-page
  spread), a clipboard (single form), or a tray (a stack). Opening/closing a
  window should feel like picking up or filing a document.
- One clear subject per window; generous margins; the page breathes (style-guide
  composition rules apply to UI too).

## Fonts (described, not specified)

- **Display / titles:** a heavy, carved, slightly fantastical serif with gold
  bevel and engraved depth — the "ASSET REPORT" treatment. Grand and official.
- **Body / ledger:** a clean, readable humanist or old-style serif that looks
  like it was set in a well-run print shop — quiet, legible, columnar.
- **Annotations / stamps:** a typewriter-ish or hand-stamped mono for form fields,
  ledger columns, and rubber-stamp words (**DENIED**, **APPROVED**, **PENDING**).
- Type should feel **printed, inked, or stamped onto paper** — never floating,
  glassy, or neon. (Note: per the style guide, **icon and illustration artwork
  carries no baked-in text**; lettering lives in the live UI layer.)

## Decorations

Wax seals, ribbons, ink blots, quills, abacus beads, coin stacks, pressed-leaf
laurels, heraldic pennants, brass clips, and stamp impressions. Use them as
accents and anchors — sparingly, to mark importance, never as wallpaper clutter.

## Interaction style

- **Buttons** feel like **official actions**: a stamp pressing paper, a wax seal
  set, a ledger line ticked, an engraved brass plate depressed. The primary CTA
  is literally "stamp it."
- **Confirmations** are stamps and seals: **APPROVED** / **DENIED** thud onto the
  form. **Notifications** are new forms landing in the IN tray, a seal pressing,
  a coin dropping into the treasury.
- **Resource bar:** a row of gold-rimmed [resource icons](Resources.md) with
  running counts — the realm's live balance sheet, always visible. Gold pieces
  (gp) read consistently with quest payouts and building costs.
- **Tooltips & menus** look **filed and indexed**: labeled tabs, ledger rows,
  catalog cards — the aesthetic of an impeccably organized civil service.
- **Badges** (wax seals, heraldic emblems) mark status, rank, and faction.

## Mood

**Warm, official, hand-made, lightly worn.** Authoritative but humane; ornate but
always legible. The UI should make doing paperwork feel *satisfying and important*
— the quiet pleasure of a stamp landing square and a ledger that balances.

## Things to avoid in UI

- Modern/corporate office UI (flat material design, fluorescent palettes,
  sticky-note skeuomorphism, cubicle clichés).
- Glassmorphism, neon glow, sci-fi HUDs, heavy drop-shadow blur.
- Clutter that buries the focal action — even a busy desk has one clear subject.
- Cold greys and pure black/white fields (style-guide limit); keep everything
  parchment-warm.
- Glowing UI chrome — only diegetic magic/faith elements emit light.

## Building-nameplate worklist

Placeholder. Reusable banner/plaque frame; the game renders the dynamic building
name + level on top of it.

<!-- worklist: ui -->
| Stable ID | Display name | Description/role | Art status | Target filename | raw_url |
| --- | --- | --- | --- | --- | --- |
| `ui-building-nameplate` | Building Nameplate | One reusable frame/plaque the game overlays each building's NAME + LEVEL onto — one art piece, not one per building; bakes no specific text | needed (placeholder) | `Assets/AssetReport/ui-building-nameplate.png` | |

Tags: `ui`, `nameplate`, `frame`. Stored under `Assets/AssetReport/` (an indexed
`ASSET_DIR`) so the placeholder gets a real `raw_url` when produced.
