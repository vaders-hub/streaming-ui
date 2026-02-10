const path = require("path");

const buildNextLintCommand = (filenames) => {
  const files = filenames
    .map((f) => path.relative(path.join(process.cwd(), "front"), f))
    .join(" --file ");
  return `pnpm --dir front exec next lint --fix --file ${files}`;
};

module.exports = {
  "server/**/*.py": [
    "uv run --project server ruff check --fix",
    "uv run --project server black",
  ],
  "front/**/*.{js,jsx,ts,tsx}": buildNextLintCommand,
};
