/* ============================================================
   DND Prompt Forge — prompt engine
   Deterministically assembles copy-ready prompts from form input.
   Exposes window.FORGE { TYPES, MODELS, STYLES, MOODS, build, examples }
   ============================================================ */
(function () {
  const TYPES = [
    { value: 'portrait',  label: 'Portrait',  icon: 'user',          comp: 'head-and-shoulders portrait, face and costume detail, expressive eyes' },
    { value: 'fullbody',  label: 'Full body', icon: 'person-standing',comp: 'full-body character illustration, full silhouette, dynamic pose, visible armor and weapon' },
    { value: 'token',     label: 'Token',     icon: 'circle-dot',     comp: 'top-down view, centered single figure, clean readable silhouette, transparent or simple background, circular VTT token framing' },
    { value: 'npc',       label: 'NPC',       icon: 'users',          comp: 'character portrait of a non-player character, memorable role-defining traits, approachable framing' },
    { value: 'monster',   label: 'Monster',   icon: 'skull',          comp: 'full creature illustration, anatomy and scale emphasis, threatening presence in its lair' },
    { value: 'scene',     label: 'Scene',     icon: 'mountain',       comp: 'wide environment illustration, establishing shot, atmosphere and encounter hook, no central character required' },
  ];

  const MODELS = [
    { value: 'midjourney', label: 'Midjourney',      suffix: '--ar {ar} --style raw --v 6.1' },
    { value: 'chatgpt',    label: 'ChatGPT (DALL·E)', suffix: '' },
    { value: 'gemini',     label: 'Gemini',           suffix: '' },
    { value: 'leonardo',   label: 'Leonardo',         suffix: '' },
    { value: 'sd',         label: 'Stable Diffusion', suffix: '(masterpiece, best quality, highly detailed:1.2)' },
    { value: 'general',    label: 'General purpose',  suffix: '' },
  ];

  const STYLES = [
    { value: 'painterly', label: 'Painterly fantasy', tag: 'painterly fantasy illustration, visible brush strokes, rich oil-painting texture' },
    { value: 'ink',       label: 'Ink & watercolor',  tag: 'ink line art with loose watercolor wash, parchment texture, sketchbook feel' },
    { value: 'realism',   label: 'Cinematic realism', tag: 'cinematic semi-realism, physically-based lighting, film still, photoreal materials' },
    { value: 'comic',     label: 'Comic / graphic',   tag: 'bold graphic comic style, clean inking, flat dramatic color blocking' },
    { value: 'storybook', label: 'Storybook',         tag: 'whimsical storybook illustration, soft gouache, warm rounded shapes' },
    { value: 'grimdark',  label: 'Grimdark',          tag: 'grimdark dark-fantasy concept art, muted desaturated palette, heavy chiaroscuro' },
  ];

  const MOODS = [
    { value: 'heroic',   label: 'Heroic',     tag: 'heroic, confident, triumphant' },
    { value: 'brooding', label: 'Brooding',   tag: 'brooding, moody, introspective' },
    { value: 'menacing', label: 'Menacing',   tag: 'menacing, ominous, dangerous' },
    { value: 'serene',   label: 'Serene',     tag: 'serene, calm, contemplative' },
    { value: 'mystical', label: 'Mystical',   tag: 'mystical, arcane, otherworldly glow' },
    { value: 'gritty',   label: 'Gritty',     tag: 'gritty, weathered, battle-worn' },
  ];

  const ANGLES = {
    portrait: 'eye-level three-quarter view, shallow depth of field',
    fullbody: 'full-length framing, low hero angle',
    token: 'direct top-down orthographic view',
    npc: 'eye-level, mid framing',
    monster: 'low dramatic angle emphasizing scale',
    scene: 'wide establishing angle, deep perspective',
  };
  const AR = { portrait: '4:5', fullbody: '2:3', token: '1:1', npc: '4:5', monster: '3:2', scene: '16:9' };

  const NEG_BASE = 'blurry, lowres, jpeg artifacts, deformed, extra limbs, extra fingers, mutated hands, bad anatomy, watermark, signature, text, logo, cropped, out of frame';
  const NEG_BY_TYPE = {
    token: 'background clutter, multiple figures, off-center, busy scenery, harsh drop shadow',
    portrait: 'full body, distant framing, flat even lighting',
    fullbody: 'cropped limbs, floating pose',
    monster: 'cute, friendly, cartoonish proportions',
    scene: 'central character hero, portrait crop',
    npc: 'generic stock-photo face, modern clothing',
  };

  const cap = (s) => s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  const clean = (s) => (s || '').trim().replace(/\s+/g, ' ').replace(/[.。]+$/, '');
  const join = (arr) => arr.filter(Boolean).map(clean).filter(Boolean).join(', ');

  function titleOf(d) {
    const t = TYPES.find(x => x.value === d.type) || TYPES[0];
    const subj = [cap(d.race), cap(d.klass)].filter(Boolean).join(' ');
    const base = subj || 'Fantasy Character';
    const kind = d.type === 'scene' ? 'Scene' : t.label;
    if (d.type === 'scene') return `${cap(d.race) || cap(d.desc) || 'Fantasy'} Scene`;
    return `${base} ${kind}`;
  }

  function build(d) {
    const type = d.type || 'portrait';
    const t = TYPES.find(x => x.value === type) || TYPES[0];
    const style = STYLES.find(x => x.value === d.style) || STYLES[0];
    const mood = MOODS.find(x => x.value === d.mood);
    const model = MODELS.find(x => x.value === d.model) || MODELS[5];

    // subject phrase
    const subjBits = [];
    if (d.gender) subjBits.push(d.gender);
    if (d.age) subjBits.push(d.age);
    if (d.race) subjBits.push(d.race);
    if (d.klass) subjBits.push(d.klass);
    let subject = subjBits.join(' ').trim();
    if (!subject) subject = type === 'scene' ? 'a fantasy location' : 'a fantasy character';
    else if (type !== 'scene') subject = `a ${subject}`;

    // descriptors
    const descr = [];
    if (d.desc) descr.push(d.desc);
    if (d.alignment) descr.push(`${d.alignment} alignment`);
    if (d.armor) descr.push(`wearing ${d.armor}`);
    if (d.weapon) descr.push(`wielding ${d.weapon}`);
    if (d.magic) descr.push(`${d.magic} magic effects`);

    const palette = d.palette ? `${d.palette} color palette` : '';
    const angle = d.camera || ANGLES[type];

    // MAIN
    const main = join([
      type === 'scene' ? subject : `${t.comp.split(',')[0]} of ${subject}`,
      type === 'scene' ? t.comp.split(',').slice(1).join(',') : t.comp.split(',').slice(1).join(','),
      ...descr,
      style.tag,
      mood && mood.tag,
      palette,
      angle,
      'intricate detail, professional fantasy art, ArtStation quality',
      model.value === 'sd' ? model.suffix : '',
    ]);

    let mainOut = main;
    if (model.value === 'midjourney') {
      mainOut = main + ' ' + model.suffix.replace('{ar}', AR[type] || '1:1');
    }

    // SHORT
    const shortBits = [
      type === 'scene' ? subject : subject.replace(/^a /, ''),
      type === 'token' ? 'top-down token' : t.label.toLowerCase(),
      d.desc && clean(d.desc).split(',')[0],
      style.label.toLowerCase(),
      mood && mood.value,
    ];
    const short = join(shortBits);

    // NEGATIVE
    const negative = join([NEG_BASE, NEG_BY_TYPE[type], d.style === 'realism' ? 'painting, illustration' : '']);

    // STYLE NOTES
    const notesMap = {
      portrait: 'Portraits read best with a clear single light source — name it (e.g. “warm rim light from the left”). Keep the background simple so the face carries the image.',
      fullbody: 'Full-body shots need a readable silhouette. Describe the pose as a verb (“striding”, “guarding”) and keep one hero prop dominant.',
      token: 'Tokens must stay centered and high-contrast against the edge. Request a plain or transparent background and avoid props that break the circular crop.',
      npc: 'NPCs land when one memorable trait leads (a scar, an heirloom, an expression). Name the role so the model dresses them in-world.',
      monster: 'Monsters benefit from a scale cue — put a small familiar object or a low horizon line in frame so size reads instantly.',
      scene: 'Scenes want depth: name a foreground, midground, and background element, plus the time of day for consistent lighting.',
    };
    let styleNote = notesMap[type];
    if (model.value === 'midjourney') styleNote += ` Midjourney aspect ratio set to ${AR[type] || '1:1'}.`;
    if (model.value === 'sd') styleNote += ' Quality boosters are prepended for Stable Diffusion.';

    // USAGE TIP
    const tip = type === 'token'
      ? 'Generate at 1:1, then export with a transparent or solid background and crop to a circle in your VTT.'
      : 'Paste the main prompt first. If the result drifts, add 1–2 words from the negative prompt into your model’s negative field rather than rewriting.';

    // TOKEN NOTES (only for token type)
    const tokenNote = type === 'token'
      ? 'Top-down VTT token: centered figure, clean outline, minimal background, 1:1 ratio. Add a subtle ground shadow only — no cast scenery. Recommended export: 512×512 PNG with transparency.'
      : null;

    return {
      title: titleOf(d),
      subtitle: [t.label, d.style && style.label, model.label].filter(Boolean).join(' · '),
      main: mainOut,
      short,
      negative,
      styleNote,
      tip,
      tokenNote,
      meta: { model: model.label, template: `${type}.v3`, rules: 'mem v2' },
    };
  }

  // Prefilled gallery / example data
  const examples = [
    { id: 'tiefling-warlock', type: 'portrait', badge: 'Portrait', name: 'Tiefling Warlock', route: '/tiefling-warlock-prompt-generator',
      excerpt: 'portrait of a tiefling warlock, crimson skin, curled obsidian horns, violet eyes…',
      fill: { type:'portrait', race:'Tiefling', klass:'Warlock', desc:'pact of the chain, cocky, infernal heritage, soul-lantern', style:'painterly', mood:'brooding', model:'midjourney', palette:'crimson and violet', magic:'eldritch' } },
    { id: 'elf-ranger', type: 'fullbody', badge: 'Full body', name: 'Elf Ranger', route: '/elf-ranger-prompt-generator',
      excerpt: 'full-body wood elf ranger, layered leather and cloak, longbow drawn, forest…',
      fill: { type:'fullbody', race:'Wood elf', klass:'Ranger', desc:'weathered scout, hooded cloak, mid-stride', style:'realism', mood:'gritty', model:'midjourney', armor:'studded leather', weapon:'a recurve longbow', palette:'mossy green and umber' } },
    { id: 'dragonborn-paladin', type: 'token', badge: 'Token', name: 'Dragonborn Paladin', route: '/dragonborn-paladin-token-prompt',
      excerpt: 'top-down token, bronze dragonborn paladin, gleaming plate, centered…',
      fill: { type:'token', race:'Bronze dragonborn', klass:'Paladin', desc:'radiant oath, shield raised', style:'painterly', mood:'heroic', model:'general', armor:'gilded plate armor', weapon:'a warhammer' } },
    { id: 'goblin-merchant', type: 'npc', badge: 'NPC', name: 'Goblin Merchant', route: '/dnd-npc-prompt-generator',
      excerpt: 'NPC portrait of a shrewd goblin merchant, overloaded backpack, gold tooth…',
      fill: { type:'npc', race:'Goblin', klass:'Merchant', desc:'shrewd, gold tooth, overloaded wares backpack, sly grin', style:'storybook', mood:'gritty', model:'chatgpt' } },
    { id: 'haunted-tavern', type: 'scene', badge: 'Scene', name: 'Haunted Tavern', route: '/dnd-tavern-scene-prompt',
      excerpt: 'wide haunted tavern interior, overturned chairs, ghostly candlelight, fog…',
      fill: { type:'scene', race:'Haunted tavern', klass:'', desc:'overturned chairs, flickering ghostly candlelight, creeping fog, abandoned hearth', style:'grimdark', mood:'menacing', model:'midjourney', palette:'desaturated teal and amber' } },
  ];

  window.FORGE = { TYPES, MODELS, STYLES, MOODS, build, examples };
})();
