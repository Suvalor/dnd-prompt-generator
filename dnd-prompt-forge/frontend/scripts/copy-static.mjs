import { cp, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const dist = path.join(root, 'dist');

const staticEntries = [
  'assets',
  'css',
  'pages',
  'manifest.json',
  'robots.txt',
  'sitemap.xml'
];

await mkdir(dist, { recursive: true });

for (const entry of staticEntries) {
  await cp(path.join(root, entry), path.join(dist, entry), {
    recursive: true,
    force: true,
    errorOnExist: false
  });
}
