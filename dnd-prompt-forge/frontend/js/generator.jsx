/* Generator — form + output panel + states (empty/loading/success/error/feedback) */

const FORGE = window.FORGE;

const BLANK = {
  type: 'portrait', race: '', klass: '', desc: '',
  style: 'painterly', mood: 'brooding', model: 'midjourney',
  gender: '', age: '', alignment: '', armor: '', weapon: '', magic: '', palette: '', camera: '',
};

const FEEDBACK_REASONS = ['Too generic', 'Not DND-specific enough', 'Wrong style', 'Missing details', 'Too long', 'Too short', 'Other'];

/* ---------- Output sub-views ---------- */

const fullPromptText = (result) => [
  'Positive prompt:',
  result.main,
  '',
  'Negative prompt:',
  result.negative,
].join('\n');

const PromptBlock = ({ name, body, tone, prose, onCopy }) => (
  <div className={`pblock ${tone === 'neg' ? 'neg' : ''}`}>
    <div className="ph">
      <span className="pname"><span className="tick" />{name}</span>
      {!prose && <CopyButton text={body} onCopied={onCopy} />}
    </div>
    {prose
      ? <div className="pbody prose" dangerouslySetInnerHTML={{ __html: body }} />
      : <div className="pbody">{body}</div>}
  </div>
);

const EmptyState = ({ onLoad }) => (
  <div className="empty">
    <div className="out-head">
      <div>
        <div className="eg">Example output</div>
        <div className="eg-title">Tiefling Warlock Portrait</div>
      </div>
      <span className="pill muted">Preview</span>
    </div>
    <div className="eg-prompt">portrait of a tiefling warlock, deep crimson skin, curled obsidian horns, glowing violet eyes, eldritch pact tattoos, ornate dark-leather coat, painterly fantasy illustration, dramatic rim light…</div>
    <div className="eg-note"><Icon name="arrow-left" size={16} />Fill the form to generate your own copy-ready prompt.</div>
    <div className="out-actions">
      <Button variant="secondary" size="sm" iconLeft="wand-2" onClick={onLoad}>Load this example</Button>
    </div>
  </div>
);

const LoadingState = () => (
  <div aria-live="polite" aria-busy="true">
    <div className="out-head"><div className="sk" style={{ width: 200, height: 24 }} /><div className="sk" style={{ width: 84, height: 22, borderRadius: 999 }} /></div>
    {[0, 1, 2].map(i => (
      <div className="pblock" key={i}>
        <div className="sk sk-row" style={{ width: 110, height: 11, marginBottom: 9 }} />
        <div className="pbody" style={{ border: 0, background: 'transparent', padding: 0 }}>
          <div className="sk sk-row" style={{ width: '100%' }} />
          <div className="sk sk-row" style={{ width: '92%' }} />
          <div className="sk sk-row" style={{ width: i === 0 ? '78%' : '54%', marginBottom: 0 }} />
        </div>
      </div>
    ))}
  </div>
);

const ErrorState = ({ onRetry }) => (
  <div aria-live="assertive">
    <div className="banner err"><Icon name="alert-triangle" size={17} />
      <div><strong>Couldn’t reach the prompt service.</strong> Your inputs are saved — try again in a moment.</div>
    </div>
    <div className="out-actions">
      <Button variant="primary" size="sm" iconLeft="rotate-ccw" onClick={onRetry}>Try again</Button>
    </div>
  </div>
);

