import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { validateBytes } from "gltf-validator";

const input = process.argv[2];
if (!input) {
  console.error("Uso: npm run validate:glb -- <ruta-al-modelo.glb>");
  process.exit(2);
}

const path = resolve(input);
const report = await validateBytes(new Uint8Array(await readFile(path)), { uri: path });
const result = {
  file: path,
  errors: report.issues.numErrors,
  warnings: report.issues.numWarnings,
  infos: report.issues.numInfos,
  messages: report.issues.messages,
};
console.log(JSON.stringify(result, null, 2));
if (result.errors || result.warnings) process.exit(1);
