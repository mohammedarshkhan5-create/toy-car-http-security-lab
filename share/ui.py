"""The single browser page: three panels and the JavaScript that drives them.

Students do not need to edit anything in this file.
"""

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Toy-Car HTTP Interceptor</title>
<style>
  :root {
    --bg:#080b12; --edge:#2a3550; --ink:#e7ecf5;
    --muted:#8ea0c0; --accent:#4da3ff; --good:#3ddc84; --warn:#ffb454;
    --bad:#ff6b6b;
    --c-client:#35d6a4; --c-server:#ffb454; --c-mitm:#ff6bb8;
  }
  * { box-sizing:border-box; }
  body { margin:0; font:14px/1.45 system-ui,Segoe UI,Roboto,sans-serif;
         background:var(--bg); color:var(--ink); }
  header { padding:10px 16px; background:#05070c; border-bottom:1px solid #1b2436;
           display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  header h1 { font-size:16px; margin:0; }
  header .summary { color:var(--muted); font-size:12px; }
  header .badge { font-size:11px; padding:2px 7px; border-radius:5px;
           background:#3a2600; color:var(--warn); border:1px solid #614100; }
  .cols { display:flex; gap:22px; padding:18px; align-items:stretch;
          min-height:calc(100vh - 56px); flex-wrap:wrap; }
  .panel { flex:1 1 0; min-height:calc(100vh - 92px); border-radius:12px; padding:16px; display:flex;
           flex-direction:column; min-width:0; position:relative;
           background:var(--surface); border:1px solid var(--line);
           box-shadow:0 0 0 1px #05070c, 0 10px 26px rgba(0,0,0,.5); }
  .panel::before { content:''; position:absolute; inset:0 0 auto 0; height:3px;
           border-radius:12px 12px 0 0; background:var(--hue); }
  .panel h2 { margin:0 0 12px; font-size:13px; letter-spacing:1.2px;
              text-transform:uppercase; color:var(--hue); }
  .panel b { color:var(--ink); }
  .p-client { --hue:var(--c-client); --surface:#0e1a1a; --line:#1d3a35; --field:#0a1412; }
  .p-server { --hue:var(--c-server); --surface:#1a1710; --line:#3a3320; --field:#12100a; }
  .p-mitm   { --hue:var(--c-mitm);   --surface:#1a1018; --line:#3d2033; --field:#120a10; }
  .panel hr { border:none; border-top:1px solid var(--line); margin:12px 0; }
  .panel code { color:var(--hue); }
  .row { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
  .keys { text-align:center; color:var(--muted); font-size:12px; }
  .btn { background:#161d2b; color:var(--ink); border:1px solid var(--edge);
         border-radius:8px; padding:6px 12px; cursor:pointer; }
  .btn:hover { border-color:var(--accent); }
  .btn.accent { background:var(--c-mitm); color:#12060e; border:none; font-weight:600; }
  select, input { background:#0d1119; color:var(--ink); border:1px solid var(--edge);
           border-radius:6px; padding:4px 6px; font:inherit; }
  .pad { display:grid; grid-template-columns:repeat(3,58px);
         grid-template-rows:repeat(3,58px); gap:8px; justify-content:center;
         margin:14px auto; }
  .pad button { font-size:20px; border:1px solid var(--line); border-radius:10px;
                background:#122320; color:var(--ink); cursor:pointer; }
  .pad button:hover { background:#183029; border-color:var(--c-client); }
  .pad button:active { transform:translateY(1px); }
  .b-F{grid-area:1/2} .b-L{grid-area:2/1} .b-R{grid-area:2/3} .b-B{grid-area:3/2}
  canvas { background:#0d0b06; border:1px solid var(--line); border-radius:8px;
           display:block; margin:6px auto; max-width:100%; }
  .status { text-align:center; min-height:20px; color:var(--muted); font-size:13px; }
  .lastcmd { text-align:center; font-family:ui-monospace,monospace; font-size:13px;
             color:var(--muted); margin-top:4px; }
  .lastcmd b { color:var(--ink); }
  .ok { color:var(--good); } .no { color:var(--bad); } .wait { color:var(--accent); }
  .props { display:flex; flex-wrap:wrap; gap:6px; margin:8px 0; }
  .prop { font-size:11px; padding:2px 8px; border-radius:20px;
          border:1px solid var(--edge); color:var(--muted); }
  .prop.on { border-color:var(--good); color:var(--good); }
  .toggle { display:flex; align-items:center; gap:10px; margin-bottom:12px; }
  .toggle button { padding:6px 12px; border-radius:8px; border:1px solid var(--edge);
                   cursor:pointer; font-weight:600; }
  .toggle .on  { background:var(--bad); color:#fff; border-color:var(--bad); }
  .toggle .off { background:#1d1420; color:var(--ink); }
  .held-list { display:flex; flex-direction:column; gap:8px; margin-bottom:8px;
               flex:0 1 198px; max-height:min(22vh, 198px); overflow-y:auto;
               overscroll-behavior:contain; }
  .held { border:1px solid var(--c-mitm); background:#25121f; border-radius:8px;
          padding:8px; display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
  .held .fwd { background:var(--good); color:#08260f; border:none; border-radius:6px;
               padding:5px 10px; cursor:pointer; font-weight:600; }
  .held .drop{ background:var(--bad); color:#fff; border:none; border-radius:6px;
               padding:5px 10px; cursor:pointer; font-weight:600; }
  .muted { color:var(--muted); font-size:12px; }
  /* logs scroll inside a capped window so the page height stays put.
     Per-region caps: the shared .scroll base carries no max-height because the
     security-checks list also uses it and needs more room. */
  .scroll { overflow:auto; flex:1 1 auto; min-height:120px; }
  .p-client > .scroll { flex:0 1 260px; max-height:min(30vh, 260px); }
  .p-mitm > .scroll   { flex:0 1 162px; max-height:min(18vh, 162px);
                        overscroll-behavior:contain; }
  #checksList { flex:0 1 220px; max-height:min(25vh, 220px); }
  #rawBox { max-height:180px; }
  table { width:100%; border-collapse:collapse; font-size:12px; }
  th,td { text-align:left; padding:4px 6px; border-bottom:1px solid var(--line);
          vertical-align:top; }
  th { color:var(--muted); position:sticky; top:0; background:var(--surface); }
  td.mono, .mono { font-family:ui-monospace,monospace; }
  td.ms { text-align:right; white-space:nowrap; font-family:ui-monospace,monospace;
          min-width:92px; }
  td.ms .bar { display:block; height:4px; margin:0 0 2px auto; width:100%;
               background:var(--edge); border-radius:2px; }
  td.ms .bar i { display:block; height:100%; background:var(--accent);
                 border-radius:2px; }
  .tag { font-size:10px; padding:1px 5px; border-radius:4px; margin-left:4px;
         background:var(--warn); color:#3a2600; }
  .s-accepted{color:var(--good)} .s-rejected{color:var(--bad); font-weight:600}
  .s-dropped{color:var(--bad)} .s-timeout{color:var(--warn)}
  .s-malformed{color:var(--warn)} .s-error{color:var(--warn)}
  textarea { width:100%; min-height:120px; resize:vertical;
             font-family:ui-monospace,monospace; font-size:11px;
             background:var(--field, #0d1119);
             color:var(--ink); border:1px solid var(--edge); border-radius:6px;
             padding:6px; white-space:pre; }
  pre.raw { font-family:ui-monospace,monospace; font-size:11px; margin:6px 0 0;
            padding:6px; background:#120a10; border:1px solid var(--edge);
            border-radius:6px; color:var(--muted); white-space:pre-wrap;
            word-break:break-all; max-height:160px; overflow:auto; width:100%; }
  /* the attacker's standing equipment: always here, out of the way until wanted */
  details.tools { margin:8px 0; }
  details.tools > summary { cursor:pointer; font-weight:600; list-style:none;
         display:flex; align-items:center; gap:6px; width:max-content; }
  details.tools > summary::-webkit-details-marker { display:none; }
  details.tools > summary::before { content:'\25B8'; color:var(--muted); }
  details.tools[open] > summary::before { content:'\25BE'; }
  .tool { display:flex; gap:6px; flex-wrap:wrap; align-items:center; margin:6px 0; }
  .tool input.text { flex:1 1 160px; font-family:ui-monospace,monospace; font-size:11px; }
  #digestOut { width:100%; font-family:ui-monospace,monospace; font-size:11px;
               color:var(--c-mitm); word-break:break-all; min-height:16px; }
  a { color:var(--accent); }
  .hint { color:var(--warn); font-size:12px; margin-top:4px; }
  .chk { padding:5px 0; border-bottom:1px solid var(--edge); }
  .chk .n { font-weight:600; }
  .chk .d { color:var(--muted); font-size:12px; }
  .chk .r { font-family:ui-monospace,monospace; font-size:12px; }
  /* the Request cell takes what is left and never widens the table */
  td.req { width:100%; max-width:0; }
  .hdr { display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .hint code { color:var(--warn); }
  /* a maintenance request being worked on: the bar grows in real time on the
     same 1,500 ms track the logs use, then freezes on the reply. */
  .proc { height:10px; border-radius:5px; background:var(--edge); overflow:hidden;
          margin:8px 0 2px; }
  .proc i { display:block; height:100%; width:0; border-radius:5px;
            background:linear-gradient(90deg,var(--server),var(--accent)); }
  .proc.done i { background:var(--good); }
  .proc.busy i { background:linear-gradient(90deg,var(--server),var(--accent)); }
  /* a small note that appears beside a control after it has done something */
  .note { display:none; font-size:11px; padding:2px 8px; border-radius:20px;
          background:var(--accent); color:#04101f; font-weight:600;
          vertical-align:middle; }
  .note.show { display:inline-block; }
  /* slow hover help: only appears if the pointer really settles on something */
  #tip { position:fixed; z-index:99; display:none; max-width:270px;
         background:#05070c; color:var(--ink); border:1px solid var(--edge);
         border-radius:8px; padding:7px 10px; font-size:12px; line-height:1.4;
         box-shadow:0 8px 22px rgba(0,0,0,.6); pointer-events:none; }
  /* narrow screens: Client and Car server side by side, Interceptor below */
  @media (max-width:1100px) {
    .cols { min-height:0; }
    .panel { flex:1 1 calc(50% - 11px); min-height:auto; }
    .p-mitm { flex-basis:100%; }
    .p-client > .scroll { max-height:240px; }
    .p-mitm > .scroll { max-height:180px; }
    .held-list { max-height:180px; }
    #checksList { max-height:240px; }
  }
</style>
</head>
<body>
<header>
  <h1>🚗 Toy-Car HTTP Interceptor</h1>
  <label class="row" data-help="Loads a scenario. Each scenario changes what the car server checks in a request."><span class="muted">Scenario</span>
    <select id="scenarioSel" onchange="selectScenario()"></select></label>
  <button class="btn" onclick="resetScenario()"
    data-help="Returns this scenario to its starting state: car, client memory, server memory, and log.">Reset Scenario</button>
  <span class="summary" id="scenarioSummary"></span>
  <span id="scenarioError" class="badge" style="display:none;background:#3a0d0d;
        color:var(--bad);border-color:#6b1b1b"></span>
</header>

<div class="cols">
  <!-- ===================== CLIENT ===================== -->
  <section class="panel p-client">
    <h2>Client</h2>
    <div class="row" id="accountRow">
      <span class="muted" data-help="The account. Every request from this panel is sent as this user.">Account&nbsp;<b>student</b></span>
      <label style="margin-left:12px" data-help="Sets the password the client panel sends with a request.">Password
        <input id="passBox" type="text" size="12" value=""></label>
      <span id="passNote" class="no" style="font-size:12px"></span>
    </div>
    <div class="pad">
      <button class="b-F" onclick="press('F')"
        data-help="Sends a forward command.">&#9650;</button>
      <button class="b-L" onclick="press('L')"
        data-help="Sends a left-turn command.">&#9668;</button>
      <button class="b-R" onclick="press('R')"
        data-help="Sends a right-turn command.">&#9658;</button>
      <button class="b-B" onclick="press('B')"
        data-help="Sends a reverse command.">&#9660;</button>
    </div>
    <div class="keys">&#9650; forward &middot; &#9660; back &middot; &#9668; left &middot; &#9658; right</div>
    <div id="maintenanceBlock" style="display:none">
      <hr>
      <div><b>Maintenance access code</b></div>
      <div class="row">
        <input id="maintCode" size="12" placeholder="5 digits" maxlength="5"
          inputmode="numeric" oninput="this.value=this.value.replace(/[^0-9]/g,'')"
          data-help="The access code the maintenance door is expecting: five digits.">
        <button class="btn" id="maintSend" onclick="sendMaintenance()"
          data-help="Sends this code to the maintenance door over the network.">Send</button>
      </div>
      <div class="row">
        <textarea id="maintList" rows="4" style="min-height:0"
          oninput="tidyCodeList(this)"
          data-help="Up to 10 codes, one per line, five digits each. They are sent in the order shown."
          placeholder="Codes (one per line, max 10)"></textarea>
      </div>
      <div class="row">
        <button class="btn" id="maintSendList" onclick="sendMaintenanceList()"
          data-help="Sends each listed code through the network, one request at a time.">Send codes</button>
        <span class="muted" id="maintProgress"></span>
      </div>
      <div class="muted">Try the maintenance door with a few access codes.
        Every code you send is recorded in both request logs.</div>
    </div>
    <hr>
    <div><b>Client request log</b></div>
    <div class="scroll" data-help="Shows each request from the client panel and the HTTP result it received."><table>
      <thead><tr><th>time</th><th>command</th><th>user</th><th>result</th>
        <th class="ms" data-help="Shows the recorded duration for this network request. Bar length uses a fixed 1,500 ms scale; the number gives the exact value.">Duration&nbsp;(ms)</th></tr></thead>
      <tbody id="sentLog"></tbody></table></div>
    <div class="muted" id="sentEmpty">No requests yet.</div>
  </section>

  <!-- ===================== SERVER ===================== -->
  <section class="panel p-server">
    <h2>Car server</h2>
    <canvas id="field" width="400" height="400"
      data-help="The car moves only when the car server accepts a command."></canvas>
    <div id="lastCmd" class="lastcmd">last command: &mdash;</div>
    <div id="serverStatus" class="status">heading 0&deg;</div>
    <div id="procBox" style="display:none" data-help="Shows a maintenance request being worked on by the car server, and how long that is taking.">
      <hr>
      <div class="row"><b>Maintenance request</b>
        <span class="muted" id="procLabel">working&hellip;</span></div>
      <div class="proc"><i id="procFill"></i></div>
    </div>
    <hr>
    <div><b>Security properties</b></div>
    <div class="props" id="props"
      data-help="Shows the security properties this scenario claims. In Student Solution these come from PROPERTIES in your file and are not checked."></div>
    <div id="checksBlock" style="display:none">
      <hr>
      <div class="row"><b>Security check results</b>
        <button class="btn" id="checksBtn" onclick="runChecks()"
          data-help="Runs a fixed set of attacks against student_solution.py as it is saved right now.">Run security checks</button>
      </div>
      <div class="muted" id="checksStatus"></div>
      <div class="scroll" id="checksList"></div>
    </div>
    <div class="row" id="doorOptions" style="display:none">
      <label class="muted" data-help="Adds up to 20 ms of random variation to each maintenance-door response."><input type="checkbox" id="optJitter"
        onchange="setOption('jitter', this.checked)"> Vary response duration</label>
    </div>
    <hr>
    <div class="row">
      <button class="btn" onclick="resetCar()"
        data-help="Resets only the car position.">Reset car</button>
    </div>
    <div id="hashesBlock" style="display:none">
      <a href="/hashes" target="_blank"
        data-help="Opens the password digest the car server stores for the user.">Stored password digest</a>
      <div class="muted">The password digest the car server keeps for the
        user, as a file.</div>
      <div class="hint" data-help="A starting point for the offline cracking exercise.">Hint:
        unsalted SHA-256, hashcat mode <code>1400</code>.</div>
    </div>
  </section>

  <!-- ===================== INTERCEPTOR ===================== -->
  <section class="panel p-mitm" id="mitmPanel">
    <h2>Interceptor</h2>
    <div class="toggle">
      <span>Intercept:</span>
      <button id="toggleBtn" class="off" onclick="toggleIntercept()"
        data-help="When ON, each request from the client panel stops here until you choose what to do.">OFF</button>
      <span class="muted">Requests stay here until you forward or drop them.</span>
    </div>

    <div><b>Held</b> <span id="heldNote" class="note"></span></div>
    <div id="heldList" class="held-list"></div>
    <div id="heldEmpty" class="muted">No held requests.</div>

    <hr>
    <div class="row"><b>Request editor</b>
      <select id="captureSel" onchange="loadCapture()"
        data-help="Loads a saved copy of an earlier request into the editor.">
        <option value="">Load a captured request&hellip;</option>
      </select>
      <button class="btn accent" onclick="sendRaw()"
        data-help="Sends the request in the editor to the car server without using the client panel.">Send</button>
      <span id="sendNote" class="note"></span>
      <span id="sendResult" class="mono muted"
        data-help="Shows the HTTP result from the car server and the time in milliseconds."></span>
    </div>
    <textarea id="rawBox" spellcheck="false"
      data-help="A full HTTP request: request line, headers, and body."></textarea>

    <details class="tools">
      <summary data-help="Extra tools. They work only on text you give them.">Attacker tools</summary>
      <div class="tool">
        <select id="digAlg" data-help="Chooses the digest algorithm.">
          <option>sha256</option><option>sha1</option><option>md5</option>
        </select>
        <input class="text" id="digText" placeholder="exact text to fingerprint"
          data-help="The exact text to fingerprint. Every character counts, including spaces, quotes and braces.">
        <button class="btn" onclick="useEditorBody()"
          data-help="Copies the body of the request in the editor above into this box, exactly as written.">Use editor body</button>
        <button class="btn" onclick="runDigest()"
          data-help="Runs the chosen algorithm on the text and shows the result below.">Compute</button>
      </div>
      <div id="digestOut"></div>
    </details>

    <hr>
    <div class="row"><b>Network log</b>
      <label class="muted" style="margin-left:auto"
        data-help="Shows the full text of each request in the log.">
        <input type="checkbox" id="showRaw"> show full requests</label></div>
    <div class="scroll">
      <table>
        <thead><tr>
          <th data-help="When the request reached the car server.">Time</th>
          <th data-help="Which page section sent the request.">From</th>
          <th data-help="Shows the request line and the start of the body.">Request</th>
          <th data-help="Shows the HTTP result from the car server.">Result</th>
          <th style="text-align:right"
            data-help="Shows the recorded duration for this network request. Bar length uses a fixed 1,500 ms scale; the number gives the exact value.">Duration&nbsp;(ms)</th>
        </tr></thead>
        <tbody id="logBody"></tbody>
      </table>
    </div>
    <div class="muted" id="logEmpty">No requests yet.</div>
  </section>
</div>

<script>
async function jget(u){ const r = await fetch(u); return r.json(); }
async function jpost(u, body){
  const r = await fetch(u, {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(body || {})});
  return r.json();
}
function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function val(id){ const e = document.getElementById(id); return e ? e.value : ''; }
function nowStr(){ return new Date().toTimeString().slice(0,8); }

// ---------------- scenario ----------------
let META = {properties:{}};
async function pollScenario(){
  try {
    const s = await jget('/scenario/state');
    META = s;
    const sel = document.getElementById('scenarioSel');
    if(sel.options.length !== s.scenarios.length){
      sel.innerHTML = s.scenarios.map(x =>
        '<option value="'+x.id+'">'+esc(x.name)+'</option>').join('');
    }
    if(document.activeElement !== sel) sel.value = s.id;
    document.getElementById('scenarioSummary').textContent = s.summary || '';
    // Scenario 0 has no one in the middle, so the panel is not there either.
    document.getElementById('mitmPanel').style.display =
      s.interceptor === false ? 'none' : '';
    const err = document.getElementById('scenarioError');
    err.style.display = s.error ? 'inline' : 'none';
    err.textContent = s.error || '';
    document.getElementById('props').innerHTML =
      Object.keys(s.properties || {}).map(k =>
        '<span class="prop'+(s.properties[k] ? ' on' : '')+'">'+esc(k)+'</span>'
      ).join('') || '<span class="muted">not declared</span>';
    document.getElementById('doorOptions').style.display =
      s.id === 'maintenance' ? 'flex' : 'none';
    const checksOn = s.id === 'student';
    document.getElementById('checksBlock').style.display =
      checksOn ? '' : 'none';
    if(checksOn && !checksSeen){ checksSeen = true; pollChecks(); }
    if(!checksOn) checksSeen = false;
    const jit = document.getElementById('optJitter');
    if(document.activeElement !== jit) jit.checked = !!(s.options||{}).jitter;
    paintAccounts();
  } catch(e){}
}
async function selectScenario(){
  await jpost('/scenario/select', {id: val('scenarioSel')});
  sent.length = 0; renderSent();
  const pn = document.getElementById('passNote'); if(pn) pn.textContent = '';
  document.getElementById('rawBox').value = ''; loadedRaw = '';
  pollScenario();
}
async function resetScenario(){
  await jpost('/scenario/reset');
  sent.length = 0; renderSent();
  const pn = document.getElementById('passNote'); if(pn) pn.textContent = '';
  document.getElementById('rawBox').value = ''; loadedRaw = '';
  pollScenario();
}
async function setOption(name, value){ await jpost('/scenario/option', {name, value}); }

// ---------------- client ----------------
// The panel only shows the controls this account is meant to use.
function paintAccounts(){
  const show = (id, ok) => {
    const el = document.getElementById(id);
    if(el) el.style.display = ok ? '' : 'none';
  };
  // The account is part of the page only in the scenarios that use it.
  // Until then the car has one driver and the panel says nothing about who.
  const accounts = !!META.accounts;
  show('accountRow', accounts);
  if(!accounts){ const n = document.getElementById('passNote'); if(n) n.textContent = ''; }
  // the stored password digest only means something once there is an account
  show('hashesBlock', accounts);
  // the maintenance door is a separate entrance, not one of the car commands
  show('maintenanceBlock', !!META.maintenance);
  // the processing bar lives with the door; nothing to work on without it
  if(!META.maintenance){ const pb = document.getElementById('procBox');
    if(pb) pb.style.display = 'none'; }
}

// Both logs draw duration the same way, on a fixed track: rows stay comparable
// across the whole run instead of rescaling as results arrive.  Scaling to the
// largest value seen so far would look tidier, but it would turn ordinary
// sub-millisecond noise in the other scenarios into dramatic-looking bars.
const MS_FULL = 1500;
function msCell(ms){
  if(ms == null) return '<td class="ms"></td>';
  const w = Math.min(100, Math.max(0, 100 * Number(ms) / MS_FULL));
  return '<td class="ms"><span class="bar"><i style="width:'+w+'%"></i></span>'
    + Number(ms).toFixed(1) + '</td>';
}

const sent = [];
function renderSent(){
  document.getElementById('sentEmpty').style.display = sent.length ? 'none':'block';
  document.getElementById('sentLog').innerHTML = sent.slice().reverse().map(s =>
    '<tr><td class="mono">'+esc(s.ts)+'</td><td class="mono">'+esc(s.command)+'</td>'
    + '<td class="mono">'+esc(s.user)+'</td>'
    + '<td class="'+s.cls+'">'+esc(s.state)+'</td>'
    + msCell(s.ms)+'</tr>').join('');
}
async function press(command){
  const accounts = !!META.accounts;
  const user = accounts ? 'student' : 'driver';
  const entry = {ts: nowStr(), command, user: accounts ? user : '',
                 state:'sending…', cls:'wait'};
  sent.push(entry);
  if(sent.length > 60) sent.shift();
  renderSent();
  try {
    const res = await jpost('/client/press',
      {command, user, password: accounts ? val('passBox') : ''});
    entry.ms = res.ms;
    if(res.status === 'accepted'){ entry.state = 'accepted'; entry.cls = 'ok'; }
    else if(res.status === 'rejected'){ entry.state = 'rejected'; entry.cls = 'no'; }
    else { entry.state = res.status || 'no reply'; entry.cls = 'no'; }
    const note = document.getElementById('passNote');
    if(note){
      note.textContent = res.auth === 'missing' ? 'Enter the password.'
        : res.auth === 'wrong' ? "That password isn't correct." : '';
    }
  } catch(e){ entry.state = 'error'; entry.cls = 'no'; }
  renderSent();
}
const CODE_OK = /^[0-9]{5}$/;
const CODE_LEN = 5, CODE_MAX = 10;

// Keep the list field to what it can actually send: digits only, five to a
// line, ten lines.  Doing it here means nothing is silently dropped later.
function tidyCodeList(el){
  const next = el.value.split('\n')
    .map(line => line.replace(/[^0-9]/g, '').slice(0, CODE_LEN))
    .slice(0, CODE_MAX).join('\n');
  if(next === el.value) return;
  const atEnd = el.selectionStart === el.value.length;
  el.value = next;
  if(atEnd) el.selectionStart = el.selectionEnd = el.value.length;
}
async function sendMaintenance(){
  if(maintBusy) return;
  const code = val('maintCode');
  const out = document.getElementById('maintProgress');
  if(!CODE_OK.test(code)){ out.textContent = 'Enter five digits.'; return; }
  out.textContent = '';
  maintLock(true);
  try { await sendOneCode(code); } finally { maintLock(false); }
}

// Sent one at a time, so each result is on screen before the next goes out.
async function sendMaintenanceList(){
  const lines = val('maintList').split('\n')
    .map(c => c.trim()).filter(c => c.length);
  const good = lines.filter(c => CODE_OK.test(c));
  const codes = good.slice(0, CODE_MAX);
  const short = lines.length - good.length;
  const over = good.length - codes.length;
  const out = document.getElementById('maintProgress');
  if(maintBusy) return;
  maintLock(true);
  try {
    for(let i = 0; i < codes.length; i++){
      out.textContent = 'Sending ' + (i+1) + ' of ' + codes.length + '…';
      await sendOneCode(codes[i]);
    }
  } finally { maintLock(false); }
  out.textContent = (codes.length ? 'Sent ' + codes.length + ' codes.' : '')
    + (short ? ' Skipped ' + short + ' that were not five digits.' : '')
    + (over ? ' Ignored ' + over + ' past the limit of ' + CODE_MAX + '.' : '');
}

// The processing bar grows in real time while the car server works on a
// maintenance code, on the same 1,500 ms track as the logs, then freezes on
// the reply.  It shows only that a request is being worked on and how long
// that takes: the same thing the Duration column records, made visible as it
// happens.  Back-to-back codes from Send codes reuse one bar in turn.
let procRAF = null;
let maintBusy = false;
// One request works at a time, so the single shared bar always belongs to the
// request in flight.  The controls come back the moment it is answered.
function maintLock(on){
  maintBusy = on;
  ['maintSend','maintSendList'].forEach(id => {
    const el = document.getElementById(id); if(el) el.disabled = on;
  });
}
function procStart(){
  const box = document.getElementById('procBox');
  const fill = document.getElementById('procFill');
  const bar = fill.parentElement;
  box.style.display = '';
  bar.className = 'proc busy';
  document.getElementById('procLabel').textContent = 'working…';
  const started = performance.now();
  cancelAnimationFrame(procRAF);
  const step = () => {
    const w = Math.min(100, 100 * (performance.now() - started) / MS_FULL);
    fill.style.width = w + '%';
    procRAF = requestAnimationFrame(step);
  };
  procRAF = requestAnimationFrame(step);
}
function procStop(ms, accepted){
  cancelAnimationFrame(procRAF); procRAF = null;
  const fill = document.getElementById('procFill');
  const bar = fill.parentElement;
  const w = ms == null ? 0 : Math.min(100, 100 * Number(ms) / MS_FULL);
  fill.style.width = w + '%';
  bar.className = 'proc done';
  document.getElementById('procLabel').textContent =
    (accepted ? 'accepted' : 'answered') + (ms != null ? ' after ' + Number(ms).toFixed(0) + ' ms' : '');
}

async function sendOneCode(code){
  const entry = {ts: nowStr(), command:'maintenance', user:'',
                 state:'sending…', cls:'wait'};
  sent.push(entry);
  if(sent.length > 60) sent.shift();
  renderSent();
  procStart();
  try {
    const res = await jpost('/client/maintenance', {code});
    entry.ms = res.ms;
    if(res.status === 'accepted'){ entry.state = 'accepted'; entry.cls = 'ok'; }
    else if(res.status === 'rejected'){ entry.state = 'rejected'; entry.cls = 'no'; }
    else { entry.state = res.status || 'no reply'; entry.cls = 'no'; }
    procStop(entry.ms, res.status === 'accepted');
  } catch(e){ entry.state = 'error'; entry.cls = 'no'; procStop(null, false); }
  renderSent();
}
async function resetCar(){ await jpost('/car/reset'); }

// ---------------- security checks ----------------
// Only the student scenario has a solution of its own to check.
let checksTimer = null;
let checksSeen = false;
async function runChecks(){
  await jpost('/checks/run', {});
  pollChecks();
}
function renderChecks(s){
  const btn = document.getElementById('checksBtn');
  const status = document.getElementById('checksStatus');
  const list = document.getElementById('checksList');
  const running = s.state === 'running';
  btn.disabled = running;
  if(running){
    status.textContent = 'Security checks are running. '
      + 'You can keep exploring the page.';
  } else if(s.state === 'error'){
    status.textContent = s.error || 'the checks could not run';
  } else if(s.state === 'done'){
    status.textContent = s.passed + ' of ' + s.total + ' checks passed.';
  } else {
    status.textContent = '';
  }
  list.innerHTML = (s.results || []).map(r =>
    '<div class="chk"><span class="n">'+esc(r.name)+'</span> '
    + '<span class="r '+(r.ok ? 'ok' : 'no')+'">'
    + (r.ok ? 'PASS - attack did not succeed'
            : 'FAIL - attack succeeded')+'</span>'
    + '<div class="d">'+esc(r.error || r.description)+'</div></div>').join('');
}
async function pollChecks(){
  try {
    const s = await jget('/checks/state');
    renderChecks(s);
    clearTimeout(checksTimer);
    if(s.state === 'running') checksTimer = setTimeout(pollChecks, 700);
  } catch(e){}
}

// ---------------- interceptor ----------------
function paintToggle(on){
  const b = document.getElementById('toggleBtn');
  b.textContent = on ? 'ON' : 'OFF';
  b.className = on ? 'on' : 'off';
}
async function toggleIntercept(){ const s = await jpost('/intercept/toggle'); paintToggle(s.on); }
// Shows a short note beside a control, then takes it away again.
const noteTimers = {};
function note(id, text){
  const el = document.getElementById(id);
  el.textContent = text;
  el.classList.add('show');
  clearTimeout(noteTimers[id]);
  noteTimers[id] = setTimeout(() => el.classList.remove('show'), 6000);
}
function sameText(a, b){ return String(a||'').trim() === String(b||'').trim(); }

async function forward(id){
  const original = (heldRaw[id] || '');
  const edited = val('held-'+id);
  await jpost('/intercept/action', {id, action:'forward',
    raw: edited, delay_ms: Number(val('delay-'+id) || 0)});
  note('heldNote', sameText(edited, original)
    ? 'Sent unmodified request' : 'Sent modified request');
}
async function drop(id){ await jpost('/intercept/action', {id, action:'drop'}); }

let captures = [];
let heldKey = '';
let heldRaw = {};         // id -> the text as it arrived, to compare on Forward
let loadedRaw = '';       // what the Request editor was last filled with
async function pollIntercept(){
  try {
    const s = await jget('/intercept/state');
    paintToggle(s.on);
    captures = s.captures || [];
    const csel = document.getElementById('captureSel');
    if(document.activeElement !== csel){
      csel.innerHTML = '<option value="">Load a captured request…</option>'
        + captures.map((c,i) => '<option value="'+i+'">'+esc(c.ts)+'  '
            + esc(c.line)+'</option>').join('');
    }
    const pend = s.pending || [];
    document.getElementById('heldEmpty').style.display = pend.length ? 'none':'block';
    const key = pend.map(p => p.id).join(',');
    if(key === heldKey) return;          // do not wipe what is being typed
    heldKey = key;
    heldRaw = {};
    pend.forEach(p => { heldRaw[p.id] = p.raw; });
    document.getElementById('heldList').innerHTML = pend.map(p =>
      '<div class="held">'
      + '<span class="muted">held '+esc(p.ts)+'</span>'
      + '<label class="muted" style="margin-left:auto" data-help="Wait time in milliseconds before forwarding this request.">delay ms '
      + '<input id="delay-'+p.id+'" size="5" value="0"></label>'
      + '<button class="fwd" onclick="forward('+p.id+')"'
      + ' data-help="Sends this request to the car server.">Forward</button>'
      + '<button class="drop" onclick="drop('+p.id+')"'
      + ' data-help="Drops this request. The car server does not receive it.">Drop</button>'
      + '<textarea id="held-'+p.id+'" spellcheck="false"'
      + ' data-help="Edit this request. The car server receives exactly what is here.">'
      + esc(p.raw)+'</textarea>'
      + '</div>').join('');
  } catch(e){}
}
function loadCapture(){
  const i = val('captureSel');
  if(i === '') return;
  const c = captures[Number(i)];
  if(c){ document.getElementById('rawBox').value = c.raw; loadedRaw = c.raw; }
  document.getElementById('captureSel').value = '';
}
async function sendRaw(){
  const box = document.getElementById('rawBox');
  const out = document.getElementById('sendResult');
  if(!box.value.trim()){ out.textContent = 'Request editor is empty.'; return; }
  out.textContent = '…';
  note('sendNote', !loadedRaw ? 'Sent new request'
    : sameText(box.value, loadedRaw) ? 'Sent unmodified request'
    : 'Sent modified request');
  const res = await jpost('/wire/send', {raw: box.value});
  out.innerHTML = '<b>'+esc(res.code || '')+'</b> '
    + esc(res.status || '') + '   ' + (res.ms != null ? res.ms.toFixed(1)+' ms' : '');
}
// The body is everything after the first blank line, exactly as it will be
// sent.  Copying it here rather than retyping it is the difference between a
// digest that matches and one that does not.
function useEditorBody(){
  const raw = val('rawBox').replace(/\r\n/g, '\n');
  const i = raw.indexOf('\n\n');
  document.getElementById('digText').value = i < 0 ? '' : raw.slice(i + 2);
}
async function runDigest(){
  const out = document.getElementById('digestOut');
  const r = await fetch('/tools/digest', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({alg: val('digAlg'), text: val('digText')})});
  const res = await r.json();
  out.textContent = res.digest || res.error || '';
}

// Every header line that is not part of plain HTTP plumbing, on one line, so
// the log shows what a request carries without opening the full text.  Long
// values are cut short; the full request is one tick of "show full requests"
// away.
function extraHeaders(headLines){
  return headLines.slice(1).filter(l => !/^(host|content-type|content-length):/i.test(l))
    .map(l => {
      const i = l.indexOf(':');
      const k = l.slice(0, i), v = l.slice(i+1).trim();
      return '<span class="hdr">' + esc(k + ': '
        + (v.length > 26 ? v.slice(0, 24) + '…' : v)) + '</span>';
    }).join('');
}
async function pollHistory(){
  try {
    const {history} = await jget('/history');
    const raw = document.getElementById('showRaw').checked;
    document.getElementById('logEmpty').style.display = history.length ? 'none' : 'block';
    document.getElementById('logBody').innerHTML = history.slice().reverse().map(h => {
      const head = (h.raw || '').split('\n\n')[0].split('\n');
      const line = head[0] || '';
      const body = (h.raw || '').split('\n\n')[1] || '';
      const tags = (h.flags || []).map(f => '<span class="tag">'+esc(f)+'</span>').join('');
      let tr = '<tr><td class="mono">'+esc(h.ts)+'</td><td>'+esc(h.source)+'</td>'
        + '<td class="mono req">'+esc(line)+tags
        + '<div class="muted mono">'+extraHeaders(head)+'</div>'
        + '<div class="muted mono">'+esc(body.slice(0,70))+'</div></td>'
        + '<td class="s-'+esc(h.status)+'">'+esc(h.code||'')+' '+esc(h.status)
        + (h.reason ? '<div class="muted">'+esc(h.reason)+'</div>' : '')+'</td>'
        + msCell(h.ms)+'</tr>';
      if(raw && h.raw) tr += '<tr><td colspan="5"><pre class="raw">'+esc(h.raw)+'</pre></td></tr>';
      return tr;
    }).join('');
  } catch(e){}
}

// ---------------- slow hover help ----------------
// Anything carrying data-help explains itself, but only after the pointer has
// stayed put for HELP_DELAY. Sweeping across the panel shows nothing.
const HELP_DELAY = 3000;
const tip = document.createElement('div');
tip.id = 'tip';
document.body.appendChild(tip);
let helpTimer = null, helpFor = null, mouseX = 0, mouseY = 0;

function hideHelp(){
  clearTimeout(helpTimer);
  helpTimer = null; helpFor = null;
  tip.style.display = 'none';
}
function showHelp(text){
  tip.textContent = text;
  tip.style.display = 'block';
  const pad = 16;
  let left = mouseX + pad, top = mouseY + pad;
  if(left + tip.offsetWidth > window.innerWidth - 8)
    left = window.innerWidth - tip.offsetWidth - 8;
  if(top + tip.offsetHeight > window.innerHeight - 8)
    top = mouseY - tip.offsetHeight - pad;
  tip.style.left = Math.max(8, left) + 'px';
  tip.style.top = Math.max(8, top) + 'px';
}
document.addEventListener('mousemove', e => { mouseX = e.clientX; mouseY = e.clientY; });
document.addEventListener('mouseover', e => {
  const el = e.target.closest ? e.target.closest('[data-help]') : null;
  if(el === helpFor) return;
  hideHelp();
  if(!el) return;
  helpFor = el;
  helpTimer = setTimeout(() => showHelp(el.getAttribute('data-help')), HELP_DELAY);
});
document.addEventListener('mousedown', hideHelp);
document.addEventListener('scroll', hideHelp, true);
window.addEventListener('blur', hideHelp);

// ---------------- car canvas ----------------
const cv = document.getElementById('field'), ctx = cv.getContext('2d');
let target = {x:200,y:200,heading:0};
let shown  = {x:200,y:200,heading:0};
const ARROW = {F:'▲ forward', B:'▼ back', L:'◄ turn left',
               R:'► turn right', ADMIN_RESET:'workshop reset'};
async function pollCar(){
  try {
    target = await jget('/car/state');
    document.getElementById('serverStatus').textContent =
      'heading '+((target.heading%360+360)%360)+'°  ·  ('
      +Math.round(target.x)+', '+Math.round(target.y)+')';
    const c = target.last_command || {};
    const box = document.getElementById('lastCmd');
    if(!c.command){ box.innerHTML = 'last command: &mdash;'; }
    else {
      const cls = c.status === 'accepted' ? 'ok' : 'no';
      box.innerHTML = 'last command: <b>'+esc(c.command)+'</b> '
        + esc(ARROW[c.command] || '') + ' · <span class="'+cls+'">'
        + esc(c.status)+'</span> · '+esc(c.ts);
    }
  } catch(e){}
}
function shortestAngle(a, b){ let d = ((b - a + 540) % 360) - 180; return a + d; }
function draw(){
  shown.x += (target.x - shown.x) * 0.25;
  shown.y += (target.y - shown.y) * 0.25;
  shown.heading += (shortestAngle(shown.heading, target.heading) - shown.heading) * 0.25;
  ctx.clearRect(0,0,400,400);
  ctx.strokeStyle = '#2b2415'; ctx.lineWidth = 1;
  for(let i=0;i<=400;i+=40){
    ctx.beginPath(); ctx.moveTo(i,0); ctx.lineTo(i,400); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0,i); ctx.lineTo(400,i); ctx.stroke();
  }
  drawCar(shown.x, shown.y, shown.heading);
  requestAnimationFrame(draw);
}
function roundRect(x, y, w, h, r){
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y,     x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x,     y + h, r);
  ctx.arcTo(x,     y + h, x,     y,     r);
  ctx.arcTo(x,     y,     x + w, y,     r);
  ctx.closePath();
}
function carBody(){
  ctx.beginPath();
  ctx.moveTo(0, -25);
  ctx.bezierCurveTo(7, -25,   11.5, -20,  11.5, -12);
  ctx.bezierCurveTo(12.5, -4, 12.5, 8,    11.5, 16);
  ctx.bezierCurveTo(11, 21,   7, 23,      0, 23);
  ctx.bezierCurveTo(-7, 23,   -11, 21,    -11.5, 16);
  ctx.bezierCurveTo(-12.5, 8, -12.5, -4,  -11.5, -12);
  ctx.bezierCurveTo(-11.5, -20, -7, -25,  0, -25);
  ctx.closePath();
}
function glass(y0, y1, w0, w1){
  ctx.beginPath();
  ctx.moveTo(-w0, y0); ctx.lineTo(w0, y0);
  ctx.lineTo(w1, y1);  ctx.lineTo(-w1, y1);
  ctx.closePath(); ctx.fill();
}
function drawCar(x, y, heading){
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(heading * Math.PI/180);
  [[-15.5,-16],[9.5,-16],[-15.5,6],[9.5,6]].forEach(([wx, wy]) => {
    ctx.fillStyle = '#28303f';
    roundRect(wx, wy, 6, 11, 2.5); ctx.fill();
    ctx.fillStyle = '#39445a';
    roundRect(wx, wy, 6, 3, 1.5); ctx.fill();
  });
  ctx.save();
  ctx.translate(1.5, 2.5);
  ctx.fillStyle = 'rgba(0,0,0,.4)';
  carBody(); ctx.fill();
  ctx.restore();
  const paint = ctx.createLinearGradient(-12, 0, 12, 0);
  paint.addColorStop(0,   '#245e9e');
  paint.addColorStop(.35, '#4da3ff');
  paint.addColorStop(.75, '#3b8ae0');
  paint.addColorStop(1,   '#1f5490');
  ctx.fillStyle = paint;
  ctx.strokeStyle = '#cfe6ff'; ctx.lineWidth = 1.2;
  carBody(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,.12)';
  roundRect(-8.5, -9, 17, 19, 5); ctx.fill();
  ctx.fillStyle = '#0a1e33';
  glass(-9.5, -15.5, 8.5, 6);
  glass(10, 15, 8.5, 6.5);
  ctx.fillStyle = '#ffeaa7';
  ctx.beginPath();
  ctx.moveTo(-9.5, -19); ctx.lineTo(-4, -22.5); ctx.lineTo(-3.5, -20);
  ctx.lineTo(-8.5, -17); ctx.closePath(); ctx.fill();
  ctx.beginPath();
  ctx.moveTo(9.5, -19); ctx.lineTo(4, -22.5); ctx.lineTo(3.5, -20);
  ctx.lineTo(8.5, -17); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#ff5f5f';
  roundRect(-9, 18.5, 6, 3, 1.5); ctx.fill();
  roundRect(3, 18.5, 6, 3, 1.5); ctx.fill();
  ctx.restore();
  const rad = heading * Math.PI/180;
  ctx.save();
  ctx.translate(x + Math.sin(rad)*32, y - Math.cos(rad)*32);
  ctx.rotate(rad);
  ctx.fillStyle = '#ffce54';
  ctx.beginPath();
  ctx.moveTo(0,-6); ctx.lineTo(-5,3); ctx.lineTo(5,3);
  ctx.closePath(); ctx.fill();
  ctx.restore();
}

// ---------------- boot ----------------
pollScenario(); pollCar(); pollIntercept(); pollHistory();
setInterval(pollCar, 150);
setInterval(pollIntercept, 300);
setInterval(pollHistory, 600);
setInterval(pollScenario, 1500);
requestAnimationFrame(draw);
</script>
</body>
</html>
"""