const Feedback = ({ phase, reasons, onToggleReason, comment, onComment, onSubmit }) => {
  if (phase === 'done') return (
    <div className="banner ok" style={{ marginTop: 'var(--s5)', marginBottom: 0 }}>
      <Icon name="check" size={17} /><div>Thanks. Future prompts will use this feedback.</div>
    </div>
  );
  return (
    <div style={{ marginTop: 'var(--s5)', paddingTop: 'var(--s5)', borderTop: '1px dashed var(--line)' }}>
      <div className="pname" style={{ marginBottom: 6 }}>What was off?</div>
      <div className="chips">
        {FEEDBACK_REASONS.map(r => (
          <button key={r} type="button" className={`chip ${reasons.includes(r) ? 'on' : ''}`}
            onClick={() => onToggleReason(r)}>{r}</button>
        ))}
      </div>
      <div style={{ marginTop: 'var(--s4)' }}>
        <textarea className="ctl" rows={2} placeholder="What should future prompts do differently? (optional)"
          value={comment} onChange={e => onComment(e.target.value)} />
      </div>
      <div className="out-actions">
        <Button variant="primary" size="sm" onClick={onSubmit}>Send feedback</Button>
      </div>
    </div>
  );
};

const SuccessState = ({ result, onRegenerate, onUseful, onNotUseful, fb, toast }) => (
  <div aria-live="polite">
    <div className="out-head">
      <div>
        <div className="title">{result.title}</div>
        <div className="sub">{result.subtitle}</div>
      </div>
      <span className="pill ok"><span className="dot" />Ready to copy</span>
    </div>

    <div className="full-copy">
      <div>
        <div className="full-copy-title">Complete prompt</div>
        <div className="full-copy-sub">Copies positive and negative prompts together.</div>
      </div>
      <CopyButton text={fullPromptText(result)} label="Copy full prompt" onCopied={() => toast('Complete prompt copied')} />
    </div>

    <PromptBlock name="Main prompt" body={result.main} onCopy={() => toast('Main prompt copied')} />
    <PromptBlock name="Negative prompt" body={result.negative} tone="neg" onCopy={() => toast('Negative prompt copied')} />

    <div style={{ marginTop: 'var(--s4)' }}>
      <Collapse label="Show short prompt, style notes & tips" openLabel="Hide extra detail">
        <PromptBlock name="Short prompt" body={result.short} onCopy={() => toast('Short prompt copied')} />
        {result.tokenNote && <PromptBlock name="Token notes (VTT)" body={result.tokenNote} prose />}
        <PromptBlock name="Style notes" body={result.styleNote} prose />
        <PromptBlock name="Usage tip" body={result.tip} prose />
      </Collapse>
    </div>

    <div className="out-meta">
      <span><b>Model</b> {result.meta.model}</span>
      <span><b>Template</b> {result.meta.template}</span>
      <span><b>Rules</b> {result.meta.rules}</span>
    </div>

    <div className="out-actions">
      <Button variant="secondary" size="sm" iconLeft="rotate-ccw" onClick={onRegenerate}>Regenerate</Button>
      <Button variant="useful" size="sm" iconLeft="thumbs-up" onClick={onUseful}>Useful</Button>
      <Button variant="nope" size="sm" iconLeft="thumbs-down" onClick={onNotUseful}>Not useful</Button>
    </div>

    {fb.phase && <Feedback {...fb} />}
  </div>
);

/* ---------- The Generator ---------- */

