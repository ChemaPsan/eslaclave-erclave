const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..");

function fromRoot(...parts) {
  return path.join(repoRoot, ...parts);
}

function readText(relativePath) {
  return fs.readFileSync(fromRoot(relativePath), "utf8");
}

function listFiles(dir, predicate = () => true) {
  const root = fromRoot(dir);
  if (!fs.existsSync(root)) return [];
  const result = [];
  const stack = [root];

  while (stack.length) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === ".git" || entry.name === "node_modules") continue;
        stack.push(fullPath);
      } else if (predicate(fullPath)) {
        result.push(path.relative(repoRoot, fullPath));
      }
    }
  }

  return result.sort();
}

function ok(message) {
  console.log(`[OK] ${message}`);
}

function fail(title, errors) {
  console.error(`[FAIL] ${title}`);
  for (const error of errors) {
    console.error(`- ${error}`);
  }
  process.exitCode = 1;
}

function unique(values) {
  return [...new Set(values)];
}

module.exports = {
  fail,
  fromRoot,
  listFiles,
  ok,
  readText,
  repoRoot,
  unique
};
