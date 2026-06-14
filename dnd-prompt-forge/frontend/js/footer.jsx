/* Footer — crawlable internal links + legal */

const FOOTER_TOOLS = [
  { label: 'Character prompts', id: 'character' },
  { label: 'Token prompts', id: 'token' },
  { label: 'Monster prompts', id: 'monster' },
  { label: 'NPC prompts', id: 'npc' },
  { label: 'Scene prompts', id: 'scene' },
];
const FOOTER_GUIDES = [
  { label: 'Character guide', href: '/character-portrait-guide' },
  { label: 'Token guide', href: '/token-guide' },
  { label: 'Monster guide', href: '/monster-guide' },
  { label: 'NPC guide', href: '/npc-guide' },
  { label: 'Scene guide', href: '/scene-guide' },
];
const FOOTER_COMPANY = [
  { label: 'About', id: 'about' },
  { label: 'Contact', id: 'contact' },
  { label: 'Privacy', id: 'privacy' },
  { label: 'Terms', id: 'terms' },
];
const FOOTER_EXTRA_TOOLS = [
  { label: 'Excel Ratio Converter', href: '/excel-ratio-converter' },
];

const Footer = ({ onNav }) => (
  <footer className="footer">
    <div className="footer-inner">
      <div className="fcol fbrand">
        <div className="name">DND Prompt <b>Forge</b></div>
        <p>A free tabletop utility that turns your character idea into copy-ready AI image prompts. Prompts only — no images generated, no login.</p>
      </div>
      <div className="fcol">
        <h4>Generators</h4>
        <ul>{FOOTER_TOOLS.map(t => <li key={t.id}><a onClick={() => onNav(t.id)}>{t.label}</a></li>)}</ul>
      </div>
      <div className="fcol">
        <h4>Guides</h4>
        <ul>{FOOTER_GUIDES.map(g => <li key={g.href}><a href={g.href}>{g.label}</a></li>)}</ul>
      </div>
      <div className="fcol">
        <h4>Site</h4>
        <ul>{FOOTER_COMPANY.map(t => <li key={t.id}><a onClick={() => onNav(t.id)}>{t.label}</a></li>)}</ul>
      </div>
      <div className="fcol">
        <h4>Extra tools</h4>
        <ul>{FOOTER_EXTRA_TOOLS.map(t => <li key={t.href}><a href={t.href}>{t.label}</a></li>)}</ul>
      </div>
    </div>
    <div className="legal">
      <span>&copy; 2026 DND Prompt Forge. Prompts are generated text, not images.</span>
      <span>Not affiliated with or endorsed by the owners of the D&D trademark.</span>
    </div>
  </footer>
);

Object.assign(window, { Footer });
