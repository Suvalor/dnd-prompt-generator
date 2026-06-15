/* Content sections */

const SectionHead = ({ kicker, title, children }) => (
  <div className="section-head">
    {kicker && <div className="kicker">{kicker}</div>}
    <h2>{title}</h2>
    {children && <p>{children}</p>}
  </div>
);

/* --- Examples gallery --- */
const useExample = (fill) => {
  if (window.__forgeLoadExample) window.__forgeLoadExample(fill);
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

const Examples = () => {
  const ex = window.FORGE.examples;
  return (
    <div className="band alt">
      <div className="wrap section">
        <SectionHead kicker="See it in action" title="Example prompts">
          Real output from the generator — load any one into the form and tweak it for your table.
        </SectionHead>
        <div className="grid c3">
          {ex.map((e, i) => (
            <React.Fragment key={e.id}>
              <article className="ex-card">
                <span className="ex-badge">{e.badge}</span>
                <h3>{e.name}</h3>
                <div className="ex-excerpt">{e.excerpt}</div>
                <div className="ex-foot">
                  <Button variant="secondary" size="sm" iconLeft="wand-2" onClick={() => useExample(e.fill)}>Use this example</Button>
                </div>
              </article>
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

/* --- Prompt type guide --- */
const GUIDE = [
  { icon: 'user', title: 'Portrait', body: 'Face, costume, lighting and personality. Best for character avatars and headshots where expression carries the image.' },
  { icon: 'person-standing', title: 'Full body', body: 'Silhouette, armor, pose and weapon. Use when the whole getup matters — class fantasy and party line-ups.' },
  { icon: 'circle-dot', title: 'Token', body: 'Top-down view, centered figure, readable outline. Built for virtual tabletops — clean edges and 1:1 framing.' },
  { icon: 'users', title: 'NPC', body: 'Role, attitude and a memorable trait. Quick, in-world faces for the merchants, guards and patrons your party meets.' },
  { icon: 'skull', title: 'Monster', body: 'Anatomy, threat, scale and environment. Adds a size cue so the creature reads as dangerous at a glance.' },
  { icon: 'mountain', title: 'Scene', body: 'Place, mood, lighting and an encounter hook. Establishing shots for locations and set-pieces, no central hero needed.' },
];
const PromptGuide = () => (
  <div className="wrap section">
    <SectionHead kicker="One tool, six outputs" title="Portraits, tokens, NPCs, monsters and scenes">
      Each prompt type changes the composition rules the generator writes for you.
    </SectionHead>
    <div className="grid c3">
      {GUIDE.map(g => (
        <div className="guide-card" key={g.title}>
          <div className="gi"><Icon name={g.icon} size={18} /></div>
          <h3>{g.title}</h3>
          <p>{g.body}</p>
        </div>
      ))}
    </div>
  </div>
);

/* --- How it works --- */
const STEPS = [
  { n: 1, title: 'Choose the prompt type', body: 'Portrait, full body, token, NPC, monster or scene — this sets the composition.' },
  { n: 2, title: 'Add your DND details', body: 'Race, class, a line of description, and a visual style. Open Advanced for armor, weapon and more.' },
  { n: 3, title: 'Copy into your image tool', body: 'Grab the main prompt and negative prompt, paste them into Midjourney, ChatGPT or any model.' },
];
const HowItWorks = () => (
  <div className="band alt">
    <div className="wrap section">
      <SectionHead kicker="Three steps" title="How the DND prompt generator works" />
      <div className="grid c3">
        {STEPS.map(s => (
          <div className="step-card" key={s.n}>
            <div className="sn">{s.n}</div>
            <div><h3>{s.title}</h3><p>{s.body}</p></div>
          </div>
        ))}
      </div>
      <div className="banner ok" style={{ marginTop: 'var(--s6)', marginBottom: 0, maxWidth: 620 }}>
        <Icon name="message-square" size={17} />
        <div>If a result isn’t useful, your feedback helps adjust the rules future prompts are built from.</div>
      </div>
    </div>
  </div>
);

/* --- Limitations --- */
const LIMITS = [
  'This tool generates prompts — text you copy elsewhere. It does not create or host images.',
  'Final image quality depends on the third-party model you paste the prompt into.',
  'No login or account is required for the current version.',
  'Avoid using copyrighted character names or claims of official artwork in your prompts.',
  'D&D is a trademark of its respective owner — this site is independent and implies no affiliation.',
];
const Limitations = () => (
  <div className="wrap section">
    <SectionHead kicker="Good to know" title="Limitations & model compatibility" />
    <div className="limits">
      {LIMITS.map((l, i) => (
        <div className="limit" key={i}><Icon name="info" size={17} /><span>{l}</span></div>
      ))}
    </div>
  </div>
);

/* --- FAQ --- */
const FAQS = [
  { q: 'What is a DND character prompt generator?', a: 'It’s a free tool that takes your character details — race, class, style, gear — and writes a structured, copy-ready text prompt you can paste into an AI image model to create portraits, tokens, NPCs, monsters or scenes.' },
  { q: 'Does this tool generate images?', a: 'No. It produces prompt text only. You copy the prompt into an image model like Midjourney or ChatGPT, which does the actual image generation.' },
  { q: 'Can I use these prompts in Midjourney or ChatGPT?', a: 'Yes. Pick your target model in Advanced and the generator tunes the wording — for Midjourney it even adds an aspect-ratio flag. The prompts also work in Gemini, Leonardo, Stable Diffusion and general-purpose tools.' },
  { q: 'Can it create top-down VTT token prompts?', a: 'Yes. Choose the Token type and the generator writes a centered, top-down figure with a clean readable outline and 1:1 framing, plus token-specific export notes for your virtual tabletop.' },
  { q: 'Is the DND prompt generator free?', a: 'Yes, it’s completely free to use, with no usage caps for the prompt generator itself.' },
  { q: 'Do I need to log in?', a: 'No. There’s no login or account required — open the page, fill the form, and copy your prompt.' },
];
const FAQ = () => {
  const [open, setOpen] = React.useState(0);
  return (
    <div className="wrap section">
      <SectionHead kicker="Questions" title="DND prompt generator FAQ" />
      <div className="faq">
        {FAQS.map((f, i) => (
          <div className="faq-item" key={i}>
            <button className={`faq-q ${open === i ? 'open' : ''}`} aria-expanded={open === i}
              onClick={() => setOpen(open === i ? -1 : i)}>
              {f.q}<Icon name="chevron-down" size={20} className="chev" />
            </button>
            {open === i && <div className="faq-a">{f.a}</div>}
          </div>
        ))}
      </div>
    </div>
  );
};

/* --- Guide cards (link to guide pages) --- */
const GUIDE_PAGES = [
  { icon: 'user', title: 'Character portrait prompts', excerpt: 'When to use portraits, composition choices, before/after examples, and model-specific tips for DND character art.', href: '/character-portrait-guide', ariaLabel: 'Read the character portrait prompt guide' },
  { icon: 'person-standing', title: 'Full-body character prompts', excerpt: 'Readable poses, strong silhouettes, layered equipment, and framing that keeps the complete character in view.', href: '/full-body-guide', ariaLabel: 'Read the full-body character prompt guide' },
  { icon: 'circle-dot', title: 'VTT token prompts', excerpt: 'Top-down token composition, clean silhouettes, transparent backgrounds, and export settings for virtual tabletops.', href: '/token-guide', ariaLabel: 'Read the token prompt guide' },
  { icon: 'skull', title: 'Monster & creature prompts', excerpt: 'Scale cues, anatomy emphasis, threatening presence, and environment integration for DND monster art.', href: '/monster-guide', ariaLabel: 'Read the monster prompt guide' },
  { icon: 'users', title: 'NPC portrait prompts', excerpt: 'Role-defining traits, memorable details, approachable framing, and quick in-world NPC generation.', href: '/npc-guide', ariaLabel: 'Read the NPC prompt guide' },
  { icon: 'mountain', title: 'Fantasy scene prompts', excerpt: 'Establishing shots, depth layers, encounter hooks, and atmospheric lighting for DND location art.', href: '/scene-guide', ariaLabel: 'Read the scene prompt guide' },
];
const GuideCards = () => (
  <div className="band alt">
    <div className="wrap section">
      <SectionHead kicker="Learn the craft" title="DND prompt guides">
        Deep dives into each prompt type — when to use it, how to compose it, and what to watch out for.
      </SectionHead>
      <div className="grid c3">
        {GUIDE_PAGES.map(g => (
          <article className="guide-card" key={g.href}>
            <div className="gi"><Icon name={g.icon} size={18} /></div>
            <h3>{g.title}</h3>
            <p>{g.excerpt}</p>
            <a href={g.href} className="guide-link" aria-label={g.ariaLabel}>
              Read the guide <Icon name="arrow-right" size={14} />
            </a>
          </article>
        ))}
      </div>
    </div>
  </div>
);

Object.assign(window, { Examples, PromptGuide, GuideCards, HowItWorks, Limitations, FAQ });
