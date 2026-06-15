/* Prose / secondary pages: About, Privacy, Terms, Contact, 404 */

const About = () => (
  <div className="prose">
    <h1>About DND Prompt Forge</h1>
    <div className="updated">Independent tool · last updated June 2026</div>
    <p className="lede">DND Prompt Forge is a small, free utility that turns a character idea into a clean, copy-ready AI image prompt. It's built for dungeon masters and players who want good art prompts without wrestling with prompt syntax.</p>
    <h2>What it does</h2>
    <p>You describe a character, creature or scene — race, class, a line of flavor, a visual style — and the Forge assembles a structured prompt: a main prompt, a short version, and a negative prompt, plus style notes and usage tips. Pick a target model and it tunes the wording to match.</p>
    <h2>What it doesn't do</h2>
    <p>It doesn't generate images, store your characters, or require an account. Prompts are produced in your browser and meant to be pasted into an image model of your choice. Nothing you type is needed to use the tool, and there's no sign-up wall.</p>
    <h2>Why we built it</h2>
    <p>Good tabletop art starts with a good prompt. Most generators bury the useful part under marketing. The Forge keeps the working surface first: open the page, fill a short form, copy your prompt. That's the whole product.</p>
  </div>
);

const Privacy = () => (
  <div className="prose">
    <h1>Privacy</h1>
    <div className="updated">Last updated June 15, 2026</div>
    <p className="lede">DND Prompt Forge does not require an account. We process only the information needed to generate prompts, protect the service from abuse, receive optional feedback, and support the site with advertising.</p>
    <h2>Prompt information</h2>
    <p>When the online generator is available, the character, creature, or scene details you enter are sent to our server to create the requested text prompt. They may also be processed by the AI service configured to provide that result. If the online service is unavailable, the browser can generate a template-based result locally instead.</p>
    <h2>Technical information and cookies</h2>
    <p>The generator creates a signed, anonymous session cookie that lasts for up to 10 days. We also process technical information such as your IP address, browser characteristics, request identifiers, and service usage. These identifiers are used for security, request limits, troubleshooting, and service auditing; quota records store hashed identifiers rather than the original IP address.</p>
    <h2>Optional feedback</h2>
    <p>If you submit feedback after generating a prompt, we store the related request ID, your rating or selected reason, and any comment you choose to provide. We use this information to diagnose poor results and improve prompt-generation rules. Please do not include personal or confidential information in feedback comments.</p>
    <h2>Analytics</h2>
    <p>We do not currently use a separate website analytics service. Normal server logs and the technical records described above may still be used to maintain and secure the service.</p>
    <h2>Google advertising</h2>
    <p>Selected content pages may display ads served by Google AdSense. Google and its partners may use cookies, device identifiers, or similar technologies to deliver, measure, and personalize ads where permitted. Learn more about <a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener noreferrer">how Google uses information from sites that use its services</a>.</p>
    <h2>Your choices</h2>
    <p>You can use the site without creating an account. You may block or delete cookies through your browser, although blocking the anonymous session cookie can prevent online prompt generation from working correctly. Where required, Google may present consent controls for advertising. You can also manage personalized advertising through <a href="https://myadcenter.google.com/" target="_blank" rel="noopener noreferrer">My Ad Center</a>.</p>
    <h2>Children and sensitive information</h2>
    <p>This site is a general-audience creative tool and is not intended to collect personal information from children. Do not enter real names, contact details, health information, financial information, or other sensitive personal data into prompt or feedback fields.</p>
    <h2>Contact</h2>
    <p>For privacy questions or requests concerning information you submitted, email <a href="mailto:support@whatai.me">support@whatai.me</a>. We may need the relevant request ID or other details to locate a record.</p>
  </div>
);

const Terms = () => (
  <div className="prose">
    <h1>Terms of use</h1>
    <div className="updated">Last updated June 2026</div>
    <p className="lede">By using DND Prompt Forge you agree to these simple terms.</p>
    <h2>The tool</h2>
    <p>DND Prompt Forge generates text prompts only. It does not generate, host, or distribute images. The quality and content of any image you create elsewhere is your responsibility and subject to the terms of the image model you use.</p>
    <h2>Acceptable use</h2>
    <p>Don't use the tool to produce prompts that infringe intellectual property, impersonate real people, or create unlawful content. Avoid copyrighted character names and any claim of official artwork.</p>
    <h2>Trademarks</h2>
    <p>“D&D” and “Dungeons & Dragons” are trademarks of their respective owner. This site is independent and is not affiliated with, sponsored by, or endorsed by the trademark owner.</p>
    <h2>No warranty</h2>
    <p>The tool is provided “as is,” without warranties of any kind. Prompts are suggestions, not guarantees of any particular result.</p>
  </div>
);

const Contact = () => (
  <div className="prose">
    <h1>Contact</h1>
    <div className="updated">We usually reply within a couple of days.</div>
    <p className="lede">Feedback on the prompts, a bug, or a prompt type you wish existed? Drop us a line.</p>
    <div style={{ marginTop: 'var(--s5)' }}>
      <Button variant="primary" iconLeft="mail" onClick={() => window.location.href = 'mailto:support@whatai.me'}>
        support@whatai.me
      </Button>
    </div>
    <p style={{ marginTop: 'var(--s5)', color: 'var(--ink-3)', fontSize: 14 }}>
      For prompt feedback, you can also use the feedback button inside the generator after any result.
    </p>
  </div>
);

const NotFound = ({ onNav }) => (
  <div className="nf">
    <div className="d20">20</div>
    <h1>You rolled a natural 404</h1>
    <p>This page wandered off the map. The encounter you're looking for isn't here — but the prompt forge is still hot.</p>
    <Button variant="primary" iconLeft="arrow-left" onClick={() => onNav('home')}>Back to the generator</Button>
  </div>
);

Object.assign(window, { About, Privacy, Terms, Contact, NotFound });
