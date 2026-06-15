#!/usr/bin/env node
/**
 * Business Acceptance Test — Sprint 1 + Sprint 2
 * Covers all 22 verification items from the acceptance criteria.
 * Runs as a pure static-file check (no Docker needed).
 */

import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const PAGES = join(ROOT, 'pages');
const DIST_PAGES = join(ROOT, 'dist', 'pages');
const JS = join(ROOT, 'js');

let passed = 0;
let failed = 0;
const failures = [];

function assert(condition, id, description) {
  if (condition) {
    console.log(`  PASS [${id}] ${description}`);
    passed++;
  } else {
    console.log(`  FAIL [${id}] ${description}`);
    failures.push({ id, description });
    failed++;
  }
}

function read(relPath) {
  const abs = join(ROOT, relPath);
  if (!existsSync(abs)) return null;
  return readFileSync(abs, 'utf-8');
}

function readAbs(absPath) {
  if (!existsSync(absPath)) return null;
  return readFileSync(absPath, 'utf-8');
}

// ─── SPRINT 1 ────────────────────────────────────────────────────────
console.log('\n=== SPRINT 1: AdSense Removal + Contact Fix ===\n');

// #1 about.html no AdSense
const about = read('pages/about.html');
assert(about !== null, 'S1-1', 'about.html exists');
assert(about && !about.includes('pagead2.googlesyndication.com'), 'S1-1', 'about.html has NO AdSense');

// #2 contact.html no AdSense
const contact = read('pages/contact.html');
assert(contact !== null, 'S1-2', 'contact.html exists');
assert(contact && !contact.includes('pagead2.googlesyndication.com'), 'S1-2', 'contact.html has NO AdSense');

// #3 privacy.html no AdSense
const privacy = read('pages/privacy.html');
assert(privacy !== null, 'S1-3', 'privacy.html exists');
assert(privacy && !privacy.includes('pagead2.googlesyndication.com'), 'S1-3', 'privacy.html has NO AdSense');

// #4 terms.html no AdSense
const terms = read('pages/terms.html');
assert(terms !== null, 'S1-4', 'terms.html exists');
assert(terms && !terms.includes('pagead2.googlesyndication.com'), 'S1-4', 'terms.html has NO AdSense');

// #5 index.html HAS AdSense
const indexHtml = read('index.html');
assert(indexHtml !== null, 'S1-5', 'index.html exists');
assert(indexHtml && indexHtml.includes('pagead2.googlesyndication.com'), 'S1-5', 'index.html HAS AdSense');
const excelTool = read('pages/excel-ratio-converter.html');
assert(
  excelTool && !excelTool.includes('pagead2.googlesyndication.com'),
  'S1-5',
  'excel-ratio-converter.html has NO AdSense'
);

// #6 contact.html no <form>
assert(contact && !contact.includes('<form'), 'S1-6', 'contact.html has NO <form> element');

// #7 contact.html has email
assert(contact && contact.includes('support@whatai.me'), 'S1-7', 'contact.html has support@whatai.me');

// #8 React Contact no form state (no useState/useToast)
const prosePages = read('js/prose-pages.jsx');
assert(prosePages !== null, 'S1-8', 'prose-pages.jsx exists');
const contactComponent = prosePages
  ? prosePages.match(/const Contact[\s\S]*?^const /m)?.[0] || prosePages.slice(prosePages.indexOf('const Contact'))
  : '';
assert(
  contactComponent && !contactComponent.includes('useState') && !contactComponent.includes('useToast'),
  'S1-8',
  'Contact component has NO useState/useToast'
);

// ─── SPRINT 2 ────────────────────────────────────────────────────────
console.log('\n=== SPRINT 2: Guide Pages + Sitemap + Nginx + Nav ===\n');

const GUIDE_SLUGS = ['character-portrait-guide', 'full-body-guide', 'token-guide', 'monster-guide', 'npc-guide', 'scene-guide'];

// #10 Guide pages exist
for (const slug of GUIDE_SLUGS) {
  const html = read(`pages/${slug}.html`);
  assert(html !== null, 'S2-10', `${slug}.html exists`);
}

// #11 Guide pages have no AdSense; advertising is homepage-only
for (const slug of GUIDE_SLUGS) {
  const html = read(`pages/${slug}.html`);
  assert(html && !html.includes('pagead2.googlesyndication.com'), 'S2-11', `${slug} has NO AdSense`);
}

// #12 Guide pages have canonical
for (const slug of GUIDE_SLUGS) {
  const html = read(`pages/${slug}.html`);
  const hasCanonical = html && html.includes('rel="canonical"');
  assert(hasCanonical, 'S2-12', `${slug} has canonical link`);
}

// #13 Guide pages have Article JSON-LD
for (const slug of GUIDE_SLUGS) {
  const html = read(`pages/${slug}.html`);
  assert(html && html.includes('"@type": "Article"'), 'S2-13', `${slug} has Article JSON-LD`);
}

// #14 Guide pages have 7+ h2
for (const slug of GUIDE_SLUGS) {
  const html = read(`pages/${slug}.html`);
  const h2Count = html ? (html.match(/<h2/g) || []).length : 0;
  assert(h2Count >= 7, 'S2-14', `${slug} has ${h2Count} h2 tags (need >= 7)`);
}

// #15 Guide pages have CTA linking to /
for (const slug of GUIDE_SLUGS) {
  const html = read(`pages/${slug}.html`);
  const hasCTA = html && (html.includes('href="/"') || html.includes("href='/'"));
  assert(hasCTA, 'S2-15', `${slug} has CTA link to /`);
}

