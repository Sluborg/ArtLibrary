#!/usr/bin/env node
// Build a fully self-contained ArtLibrary viewer that loads with zero network.
//
// Some WebViews (notably Android, when a raw viewer is uploaded to claude.ai as
// an artifact) block the redirect to the live GitHub Pages URL with
// ERR_BLOCKED_BY_CSP. The fix is to ship the data inline: this script takes
// docs/index.html and replaces the JSON between the marker pairs
//
//     var EMBEDDED_MANIFEST = /*@@MANIFEST@@*/null/*@@END@@*/;
//     var EMBEDDED_NEEDS    = /*@@NEEDS@@*/null/*@@END@@*/;
//
// with the real manifest / needs data, writing dist/ArtLibrary-standalone.html.
// Only the bytes strictly between each marker pair are touched; nothing else in
// the source is modified.
//
// Data sources (local is preferred over network for each):
//   manifest : ./asset-index.json          else MANIFEST_URL
//   needs    : ../game/art-needs.json       else NEEDS_URL
// No runtime dependencies, no analytics, no service worker.

import { readFile, writeFile, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "..");

const MANIFEST_URL = "https://raw.githubusercontent.com/Sluborg/ArtLibrary/main/asset-index.json";
const NEEDS_URL    = "https://raw.githubusercontent.com/Sluborg/game/dev/art-needs.json";

const SRC_HTML  = resolve(repoRoot, "docs/index.html");
const OUT_DIR   = resolve(repoRoot, "dist");
const OUT_HTML  = resolve(OUT_DIR, "ArtLibrary-standalone.html");

// Local-first candidates for each source.
const LOCAL_MANIFEST = resolve(repoRoot, "asset-index.json");
const LOCAL_NEEDS    = resolve(repoRoot, "../game/art-needs.json");

async function loadJson({ label, localPath, url }) {
  if (existsSync(localPath)) {
    const text = await readFile(localPath, "utf8");
    const data = JSON.parse(text);
    console.log(`  ${label}: local ${localPath}`);
    return data;
  }
  console.log(`  ${label}: fetching ${url}`);
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`${label}: HTTP ${res.status} fetching ${url}`);
  const data = await res.json();
  return data;
}

// Replace exactly the bytes between /*@@NAME@@*/ and the next /*@@END@@*/.
// The markers themselves are preserved, so the output can be rebuilt idempotently.
function replaceBlock(html, name, replacement) {
  const open  = `/*@@${name}@@*/`;
  const close = `/*@@END@@*/`;
  const start = html.indexOf(open);
  if (start === -1) throw new Error(`marker ${open} not found in ${SRC_HTML}`);
  const from = start + open.length;
  const end  = html.indexOf(close, from);
  if (end === -1) throw new Error(`closing marker ${close} for ${open} not found`);
  return html.slice(0, from) + replacement + html.slice(end);
}

function assetCount(manifest) {
  if (Array.isArray(manifest?.assets)) return manifest.assets.length;
  if (typeof manifest?.asset_count === "number") return manifest.asset_count;
  return 0;
}

function needsCount(needs) {
  if (Array.isArray(needs)) return needs.length;
  if (Array.isArray(needs?.needs)) return needs.needs.length;
  return 0;
}

async function main() {
  console.log("Loading data sources (local preferred)…");
  const manifest = await loadJson({ label: "manifest", localPath: LOCAL_MANIFEST, url: MANIFEST_URL });
  const needs    = await loadJson({ label: "needs",    localPath: LOCAL_NEEDS,    url: NEEDS_URL });

  const html = await readFile(SRC_HTML, "utf8");

  // JSON.stringify produces a valid JavaScript expression. Guard against the
  // one sequence that could prematurely close the <script> element.
  const manifestJson = JSON.stringify(manifest).replace(/<\/script/gi, "<\\/script");
  const needsJson    = JSON.stringify(needs).replace(/<\/script/gi, "<\\/script");

  let out = html;
  out = replaceBlock(out, "MANIFEST", manifestJson);
  out = replaceBlock(out, "NEEDS", needsJson);

  await mkdir(OUT_DIR, { recursive: true });
  await writeFile(OUT_HTML, out, "utf8");

  const bytes = Buffer.byteLength(out, "utf8");
  console.log("\nBuilt standalone viewer:");
  console.log(`  path          : ${OUT_HTML}`);
  console.log(`  size          : ${bytes} bytes`);
  console.log(`  assets        : ${assetCount(manifest)}`);
  console.log(`  needs         : ${needsCount(needs)}`);
}

main().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
