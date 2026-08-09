const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];
let teams = [], teamById = {}, simulations = [], current = null, activeTab = "overview";
const statusIndex = {setup:0, qualified:1, drawn:2, completed:3};

function esc(v=""){return String(v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function t(id){ return teamById[id] || {name:id,code:"???",confederation:"",fifaRank:null,rankingLabel:"NR"}; }
function rankLabel(id){ return t(id).fifaRank ? `#${t(id).fifaRank}` : "NR"; }
function teamPill(id){
  const x=t(id); return `<span class="team-pill ${x.fifaRank?'':'nr'}"><span class="rank">${rankLabel(id)}</span>${esc(x.name)}</span>`;
}
function showToast(msg, error=false){
  const el=$("#toast"); el.textContent=msg; el.className=`toast show ${error?"error":""}`;
  clearTimeout(window._toast); window._toast=setTimeout(()=>el.className="toast",2800);
}
async function api(url, opts={}){
  const res=await fetch(url,{headers:{"Content-Type":"application/json"},...opts});
  const data=await res.json().catch(()=>({}));
  if(!res.ok) throw new Error(data.error||`Request failed (${res.status})`);
  return data;
}
async function refreshList(){
  const data=await api("/api/simulations"); simulations=data.simulations; renderSimList();
}
function renderSimList(){
  const box=$("#simList");
  if(!simulations.length){box.innerHTML=`<p class="rail-empty">No saved tournaments yet. Create one and every qualifier, draw and match result will be kept here.</p>`;return}
  box.innerHTML=simulations.map(s=>`
    <button class="sim-item ${current?.id===s.id?"active":""}" data-id="${s.id}">
      <b>${esc(s.name)}</b><span><i>${esc(s.hostName)} · ${s.year}</i><i>${s.status}</i></span>
    </button>`).join("");
  $$(".sim-item",box).forEach(b=>b.onclick=()=>openSimulation(b.dataset.id));
}
async function openSimulation(id){
  try{
    current=await api(`/api/simulations/${id}`); activeTab="overview";
    $("#welcome").classList.add("hidden"); $("#workspace").classList.remove("hidden");
    renderWorkspace(); renderSimList();
  }catch(e){showToast(e.message,true)}
}
function openNew(){
  const d=$("#newDialog"); $("#nameInput").value=`World Cup ${new Date().getFullYear()+4}`;
  $("#yearInput").value=Math.max(2030,new Date().getFullYear()+4); $("#hostInput").value=""; d.showModal();
}
async function createSimulation(e){
  e.preventDefault();
  const hostName=$("#hostInput").value.trim().toLowerCase();
  const host=teams.find(x=>x.name.toLowerCase()===hostName);
  if(!host){showToast("Choose a host from the team list.",true);return}
  try{
    document.body.classList.add("busy");
    current=await api("/api/simulations",{method:"POST",body:JSON.stringify({
      name:$("#nameInput").value.trim(),year:Number($("#yearInput").value),hostId:host.id
    })});
    $("#newDialog").close(); activeTab="overview"; await refreshList();
    $("#welcome").classList.add("hidden"); $("#workspace").classList.remove("hidden"); renderWorkspace();
    showToast("Tournament created and saved.");
  }catch(e){showToast(e.message,true)}finally{document.body.classList.remove("busy")}
}
function renderWorkspace(){
  if(!current)return;
  $("#simTitle").textContent=current.name;
  $("#simMeta").textContent=`${current.year} EDITION // HOST: ${t(current.hostId).name}`;
  $("#statusBadge").textContent=current.status.toUpperCase();
  $$("#tabs button").forEach(b=>b.classList.toggle("active",b.dataset.tab===activeTab));
  renderTab();
}
function renderTab(){
  const box=$("#tabContent");
  if(activeTab==="overview") box.innerHTML=overviewHTML();
  if(activeTab==="qualifiers") box.innerHTML=qualifiersHTML();
  if(activeTab==="draw") box.innerHTML=drawHTML();
  if(activeTab==="finals") box.innerHTML=finalsHTML();
  wireDynamic();
}
function resultCount(){
  if(!current)return 0;
  let n=(current.qualifiers?.matches?.length||0)+(current.qualifiers?.intercontinental?.matches?.length||0);
  n+=(current.tournament?.groupMatches?.length||0);
  (current.tournament?.knockoutRounds||[]).forEach(r=>n+=r.matches.length);
  if(current.tournament?.thirdPlaceMatch)n++;
  return n;
}
function overviewHTML(){
  const host=t(current.hostId), finalists=current.finalTeams?.length||0;
  const steps=[
    ["SETUP","Host locked",0],["QUALIFIERS","46 direct + 2 playoff",1],
    ["DRAW","4 pots · 12 groups",2],["FINALS","Group stage to trophy",3]
  ];
  return `
    <div class="stat-grid">
      <div class="stat"><span>HOST</span><b>${esc(host.name)}</b><small>${host.confederation} · ${rankLabel(host.id)}</small></div>
      <div class="stat"><span>FIELD</span><b>${finalists || "—"} / 48</b><small>${finalists===48?"qualification complete":"awaiting qualifiers"}</small></div>
      <div class="stat"><span>RESULTS SAVED</span><b>${resultCount()}</b><small>qualifiers + finals</small></div>
      <div class="stat"><span>SEEDING SOURCE</span><b>JUL 2026</b><small>official ranking order</small></div>
    </div>
    <div class="section">
      <div class="section-head"><h3>Competition route</h3><p>Each stage unlocks the next.</p></div>
      <div class="progress">${steps.map(([a,b,i])=>`<div class="step ${statusIndex[current.status]>i?"done":statusIndex[current.status]===i?"current":""}"><b>0${i+1} ${a}</b><span>${b}</span></div>`).join("")}</div>
      <div class="action-row">
        ${current.status==="setup"?`<button class="primary" data-action="qualifiers">SIMULATE QUALIFIERS →</button>`:""}
        ${current.status==="qualified"?`<button class="primary" data-action="draw">RUN RANDOM DRAW →</button>`:""}
        ${current.status==="drawn"?`<button class="primary" data-action="finals">SIMULATE FINAL TOURNAMENT →</button>`:""}
        ${current.status==="completed"?`<button class="primary" data-tabgo="finals">VIEW CHAMPION →</button>`:""}
        <button class="ghost" data-action="reset">RESET TO SETUP</button>
        <button class="danger-btn" data-action="delete">DELETE SAVE</button>
      </div>
    </div>
    <div class="section">
      <div class="section-head"><h3>Simulation log</h3><p>Persisted with the tournament.</p></div>
      <div class="panel timeline">${current.timeline.map(x=>`<div class="timeline-item"><b>${esc(x.label)}</b><span>${esc(x.detail)}</span></div>`).join("")}</div>
    </div>`;
}
function qualifiersHTML(){
  if(!current.qualifiers)return `
    <div class="locked"><b>Qualifiers not simulated.</b><p>Run six confederation campaigns plus the six-team intercontinental playoff. The host is already qualified.</p><button class="primary" data-action="qualifiers">SIMULATE ALL QUALIFIERS</button></div>`;
  const q=current.qualifiers;
  const confeds=Object.entries(q.confederations);
  return `
    <div class="stat-grid">
      <div class="stat"><span>QUALIFIER MATCHES</span><b>${q.matches.length}</b><small>all results saved</small></div>
      <div class="stat"><span>DIRECT QUALIFIERS</span><b>${q.directQualified.length}</b><small>including host</small></div>
      <div class="stat"><span>PLAYOFF CANDIDATES</span><b>6</b><small>two seeded to finals</small></div>
      <div class="stat"><span>FINAL FIELD</span><b>48</b><small>ready for draw</small></div>
    </div>
    <div class="section">
      <div class="section-head"><h3>Qualified by confederation</h3><p>48-team allocation with host slot consumed.</p></div>
      <div class="confed-grid">
        ${confeds.map(([c,v])=>`<div class="confed-card"><h4>${c}</h4><div class="slotline">${v.directSlots} DIRECT · ${v.playoffSlots} PLAYOFF ${v.hostSlotConsumed?"· HOST SLOT":""}</div><div class="team-list">${v.directQualified.map(teamPill).join("") || "<span class='slotline'>Host consumed the direct place.</span>"}</div></div>`).join("")}
        <div class="confed-card ic-card"><h4>INTERCONTINENTAL PLAYOFF</h4><div class="slotline">2 TICKETS WON</div><div class="team-list">${q.intercontinental.winners.map(teamPill).join("")}</div></div>
      </div>
    </div>
    <div class="section">
      <div class="section-head"><h3>Match explorer</h3><div class="match-toolbar"><select id="matchConfed">${confeds.map(([c])=>`<option value="${c}">${c}</option>`).join("")}<option value="IC">INTERCONTINENTAL</option></select></div></div>
      <div class="panel flush"><div class="table-wrap"><table class="data-table"><thead><tr><th>STAGE</th><th>HOME</th><th class="score">SCORE</th><th>AWAY</th><th>GROUP</th></tr></thead><tbody id="matchRows"></tbody></table></div></div>
    </div>`;
}
function formatScore(m){
  let s=`${m.homeGoals}–${m.awayGoals}`;
  if(m.penalties)s+=` (${m.penalties.home}–${m.penalties.away} pens)`;
  else if(m.extraTime)s+=" aet";
  return s;
}
function renderMatchRows(filter){
  if(!current.qualifiers)return;
  let matches=[];
  if(filter==="IC") matches=current.qualifiers.intercontinental.matches;
  else matches=current.qualifiers.matches.filter(m=>m.stage.startsWith(filter));
  $("#matchRows").innerHTML=matches.map(m=>`<tr><td>${esc(m.stage)}</td><td>${esc(t(m.homeId).name)}</td><td class="score">${formatScore(m)}</td><td>${esc(t(m.awayId).name)}</td><td>${m.group||"—"}</td></tr>`).join("");
}
function drawHTML(){
  if(!current.qualifiers)return `<div class="locked"><b>Draw locked.</b><p>Complete qualifying first. Exactly 48 teams are required before the pots can be formed.</p><button class="primary" data-tabgo="qualifiers">GO TO QUALIFIERS</button></div>`;
  if(!current.groups){
    const ordered=[...current.finalTeams].sort((a,b)=>(t(a).fifaRank||999)-(t(b).fifaRank||999));
    const pots=[0,1,2,3].map(i=>ordered.slice(i*12,i*12+12));
    return `<div class="section-head"><div><p class="kicker">SEEDING PREVIEW</p><h3>Four pots, ranking first.</h3></div><button class="primary" data-action="draw">RUN RANDOM DRAW →</button></div>${potsHTML(pots)}`;
  }
  return `
    <div class="section"><div class="section-head"><h3>Ranking pots</h3><p>12 teams per pot · July 20, 2026 order.</p></div>${potsHTML(current.pots.map(p=>p.teamIds))}</div>
    <div class="section"><div class="section-head"><h3>Groups A–L</h3><p>Max 2 UEFA teams; max 1 from every other confederation.</p></div>
      <div class="group-grid">${current.groups.map(g=>`<div class="group-card"><h4>GROUP ${g.group}</h4>${g.teamIds.map(id=>`<div class="group-team"><span>${esc(t(id).name)}</span><b>${rankLabel(id)} · ${t(id).confederation}</b></div>`).join("")}</div>`).join("")}</div>
    </div>
    ${current.status==="drawn"?`<div class="action-row"><button class="primary" data-action="finals">SIMULATE FINAL TOURNAMENT →</button></div>`:""}`;
}
function potsHTML(pots){
  return `<div class="pot-grid">${pots.map((p,i)=>`<div class="pot"><h4>POT ${i+1}</h4><ol>${p.map(id=>`<li><b>${esc(t(id).name)}</b><span>${rankLabel(id)} · ${t(id).confederation}</span></li>`).join("")}</ol></div>`).join("")}</div>`;
}
function finalsHTML(){
  if(!current.groups)return `<div class="locked"><b>Final tournament locked.</b><p>Complete the random draw before simulating Groups A–L and the knockout rounds.</p><button class="primary" data-tabgo="draw">GO TO DRAW</button></div>`;
  if(!current.tournament)return `
    <div class="locked"><b>The stage is set.</b><p>Simulate all 72 group matches, rank the eight best third-placed teams, then play the Round of 32 through the final.</p><button class="primary" data-action="finals">SIMULATE FINAL TOURNAMENT</button></div>`;
  const tr=current.tournament, champ=t(tr.championId);
  return `
    <div class="champion"><div><span>${current.year} WORLD CHAMPION</span><b>${esc(champ.name)}</b></div><div><span>${rankLabel(champ.id)} · ${champ.confederation}</span></div></div>
    <div class="section"><div class="section-head"><h3>Group standings</h3><p>Top two + eight best third-placed teams advance.</p></div>
      <div class="group-grid">${tr.groupTables.map(g=>`<div class="group-card"><h4>GROUP ${g.group}</h4><table class="standing"><thead><tr><th>TEAM</th><th>P</th><th>GD</th><th>PTS</th></tr></thead><tbody>${g.standings.map(r=>`<tr><td>${esc(t(r.teamId).name)}</td><td>${r.played}</td><td>${r.gd>0?"+":""}${r.gd}</td><td><b>${r.points}</b></td></tr>`).join("")}</tbody></table></div>`).join("")}</div>
    </div>
    <div class="section"><div class="section-head"><h3>Knockout bracket</h3><p>Round of 32 to the trophy.</p></div>
      <div class="knockout">${tr.knockoutRounds.map(r=>`<div class="round"><h4>${r.round.toUpperCase()}</h4><div class="fixture-grid">${r.matches.map(m=>fixtureHTML(m)).join("")}</div></div>`).join("")}
      <div class="round"><h4>THIRD-PLACE PLAYOFF</h4><div class="fixture-grid">${fixtureHTML(tr.thirdPlaceMatch)}</div></div></div>
    </div>`;
}
function fixtureHTML(m){return `<div class="fixture"><span class="home">${esc(t(m.homeId).name)}</span><strong>${formatScore(m)}</strong><span>${esc(t(m.awayId).name)}</span></div>`}
function wireDynamic(){
  $$("[data-tabgo]").forEach(b=>b.onclick=()=>{activeTab=b.dataset.tabgo;renderWorkspace()});
  $$("[data-action]").forEach(b=>b.onclick=()=>runAction(b.dataset.action));
  const mc=$("#matchConfed"); if(mc){mc.onchange=()=>renderMatchRows(mc.value);renderMatchRows(mc.value)}
}
async function runAction(action){
  if(!current)return;
  if(action==="delete"){
    if(!confirm(`Delete "${current.name}"? This removes all saved results.`))return;
    try{await api(`/api/simulations/${current.id}`,{method:"DELETE"});current=null;await refreshList();$("#workspace").classList.add("hidden");$("#welcome").classList.remove("hidden");showToast("Simulation deleted.");}catch(e){showToast(e.message,true)}
    return;
  }
  if(action==="reset"&&!confirm("Reset this tournament to setup? Saved qualifier, draw and final results will be cleared."))return;
  try{
    document.body.classList.add("busy"); $("#saveState").textContent="● UPDATING";
    current=await api(`/api/simulations/${current.id}/${action}`,{method:"POST",body:"{}"});
    if(action==="qualifiers")activeTab="qualifiers"; if(action==="draw")activeTab="draw"; if(action==="finals")activeTab="finals"; if(action==="reset")activeTab="overview";
    await refreshList(); renderWorkspace(); showToast(action==="reset"?"Tournament reset.":`${action[0].toUpperCase()+action.slice(1)} complete and saved.`);
  }catch(e){showToast(e.message,true)}finally{document.body.classList.remove("busy");$("#saveState").textContent="● SAVED"}
}
async function boot(){
  try{
    const [teamData,simData]=await Promise.all([api("/api/teams"),api("/api/simulations")]);
    teams=teamData.teams; teamById=Object.fromEntries(teams.map(x=>[x.id,x])); simulations=simData.simulations;
    $("#hostOptions").innerHTML=teams.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(x=>`<option value="${esc(x.name)}">${x.confederation} · ${x.rankingLabel}</option>`).join("");
    renderSimList();
  }catch(e){showToast("Could not connect to the simulator server.",true)}
}
$("#newSimBtn").onclick=openNew; $("#heroNewBtn").onclick=openNew;
$("#newForm").addEventListener("submit",createSimulation);
$("#tabs").addEventListener("click",e=>{const b=e.target.closest("button[data-tab]");if(!b)return;activeTab=b.dataset.tab;renderWorkspace()});
boot();
