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

/** 渲染模式徽章：LLM/Fallback/Local */
const ModeBadge = ({ mode }) => {
  var label = 'Offline';
  var cls = 'pill local';
  if (mode === 'llm') { label = 'AI Enhanced'; cls = 'pill llm'; }
  else if (mode === 'fallback') { label = 'Standard'; cls = 'pill fallback'; }
  return (
    <span className={cls} aria-label={'Generation mode: ' + label}>
      {(mode === 'llm' || mode === 'fallback') && <span className="dot" />}
      {label}
    </span>
  );
};

/** 渲染配额显示 */
const QuotaDisplay = ({ quota, mode }) => {
  if (!quota || mode === 'local') return null;
  var remaining = quota.remaining;
  var limit = quota.limit;
  var colorClass = '';
  var ariaLabel = 'Quota: ' + remaining + ' of ' + limit + ' remaining';
  if (remaining === 0) { colorClass = 'quota-exhausted'; ariaLabel = 'Quota exhausted: 0 of ' + limit + ' remaining'; }
  else if (remaining <= 2) { colorClass = 'quota-low'; }
  return (
    <span className={colorClass} aria-label={ariaLabel}>
      <b>Quota</b> {remaining} / {limit}
    </span>
  );
};

/** 配额耗尽提示横幅 */
const QuotaExhaustedBanner = ({ quota, mode }) => {
  if (mode !== 'fallback' || !quota || quota.remaining !== 0) return null;
  return (
    <div className="banner warn" role="status">
      <Icon name="alert-circle" size={17} />
      <div>AI-enhanced prompts have reached the hourly limit. Using standard generation. Limit resets each hour.</div>
    </div>
  );
};

/** 离线模式提示横幅 */
const OfflineBanner = ({ show }) => {
  if (!show) return null;
  return (
    <div className="banner warn" role="status">
      <Icon name="wifi-off" size={17} />
      <div>Using offline mode — prompts are generated locally from templates.</div>
    </div>
  );
};

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