// #16 Guide pages have related guides
for (const slug of GUIDE_SLUGS) {
  const html = read(`pages/${slug}.html`);
  // Check that the page links to at least one OTHER guide
  const otherGuides = GUIDE_SLUGS.filter(s => s !== slug);
  const hasRelated = html && otherGuides.some(og => html.includes(`/${og}`));
  assert(hasRelated, 'S2-16', `${slug} has related guide links`);
}

// #17 Sitemap has 12 URLs
const sitemap = read('sitemap.xml');
const locCount = sitemap ? (sitemap.match(/<loc>/g) || []).length : 0;
assert(locCount === 12, 'S2-17', `Sitemap has ${locCount} <loc> entries (need 12)`);

// #18 Sitemap has lastmod
const lastmodCount = sitemap ? (sitemap.match(/<lastmod>/g) || []).length : 0;
assert(lastmodCount === locCount, 'S2-18', `Sitemap has ${lastmodCount} <lastmod> entries (matching ${locCount} URLs)`);

// #19 Nginx routing — check docker-compose references nginx
const dockerCompose = readAbs(join(ROOT, '..', 'docker-compose.yml')) || readAbs(join(ROOT, 'docker-compose.yml'));
if (dockerCompose) {
  const hasNginx = dockerCompose.includes('nginx');
  assert(hasNginx, 'S2-19', 'docker-compose.yml references nginx service');
} else {
  const possibleNginxPaths = [
    join(ROOT, '..', 'nginx', 'default.conf'),
    join(ROOT, '..', 'nginx', 'nginx.conf'),
    join(ROOT, '..', 'nginx.conf'),
    join(ROOT, 'Dockerfile'),
  ];
  let nginxContent = null;
  for (const p of possibleNginxPaths) {
    if (existsSync(p)) {
      nginxContent = readAbs(p);
      break;
    }
  }
  assert(nginxContent !== null, 'S2-19', 'Nginx config or Dockerfile exists for routing');
}

// #20 GuideCards have aria-label
const contentSections = read('js/content-sections.jsx');
assert(contentSections !== null, 'S2-20', 'content-sections.jsx exists');
// The template uses aria-label={g.ariaLabel} — verify:
// 1. The template renders aria-label attribute
// 2. Each GUIDE_PAGES entry has an ariaLabel property
const guideCardsSection = contentSections
  ? contentSections.slice(contentSections.indexOf('GUIDE_PAGES'))
  : '';
assert(
  guideCardsSection && guideCardsSection.includes('aria-label'),
  'S2-20',
  'GuideCards template renders aria-label attribute'
);
// Count data-driven ariaLabel properties in GUIDE_PAGES array
const ariaLabelDataCount = guideCardsSection ? (guideCardsSection.match(/ariaLabel:/g) || []).length : 0;
assert(ariaLabelDataCount >= 6, 'S2-20', `GUIDE_PAGES data has ${ariaLabelDataCount} ariaLabel properties (need >= 6)`);

// #21 Footer has FOOTER_GUIDES
const footer = read('js/footer.jsx');
assert(footer !== null, 'S2-21', 'footer.jsx exists');
assert(footer && footer.includes('FOOTER_GUIDES'), 'S2-21', 'footer.jsx contains FOOTER_GUIDES');
// Verify the Guides column is rendered
assert(footer && footer.includes('>Guides<'), 'S2-21', 'Footer renders Guides column heading');
assert(
  footer && footer.includes("id: 'fullbody'") && contentSections.includes("href: '/full-body-guide'"),
  'S2-21',
  'Full-body generator and guide links are present'
);

// #22 Footer Excel uses clean URL — JSX may use single or double quotes
assert(
  footer && (footer.includes('"/excel-ratio-converter"') || footer.includes("'/excel-ratio-converter'")),
  'S2-22',
  'Footer Excel link uses clean URL /excel-ratio-converter'
);

// ─── BUILD VERIFICATION ──────────────────────────────────────────────
console.log('\n=== BUILD VERIFICATION ===\n');
// Check dist directory exists and mirrors pages
const distPages = existsSync(DIST_PAGES);
assert(distPages, 'BUILD', 'dist/pages/ directory exists');
if (distPages) {
  const distIndex = existsSync(join(ROOT, 'dist', 'index.html'));
  assert(distIndex, 'BUILD', 'dist/index.html exists');
  const distSitemap = existsSync(join(ROOT, 'dist', 'sitemap.xml'));
  assert(distSitemap, 'BUILD', 'dist/sitemap.xml exists');
  const distStaticCss = existsSync(join(ROOT, 'dist', 'css', 'style.css'));
  assert(distStaticCss, 'BUILD', 'dist/css/style.css exists');
  for (const slug of GUIDE_SLUGS) {
    assert(existsSync(join(DIST_PAGES, `${slug}.html`)), 'BUILD', `dist/pages/${slug}.html exists`);
  }
}

// ─── SUMMARY ─────────────────────────────────────────────────────────
console.log('\n=== TEST SUMMARY ===\n');
console.log(`  Total: ${passed + failed} | Passed: ${passed} | Failed: ${failed}`);

if (failures.length > 0) {
  console.log('\n  Failed items:');
  for (const f of failures) {
    console.log(`    [${f.id}] ${f.description}`);
  }
}

process.exit(failed > 0 ? 1 : 0);
