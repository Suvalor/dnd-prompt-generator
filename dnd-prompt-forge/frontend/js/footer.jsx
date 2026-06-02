/* Footer — crawlable internal links + legal */

const FOOTER_TOOLS = [
  { label: 'Character prompts', id: 'character' },
  { label: 'Token prompts', id: 'token' },
  { label: 'Monster prompts', id: 'monster' },
  { label: 'NPC prompts', id: 'npc' },
  { label: 'Scene prompts', id: 'scene' },
];
const FOOTER_GUIDES = [
  { label: 'Fantasy character prompts', href: '/fantasy-character-prompt-generator' },
  { label: 'Tiefling warlock', href: '/tiefling-warlock-prompt-generator' },
  { label: 'Elf ranger', href: '/elf-ranger-prompt-generator' },
  { label: 'Dragonborn paladin token', href: '/dragonborn-paladin-token-prompt' },
  { label: 'Haunted tavern scene', href: '/dnd-tavern-scene-prompt' },
];
const FOOTER_COMPANY = [
  { label: 'About', id: 'about' },
  { label: 'Contact', id: 'contact' },
  { label: 'Privacy', id: 'privacy' },
  { label: 'Terms', id: 'terms' },
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
        <h4>Examples</h4>
        <ul>{FOOTER_GUIDES.map(t => <li key={t.href}><a href={t.href} onClick={e => e.preventDefault()}>{t.label}</a></li>)}</ul>
      </div>
      <div className="fcol">
        <h4>Site</h4>
        <ul>{FOOTER_COMPANY.map(t => <li key={t.id}><a onClick={() => onNav(t.id)}>{t.label}</a></li>)}</ul>
      </div>
    </div>
    <div className="legal">
      <span>© 2026 DND Prompt Forge. Prompts are generated text, not images.</span>
      <span>Not affiliated with or endorsed by the owners of the D&D trademark.</span>
    </div>
  </footer>
);

Object.assign(window, { Footer });
