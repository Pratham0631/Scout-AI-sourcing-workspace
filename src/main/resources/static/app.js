const state = {
  sessionId: null,
  query: "",
  filters: null,
  rubric: null,
  results: [],
  filteredCount: 0,
  frozen: false,
  lastAction: null
};

const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));

function setLoading(show, title="Thinking…", text="Turning the brief into a recruiter-ready search.") {
  $("loading").classList.toggle("hidden", !show);
  $("loadingTitle").textContent = title;
  $("loadingText").textContent = text;
}
function setError(message, retry=true) {
  const el=$("errorBanner");
  el.classList.toggle("hidden", !message);
  el.innerHTML = message ? `<span>${esc(message)}</span>${retry ? '<button class="retry" id="retryBtn">Retry</button>' : ''}` : "";
  if (retry && message) $("retryBtn").onclick = () => {
    if (state.lastAction) state.lastAction();
  };
}
function addChat(text, who="assistant") {
  const el=document.createElement("div");
  el.className=`chat-message ${who}`;
  el.textContent=text;
  $("chatMessages").appendChild(el);
  $("chatMessages").scrollTop=$("chatMessages").scrollHeight;
}
function initials(name){return name.split(" ").map(x=>x[0]).slice(0,2).join("").toUpperCase()}

async function api(url, options={}) {
  const res=await fetch(url,{headers:{"Content-Type":"application/json"},...options});
  const body=await res.json().catch(()=>({error:"The server returned an unreadable response."}));
  if(!res.ok) throw new Error(body.error || "Request failed.");
  return body;
}

function setFrozenUi(frozen) {
  state.frozen = frozen;
  ["saveFilters","saveRubric","refineBtn","freezeBtn","feedback"].forEach(id => {
    const el = $(id);
    if (el) el.disabled = frozen;
  });
  document.querySelectorAll(".feedback-quick button, .company-checks input, .filter-input, [data-rubric-name], [data-rubric-desc], [data-rubric-weight], .vote")
    .forEach(el => { el.disabled = frozen; });
  if (frozen) {
    $("sessionBadge").textContent = "FROZEN";
    $("feedback").placeholder = "Search is frozen. Start a new search to continue refining.";
  }
}

