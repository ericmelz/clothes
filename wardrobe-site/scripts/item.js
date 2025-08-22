import { qs, getJSON, getParam, imageFallback, loadNotesMap, saveNotesMap } from "./utils.js";

const titleEl = qs("#title");
const categoryEl = qs("#category");
const filenameEl = qs("#filename");
const notesEl = qs("#notes");
const notesEditEl = qs("#notes-edit");
const imgEl = qs("#image");
const prevEl = qs("#prev");
const nextEl = qs("#next");

let ITEMS = [];
let NOTES = loadNotesMap();
let currentIndex = -1;

init();

async function init(){
  const data = await getJSON("data/items.json");
  ITEMS = (data.items || []).map((it, i) => ({...it, index: i, slug: it.id || `${(it.category||'').toLowerCase()}-${(it.filename||'').toLowerCase()}`}));

  const slug = getParam("id");
  const idx = ITEMS.findIndex(i => i.slug === slug);
  currentIndex = idx >= 0 ? idx : 0;
  render();
  attachEvents();
}

function render(){
  const it = ITEMS[currentIndex];
  const override = NOTES[it.slug];
  const notes = override?.notes ?? it.notes ?? "";

  titleEl.textContent = it.title || it.filename || it.slug;
  categoryEl.textContent = it.category || "Uncategorized";
  filenameEl.textContent = it.filename || "";
  notesEl.textContent = notes;
  notesEditEl.value = notes;

  imgEl.src = it.src || "assets/placeholder.svg";
  imgEl.alt = it.title || it.filename || it.slug;
  imageFallback(imgEl);

  const prevIdx = (currentIndex - 1 + ITEMS.length) % ITEMS.length;
  const nextIdx = (currentIndex + 1) % ITEMS.length;
  prevEl.href = `item.html?id=${encodeURIComponent(ITEMS[prevIdx].slug)}`;
  nextEl.href = `item.html?id=${encodeURIComponent(ITEMS[nextIdx].slug)}`;
}

function attachEvents(){
  qs("#save-notes").addEventListener("click", () => {
    const it = ITEMS[currentIndex];
    NOTES[it.slug] = { notes: notesEditEl.value };
    saveNotesMap(NOTES);
    render();
  });
  qs("#reset-notes").addEventListener("click", () => {
    const it = ITEMS[currentIndex];
    delete NOTES[it.slug];
    saveNotesMap(NOTES);
    render();
  });
}
