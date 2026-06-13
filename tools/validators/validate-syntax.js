const { spawnSync } = require("child_process");
const { fail, listFiles, ok } = require("./shared");

const jsFiles = [
  ...listFiles("frontend", (file) => file.endsWith(".js")),
  ...listFiles("tools", (file) => file.endsWith(".js"))
];

const errors = [];

for (const file of jsFiles) {
  const result = spawnSync(process.execPath, ["--check", file], { encoding: "utf8" });
  if (result.status !== 0) {
    errors.push(`${file}\n${result.stderr || result.stdout}`.trim());
  }
}

if (errors.length) {
  fail("JavaScript syntax validation failed", errors);
} else {
  ok(`JavaScript syntax is valid in ${jsFiles.length} files.`);
}
