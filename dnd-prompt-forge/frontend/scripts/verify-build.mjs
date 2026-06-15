/** 构建验证脚本：检查 AdSense 脚本 + 指南页面结构完整性 */
import { access, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const adsenseClient = 'ca-pub-9123849728110588';

/** 必须包含 AdSense 脚本的页面 */
const adsenseRequired = [
  'dist/index.html',
  'dist/pages/character-portrait-guide.html',
  'dist/pages/full-body-guide.html',
  'dist/pages/token-guide.html',
  'dist/pages/monster-guide.html',
  'dist/pages/npc-guide.html',
  'dist/pages/scene-guide.html',
];

/** 禁止包含 AdSense 脚本的页面 */
const adsenseForbidden = [
  'dist/pages/about.html',
  'dist/pages/contact.html',
  'dist/pages/privacy.html',
  'dist/pages/terms.html',
];

/** 指南页面及其对应的 clean URL 路径 */
const guidePages = [
  { file: 'dist/pages/character-portrait-guide.html', canonicalPath: '/character-portrait-guide' },
  { file: 'dist/pages/full-body-guide.html', canonicalPath: '/full-body-guide' },
  { file: 'dist/pages/token-guide.html', canonicalPath: '/token-guide' },
  { file: 'dist/pages/monster-guide.html', canonicalPath: '/monster-guide' },
  { file: 'dist/pages/npc-guide.html', canonicalPath: '/npc-guide' },
  { file: 'dist/pages/scene-guide.html', canonicalPath: '/scene-guide' },
];

/** 读取文件全文 */
async function readFull(file) {
  const absolute = path.join(root, file);
  return readFile(absolute, 'utf8');
}

/** 提取 HTML 文件的 <head> 内容 */
async function getHead(file) {
  const html = await readFull(file);
  return html.match(/<head\b[^>]*>([\s\S]*?)<\/head>/i)?.[1] ?? '';
}

/** 检查 <head> 中是否包含 AdSense 脚本 */
function hasAdSense(head) {
  return head.includes(adsenseClient) && head.includes('pagead2.googlesyndication.com');
}

// ---- 验证 1: AdSense 存在/缺失 ----
for (const file of adsenseRequired) {
  const head = await getHead(file);
  if (!hasAdSense(head)) {
    throw new Error(`AdSense script is missing from <head>: ${file}`);
  }
}

for (const file of adsenseForbidden) {
  const head = await getHead(file);
  if (hasAdSense(head)) {
    throw new Error(`AdSense script should NOT be present in <head>: ${file}`);
  }
}

console.log(`Verified AdSense in ${adsenseRequired.length} required files, absent from ${adsenseForbidden.length} forbidden files.`);

// ---- 验证 2: 指南页面结构完整性 ----
const MIN_H2_COUNT = 7;

for (const { file, canonicalPath } of guidePages) {
  const html = await readFull(file);
  const head = html.match(/<head\b[^>]*>([\s\S]*?)<\/head>/i)?.[1] ?? '';
  const errors = [];

  // 2a: <link rel="canonical"> 包含正确的 clean URL
  const canonicalMatch = head.match(/<link\s+rel="canonical"\s+href="([^"]+)"/i);
  if (!canonicalMatch) {
    errors.push('Missing <link rel="canonical">');
  } else if (!canonicalMatch[1].endsWith(canonicalPath)) {
    errors.push(`Canonical href "${canonicalMatch[1]}" does not end with "${canonicalPath}"`);
  }

  // 2b: og:type 为 article
  const ogTypeMatch = head.match(/<meta\s+property="og:type"\s+content="([^"]+)"/i);
  if (!ogTypeMatch) {
    errors.push('Missing og:type meta tag');
  } else if (ogTypeMatch[1] !== 'article') {
    errors.push(`og:type is "${ogTypeMatch[1]}", expected "article"`);
  }

  // 2c: JSON-LD @type 为 Article
  const ldJsonMatch = html.match(/<script\s+type="application\/ld\+json">([\s\S]*?)<\/script>/i);
  if (!ldJsonMatch) {
    errors.push('Missing JSON-LD script block');
  } else {
    try {
      const ldObj = JSON.parse(ldJsonMatch[1]);
      if (ldObj['@type'] !== 'Article') {
        errors.push(`JSON-LD @type is "${ldObj['@type']}", expected "Article"`);
      }
    } catch {
      errors.push('JSON-LD is not valid JSON');
    }
  }

  // 2d: 至少有 MIN_H2_COUNT 个 <h2> 标签
  const h2Count = (html.match(/<h2>/g) || []).length;
  if (h2Count < MIN_H2_COUNT) {
    errors.push(`Found ${h2Count} <h2> tags, expected at least ${MIN_H2_COUNT}`);
  }

  // 2e: 存在 CTA 链接（href="/"）
  if (!html.includes('href="/"') && !html.includes('href="/?type=')) {
    errors.push('Missing CTA link (href="/" or href="/?type=...")');
  }

  // 2f: 存在 Related guides 链接
  if (!html.includes('guide-related')) {
    errors.push('Missing related guides section (class "guide-related")');
  }

  if (errors.length > 0) {
    throw new Error(`Guide page structure check failed for ${file}:\n  - ${errors.join('\n  - ')}`);
  }
}

console.log(`Verified structure for ${guidePages.length} guide pages (canonical, og:type, JSON-LD, h2>=${MIN_H2_COUNT}, CTA, related guides).`);

// ---- 验证 3: 静态页面依赖的共享样式已发布 ----
await access(path.join(root, 'dist/css/style.css'));
for (const { file } of guidePages) {
  const html = await readFull(file);
  if (!html.includes('href="../css/style.css"')) {
    throw new Error(`Static stylesheet reference is missing from ${file}`);
  }
}
console.log('Verified shared static stylesheet is published for guide and prose pages.');
