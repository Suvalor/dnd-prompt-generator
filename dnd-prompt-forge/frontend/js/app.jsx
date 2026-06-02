/* App root — routing, theme/tweaks, page composition */

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "dark": false,
  "accent": "brass",
  "texture": true,
  "layout": "side",
  "demoState": "auto"
}/*EDITMODE-END*/;

const TYPE_ROUTES = { character: 'portrait', token: 'token', monster: 'monster', scene: 'scene', npc: 'npc' };

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [route, setRoute] = React.useState('home');
  const [initType, setInitType] = React.useState('portrait');

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

  const Home = (
    <React.Fragment>
      <Generator layout={t.layout} forceState={t.demoState} initialType={initType} />
      <AdAfterTool />
      <Examples />
      <PromptGuide />
      <HowItWorks />
      <Limitations />
      <AdBeforeFaq />
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