const Generator = ({ layout = 'side', forceState = 'auto', initialType }) => {
  const toast = useToast();
  const [form, setForm] = React.useState({ ...BLANK, type: initialType || BLANK.type });
  const [status, setStatus] = React.useState('empty'); // empty|loading|success|error
  const [result, setResult] = React.useState(null);
  const [errors, setErrors] = React.useState({});
  const [fb, setFb] = React.useState({ phase: null, reasons: [], comment: '' });
  const lastRef = React.useRef(null);

  React.useEffect(() => { if (initialType) setForm(f => ({ ...f, type: initialType })); }, [initialType]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const validate = () => {
    const e = {};
    if (!form.race.trim() && !form.desc.trim()) {
      e.race = 'Add a race/creature or a short description to start.';
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const runGenerate = (data) => {
    setStatus('loading');
    setFb({ phase: null, reasons: [], comment: '' });
    clearTimeout(lastRef.current);
    lastRef.current = setTimeout(() => {
      setResult(FORGE.build(data));
      setStatus('success');
    }, 850);
  };

  const onGenerate = () => { if (validate()) runGenerate(form); };
  const onRegenerate = () => runGenerate(form);
  const onRetry = () => runGenerate(form);

  const onClear = () => {
    setForm({ ...BLANK, type: form.type });
    setStatus('empty'); setResult(null); setErrors({}); setFb({ phase: null, reasons: [], comment: '' });
  };

  const loadExample = (fill) => {
    const data = { ...BLANK, ...fill };
    setForm(data); setErrors({});
    runGenerate(data);
  };
  React.useEffect(() => { window.__forgeLoadExample = loadExample; }, []);

  const onNotUseful = () => setFb(s => ({ ...s, phase: 'asking' }));
  const onUseful = () => toast('Thanks — glad it helped');
  const toggleReason = (r) => setFb(s => ({ ...s, reasons: s.reasons.includes(r) ? s.reasons.filter(x => x !== r) : [...s.reasons, r] }));
  const submitFb = () => setFb(s => ({ ...s, phase: 'done' }));

  // demo override from tweaks
  const effStatus = forceState !== 'auto' ? forceState : status;
  const demoResult = result || FORGE.build({ ...BLANK, race: 'Tiefling', klass: 'Warlock', desc: 'pact of the chain, infernal heritage' });

  return (
    <section className="hero hero-bg">
      <div className="wrap hero-inner">
        <div className="intro">
          <div className="kicker">Tabletop prompt utility · free</div>
          <h1>DND Character Prompt Generator</h1>
          <p className="lede">Turn your race, class, style, weapon, and backstory idea into a copy-ready AI image prompt for portraits, VTT tokens, NPCs, monsters, and fantasy scenes.</p>
          <p className="support">No login required. Copy prompts into Midjourney, ChatGPT, Gemini, Leonardo, Stable Diffusion, or any image model.</p>
          <div className="trust">
            <span><Icon name="check" size={15} />No login</span>
            <span><Icon name="check" size={15} />Prompt only</span>
            <span><Icon name="check" size={15} />Works with any image tool</span>
            <span><Icon name="check" size={15} />Includes a negative prompt</span>
          </div>
        </div>

        <div className={`bench ${layout === 'side' ? 'side' : ''}`}>
          {/* FORM */}
          <div className="panel">
            <div className="pad">
              <div className="step">
                <div className="step-lbl"><span className="step-no">1</span>Prompt type</div>
                <Segmented options={FORGE.TYPES} value={form.type} onChange={v => set('type', v)} ariaLabel="Prompt type" />
                {form.type === 'token' && (
                  <div className="banner ok" style={{ marginTop: 'var(--s3)', marginBottom: 0 }}>
                    <Icon name="info" size={17} /><div>Token mode builds a top-down, centered VTT figure with a clean outline and 1:1 framing.</div>
                  </div>
                )}
              </div>

              <div className="step">
                <div className="step-lbl"><span className="step-no">2</span>Core details</div>
                <div className="field-stack">
                  <div className="row2">
                    <Field label={form.type === 'scene' ? 'Place / setting' : 'Race / creature'} htmlFor="f-race" error={errors.race}>
                      <input id="f-race" className={`ctl ${errors.race ? 'bad' : ''}`}
                        placeholder={form.type === 'scene' ? 'Haunted tavern' : 'Tiefling'}
                        value={form.race} onChange={e => set('race', e.target.value)} />
                    </Field>
                    <Field label={form.type === 'scene' ? 'Focus / hook' : 'Class / role'} htmlFor="f-class">
                      <input id="f-class" className="ctl"
                        placeholder={form.type === 'scene' ? 'ambush' : 'Warlock'}
                        value={form.klass} onChange={e => set('klass', e.target.value)} />
                    </Field>
                  </div>
                  <Field label="Short description" htmlFor="f-desc" hint="A line of flavor — personality, gear, a signature detail.">
                    <textarea id="f-desc" className="ctl" rows={2}
                      placeholder="Pact of the chain, cocky, infernal heritage, soul-lantern…"
                      value={form.desc} onChange={e => set('desc', e.target.value)} />
                  </Field>
                </div>
              </div>

              <div className="step">
                <div className="step-lbl"><span className="step-no">3</span>Visual style</div>
                <Select id="f-style" value={form.style} onChange={v => set('style', v)} options={FORGE.STYLES} />
              </div>

              <div className="step">
                <Collapse label="Advanced — mood, model & refinements" openLabel="Advanced — hide refinements">
                  <div className="field-stack">
                    <div className="row2">
                      <Field label="Mood"><Select value={form.mood} onChange={v => set('mood', v)} options={FORGE.MOODS} /></Field>
                      <Field label="Target model"><Select value={form.model} onChange={v => set('model', v)} options={FORGE.MODELS} /></Field>
                    </div>
                    <div className="row2">
                      <Field label="Gender presentation"><input className="ctl" placeholder="any" value={form.gender} onChange={e => set('gender', e.target.value)} /></Field>
                      <Field label="Age"><input className="ctl" placeholder="young adult" value={form.age} onChange={e => set('age', e.target.value)} /></Field>
                    </div>
                    <div className="row2">
                      <Field label="Alignment"><input className="ctl" placeholder="chaotic neutral" value={form.alignment} onChange={e => set('alignment', e.target.value)} /></Field>
                      <Field label="Color palette"><input className="ctl" placeholder="crimson and violet" value={form.palette} onChange={e => set('palette', e.target.value)} /></Field>
                    </div>
                    <div className="row2">
                      <Field label="Armor"><input className="ctl" placeholder="ornate dark leather" value={form.armor} onChange={e => set('armor', e.target.value)} /></Field>
                      <Field label="Weapon"><input className="ctl" placeholder="a soul-lantern" value={form.weapon} onChange={e => set('weapon', e.target.value)} /></Field>
                    </div>
                    <div className="row2">
                      <Field label="Magic / spell theme"><input className="ctl" placeholder="eldritch" value={form.magic} onChange={e => set('magic', e.target.value)} /></Field>
                      <Field label="Camera angle"><input className="ctl" placeholder="three-quarter view" value={form.camera} onChange={e => set('camera', e.target.value)} /></Field>
                    </div>
                  </div>
                </Collapse>
              </div>

              <div className="out-actions" style={{ marginTop: 'var(--s5)' }}>
                <Button variant="primary" size="lg" iconLeft="wand-2" className="block" style={{ flex: 1 }}
                  disabled={effStatus === 'loading'} onClick={onGenerate}>
                  {effStatus === 'loading' ? 'Generating…' : 'Generate prompt'}
                </Button>
              </div>
              <div className="out-actions" style={{ marginTop: 'var(--s2)' }}>
                <Button variant="ghost" size="sm" iconLeft="wand-2" onClick={() => loadExample(FORGE.examples[0].fill)}>Load example</Button>
                <Button variant="ghost" size="sm" iconLeft="eraser" onClick={onClear}>Clear</Button>
              </div>
            </div>
          </div>

          {/* OUTPUT */}
          <div className="out-wrap">
            <div className="panel">
              <div className="pad">
                {effStatus === 'empty' && <EmptyState onLoad={() => loadExample(FORGE.examples[0].fill)} />}
                {effStatus === 'loading' && <LoadingState />}
                {effStatus === 'error' && <ErrorState onRetry={onRetry} />}
                {effStatus === 'success' && (
                  <SuccessState result={demoResult} onRegenerate={onRegenerate}
                    onUseful={onUseful} onNotUseful={onNotUseful} fb={fb} toast={toast} />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

Object.assign(window, { Generator });
