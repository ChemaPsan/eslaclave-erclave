// Verify the bytes served by Hosting against the immutable candidate artifact.
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

async function verifyHosting(artifact, expectedSha, fetchFile = fetch) {
  if (!/^[0-9a-f]{40}$/.test(expectedSha || "")) throw new Error("Expected immutable release SHA.");
  const manifest = JSON.parse(fs.readFileSync(path.join(artifact, "release-manifest.json"), "utf8"));
  if (manifest.environment !== "qa" || manifest.sourceSha !== expectedSha) throw new Error("Candidate SHA mismatch.");
  const lines = fs.readFileSync(path.join(artifact, "SHA256SUMS"), "utf8").trim().split(/\r?\n/);
  const entries = lines.map((line) => {
    const match = /^([0-9a-f]{64})  (?:\.\/)?(.+)$/.exec(line);
    if (!match) throw new Error("Invalid artifact hash manifest.");
    const relative = match[2];
    if (relative.startsWith("/") || relative.includes("\\") || relative.split("/").some((p) => p === ".." || p === ".")) {
      throw new Error("Artifact paths must remain inside the QA release.");
    }
    return { digest: match[1], relative };
  });
  const names = new Set(entries.map((entry) => entry.relative));
  if (names.size !== entries.length || !["index.html", "env.js", "backoffice/env.js", "release-manifest.json"].every((name) => names.has(name))) {
    throw new Error("Incomplete or duplicate artifact hash manifest.");
  }
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(4, entries.length) }, async () => {
    while (next < entries.length) {
      const entry = entries[next++];
      const url = "https://erclave.web.app/" + entry.relative.split("/").map(encodeURIComponent).join("/");
      let valid = false;
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const response = await fetchFile(url, { headers: { "Cache-Control": "no-cache" }, redirect: "error", signal: AbortSignal.timeout(20000) });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          const digest = crypto.createHash("sha256").update(Buffer.from(await response.arrayBuffer())).digest("hex");
          if (digest === entry.digest) { valid = true; break; }
        } catch { /* Retry transient CDN/network failures without storing responses. */ }
      }
      if (!valid) throw new Error(`Hosting does not serve the approved artifact: ${entry.relative}`);
    }
  }));
  return entries.length;
}

module.exports = { verifyHosting };
if (require.main === module) {
  verifyHosting(path.resolve(process.argv[2] || "dist/qa-frontend"), process.env.RELEASE_SHA)
    .then((count) => console.log(`[OK] Hosting serves ${count} files with the approved candidate hashes.`))
    .catch((error) => { console.error(error.message); process.exitCode = 1; });
}
