/* App root — routing, theme/tweaks, page composition */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "dark": false,
  "accent": "brass",
  "texture": true,
  "layout": "side",
  "demoState": "auto"
}/*EDITMODE-END*/;

const TYPE_ROUTES = { character: 'portrait', token: 'token', monster: 'monster', scene: 'scene', npc: 'npc' };

// Prefill 字段映射：URL query 参数名 -> Generator 表单字段名
// 参考 design-spec.md 第4.2节
const PREFILL_QUERY_MAP = {
  'type': 'type',
  'race': 'race',
  'class': 'klass',
  'style': 'style',
  'mood': 'mood',
  'model': 'model',
};

/** 验证 prefill 参数值：trim、max 50 chars、reject < > */
function validatePrefillValue(value) {
  if (typeof value !== 'string') return null;
  var cleaned = value.trim();
  if (cleaned.length === 0 || cleaned.length > 50) return null;
  if (cleaned.indexOf('<') >= 0 || cleaned.indexOf('>') >= 0) return null;
  return cleaned;
}

/** 从 window.location.search 解析 prefill 参数，映射为 Generator 表单初始值 */
function parsePrefillFromURL() {
  const params = new URLSearchParams(window.location.search);
  var prefill = {};
  for (var queryKey in PREFILL_QUERY_MAP) {
    var formKey = PREFILL_QUERY_MAP[queryKey];
    var value = params.get(queryKey);
    var validated = validatePrefillValue(value);
    if (validated) {
      prefill[formKey] = validated;
    }
  }
  // 只有包含至少 type 字段才视为有效 prefill
  if (prefill.type) {
    return prefill;
  }
  return null;
}

/** 从页面内嵌 <script type="application/json" id="generator-prefill"> 解析 prefill */
function parsePrefillFromEmbeddedJSON() {
  var scriptEl = document.querySelector('script[type="application/json"][id="generator-prefill"]');
  if (!scriptEl) return null;
  try {
    var data = JSON.parse(scriptEl.textContent);
    // 映射 klass 字段（JSON 中可能使用 klass 或 class_role）
    if (data.class_role && !data.klass) {
      data.klass = data.class_role;
    }
    // URL 参数使用 class，但表单使用 klass
    if (data.klass) {
      // 保持 klass 字段供 Generator 使用
    }
    if (data.type) {
      return data;
    }
    return null;
  } catch (e) {
    // JSON 解析失败，忽略
    return null;
  }
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [route, setRoute] = React.useState('home');
  const [initType, setInitType] = React.useState('portrait');
  const [prefill, setPrefill] = React.useState(null);

  /** API 配置状态：bootstrap 结果 + apiAvailable 标记 */
  const [apiConfig, setApiConfig] = React.useState({ apiAvailable: false, features: null });

  // mount 时解析 URL 参数和内嵌 JSON，设置 prefill 状态
  React.useEffect(() => {
    var urlPrefill = parsePrefillFromURL();
    if (urlPrefill) {
      setPrefill(urlPrefill);
      return;
    }
    var embeddedPrefill = parsePrefillFromEmbeddedJSON();
    if (embeddedPrefill) {
      setPrefill(embeddedPrefill);
    }
  }, []);

  /** mount 时调用 ApiClient.bootstrap()，初始化 session 和 CSRF token */
  React.useEffect(() => {
    if (!window.ApiClient || !window.ApiClient.bootstrap) return;
    window.ApiClient.bootstrap().then(function (result) {
      setApiConfig({ apiAvailable: true, features: result.features });
    }).catch(function () {
      /** bootstrap 失败：标记 API 不可用且进入离线模式 */
      setApiConfig({ apiAvailable: false, features: null, offlineMode: true });
    });
  }, []);

  // apply theme/accent/texture classes to <html>
  React.useEffect(() => {
    const cls = ['theme-forge'];
    if (t.dark) cls.push('dark');
    if (t.accent === 'crimson') cls.push('accent-crimson');
    if (t.accent === 'forest') cls.push('accent-forest');
    if (t.texture) cls.push('texture-on');
    document.documentElement.className = cls.join(' ');
  }, [t.dark, t.accent, t.texture]);

  const handleNav = React.useCallback((id) => {
    if (TYPE_ROUTES[id]) {
      setInitType(TYPE_ROUTES[id]);
      setRoute('home');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      setRoute(id);
      window.scrollTo({ top: 0 });
    }
  }, []);

  React.useEffect(() => { window.__navigate = handleNav; }, [handleNav]);
  React.useEffect(() => { if (window.lucide) window.lucide.createIcons(); });

  // 当 prefill 含有 type 时，映射为 initType 使 Generator 初始化正确类型
  React.useEffect(() => {
    if (prefill && prefill.type) {
      var mapped = TYPE_ROUTES[prefill.type] || prefill.type;
      if (FORGE.TYPES && FORGE.TYPES.indexOf(mapped) >= 0) {
        setInitType(mapped);
      }
    }
  }, [prefill]);

  const Home = (
    <React.Fragment>
      <Generator layout={t.layout} forceState={t.demoState} initialType={initType} prefill={prefill} apiConfig={apiConfig} />
      <Examples />
      <PromptGuide />
      <HowItWorks />
      <Limitations />
      <FAQ />
      <InternalLinks />
    </React.Fragment>
  );

  let body;
  switch (route) {
    case 'about': body = <About />; break;
    case 'privacy': body = <Privacy />; break;
    case 'terms': body = <Terms />; break;
    case 'contact': body = <Contact />; break;
    case '404': body = <NotFound onNav={handleNav} />; break;
    default: body = Home;
  }

  return (
    <ToastHost>
      <Header route={route} onNav={handleNav} theme={t.dark ? 'dark' : 'light'}
        onToggleTheme={() => setTweak('dark', !t.dark)} />
      {body}
      <Footer onNav={handleNav} />

      <TweaksPanel>
        <TweakSection label="Workbench" />
        <TweakToggle label="Dark workbench" value={t.dark} onChange={v => setTweak('dark', v)} />
        <TweakColor label="Primary accent" value={accentColor(t)}
          options={[ACCENTS.brass, ACCENTS.crimson, ACCENTS.forest]}
          onChange={v => setTweak('accent', COLOR_TO_ACCENT[v] || 'brass')} />
        <TweakToggle label="Parchment texture" value={t.texture} onChange={v => setTweak('texture', v)} />
        <TweakRadio label="Output layout" value={t.layout} options={['side', 'stacked']}
          onChange={v => setTweak('layout', v)} />
        <TweakSection label="Preview a state" />
        <TweakSelect label="Output state" value={t.demoState}
          options={['auto', 'empty', 'loading', 'success', 'error']}
          onChange={v => setTweak('demoState', v)} />
      </TweaksPanel>
    </ToastHost>
  );
}

// accent swatches reflect the live (light) primary of each option
const ACCENTS = { brass: '#9A6E22', crimson: '#A8362A', forest: '#1F7A52' };
const COLOR_TO_ACCENT = { '#9A6E22': 'brass', '#A8362A': 'crimson', '#1F7A52': 'forest' };
const accentColor = (t) => ACCENTS[t.accent] || ACCENTS.brass;

ReactDOM.createRoot(document.getElementById('app')).render(<App />);