function renderFilters() {
  const f=state.filters || {skills:[], companyTypes:[], minYearsExperience:null, maxYearsExperience:null, location:null};
  $("filters").innerHTML=`
    <div class="filter-card">
      <div class="filter-label">Skills · all required</div>
      <input id="skillsInput" class="filter-input" value="${esc((f.skills||[]).join(", "))}" placeholder="e.g. AWS RDS, PostgreSQL" ${state.frozen?"disabled":""}>
    </div>
    <div class="filter-card">
      <div class="filter-label">Experience · years</div>
      <div class="years">
        <input id="minExp" class="filter-input" type="number" min="0" max="50" value="${f.minYearsExperience ?? ""}" placeholder="Min" ${state.frozen?"disabled":""}>
        <input id="maxExp" class="filter-input" type="number" min="0" max="50" value="${f.maxYearsExperience ?? ""}" placeholder="Max" ${state.frozen?"disabled":""}>
      </div>
    </div>
    <div class="filter-card">
      <div class="filter-label">Location</div>
      <input id="locationInput" class="filter-input" value="${esc(f.location ?? "")}" placeholder="Any location" ${state.frozen?"disabled":""}>
    </div>
    <div class="filter-card">
      <div class="filter-label">Company background · any</div>
      <div class="company-checks">
        ${["startup","scaleup","enterprise","agency"].map(t=>`<label><input type="checkbox" value="${t}" ${(f.companyTypes||[]).includes(t)?"checked":""} ${state.frozen?"disabled":""}> ${t}</label>`).join("")}
      </div>
    </div>`;
}
function readFilters(){
  const skillText=$("skillsInput").value;
  state.filters={
    skills:skillText.split(",").map(s=>s.trim()).filter(Boolean),
    minYearsExperience:$("minExp").value===""?null:Number($("minExp").value),
    maxYearsExperience:$("maxExp").value===""?null:Number($("maxExp").value),
    location:$("locationInput").value.trim() || null,
    companyTypes:[...document.querySelectorAll(".company-checks input:checked")].map(x=>x.value)
  };
}
function renderRubric(){
  if (!state.rubric?.criteria?.length) {
    $("rubric").innerHTML = `<p class="muted">No rubric yet.</p>`;
    return;
  }
  $("rubric").innerHTML=state.rubric.criteria.map((c,i)=>`
    <div class="rubric-item">
      <input data-rubric-name="${i}" value="${esc(c.name)}" ${state.frozen?"disabled":""}>
      <textarea data-rubric-desc="${i}" rows="2" ${state.frozen?"disabled":""}>${esc(c.description)}</textarea>
      <div class="weight-row"><span>Weight</span><input data-rubric-weight="${i}" type="number" min="1" max="100" value="${c.weight}" ${state.frozen?"disabled":""}>%</div>
    </div>`).join("");
}
function readRubric(){
  state.rubric={criteria:state.rubric.criteria.map((c,i)=>({
    name:document.querySelector(`[data-rubric-name="${i}"]`).value.trim(),
    description:document.querySelector(`[data-rubric-desc="${i}"]`).value.trim(),
    weight:Number(document.querySelector(`[data-rubric-weight="${i}"]`).value)
  }))};
}
function renderCandidates(){
  const container=$("candidates");
  $("emptyState").classList.toggle("hidden",state.results.length!==0 || state.filteredCount!==0);
  container.innerHTML=state.results.map((r,i)=>{
    const p=r.profile;
    const facts=[`${p.years_experience} yrs`,p.location,p.current_company, p.current_company_type];
    return `<article class="candidate">
      <div class="candidate-top">
        <div class="identity"><div class="avatar">${initials(p.name)}</div><div><h3>${esc(p.name)}</h3><p>${esc(p.current_title)} · ${esc(p.current_company)}</p></div></div>
        <div class="score">${r.score}/100</div>
      </div>
      <div class="candidate-facts">${facts.map(x=>`<span class="fact">${esc(x)}</span>`).join("")}</div>
      <p class="explanation">${esc(r.explanation)}</p>
      <div class="evidence">${(r.evidence||[]).map(x=>`<span>${esc(x)}</span>`).join("")}</div>
      <div class="candidate-actions">
        <button class="vote" data-vote="${i}" data-value="not a match" ${state.frozen?"disabled":""}>× Not a match</button>
        <button class="vote" data-vote="${i}" data-value="is a strong match" ${state.frozen?"disabled":""}>✓ Strong match</button>
      </div>
    </article>`;
  }).join("");
  document.querySelectorAll("[data-vote]").forEach(btn=>btn.onclick=()=>{
    if (state.frozen) return;
    const i=Number(btn.dataset.vote);
    const p=state.results[i].profile;
    $("feedback").value += ($("feedback").value ? " " : "") + `${i+1} (${p.name}) ${btn.dataset.value}.`;
    $("feedback").focus();
  });
  $("resultsMeta").textContent=`${state.results.length} shown · ${state.filteredCount} pass hard filters`;
  $("filteredCount").textContent=state.filteredCount;
}
function renderAll(){
  renderFilters(); renderRubric(); renderCandidates();
  if (state.frozen) setFrozenUi(true);
}
function showWorkspace(){
  $("startView").classList.add("hidden");
  $("workspace").classList.remove("hidden");
  $("sessionBadge").classList.remove("hidden");
  $("briefText").textContent=state.query;
}
function changesBanner(changes){
  if(!changes?.length){$("changeBanner").classList.add("hidden");return;}
  $("changeBanner").classList.remove("hidden");
  $("changeBanner").innerHTML=`<strong>Search refined</strong><div class="change-list">${changes.map(c=>`<div>• <b>${esc(c.field)}</b>: ${esc(c.before)} → ${esc(c.after)} <span>— ${esc(c.reason)}</span></div>`).join("")}</div>`;
}
async function startSearch(){
  const query=$("query").value.trim();
  if(!query) return;
  state.query=query; state.lastAction=startSearch; setError(null); setLoading(true);
  $("searchBtn").disabled=true;
  try{
    const data=await api("/api/search",{method:"POST",body:JSON.stringify({query})});
    if (!data.filters || !data.rubric) {
      throw new Error(data.error || "Search completed without filters or rubric. Please retry.");
    }
    state.sessionId=data.sessionId; state.filters=data.filters; state.rubric=data.rubric;
    state.results=data.results||[]; state.filteredCount=data.filteredCount||0;
    state.frozen=false;
    showWorkspace(); renderAll();
    if (state.filteredCount === 0) {
      addChat("No profiles passed the hard filters. Loosen skills, experience, location, or company background, then Apply — or tell me what to change.");
    } else {
      addChat("I found the first shortlist. Review the evidence and tell me what I got wrong or right.");
    }
  }catch(e){setError(e.message)}
  finally{setLoading(false);$("searchBtn").disabled=false}
}
async function applyEdits(){
  if(!state.sessionId || state.frozen)return;
  readFilters(); readRubric(); state.lastAction=applyEdits; setError(null); setLoading(true,"Re-ranking…","Applying your edited filters and rubric to the local talent pool, then scoring survivors.");
  try{
    const data=await api(`/api/sessions/${state.sessionId}/edit`,{method:"POST",body:JSON.stringify({filters:state.filters,rubric:state.rubric})});
    state.filters=data.filters; state.rubric=data.rubric; state.results=data.results; state.filteredCount=data.filteredCount;
    renderAll(); addChat("Applied your edits and re-ranked the shortlist.");
  }catch(e){setError(e.message)}
  finally{setLoading(false)}
}
async function refine(){
  if(state.frozen)return;
  const feedback=$("feedback").value.trim();
  if(!feedback)return;

  state.lastAction=refine;
  setError(null);
  setLoading(
      true,
      "Learning from your feedback…",
      "Updating the search, then re-running the shortlist."
  );

  addChat(feedback,"user");
  $("feedback").value="";

  try{
    const data=await api(
        `/api/sessions/${state.sessionId}/refine`,
        {
          method:"POST",
          body:JSON.stringify({
            filters: state.filters,
            rubric: state.rubric,
            shownProfiles: state.results,
            feedback: feedback
          })
        }
    );

    state.filters=data.filters;
    state.rubric=data.rubric;
    state.results=data.results;
    state.filteredCount=data.filteredCount;

    renderAll();
    changesBanner(data.changes);

    if(data.changes?.length)
      addChat(data.changes.map(c=>`${c.field}: ${c.reason}`).join(" "));
    else
      addChat("I re-ran the search, but the feedback did not require a filter or rubric change.");

  }catch(e){
    setError(e.message);
    addChat("I couldn't safely apply that refinement. Nothing was changed; retry when the LLM is available.");
  }finally{
    setLoading(false);
  }
}
async function freeze(){
  if(!state.sessionId || state.frozen)return;
  setError(null); setLoading(true,"Freezing…","Creating the final recruiter-ready snapshot.");
  try{
    const data=await api(`/api/sessions/${state.sessionId}/freeze`,{method:"POST"});
    setFrozenUi(true);
    renderAll();
    renderFrozen(data);
    $("freezeModal").classList.remove("hidden");
    addChat("Search frozen. Filters and rubric are locked.");
  }catch(e){setError(e.message)}
  finally{setLoading(false)}
}
function renderFrozen(data){
  const f=data.filters, r=data.rubric;
  $("frozenSummary").innerHTML=`
    <div class="frozen-grid">
      <div class="frozen-box"><h4>FINAL FILTERS</h4>
        <p><b>Skills:</b> ${esc((f.skills||[]).join(", ")||"Any")}</p>
        <p><b>Experience:</b> ${f.minYearsExperience??"Any"}–${f.maxYearsExperience??"Any"} years</p>
        <p><b>Location:</b> ${esc(f.location||"Any")}</p>
        <p><b>Company:</b> ${esc((f.companyTypes||[]).join(", ")||"Any")}</p>
      </div>
      <div class="frozen-box"><h4>FINAL RUBRIC</h4>
        ${(r.criteria||[]).map(c=>`<p><b>${esc(c.name)}</b> · ${c.weight}% — ${esc(c.description)}</p>`).join("")}
      </div>
    </div>
    <div class="frozen-box"><h4>RANKED SHORTLIST</h4>
      ${(data.finalShortlist||[]).map((x,i)=>`<div class="frozen-candidate"><strong>${i+1}. ${esc(x.profile.name)}</strong><span>${x.score}/100</span></div>`).join("")}
    </div>`;
}
document.querySelectorAll("[data-example]").forEach(b=>b.onclick=()=>{$("query").value=b.dataset.example;$("query").focus()});
document.querySelectorAll("[data-feedback]").forEach(b=>b.onclick=()=>{
  if (state.frozen) return;
  const phrase = b.dataset.feedback;
  const prefix = $("feedback").value ? " " : "";
  $("feedback").value += `${prefix}The shortlist ${phrase}.`;
  $("feedback").focus();
});
$("searchBtn").onclick=startSearch;
$("refineBtn").onclick=refine;
$("saveFilters").onclick=applyEdits;
$("saveRubric").onclick=applyEdits;
$("freezeBtn").onclick=freeze;
$("closeModal").onclick=()=>{$("freezeModal").classList.add("hidden")};
$("doneBtn").onclick=()=>{$("freezeModal").classList.add("hidden")};
$("newSearch").onclick=()=>location.reload();
$("feedback").addEventListener("keydown",e=>{if((e.metaKey||e.ctrlKey)&&e.key==="Enter")refine()});
document.addEventListener("keydown",e=>{if(e.key==="Escape")$("freezeModal").classList.add("hidden")});
