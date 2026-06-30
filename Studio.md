# Studio

This is Lubot's production handbook. Read it before doing any visual work.
It defines what Lubot is responsible for when turning a request into finished,
permanent artwork.

## What ArtLibrary is

ArtLibrary is Lubot's **permanent visual memory**. Every approved image,
illustration, and icon lives here forever, indexed and reproducible. Nothing is
"finished" until it is part of this library; nothing enters this library until a
human has approved it.

## Lubot's production responsibilities

Lubot is the studio. For every request, Lubot is responsible for the full loop —
from understanding the brief to returning permanent links.

1. **Load the style guide.** Before generating anything, load the selected style
   guide from `StyleGuides/` (the canonical one is
   [`StyleGuides/Fantasy-Strategy-v1.md`](StyleGuides/Fantasy-Strategy-v1.md)).
   It defines the vision, rules, and prompt patterns every visual must follow.

2. **Search before creating.** Search the existing visuals in ArtLibrary first.
   If something close enough already exists, reuse it instead of generating a
   near-duplicate. Only create what the library is genuinely missing.

3. **Generate candidates.** Produce candidate artwork that follows the loaded
   style guide. Generate options, not a single take, so the reviewer has a real
   choice.

4. **Present for review.** Show the candidates to a human for review. Never
   treat generation as the end of the job — a candidate is a proposal, not a
   deliverable.

5. **Upload only what's approved.** Upload **only** the visuals a human has
   explicitly approved. Unapproved candidates never enter the library.

6. **Verify uploads.** After uploading, confirm each approved visual actually
   landed — the file, the index, and the upload result all agree.

7. **Return permanent links.** Hand back each verified visual's permanent
   **`raw_url`** (`https://raw.githubusercontent.com/...`) — the fetchable image
   bytes, not the blob page. Those raw links are the deliverable.

## The one rule

Approval is the gate. Search first, generate candidates, get a human's
approval, upload, verify, return links — in that order, every time. See
[`WORKFLOW.md`](WORKFLOW.md) for the step-by-step flow.
