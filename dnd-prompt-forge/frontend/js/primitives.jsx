/* Primitives — stateless atoms + a couple tiny hooks. Exported to window. */

const Icon = ({ name, size, style, className }) => {
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (window.lucide && ref.current) {
      ref.current.innerHTML = '';
      const i = document.createElement('i');
      i.setAttribute('data-lucide', name);
      ref.current.appendChild(i);
      window.lucide.createIcons({ nameAttr: 'data-lucide' });
    }
  }, [name]);
  return <span ref={ref} className={className} aria-hidden="true"
    style={{ display: 'inline-flex', width: size || 18, height: size || 18, ...style }} />;
};

const Button = ({ variant = 'secondary', size, iconLeft, iconRight, children, className = '', ...rest }) => {
  const cls = ['btn', variant, size === 'lg' ? 'lg' : size === 'sm' ? 'sm' : '', className].filter(Boolean).join(' ');
  const isz = size === 'sm' ? 14 : 16;
  return (
    <button className={cls} {...rest}>
      {iconLeft && <Icon name={iconLeft} size={isz} />}
      {children}
      {iconRight && <Icon name={iconRight} size={isz} />}
    </button>
  );
};

const Field = ({ label, required, error, hint, htmlFor, children }) => (
  <div className="field">
    {label && <label htmlFor={htmlFor}>{label}{required && <span className="req"> *</span>}</label>}
    {children}
    {error && <span className="err-msg">{error}</span>}
    {hint && !error && <span className="hint">{hint}</span>}
  </div>
);

const Segmented = ({ options, value, onChange, ariaLabel }) => (
  <div className="seg" role="tablist" aria-label={ariaLabel}>
    {options.map(o => (
      <button key={o.value} role="tab" type="button" aria-selected={value === o.value}
        className={value === o.value ? 'on' : ''} onClick={() => onChange(o.value)}>
        {o.icon && <Icon name={o.icon} size={15} />}{o.label}
      </button>
    ))}
  </div>
);

const Select = ({ value, onChange, options, id, ...rest }) => (
  <select id={id} className="ctl" value={value} onChange={e => onChange(e.target.value)} {...rest}>
    {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
  </select>
);

const CopyButton = ({ text, label = 'Copy', onCopied }) => {
  const [done, setDone] = React.useState(false);
  const copy = () => {
    const fall = () => { try {
      const ta = document.createElement('textarea'); ta.value = text;
      ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta);
      ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
    } catch (e) {} };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(fall);
    } else fall();
    setDone(true); onCopied && onCopied();
    setTimeout(() => setDone(false), 1600);
  };
  return (
    <button type="button" className={`copy-btn ${done ? 'done' : ''}`} onClick={copy}>
      <Icon name={done ? 'check' : 'copy'} size={13} />{done ? 'Copied' : label}
    </button>
  );
};

const Collapse = ({ label, openLabel, defaultOpen = false, children }) => {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <div>
      <button type="button" className={`collapse-head ${open ? 'open' : ''}`} aria-expanded={open}
        onClick={() => setOpen(o => !o)}>
        <span>{open && openLabel ? openLabel : label}</span>
        <Icon name="chevron-down" size={17} className="chev" />
      </button>
      {open && <div className="collapse-body">{children}</div>}
    </div>
  );
};

// Toast (single, app-level)
const ToastCtx = React.createContext(() => {});
const useToast = () => React.useContext(ToastCtx);
const ToastHost = ({ children }) => {
  const [msg, setMsg] = React.useState(null);
  const show = React.useCallback((m) => { setMsg(m); }, []);
  React.useEffect(() => {
    if (!msg) return;
    const t = setTimeout(() => setMsg(null), 1900);
    return () => clearTimeout(t);
  }, [msg]);
  return (
    <ToastCtx.Provider value={show}>
      {children}
      {msg && <div className="toast"><Icon name="check" size={16} />{msg}</div>}
    </ToastCtx.Provider>
  );
};

Object.assign(window, { Icon, Button, Field, Segmented, Select, CopyButton, Collapse, ToastHost, useToast });
