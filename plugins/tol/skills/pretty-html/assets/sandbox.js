// Playable-sandbox kit for /pretty-html reports. Paste into a <script> and call the pieces you need.

// Fixed-step loop: the simulation always steps at `dt` (match the game's physics rate), whatever the
// frame rate. `step()` runs only while `active()` is true (the canvas has focus); `draw()` every frame.
function runLoop({ dt, step, draw, active }) {
  let acc = 0, last = performance.now();
  function frame(now) {
    const f = Math.min(0.1, (now - last) / 1000); last = now; acc += f;
    if (active()) while (acc >= dt) { step(); acc -= dt; } else acc = 0;
    draw(f); requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

// Keyboard on one focusable element (give the canvas tabindex="0"). held[code] while down,
// pressed[code] true for one step after the press (call keys.consume() at the end of step()).
// Keys in `capture` don't scroll the page; everything is released on blur so keys never stick.
function keyInput(el, capture = ['Space', 'ShiftLeft', 'ShiftRight', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']) {
  const k = { held: {}, pressed: {}, consume() { this.pressed = {}; } };
  el.addEventListener('keydown', e => { if (capture.includes(e.code)) e.preventDefault(); if (!k.held[e.code]) k.pressed[e.code] = true; k.held[e.code] = true; });
  el.addEventListener('keyup', e => { k.held[e.code] = false; });
  el.addEventListener('blur', () => { k.held = {}; k.pressed = {}; });
  return k;
}

// Mouse position in canvas pixels, correct when CSS scales the canvas.
function pointer(cv) {
  const p = { x: cv.width / 2, y: cv.height / 2 };
  cv.addEventListener('mousemove', e => { const r = cv.getBoundingClientRect(); p.x = (e.clientX - r.left) / r.width * cv.width; p.y = (e.clientY - r.top) / r.height * cv.height; });
  return p;
}

// Full screen: the canvas takes the monitor's real pixels, so a camera that copies the game's
// framing (e.g. world units of screen height) looks as it does in the game. Scale HUD text by H / 720.
// CSS needed: canvas:fullscreen { width:100vw; height:100vh; aspect-ratio:auto; }
function fullscreenButton(btn, cv, base = [1280, 720]) {
  btn.onclick = () => { cv.requestFullscreen && cv.requestFullscreen(); cv.focus(); };
  document.addEventListener('fullscreenchange', () => {
    const on = document.fullscreenElement === cv, d = window.devicePixelRatio || 1;
    cv.width = on ? Math.round(innerWidth * d) : base[0]; cv.height = on ? Math.round(innerHeight * d) : base[1]; cv.focus();
  });
}

// Tunable values: defaults per id, the operator's edits on top, kept in localStorage.
// Bump the key's version when the shape of the values changes, or old edits leak into new ones.
function tuning(storeKey, defaults) {
  let edits; try { edits = JSON.parse(localStorage.getItem(storeKey) || '{}'); } catch (e) { edits = {}; }
  const save = () => localStorage.setItem(storeKey, JSON.stringify(edits));
  return {
    get: id => ({ ...defaults[id], ...(edits[id] || {}) }),
    set(id, key, v) { edits[id] = { ...(edits[id] || {}), [key]: v }; save(); },
    reset(id) { delete edits[id]; save(); },
    // every id's live values, for the operator to paste back
    exportJson() { const o = {}; for (const id in defaults) o[id] = this.get(id); return JSON.stringify(o, null, 1); },
  };
}

// Slider and dropdown rows (grid: label | control | value).
function slider(parent, label, min, max, step, val, onSet) {
  const l = document.createElement('label');
  l.innerHTML = `<span>${label}</span><input type="range" min="${min}" max="${max}" step="${step}" value="${val}"><output>${val}</output>`;
  const inp = l.querySelector('input'), out = l.querySelector('output');
  inp.oninput = () => { out.textContent = inp.value; onSet(+inp.value); };
  parent.appendChild(l);
}
function choice(parent, label, opts, val, onSet) {
  const l = document.createElement('label');
  l.innerHTML = `<span>${label}</span><select>${opts.map(([v, t]) => `<option value="${v}" ${String(v) === String(val) ? 'selected' : ''}>${t}</option>`).join('')}</select>`;
  l.querySelector('select').onchange = e => onSet(e.target.value);
  parent.appendChild(l);
}

// Seeded random, so a generated arena is the same on every load and every lap time is comparable.
function seeded(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// Headless self-test: open the page with #selftest, drive step() with scripted input, and publish the
// results in document.title. Read them with:
//   chrome --headless=new --disable-gpu --virtual-time-budget=4000 --dump-dom "file:///…/page.html#selftest"
function selfTest(run) {
  if (location.hash !== '#selftest') return;
  try { document.title = 'SELFTEST ' + run().join(' | '); } catch (e) { document.title = 'SELFTEST FAILED ' + e; }
}
