// utils.js (ES modules)
export function qs(sel, el=document){ return el.querySelector(sel); }
export function qsa(sel, el=document){ return [...el.querySelectorAll(sel)]; }

export function getJSON(path){
  return fetch(path, {cache: "no-store"}).then(r=>{
    if(!r.ok) throw new Error(`Failed to load ${path}`);
    return r.json();
  });
}

export function slugify(str){
  return String(str).toLowerCase()
    .replace(/[^a-z0-9]+/g,'-')
    .replace(/(^-|-$)+/g,'');
}

export function getParam(name){
  const url = new URL(window.location.href);
  return url.searchParams.get(name);
}

export function downloadJSON(obj, filename="notes.json"){
  const blob = new Blob([JSON.stringify(obj, null, 2)], {type: "application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

export function imageFallback(el){
  el.addEventListener("error", () => {
    el.src = "assets/placeholder.svg";
    el.classList.add("img-missing");
  }, {once:true});
}

// Notes stored per item slug in localStorage
const NOTES_KEY = "wardrobeNotesV1";
export function loadNotesMap(){
  try{
    const raw = localStorage.getItem(NOTES_KEY);
    return raw ? JSON.parse(raw) : {};
  }catch(e){ return {}; }
}
export function saveNotesMap(map){
  localStorage.setItem(NOTES_KEY, JSON.stringify(map));
}
