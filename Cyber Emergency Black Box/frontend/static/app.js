const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt=t=>t?esc(String(t).replace('T',' ').slice(0,19)):'—',B=(c,t)=>`<span class="b ${esc(c)}">${esc(t??c)}</span>`;
// Mr. Masud was here.
// Evidence tells the story; people make the call.
const ICON={login_success:'AUTH',login_failure:'AUTH',process_start:'PROC',process_stop:'PROC',file_created:'FILE',file_modified:'FILE',file_deleted:'FILE',network_connection:'NET'};
const MITRE={
 'R-01':[{id:'T1078',name:'Valid Accounts'},{id:'T1110',name:'Brute Force'}],
 'R-02':[{id:'T1059',name:'Command and Scripting Interpreter'}],
 'R-03':[{id:'T1486',name:'Data Encrypted for Impact'},{id:'T1083',name:'File and Directory Discovery'}]
};
const BASE=location.protocol==='file:'?'http://127.0.0.1:8000':'';let timer=null,routeGeneration=0,authInitialized=false,authed=false;
function toast(m){const d=document.createElement('div');d.textContent=m;$('#toast').append(d);setTimeout(()=>d.remove(),5000)}
async function api(p,o={}){const r=await fetch(BASE+'/api/v1'+p,{credentials:'same-origin',...o});let payload={};try{payload=await r.json()}catch{}if(!r.ok)throw new Error(payload.detail||payload.error?.message||`Request failed (${r.status})`);return payload&&Object.prototype.hasOwnProperty.call(payload,'data')?payload.data:payload}
function mitreBadges(ruleId,compact=false){const techniques=MITRE[ruleId]||[];if(!techniques.length)return '<span class="sub">No ATT&amp;CK mapping</span>';return `<span class="mitre-group ${compact?'compact':''}" title="Suggested investigative mapping only; this does not confirm technique execution.">${techniques.map(t=>`<a class="b mitre" href="https://attack.mitre.org/techniques/${t.id}/" target="_blank" rel="noopener noreferrer" title="${esc(t.name)} — investigative hypothesis">MITRE ${t.id}</a>`).join(' ')}</span>`}
function showAbout(){let dialog=$('#about-modal');if(!dialog){dialog=document.createElement('dialog');dialog.id='about-modal';dialog.className='about-modal';dialog.innerHTML=`<button class="modal-close" type="button" aria-label="Close dialog">×</button><div class="eyebrow">ACADEMIC PROJECT</div><h2>Cyber Emergency Black Box</h2><p class="sub">CEBB · Local endpoint incident response prototype</p><p>Final Project for <strong>INSA Cyber Talent Center 5th round summer camp 2026</strong>.</p><p>A lightweight host-based digital forensics and incident response prototype that collects security telemetry, correlates event patterns, and preserves linked evidence for analyst review.</p><h3>Technical pillars</h3><ul><li>Continuous endpoint telemetry</li><li>SHA-256 event chaining and evidence manifests</li><li>Explainable rule-based correlation</li><li>Evidence package integrity verification</li></ul><a class="btn" href="https://github.com/shalomtesfaye22-design/Cyber-Emergency-Black-Box" target="_blank" rel="noopener noreferrer">View project on GitHub</a><p class="disc">ATT&amp;CK labels in CEBB are investigative hypotheses and do not confirm adversary behavior.</p>`;document.body.append(dialog);dialog.querySelector('.modal-close').onclick=()=>dialog.close();dialog.addEventListener('click',event=>{if(event.target===dialog)dialog.close()})}dialog.showModal()}
/* ---- shell ---- */
const NAV=[['dashboard','Dashboard'],['events','Events'],['incidents','Incidents'],['evidence','Evidence'],['settings','Settings'],['security','Security']];
function shell(page,title,body){$('#root').innerHTML=`<div id="app"><nav><div class="logo"><svg><use href="#sh"/></svg>CEBB</div>${NAV.map(n=>`<a href="#/${n[0]}" class="${n[0]===page?'on':''}">${n[1]}</a>`).join('')}<button type="button" class="nav-about" id="about-open">About CEBB</button></nav><div><header><h2>${esc(title)}</h2><div class="who">Local operator<br><a href="#/logout" style="color:var(--acc)">Sign out</a></div></header><main>${body}</main></div></div>`}
function passwordRules(p){return p.length>=8&&/[a-z]/.test(p)&&/[A-Z]/.test(p)&&/\d/.test(p)&&/[^A-Za-z0-9]/.test(p)}
function authView(setup=false){$('#root').innerHTML=`<div id="login"><div class="brand"><svg class="shield"><use href="#sh"/></svg><h1>CEBB</h1><div>Cyber Emergency Black Box</div><p style="color:var(--mut)"><b style="color:var(--tx)">Detect. Investigate. Preserve.</b><br>Local endpoint incident response prototype.</p></div><form class="box" id="lf"><h2 style="margin:0">${setup?'Set up master password':'Master password'}</h2><div class="sub">${setup?'Create the local operator password to protect this dashboard.':'Enter the local operator password to continue.'}</div>${setup?'<label for="pw">New password</label>':'<label for="pw">Password</label>'}<input type="password" id="pw" required minlength="8" autocomplete="${setup?'new-password':'current-password'}">${setup?'<label for="pw2">Confirm password</label><input type="password" id="pw2" required autocomplete="new-password"><ul class="sub rules"><li id="rule-length">At least 8 characters</li><li id="rule-lower">A lowercase letter</li><li id="rule-upper">An uppercase letter</li><li id="rule-number">A number</li><li id="rule-symbol">A symbol</li></ul>':''}<p class="sub" id="auth-error" role="alert"></p><button class="btn" style="width:100%;margin-top:14px">${setup?'Create password':'Unlock dashboard'}</button><p class="sub" style="text-align:center">Password is stored as a salted PBKDF2 hash on this computer.</p></form></div>`;
 const form=$('#lf'),pw=$('#pw'),rules=[['rule-length',v=>v.length>=8],['rule-lower',v=>/[a-z]/.test(v)],['rule-upper',v=>/[A-Z]/.test(v)],['rule-number',v=>/\d/.test(v)],['rule-symbol',v=>/[^A-Za-z0-9]/.test(v)]];pw?.addEventListener('input',()=>rules.forEach(([id,test])=>{const item=$('#'+id);if(item){item.classList.toggle('passed',test(pw.value));item.setAttribute('aria-label',`${test(pw.value)?'Met':'Missing'}: ${item.textContent}`)}}));form.onsubmit=async e=>{e.preventDefault();const error=$('#auth-error');error.textContent='';if(setup&&pw.value!==$('#pw2').value){error.textContent='Passwords do not match.';return}if(setup&&!passwordRules(pw.value)){error.textContent='Password does not meet the requirements.';return}const button=form.querySelector('button');button.disabled=true;try{await api(setup?'/auth/setup':'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:pw.value})});authed=true;location.hash='#/dashboard';await route()}catch(err){error.textContent=err.message}finally{button.disabled=false}}}
function offlineView(error){$('#root').innerHTML=`<main class="offline"><div class="card"><h2>Backend Offline</h2><p>The dashboard cannot reach the local CEBB API, so it is not showing sample telemetry.</p><p class="sub">${esc(error?.message||'Start the backend at http://127.0.0.1:8000 and retry.')}</p><button class="btn" id="retry">Retry connection</button></div></main>`;$('#retry').onclick=route}
/* ---- views ---- */
async function dashboard(generation=routeGeneration){
 const [s,ev,st,inc]=await Promise.all([api('/dashboard/summary'),api('/events?limit=500'),api('/system/status'),api('/incidents?limit=100')]);
 if(generation!==routeGeneration)return;
 const list = Array.isArray(inc) ? inc : [];
 const open = list.filter(i => i.status === 'OPEN' || i.status === 'INVESTIGATING').length;
 const evs = Array.isArray(ev) ? ev : [];
 let ts=evs.map(e=>+new Date(e.timestamp)),lo=Math.min(...ts),hi=Math.max(...ts,lo+1),n=12,bk=Array(n).fill(0);
 ts.forEach(t=>bk[Math.min(n-1,Math.floor((t-lo)/(hi-lo)*n))]++);const mx=Math.max(...bk,1);
 const pts=bk.map((v,i)=>`${10+i*(380/(n-1))},${120-v/mx*100}`).join(' ');
 const by={};list.forEach(i=>by[i.rule_name]=(by[i.rule_name]||0)+1);const cols=['#ef4458','#2a6cf6','#22c58b','#f0a43a'];let acc=0,tot=list.length||1,arcs='';
 Object.values(by).forEach((v,i)=>{const f=v/tot*100;arcs+=`<circle r="15.9" cx="21" cy="21" fill="none" stroke="${cols[i%4]}" stroke-width="5" stroke-dasharray="${f} ${100-f}" stroke-dashoffset="${25-acc}"/>`;acc+=f});
 const collectors=Array.isArray(st.collectors)?st.collectors:[];const on=collectors.filter(c=>c.enabled&&c.available).length;
 shell('dashboard','Cyber security overview',`<div class="bar"><button class="btn" id="sim">Run attack simulation (SIM-001)</button><span class="sub"><span class="dot ${s.monitoring_active?'pulse':''}"></span>${s.monitoring_active?'Monitoring active':'Monitoring paused'} · uptime ${Math.floor((s.uptime_seconds ?? 0) / 3600)}h ${Math.floor(((s.uptime_seconds ?? 0) % 3600) / 60)}m</span></div>
 <div class="grid g4"><div class="card"><h3>Total events</h3><div class="big">${(s.event_count ?? 0).toLocaleString()}</div></div><div class="card"><h3>Open incidents</h3><div class="big" style="color:${open?'var(--crit)':'inherit'}">${open}</div></div><div class="card"><h3>Closed incidents</h3><div class="big">${list.length-open}</div></div><div class="card"><h3>System status</h3><div class="big" style="color:${st.status==='operational'?'var(--ok)':'var(--warn)'};font-size:22px">${esc(st.status==='operational'?'Online':'Degraded')}</div><div class="sub">${on} collectors available</div></div></div>
 <div class="grid g2" style="margin-top:14px"><div class="card"><h3>Events over the retention window</h3><svg viewBox="0 0 400 130" width="100%"><polyline points="${pts}" fill="none" stroke="#2a6cf6" stroke-width="2"/><polygon points="10,120 ${pts} 390,120" fill="#2a6cf633"/></svg></div>
 <div class="card"><h3>Incident types</h3><div style="display:flex;align-items:center;gap:16px"><svg viewBox="0 0 42 42" width="130"><circle r="15.9" cx="21" cy="21" fill="none" stroke="#1a2b49" stroke-width="5"/>${arcs}<text x="21" y="23" text-anchor="middle" fill="#fff" font-size="8">${list.length}</text></svg><div>${Object.entries(by).map(([k,v],i)=>`<div class="sub"><span style="color:${cols[i%4]}">●</span> ${esc(k)} (${v})</div>`).join('')||'<span class="sub">No incidents yet</span>'}</div></div></div></div>
 <div class="card" style="margin-top:14px"><h3>Recent incidents</h3>${incTable(list.slice(0,3))}</div>`);
 $('#sim').onclick=async e=>{e.target.disabled=true;e.target.textContent='Injecting synthetic threat sequence…';try{await api('/simulator/run',{method:'POST',headers:{'Content-Type':'application/json'},body:'{"scenario":"account_compromise"}'});toast('Simulation started — an incident should appear within about 10 seconds.')}catch(x){toast('Simulation failed: '+x.message)}setTimeout(()=>{if(generation===routeGeneration)route()},8000)}}
function incTable(l){return l.length?`<div class="wrap"><table><tr><th>Incident</th><th>Detected</th><th>Rule</th><th>ATT&amp;CK hypotheses</th><th>Severity</th><th>Status</th><th>Events</th></tr>${l.map(i=>`<tr class="row" data-incident="${esc(encodeURIComponent(i.incident_id))}"><td class="m">${esc(i.incident_id)}</td><td class="m">${fmt(i.detection_time)}</td><td>${esc(i.rule_name)}</td><td>${mitreBadges(i.rule_id,true)}</td><td>${B(i.severity)}</td><td>${B(i.status)}</td><td>${Number(i.event_count)||0}</td></tr>`).join('')}</table></div>`:'<p class="sub">No incidents detected. Run the simulation to see one.</p>'}
let F={q:'',t:'',s:'',h:false};
function inspectionField(label,value){return `<div class="inspect-field"><dt>${esc(label)}</dt><dd>${esc(value??'—')||'—'}</dd></div>`}
function forensicInspector(event){const val=(v)=>v===null||v===undefined||v===''?'—':v;return `<tr class="x"><td colspan="7"><section class="forensic-inspector"><div class="inspector-head"><div>${B(event.event_type)} ${B(event.severity)} ${event.is_simulated?B('SIM','SIMULATED'):B('REAL','LIVE')}</div><time>${fmt(event.timestamp)}</time></div><div class="inspection-grid"><section><h4>Subject &amp; attribution</h4><dl>${inspectionField('User',event.user_name)}${inspectionField('Process',event.process_name)}${inspectionField('Action',event.action)}${inspectionField('Target',event.target)}</dl></section><section><h4>Network telemetry</h4><dl>${inspectionField('Source IP',event.source_ip)}${inspectionField('Destination IP',event.destination_ip)}${inspectionField('Destination port',event.destination_port)}${inspectionField('Protocol',event.protocol)}</dl></section><section class="integrity-section"><h4>Cryptographic integrity</h4><div class="hash-copy"><span class="sub">Raw event SHA-256</span><code>${esc(val(event.raw_hash))}</code><button class="btn ghost sm copy-hash" type="button" data-hash="${esc(val(event.raw_hash))}" ${event.raw_hash?'':'disabled'}>Copy hash</button></div><div class="hash-copy"><span class="sub">Previous event SHA-256</span><code>${esc(val(event.previous_hash))}</code><button class="btn ghost sm copy-hash" type="button" data-hash="${esc(val(event.previous_hash))}" ${event.previous_hash?'':'disabled'}>Copy hash</button></div></section></div><details class="raw-inspector"><summary>View raw JSON</summary><pre>${esc(JSON.stringify(event,null,2))}</pre></details></section></td></tr>`}
async function events(generation=routeGeneration){
 const q=new URLSearchParams({limit:500});if(F.t)q.set('event_type',F.t);if(F.s)q.set('severity',F.s);if(F.h)q.set('simulated_only','false');
 const d=await api('/events?'+q);if(generation!==routeGeneration)return;let rows=(Array.isArray(d)?d:[]).filter(e=>!F.q||[e.user_name,e.process_name,e.target,e.action].join(' ').toLowerCase().includes(F.q.toLowerCase()));
 const types=Object.keys(ICON),opt=(a,v)=>a.map(x=>`<option ${x===v?'selected':''}>${x}</option>`).join('');
 shell('events','Security events',`<div class="bar"><input type="text" id="fq" placeholder="Search user, process or target" value="${esc(F.q)}"><select id="ft"><option value="">All types</option>${opt(types,F.t)}</select><select id="fs"><option value="">All severities</option>${opt(['LOW','MEDIUM','HIGH','CRITICAL'],F.s)}</select><label class="chk" style="margin:0"><input type="checkbox" id="fh" ${F.h?'checked':''}>Hide simulated</label><button class="btn sm" id="csv" style="margin-left:auto">Export CSV</button></div>
 <div class="card wrap"><table class="events-table"><tr><th>Time (UTC)</th><th>Type</th><th>User</th><th>Process</th><th>Action / target</th><th>Severity</th><th>Source</th></tr>${rows.map((e,i)=>`<tr class="row" data-i="${i}"><td class="m">${fmt(e.timestamp)}</td><td>${esc(e.event_type)}</td><td>${esc(e.user_name)}</td><td>${esc(e.process_name)}</td><td>${esc(e.action||e.target)}</td><td>${B(e.severity)}</td><td>${e.is_simulated?B('SIM','SIMULATED'):B('REAL','REAL')}</td></tr>`).join('')||'<tr><td colspan=7 class="sub">No events match these filters.</td></tr>'}</table></div>`);
 $('#fq').oninput=e=>{F.q=e.target.value;clearTimeout(window._d);window._d=setTimeout(events,300)};$('#ft').onchange=e=>{F.t=e.target.value;events()};$('#fs').onchange=e=>{F.s=e.target.value;events()};$('#fh').onchange=e=>{F.h=e.target.checked;events()};
 $('#fq').focus();$('#fq').setSelectionRange(99,99);
 document.querySelectorAll('tr.row').forEach(r=>r.onclick=()=>{const nx=r.nextElementSibling;if(nx&&nx.classList.contains('x')){nx.remove();r.setAttribute('aria-expanded','false');return}const e=rows[r.dataset.i];r.after(document.createRange().createContextualFragment(forensicInspector(e)));r.setAttribute('aria-expanded','true')});
 document.querySelectorAll('.copy-hash').forEach(button=>button.onclick=async()=>{try{await navigator.clipboard.writeText(button.dataset.hash);toast('SHA-256 copied to clipboard')}catch{toast('Clipboard access is unavailable in this browser')}});
 $('#csv').onclick=()=>{const h=['event_id','timestamp','event_type','severity','user_name','process_name','action','target','raw_hash'],labels=['Event ID','Timestamp (UTC)','Event Type','Severity','User','Process','Action','Target','SHA-256'],c=[labels.join(',')].concat(rows.map(e=>h.map(k=>JSON.stringify(e[k]??'')).join(',')));const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([c.join('\r\n')],{type:'text/csv'}));a.download='cebb_events.csv';a.click();URL.revokeObjectURL(a.href)}}
async function incidents(st='',generation=routeGeneration){
 const result=await api('/incidents?limit=200'),all=Array.isArray(result)?result:[],cnt=s=>all.filter(i=>!s||i.status===s).length,l=all.filter(i=>!st||i.status===st);
 if(generation!==routeGeneration)return;
 shell('incidents','Incidents',`<div class="bar"><div class="pills">${
[['','All'],['OPEN','Open'],['INVESTIGATING','Investigating'],['RESOLVED','Resolved'],['FALSE_POSITIVE','False positive']]
.map(p=>`<a href="#/incidents/${encodeURIComponent(p[0])}" class="${p[0]===st?'on':''}">${p[1]} (${cnt(p[0])})</a>`).join('')}</div></div>${l.map(i=>`<div class="card inc" data-incident="${esc(encodeURIComponent(i.incident_id))}"><div><span class="sub">${esc(i.incident_id)}</span><b>${esc(i.rule_name)}</b><span class="sub">${esc(i.summary)}</span><div class="mitre-row">${mitreBadges(i.rule_id,true)}</div></div><div style="text-align:right">${B(i.severity)} ${B(i.status)}<div class="sub">${fmt(i.detection_time)}</div></div></div>`).join('')||'<p class="sub">No incidents with this status.</p>'}`)}
async function incident(id,tab='overview',generation=routeGeneration){
const [incidentRes, timelineRes] = await Promise.all([
  api('/incidents/' + encodeURIComponent(id)),
  api(`/incidents/${encodeURIComponent(id)}/timeline`)
]);
if(generation!==routeGeneration)return;

const i = incidentRes;
const events = Array.isArray(timelineRes) ? timelineRes : (timelineRes.events || []);
events.sort((a,b)=>new Date(a.timestamp)-new Date(b.timestamp));
const x = i.interpretation || {};
const cnt = {};

events.forEach(e => {
  cnt[e.event_type] = (cnt[e.event_type] || 0) + 1;
});

 const li=a=>`<ul>${(a||[]).map(v=>`<li>${esc(v)}</li>`).join('')}</ul>`;
 const interp=`<h3>Confirmed facts</h3>${li(x.confirmed_facts)}<h3>Detection result</h3><p>${esc(x.detection_result||i.summary)}</p><h3>Interpretation</h3><p>${esc(x.interpretation)}</p><h3>Recommended next steps</h3>${li(x.recommendations)}<div class="disc">${esc(x.disclaimer||'Automated analysis prototype. Human verification required.')}</div>`;
 let body='';
 const first=events[0]?.timestamp,last=events.at(-1)?.timestamp;
 if(tab==='overview')body=`<div class="grid g2"><div class="card"><h3>Detection result</h3><p>${esc(i.summary)}</p><div class="sub">First event: ${fmt(first)}<br>Last event: ${fmt(last)}<br>Rule: ${esc(i.rule_id)} · ${esc(i.rule_name)}</div><h3 class="mt">MITRE ATT&amp;CK investigative hypotheses</h3>${mitreBadges(i.rule_id)}</div><div class="card"><h3>Related events</h3>${Object.entries(cnt).map(([k,v])=>`<div><span class="mono sub">${ICON[k]||''}</span> ${v} × ${esc(k)}</div>`).join('')}<a class="btn" style="display:inline-block;margin-top:12px" href="#/incident/${encodeURIComponent(id)}/timeline">View full timeline</a></div></div>`;
 if(tab==='timeline')body=`<div class="grid g2"><div class="tl">${events.map((e,k)=>`<div class="ev ${e.is_trigger?'trig':''}" data-k="${k}"><span class="sub">${fmt(e.timestamp)}</span> ${e.is_trigger?`${B('CRITICAL','TRIGGER EVIDENCE')} ${mitreBadges(i.rule_id,true)}`:''}<div><span class="mono sub">${ICON[e.event_type]||''}</span> ${esc(e.action||e.event_type)}</div><div class="sub">User: ${esc(e.user_name||'—')} · Process: ${esc(e.process_name||'—')} · Target: ${esc(e.target||'—')}</div></div>`).join('')}</div><div class="card" id="det"><h3>Event details</h3><span class="sub">Select an event to see its record.</span></div></div>`;
 if(tab==='events')body=`<div class="card wrap"><table><tr><th>Time</th><th>Type</th><th>User</th><th>Process</th><th>Action / target</th><th>Severity</th></tr>${events.map(e=>`<tr><td>${fmt(e.timestamp)}</td><td>${esc(e.event_type)}</td><td>${esc(e.user_name)}</td><td>${esc(e.process_name)}</td><td>${esc(e.action||e.target)}</td><td>${B(e.severity)}</td></tr>`).join('')}</table></div>`;
 if(tab==='evidence')body=`<div id="evb" class="card">Loading evidence…</div>`;
 if(tab==='explanation')body=`<div class="card">${interp}</div>`;
 const TB=[['overview','Overview'],['timeline','Timeline'],['events','Related events'],['evidence','Evidence'],['explanation','Explanation']];
 shell('incidents',`Incident ${esc(id)}`,`<h2 style="margin:0 0 6px">${esc(i.rule_name)} ${B(i.severity)} ${B(i.status)}</h2><div class="bar">
<select id="st">${['OPEN','INVESTIGATING','RESOLVED','FALSE_POSITIVE'].map(s=>`<option ${s===i.status?'selected':''}>${s}</option>`).join('')}</select>
<a class="btn ghost sm" href="${BASE}/api/v1/incidents/${id}/report" target="_blank" rel="noopener">View report</a></div><div class="tabs">${TB.map(t=>`<a href="#/incident/${id}/${t[0]}" class="${t[0]===tab?'on':''}">${t[1]}</a>`).join('')}</div>${body}`);
 $('#st').onchange=async e=>{try{await api('/incidents/'+encodeURIComponent(id),{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:e.target.value})});toast('Status updated to '+e.target.value)}catch(x){toast('Update failed: '+x.message)}};
 document.querySelectorAll('.tl .ev').forEach(el=>el.onclick=()=>{$('#det').innerHTML='<h3>Event details</h3><pre>'+esc(JSON.stringify(events[el.dataset.k],null,2))+'</pre>'});
 if(tab==='evidence')evidencePanel(id,$('#evb'),i.rule_id)}

async function evidencePanel(id, el, ruleId=null) {
  const res = await api(`/incidents/${encodeURIComponent(id)}/evidence`);
  const ev = res;

  el.innerHTML = `
    <h3>Preserved evidence · ${fmt(ev.created_at)}</h3>
    <div class="mitre-report"><span class="sub">MITRE ATT&amp;CK investigative hypotheses</span>${mitreBadges(ruleId)}</div>
    <div class="wrap">
      <table>
        <tr><th>File</th><th>Size</th><th>SHA-256</th></tr>
        ${Object.entries(ev.files || {}).map(([name, f]) => `
          <tr>
            <td>${esc(name)}</td>
            <td>${esc(f.size_bytes)} B</td>
            <td class="hash">${esc(f.sha256 || '')}</td>
          </tr>
        `).join('')}
      </table>
    </div>
    <div class="bar" style="margin-top:14px">
      <button class="btn" id="vf">Verify integrity</button>
      <a class="btn ghost" href="${BASE}/api/v1/incidents/${encodeURIComponent(id)}/evidence/download">Export evidence (.zip)</a>
    </div>
    <div id="vr"></div>
  `;

  $('#vf').onclick = async () => {
    try {
      const response = await api(
        `/incidents/${encodeURIComponent(id)}/evidence/verify`
      );
      const v = response;

      $('#vr').innerHTML = v.valid
        ? `<div class="okbox">Integrity verified — evidence files match their recorded hashes.</div>`
        : `<div class="okbox badbox">Integrity check failed — ${esc((v.missing || []).join(', ') || 'Evidence files are missing or have changed.')}</div>`;
    } catch (err) {
      $('#vr').innerHTML =
        `<div class="okbox badbox">Verification failed: ${esc(err.message)}</div>`;
    }
  };
}

async function evidence(sel,generation=routeGeneration){
 const result=await api('/incidents?limit=200');if(generation!==routeGeneration)return;const l=Array.isArray(result)?result:[];sel=sel||l[0]?.incident_id;const selected=l.find(i=>i.incident_id===sel);
 shell('evidence','Export evidence',`<div class="bar"><select id="si">${l.map(i=>`<option value="${esc(i.incident_id)}" ${i.incident_id===sel?'selected':''}>${esc(i.incident_id)} · ${esc(i.rule_name)}</option>`).join('')||'<option>No incidents</option>'}</select></div><div id="ep" class="card">${sel?'':'<span class="sub">Evidence packages are created automatically when an incident is detected.</span>'}</div>`);
 $('#si').onchange=e=>evidence(e.target.value);if(sel)evidencePanel(sel,$('#ep'),selected?.rule_id)}
function securityView(){
 shell('security','Security',`<form class="card" id="password-form" style="max-width:520px"><h3>Change master password</h3><div class="f"><label for="current-password">Current password</label><input id="current-password" type="password" required autocomplete="current-password"></div><div class="f"><label for="new-password">New password</label><input id="new-password" type="password" required autocomplete="new-password"><div class="sub">At least 8 characters with uppercase, lowercase, number, and symbol.</div></div><div class="f"><label for="confirm-password">Confirm new password</label><input id="confirm-password" type="password" required autocomplete="new-password"></div><p id="password-error" class="error" role="alert"></p><button class="btn">Update password</button></form>`);
 $('#password-form').onsubmit=async e=>{e.preventDefault();const current_password=$('#current-password').value,new_password=$('#new-password').value;if(new_password!==$('#confirm-password').value){$('#password-error').textContent='New passwords do not match.';return}try{await api('/auth/change-password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password,new_password})});e.target.reset();toast('Master password updated.')}catch(err){$('#password-error').textContent=err.message}}}

async function settings(generation=routeGeneration){
 const [settingsRes, hostRes, statusRes] = await Promise.all([
   api('/settings'),
   api('/system/info'),
   api('/system/status')
 ]);
 if(generation!==routeGeneration)return;

 const s = settingsRes;
 const h = hostRes;
 const st = statusRes;

 const fld = (k, l, t = 'number') =>
   `<div class="f"><label>${l}</label><input type="${t}" name="${k}" value="${esc(s[k] ?? '')}"></div>`;

 shell('settings','Settings',`
   <div class="grid g2">
     <form class="card" id="sf">
       <h3>Runtime configuration</h3>
       ${fld('retention_minutes','Retention window (minutes)')}
       ${fld('correlation_interval_seconds','Correlation interval (seconds)')}
       ${fld('evidence_context_minutes','Evidence context (minutes)')}
       <fieldset class="f"><legend>Enabled collectors</legend>${['process','file','network','system_info','login','usb'].map(name=>`<label class="chk"><input type="checkbox" name="enabled_collectors" value="${name}" ${(Array.isArray(s.enabled_collectors)?s.enabled_collectors:[]).includes(name)?'checked':''}>${esc(name)}</label>`).join('')}</fieldset>
       <p class="sub">Collector changes take effect after the application restarts.</p>
       <div class="f">
         <label>Monitored path</label>
         <input type="text" value="${esc(s.monitored_paths ?? '')}" disabled>
       </div>
       <p id="settings-error" class="error" role="alert"></p><button class="btn">Save settings</button>
     </form>

     <div class="card">
       <h3>Host</h3>
       <div>${esc(h.hostname ?? 'Unknown')} · ${esc([h.os_name,h.os_version].filter(Boolean).join(' ')||'Unknown OS')}</div>
       <div class="sub">
         CPU ${h.cpu_percent ?? 'N/A'}% ·
         Memory ${h.memory_percent ?? 'N/A'}% ·
         Boot ${h.boot_time ? fmt(h.boot_time) : 'Unknown'}
       </div>
       <h3 style="margin-top:16px">Collectors</h3>
       ${(Array.isArray(st.collectors)?st.collectors:[]).map(v =>
         `<div><span class="dot" style="background:${v.enabled&&v.available?'var(--ok)':'var(--mut)'}"></span>${esc(v.name)}: ${v.available?'available':'unavailable'}${v.enabled?'':' (disabled)'}</div>`
       ).join('') || '<div class="sub">No collector information available.</div>'}
     </div>
   </div>
 `);

 $('#sf').onsubmit = async e => {
   e.preventDefault();
   const b = {};
   new FormData(e.target).forEach((v,k) => {if(k==='enabled_collectors'){(b[k]??=[]).push(v)}else if(v!=='')b[k]=Number(v)});
   b.enabled_collectors=Array.from(e.target.querySelectorAll('[name="enabled_collectors"]:checked'),input=>input.value);
   try {
     await api('/settings',{
       method:'PUT',
       headers:{'Content-Type':'application/json'},
       body:JSON.stringify(b)
     });
     $('#settings-error').textContent='';toast('Settings saved');
     await settings(generation);
   } catch(x) {
     if(generation!==routeGeneration)return;
     $('#settings-error').textContent=x.message;
   }
 };
}
/* ---- router ---- */
async function route(){
 clearInterval(timer);const generation=++routeGeneration;const [, page='dashboard',a,b]=location.hash.slice(1).split('/').map(decodeURIComponent);
 try{
  const status=await api('/auth/status');authInitialized=!!status.initialized;authed=!!status.authenticated;
 }catch(error){if(generation===routeGeneration)offlineView(error);return}
 if(generation!==routeGeneration)return;
 if(page==='logout'){try{await api('/auth/logout',{method:'POST'})}catch{}authed=false;location.hash='#/dashboard';return}
 if(!authed)return authView(!authInitialized);
 try{
  if(page==='dashboard'){await dashboard(generation);if(generation!==routeGeneration)return;timer=setInterval(()=>{const activePage=location.hash.slice(1).split('/')[1]||'dashboard';if(generation===routeGeneration&&activePage==='dashboard'&&(!document.activeElement||document.activeElement.tagName!=='BUTTON'))dashboard(generation).catch(()=>{if(generation===routeGeneration)route()})},10000)}
  else if(page==='events')await events(generation);else if(page==='incidents')await incidents(a||'',generation);
  else if(page==='incident')await incident(a,b||'overview',generation);else if(page==='evidence')await evidence(undefined,generation);
  else if(page==='security')securityView();else if(page==='settings')await settings(generation);else location.hash='#/dashboard';
 }catch(e){if(generation!==routeGeneration)return;if(e instanceof TypeError)return offlineView(e);shell(page,'Something went wrong',`<div class="card"><b>Couldn't load this page.</b><p class="sub">${esc(e.message)}</p><button class="btn" id="retry-page">Retry</button></div>`);$('#retry-page').onclick=route}}
document.addEventListener('click',event=>{if(event.target.closest('#about-open')){showAbout();return}if(event.target.closest('a,button'))return;const row=event.target.closest('[data-incident]');if(row)location.hash=`#/incident/${decodeURIComponent(row.dataset.incident)}/overview`});
addEventListener('hashchange',route);route();
