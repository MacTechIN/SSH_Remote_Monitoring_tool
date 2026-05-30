#!/usr/bin/env node
/**
 * Figma Variables JSON export → tokens.json / tokens.css 갱신 (스켈레톤).
 *
 * Usage (구현 완료 후):
 *   node scripts/sync-tokens-from-figma.mjs ./figma/export/variables.json
 *
 * 입력 형식은 팀 Figma 플러그인(Variables export)에 맞게 확장.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const mapPath = join(root, "src/design-tokens/figma-map.json");

const input = process.argv[2];
if (!input) {
  console.error("Usage: node scripts/sync-tokens-from-figma.mjs <figma-variables.json>");
  process.exit(1);
}

const figmaExport = JSON.parse(readFileSync(input, "utf8"));
const map = JSON.parse(readFileSync(mapPath, "utf8"));

console.log(
  `[tokens:sync] Loaded ${map.mappings?.length ?? 0} mappings; figma keys: ${Object.keys(figmaExport).length}`,
);
console.log("[tokens:sync] TODO: merge into tokens.json and regenerate tokens.css");

// Placeholder: implement merge using map.mappings[].figma → tokenPath
writeFileSync(
  join(root, "src/design-tokens/.sync-last-run.json"),
  JSON.stringify({ at: new Date().toISOString(), input }, null, 2),
);
