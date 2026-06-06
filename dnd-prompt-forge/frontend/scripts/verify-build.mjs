import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const adsenseClient = 'ca-pub-9123849728110588';
const files = [
  'dist/index.html',
  'dist/pages/about.html',
  'dist/pages/contact.html',
  'dist/pages/privacy.html',
  'dist/pages/terms.html'
];

for (const file of files) {
  const absolute = path.join(root, file);
  const html = await readFile(absolute, 'utf8');
  const head = html.match(/<head\b[^>]*>([\s\S]*?)<\/head>/i)?.[1] ?? '';

  if (!head.includes(adsenseClient) || !head.includes('pagead2.googlesyndication.com')) {
    throw new Error(`AdSense script is missing from <head>: ${file}`);
  }
}

console.log(`Verified AdSense script in ${files.length} production HTML files.`);
