// annotation layer: hover a block, press "+", write a note; notes live in localStorage until exported
(() => {
  const KEY = "notes:" + location.pathname;
  const BLOCKS = "main h2, main h3, main p, main li, main tr, main pre, main .stat, main .callout";
  const notes = JSON.parse(localStorage.getItem(KEY) || "{}");
  const save = () => { localStorage.setItem(KEY, JSON.stringify(notes)); count.textContent = Object.keys(notes).length; };
  const css = document.createElement("style");
  css.textContent = `.an-host{position:relative}.an-add{position:absolute;left:-26px;top:2px;width:20px;height:20px;border-radius:50%;
    border:1px solid var(--line);background:var(--raise);color:var(--accent);font:14px/18px sans-serif;text-align:center;cursor:pointer;opacity:0}
    .an-host:hover>.an-add{opacity:1}.an-note{margin:6px 0 10px;padding:6px 10px;border-left:3px solid var(--you);background:#1d1830;border-radius:0 6px 6px 0}
    .an-note textarea{width:100%;min-height:60px;background:#0b0d10;color:var(--text);border:1px solid var(--line);border-radius:4px;font:inherit;padding:6px}
    .an-note button,.an-bar button{font:12px sans-serif;margin:4px 6px 0 0;padding:3px 10px;border-radius:4px;border:1px solid var(--line);background:#0b0d10;color:var(--text);cursor:pointer}
    .an-bar{position:fixed;top:10px;right:12px;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:6px 10px;font:12px sans-serif;color:var(--dim);z-index:9}
    td.an-host .an-add{left:-22px}`;
  document.head.appendChild(css);
  const bar = document.createElement("div");
  bar.className = "an-bar";
  bar.innerHTML = `Notes: <b class="acc">0</b> <button>Export</button>`;
  document.body.appendChild(bar);
  const count = bar.querySelector("b");

  const blocks = [...document.querySelectorAll(BLOCKS)];
  const excerpt = el => el.innerText.replace(/\s+/g, " ").trim().slice(0, 140);

  function render(el, id) {
    el.parentNode.querySelectorAll(`[data-an="${id}"]`).forEach(n => n.remove());
    if (!notes[id]) return;
    const box = document.createElement(el.tagName === "TR" ? "tr" : el.tagName === "LI" ? "li" : "div");
    box.dataset.an = id;
    const inner = el.tagName === "TR" ? `<td colspan="99"><div class="an-note"></div></td>` : `<div class="an-note"></div>`;
    box.innerHTML = inner;
    if (el.tagName === "LI") box.style.listStyle = "none";
    const n = box.querySelector(".an-note");
    n.innerHTML = `<div></div><button data-e>Edit</button><button data-d>Delete</button>`;
    n.firstChild.textContent = notes[id].note;
    n.querySelector("[data-e]").onclick = () => edit(el, id);
    n.querySelector("[data-d]").onclick = () => { delete notes[id]; save(); render(el, id); };
    el.after(box);
  }

  function edit(el, id) {
    el.parentNode.querySelectorAll(`[data-an="${id}"]`).forEach(n => n.remove());
    const box = document.createElement(el.tagName === "TR" ? "tr" : "div");
    box.dataset.an = id;
    box.innerHTML = el.tagName === "TR" ? `<td colspan="99"><div class="an-note"></div></td>` : `<div class="an-note"></div>`;
    const n = box.querySelector(".an-note");
    n.innerHTML = `<textarea></textarea><button data-s>Save</button><button data-c>Cancel</button>`;
    const ta = n.querySelector("textarea");
    ta.value = notes[id]?.note || "";
    n.querySelector("[data-s]").onclick = () => {
      if (ta.value.trim()) notes[id] = { block: id, excerpt: excerpt(el), note: ta.value.trim(), at: new Date().toISOString() };
      else delete notes[id];
      save(); render(el, id);
    };
    n.querySelector("[data-c]").onclick = () => render(el, id);
    el.after(box);
    ta.focus();
  }

  blocks.forEach((el, i) => {
    const id = "b" + i;
    const host = el.tagName === "TR" ? el.firstElementChild : el;
    if (!host) return;
    host.classList.add("an-host");
    const add = document.createElement("span");
    add.className = "an-add";
    add.textContent = "+";
    add.title = "Add a note";
    add.onclick = e => { e.stopPropagation(); edit(el, id); };
    host.prepend(add);
    render(el, id);
  });

  bar.querySelector("button").onclick = () => {
    const list = Object.values(notes);
    const md = `# Notes on ${document.title}\n\n` + list.map(n => `> ${n.excerpt}\n\n${n.note}\n`).join("\n");
    navigator.clipboard?.writeText(md).catch(() => {});
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify({ page: location.href, notes: list }, null, 1)], { type: "application/json" }));
    a.download = location.pathname.split("/").pop().replace(/\.html?$/, "") + ".notes.json";
    a.click();
  };
  save();
})();
