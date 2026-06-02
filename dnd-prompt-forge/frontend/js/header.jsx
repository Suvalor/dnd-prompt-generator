/* Header — sticky nav + mobile sheet + theme toggle */

const BrandMark = () => (
  <span className="mark">
    <svg width="19" height="19" viewBox="0 0 24 24" fill="none">
      <path d="M12 2l8.66 5v10L12 22 3.34 17V7L12 2z" stroke="var(--brass)" strokeWidth="1.6" strokeLinejoin="round"/>
      <path d="M12 6.5l4 2.3v4.6L12 15.7l-4-2.3V8.8l4-2.3z" fill="var(--brass)"/>
    </svg>
  </span>
);

const NAV = [
  { id: 'character', label: 'Character' },
  { id: 'token', label: 'Token' },
  { id: 'monster', label: 'Monster' },
  { id: 'scene', label: 'Scene' },
  { id: 'about', label: 'About' },
  { id: 'contact', label: 'Contact' },
];

const Header = ({ route, onNav, theme, onToggleTheme }) => {
  const [open, setOpen] = React.useState(false);
  const go = (id) => { setOpen(false); onNav(id); };
  return (
    <React.Fragment>
      <header className="hdr">
        <div className="hdr-inner">
          <div className="brand" onClick={() => go('home')} role="link" tabIndex={0}
               onKeyDown={e => e.key === 'Enter' && go('home')}>
            <BrandMark />
            <span className="name">DND Prompt <b>Forge</b></span>
          </div>
          <nav className="nav" aria-label="Prompt types">
            {NAV.map(n => (
              <a key={n.id} className={route === n.id ? 'active' : ''}
                 onClick={() => go(n.id)} tabIndex={0}
                 onKeyDown={e => e.key === 'Enter' && go(n.id)}>{n.label}</a>
            ))}
          </nav>
          <div className="hdr-right">
            <Button variant="ghost" className="icon" aria-label="Toggle dark mode"
              onClick={onToggleTheme}>
              <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={17} />
            </Button>
            <Button variant="ghost" className="icon menu-btn" aria-label="Menu"
              aria-expanded={open} onClick={() => setOpen(o => !o)}>
              <Icon name={open ? 'x' : 'menu'} size={18} />
            </Button>
          </div>
        </div>
      </header>
      {open && (
        <div className="sheet">
          {NAV.map(n => <a key={n.id} onClick={() => go(n.id)}>{n.label}</a>)}
        </div>
      )}
    </React.Fragment>
  );
};

Object.assign(window, { Header, BrandMark });