const SuccessState = ({ result, onRegenerate, onUseful, onNotUseful, fb, toast, mode, quota, offlineMode }) => (
  <div aria-live="polite">
    <OfflineBanner show={offlineMode} />
    <div className="out-head">
      <div>
        <div className="title">{result.title}</div>
        <div className="sub">{result.subtitle}</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <ModeBadge mode={mode} />
        <span className="pill ok"><span className="dot" />Ready to copy</span>
      </div>
    </div>

    <QuotaExhaustedBanner quota={quota} mode={mode} />

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
        {/* LLM/fallback 模式下不使用 dangerouslySetInnerHTML 渲染，防止 XSS */}
        <PromptBlock name="Style notes" body={result.styleNote} prose={mode === 'local'} />
        <PromptBlock name="Usage tip" body={result.tip} prose={mode === 'local'} />
      </Collapse>
    </div>

    <div className="out-meta">
      <span><b>Model</b> {result.meta.model}</span>
      <span><b>Template</b> {result.meta.template}</span>
      <span><b>Rules</b> {result.meta.rules}</span>
      <QuotaDisplay quota={quota} mode={mode} />
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

/** 最小加载时长常量（ms），防止闪烁 */
var MIN_LOADING_MS = 600;

/** 连续失败阈值，达到后显示离线横幅 */
var OFFLINE_THRESHOLD = 3;

const Generator = ({ layout = 'side', forceState = 'auto', initialType, prefill, apiConfig }) => {
  const toast = useToast();
  const [form, setForm] = React.useState({ ...BLANK, type: initialType || BLANK.type });
  const [status, setStatus] = React.useState('empty'); // empty|loading|success|error
  const [result, setResult] = React.useState(null);
  const [errors, setErrors] = React.useState({});
  const [fb, setFb] = React.useState({ phase: null, reasons: [], comment: '' });
  const lastRef = React.useRef(null);

  /** 生成模式：llm / fallback / local */
  const [mode, setMode] = React.useState('local');
  /** 配额信息：{ remaining, limit } */
  const [quota, setQuota] = React.useState(null);
  /** 离线模式标记：3+ 连续失败后为 true，或 bootstrap 失败时从 apiConfig 继承 */
  const [offlineMode, setOfflineMode] = React.useState(
    !!(apiConfig && apiConfig.offlineMode)
  );
  /** 连续失败计数器 */
  const failCountRef = React.useRef(0);
  /** 上一次请求的 requestId，用于反馈提交 */
  const requestIdRef = React.useRef(null);

  /** 组件卸载时清理 timer，防止内存泄漏 */
  React.useEffect(() => {
    return function () {
      clearTimeout(lastRef.current);
    };
  }, []);

  /** apiConfig 变更时同步离线模式状态 */
  React.useEffect(() => {
    if (apiConfig && apiConfig.offlineMode) {
      setOfflineMode(true);
    }
  }, [apiConfig]);

  React.useEffect(() => { if (initialType) setForm(f => ({ ...f, type: initialType })); }, [initialType]);

  // prefill 变更时合并到表单状态（覆盖空白字段）
  React.useEffect(() => {
    if (prefill) {
      setForm(f => {
        var merged = { ...f };
        for (var key in prefill) {
          if (prefill[key] && prefill[key] !== '') {
            merged[key] = prefill[key];
          }
        }
        return merged;
      });
    }
  }, [prefill]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const validate = () => {
    const e = {};
    if (!form.race.trim() && !form.desc.trim()) {
      e.race = 'Add a race/creature or a short description to start.';
    }
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  /** 记录一次失败，更新离线模式状态 */
  function recordFailure() {
    failCountRef.current += 1;
    if (failCountRef.current >= OFFLINE_THRESHOLD) {
      setOfflineMode(true);
    }
  }

  /** 记录一次成功，重置失败计数和离线模式 */
  function recordSuccess() {
    failCountRef.current = 0;
    setOfflineMode(false);
  }

  /** 异步生成提示词：优先调用后端 API，支持重试和 403 re-bootstrap，最终 fallback 到本地 FORGE.build() */
  const runGenerate = async (data) => {
    setStatus('loading');
    setFb({ phase: null, reasons: [], comment: '' });
    clearTimeout(lastRef.current);

    var startTime = Date.now();
    var apiAvailable = apiConfig && apiConfig.apiAvailable;
    var features = apiConfig && apiConfig.features;
    var llmEnabled = features && features.llm_enabled;

    /** 补齐最小加载时长，防止闪烁 */
    function ensureMinLoad(callback) {
      var elapsed = Date.now() - startTime;
      var remaining = MIN_LOADING_MS - elapsed;
      if (remaining > 0) {
        lastRef.current = setTimeout(callback, remaining);
      } else {
        callback();
      }
    }

    /** 使用本地 FORGE.build() 生成结果 */
    function localBuild() {
      var localResult = FORGE.build(data);
      setMode('local');
      setQuota(null);
      requestIdRef.current = null;
      setResult(localResult);
      setStatus('success');
      recordFailure();
    }

    /** 如果 API 不可用或 LLM 未启用，直接走本地生成 */
    if (!apiAvailable || !llmEnabled) {
      ensureMinLoad(localBuild);
      return;
    }

    /** 获取指纹哈希（best-effort） */
    var fingerprintHash = '';
    try {
      fingerprintHash = await ApiClient.getFingerprintHash();
    } catch (e) { /* fingerprint 失败时传空 */ }

    /** 映射表单字段到 API 字段，传入指纹哈希 */
    var apiForm = ApiClient.mapFormToApi(data, fingerprintHash);

    /** 尝试调用后端生成 API 并处理结果 */
    async function handleApiSuccess(apiResponse) {
      var mapped = ApiClient.mapApiToResult(apiResponse);
      var localMeta = FORGE.build(data);
      mapped.title = localMeta.title;
      mapped.subtitle = localMeta.subtitle;
      mapped.tokenNote = localMeta.tokenNote;
      mapped.meta = localMeta.meta;
      ensureMinLoad(function () {
        setMode(mapped.mode);
        setQuota(mapped.quota);
        requestIdRef.current = mapped.requestId;
        setResult(mapped);
        setStatus('success');
        recordSuccess();
      });
    }

    try {
      /** 调用后端生成 API */
      var apiResponse = await ApiClient.generatePrompt(apiForm);
      await handleApiSuccess(apiResponse);
    } catch (err) {
      /** 403 错误：尝试 re-bootstrap 一次，成功后重试 generate */
      if (err && err.status === 403) {
        try {
          await ApiClient.bootstrap();
          var retryResponse = await ApiClient.generatePrompt(apiForm);
          await handleApiSuccess(retryResponse);
          return;
        } catch (bootstrapOrRetryErr) {
          /** re-bootstrap 或重试失败，fallback 到本地 */
          ensureMinLoad(localBuild);
          return;
        }
      }

      /** 网络错误（非 403）：延迟 1 秒后重试一次 */
      var isNetworkError = !err || !err.status;
      if (isNetworkError) {
        try {
          await new Promise(function (resolve) { setTimeout(resolve, 1000); });
          var retryResp = await ApiClient.generatePrompt(apiForm);
          await handleApiSuccess(retryResp);
          return;
        } catch (retryErr) {
          /** 重试仍失败，fallback 到本地 */
          ensureMinLoad(localBuild);
          return;
        }
      }

      /** 其他错误（如 4xx/5xx），直接 fallback */
      ensureMinLoad(localBuild);
    }
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

  /** 提交反馈：若有 requestId 且 session 就绪则调后端 API，失败时仅 console.warn */
  const submitFb = async () => {
    setFb(s => ({ ...s, phase: 'done' }));
    if (requestIdRef.current && ApiClient.isSessionReady()) {
      try {
        await ApiClient.submitFeedback({
          request_id: requestIdRef.current,
          feedback: 'not_useful',
          reason: fb.reasons.length > 0 ? fb.reasons.join(', ') : null,
          comment: fb.comment || null,
        });
      } catch (e) {
        console.warn('Feedback submission failed:', e);
      }
    }
  };

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
                    onUseful={onUseful} onNotUseful={onNotUseful} fb={fb} toast={toast}
                    mode={mode} quota={quota} offlineMode={offlineMode} />
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
