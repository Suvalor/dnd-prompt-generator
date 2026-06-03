import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const entryDir = path.join(root, 'src');
const entryFile = path.join(entryDir, 'legacy-app.jsx');

const legacyFiles = [
  'js/prompt-engine.jsx',
  'js/tweaks-panel.jsx',
  'js/primitives.jsx',
  'js/header.jsx',
  'js/footer.jsx',
  'js/api-client.jsx',
  'js/generator.jsx',
  'js/content-sections.jsx',
  'js/prose-pages.jsx',
  'js/app.jsx'
];

const prelude = [
  "import React from 'react';",
  "import { createRoot } from 'react-dom/client';",
  "import * as lucide from 'lucide';",
  "import '../css/style.css';",
  '',
  'const ReactDOM = { createRoot };',
  'window.React = React;',
  'window.ReactDOM = ReactDOM;',
  'window.lucide = lucide;',
  ''
].join('\n');

const chunks = [];
for (const file of legacyFiles) {
  const absolute = path.join(root, file);
  const source = await readFile(absolute, 'utf8');
  chunks.push(`\n/* ---- ${file} ---- */\n${source}\n`);
}

await mkdir(entryDir, { recursive: true });
await writeFile(
  entryFile,
  `${prelude}${chunks.join('\n')}`,
  'utf8'
);

