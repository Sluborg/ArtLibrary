# Workflow

This is Lubot's production workflow for creating visuals. Follow it for every
request. It exists so that a fresh chat — with no prior conversation — can run
the full loop correctly from the first message.

> Before starting, load the selected style guide (the canonical one is
> [`StyleGuides/Fantasy-Strategy-v1.md`](StyleGuides/Fantasy-Strategy-v1.md))
> and search ArtLibrary for visuals that already satisfy the request. See
> [`Studio.md`](Studio.md) for Lubot's full responsibilities.

## The loop

```
Request
   ↓
Generate candidate visuals
   ↓
Human review
   ↓
Approve  /  Needs tweaks
   ↓
Regenerate only the requested visuals
   ↓
Upload approved visuals
   ↓
Verify upload
   ↓
Return GitHub URLs
```

## Step by step

1. **Request.** A human asks for one or more visuals. Restate the brief and the
   style guide being used so expectations are explicit.

2. **Generate candidate visuals.** Produce candidates that follow the loaded
   style guide. These are proposals — nothing is final yet.

3. **Human review.** Present every candidate to a human and wait for a decision.
   Generation is never the finish line.

4. **Approve / Needs tweaks.** The human approves visuals they're happy with and
   flags the rest as needing tweaks, with notes on what to change.

5. **Regenerate only the requested visuals.** Re-run generation **only** for the
   visuals that need tweaks. Never regenerate or alter visuals that were already
   approved. Return to step 3 with the new candidates until everything is
   approved.

6. **Upload approved visuals.** Upload only the approved visuals into ArtLibrary.
   Prefer the batch upload when there is more than one, so the whole set lands in
   one commit.

7. **Verify upload.** Confirm each approved visual actually landed — the file,
   the index, and the upload result must all agree.

8. **Return GitHub URLs.** Return the permanent GitHub URLs for the verified
   visuals. Those links are the deliverable.

## Rules

- **Never upload unapproved visuals.** Approval by a human is the only gate into
  the library. Candidates that were not approved are discarded, never uploaded.
- **Every approved visual becomes part of the permanent ArtLibrary.** Once
  uploaded, a visual is permanent, indexed, and reusable — it is part of the
  library's lasting visual memory.
- **Future generations should search ArtLibrary first.** Before creating
  anything similar, search the library. Reuse what already exists instead of
  generating near-duplicates; only create what is genuinely missing.
