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
    <div className="updated">Last updated June 2026</div>
    <p className="lede">The short version: the prompt generator runs in your browser, and we keep data collection to a minimum.</p>
    <h2>What we collect</h2>
    <p>The character details you type are used to build your prompt and are not required to be saved. We use basic, privacy-respecting analytics to understand which prompt types are popular so we can improve them.</p>
    <h2>Advertising</h2>
    <p>This site may display ads from third-party networks to keep the tool free. Ad partners may use cookies to serve relevant ads. Ads are always clearly labeled and kept separate from the tool and its output.</p>
    <h2>Your choices</h2>
    <p>You can use the generator without providing any personal information. Browser cookies can be cleared or blocked at any time through your browser settings.</p>
    <h2>Contact</h2>
    <p>Questions about privacy? Reach us through the <a onClick={() => window.__navigate && window.__navigate('contact')}>contact page</a>.</p>
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
      <Button variant="primary" iconLeft="mail" onClick={() => window.location.href = 'mailto:support@dnd.whatai.me'}>
        support@dnd.whatai.me
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
