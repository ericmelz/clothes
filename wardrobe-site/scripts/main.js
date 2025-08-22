import { qs, getJSON, slugify, downloadJSON, imageFallback, loadNotesMap } from "./utils.js";

const grid = qs("#grid");
const searchEl = qs("#search");
const categoryEl = qs("#category");
const sortEl = qs("#sort");
const exportBtn = qs("#export-notes");
const importInput = document.querySelector("#import-notes");

let ITEMS = [];
let NOTES = loadNotesMap();

init();

async function init(){
  const data = await getJSON("data/items.json");
  ITEMS = (data.items || []).map(it => ({...it, slug: it.id || slugify(`${it.category}-${it.filename}`)}));
  hydrateCategories();
  render();
  attachEvents();
}

function hydrateCategories(){
  const set = new Set(ITEMS.map(i => i.category).filter(Boolean));
  const opts = [...set].sort().map(cat => {
    const op = document.createElement("option");
    op.value = cat; op.textContent = cat;
    return op;
  });
  opts.forEach(op => categoryEl.appendChild(op));
}

function attachEvents(){
  searchEl.addEventListener("input", render);
  categoryEl.addEventListener("change", render);
  sortEl.addEventListener("change", render);
  exportBtn.addEventListener("click", () => {
    downloadJSON(NOTES, "wardrobe-notes.json");
  });
  importInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if(!file) return;
    const text = await file.text();
    try{
      const incoming = JSON.parse(text);
      if(typeof incoming === "object" && !Array.isArray(incoming)){
        const merged = {...NOTES, ...incoming};
        localStorage.setItem("wardrobeNotesV1", JSON.stringify(merged));
        NOTES = merged;
        render();
        alert("Notes imported and merged.");
      }else{
        alert("Invalid JSON format.");
      }
    }catch(err){
      alert("Could not parse JSON.");
    }finally{
      importInput.value = "";
    }
  });
}

function render(){
  const q = searchEl.value.trim().toLowerCase();
  const cat = categoryEl.value;
  const sort = sortEl.value;

  let list = ITEMS.map(it => {
    const override = NOTES[it.slug];
    const notes = override?.notes ?? it.notes ?? "";
    return {...it, effectiveNotes: notes};
  });

  if(cat){
    list = list.filter(i => i.category === cat);
  }
  if(q){
    list = list.filter(i => {
      const hay = `${i.title||""} ${i.effectiveNotes||""} ${i.filename||""}`.toLowerCase();
      return hay.includes(q);
    });
  }

  list.sort((a,b) => {
    const [field, dir] = sort.split("-");
    let av = field === "title" ? (a.title||"") : (a.category||"");
    let bv = field === "title" ? (b.title||"") : (b.category||"");
    const cmp = av.localeCompare(bv, undefined, {sensitivity:"base"});
    return dir === "asc" ? cmp : -cmp;
  });

  grid.innerHTML = "";
  const tpl = document.querySelector("#card-tpl");
  list.forEach(it => {
    const a = tpl.content.firstElementChild.cloneNode(true);
    const img = a.querySelector("img.thumb");
    const title = a.querySelector(".title");
    const sub = a.querySelector(".sub");
    a.href = `item.html?id=${encodeURIComponent(it.slug)}`;
    img.src = it.thumb || it.src || "assets/placeholder.svg";
    img.alt = it.title || it.filename || it.slug;
    imageFallback(img);
    title.textContent = it.title || it.filename;
    sub.textContent = `${it.category || "Uncategorized"}` + (it.effectiveNotes ? ` • ${it.effectiveNotes}` : "");
    grid.appendChild(a);
  });
}
