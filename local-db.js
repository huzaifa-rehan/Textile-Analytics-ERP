/* local-db.js — stand-in for the hosted claude.use("db") / claude.use("downloads")
   so the app runs on any static host (GitHub Pages) or from `python -m http.server`.
   Storage: IndexedDB in the visitor's own browser. Nothing leaves the machine.
   First run seeds from sample-data/demo-db.json. "Reset demo data" = clear site data. */
(function(){
  if(window.claude&&window.claude.use)return;           // hosted runtime present: do nothing
  const DB="yarn-dispatch-desk-demo",ST="docs";
  const open=()=>new Promise((res,rej)=>{const r=indexedDB.open(DB,1);
    r.onupgradeneeded=()=>r.result.createObjectStore(ST);
    r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);});
  const tx=(db,mode,fn)=>new Promise((res,rej)=>{const t=db.transaction(ST,mode);const st=t.objectStore(ST);
    const out=fn(st);t.oncomplete=()=>res(out&&out.result!==undefined?out.result:undefined);t.onerror=()=>rej(t.error);});
  async function makeDb(){
    const idb=await open();
    const all=await new Promise((res,rej)=>{const o={};const c=idb.transaction(ST).objectStore(ST).openCursor();
      c.onsuccess=e=>{const k=e.target.result;if(k){o[k.key]=k.value;k.continue();}else res(o);};c.onerror=()=>rej(c.error);});
    let docs=all;
    if(!Object.keys(docs).length){
      try{const r=await fetch("sample-data/demo-db.json",{cache:"no-store"});
        const j=await r.json();docs=j.docs||{};
        await tx(idb,"readwrite",st=>{Object.keys(docs).forEach(k=>st.put(docs[k],k));});
      }catch(e){console.warn("No demo data found — starting empty",e);}
    }
    const snap=(id,v)=>({id,exists:v!==undefined,data:()=>v===undefined?undefined:JSON.parse(JSON.stringify(v))});
    return{
      doc:path=>({
        get:async()=>snap(path.split("/").pop(),docs[path]),
        set:async v=>{docs[path]=JSON.parse(JSON.stringify(v));await tx(idb,"readwrite",st=>st.put(docs[path],path));},
        delete:async()=>{delete docs[path];await tx(idb,"readwrite",st=>st.delete(path));}
      }),
      collection:name=>({get:async()=>({docs:Object.keys(docs).filter(k=>k.startsWith(name+"/"))
        .map(k=>snap(k.slice(name.length+1),docs[k]))})})
    };
  }
  const downloads={save:async({filename,data})=>{
    const b=data instanceof Blob?data:new Blob([data],{type:/\.html?$/.test(filename)?"text/html":"text/plain"});
    const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download=filename;
    document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},500);}};
  window.claude={use:async n=>n==="db"?makeDb():n==="downloads"?downloads:null};
})();
