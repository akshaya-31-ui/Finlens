const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let chosen = null;

fetch('/api/health').then(r => r.json()).then(h => { if (h.llm) $('strategyField').hidden = false; }).catch(() => {});

function pick(f) {
  if (!f) return;
  if (!/\.pdf$/i.test(f.name)) return show(`<div class="err">That file is not a PDF. Export the report as a PDF and try again.</div>`);
  chosen = f; $('dropTitle').textContent = f.name;
  $('dropHint').textContent = (f.size / 1048576).toFixed(1) + ' MB. Choose another file to replace it.';
  $('drop').classList.add('has'); $('go').disabled = false;
}
$('file').addEventListener('change', e => pick(e.target.files[0]));
$('drop').addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); $('file').click(); } });
['dragenter','dragover'].forEach(t => $('drop').addEventListener(t, e => { e.preventDefault(); $('drop').classList.add('over'); }));
['dragleave','drop'].forEach(t => $('drop').addEventListener(t, e => { e.preventDefault(); $('drop').classList.remove('over'); }));
$('drop').addEventListener('drop', e => pick(e.dataTransfer.files[0]));
$('form').addEventListener('submit', e => { e.preventDefault(); run(false); });
$('sample').addEventListener('click', () => run(true));

function show(html) { $('out').innerHTML = html; }

async function run(sample) {
  const fd = new FormData();
  fd.append('strategy', $('strategy').value);
  if (sample) fd.append('sample', '1'); else fd.append('file', chosen);
  $('go').disabled = true;
  show(`<div class="busy"><span class="spin"></span>Reading the report. Large files can take up to a minute.</div>`);
  try {
    const r = await fetch('/api/analyze', { method: 'POST', body: fd });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || 'Analysis failed.');
    render(d);
  } catch (err) {
    show(`<div class="err"><strong>Could not analyze this report.</strong><br>${esc(err.message)}</div>`);
  } finally { $('go').disabled = !chosen; }
}

const fmt = n => n == null ? '–' : Math.abs(n) >= 100 ? n.toLocaleString('en-US', {maximumFractionDigits: 1}) : n.toLocaleString('en-US', {maximumFractionDigits: 2});
const pct = c => c == null ? '–' : `<span class="${c >= 0 ? 'up' : 'down'}">${c >= 0 ? '+' : '−'}${Math.abs(c * 100).toFixed(1)}%</span>`;
const word = {good: 'Healthy', watch: 'Watch', weak: 'Weak'};

function render(d) {
  let h = '';
  if (d.health) h += `<div class="panel"><div class="head"><div><div class="score">${d.health.score}<small>out of 100, ${esc(d.health.label)}</small></div></div>
    <p class="sub">Based on ${d.health.based_on} ratios found in the report</p></div>
    <div class="meter" role="img" aria-label="Score ${d.health.score} out of 100"><i style="width:${d.health.score}%"></i></div>
    <p class="sum">${esc(d.summary)}</p></div>`;
  else h += `<div class="panel"><h2>Summary</h2><p class="sum">${esc(d.summary)}</p></div>`;

  if (d.figures.length) {
    h += `<div class="panel"><h2>Figures from the statements${d.units ? ` <span class="sub">(in ${esc(d.units)})</span>` : ''}</h2><div class="scroll"><table class="ledger"><thead><tr><th>Figure</th><th class="n">This year</th><th class="n">Last year</th><th class="n">Change</th></tr></thead><tbody>` +
      d.figures.map(f => `<tr><td>${esc(f.label)}${f.derived ? ' <span class="why">(calculated)</span>' : ''}</td><td class="n">${fmt(f.current)}</td><td class="n">${fmt(f.prior)}</td><td class="n">${pct(f.change)}</td></tr>`).join('') + `</tbody></table></div></div>`;
  } else h += `<div class="panel"><h2>Figures from the statements</h2><p class="none">No standard statement lines were recognised. Reports that present tables as images cannot be read.</p></div>`;

  if (d.ratios.length) {
    h += `<div class="panel"><h2>Ratios</h2><div class="scroll"><table class="ledger"><thead><tr><th>Ratio</th><th class="n">Value</th><th>Rating</th><th>What it tells you</th></tr></thead><tbody>` +
      d.ratios.map(r => `<tr><td>${esc(r.label)}</td><td class="n">${esc(r.value)}</td><td><span class="chip ${r.status}">${word[r.status]}</span></td><td class="why">${esc(r.note)}</td></tr>`).join('') + `</tbody></table></div></div>`;
  }

  const q = (L, cls) => L.length ? L.map(x => `<p class="quote ${cls}">${esc(x.text)}<small>Model confidence ${Math.round(x.confidence * 100)}%</small></p>`).join('') : `<p class="none">Nothing flagged.</p>`;
  h += `<div class="panel"><h2>What the narrative says</h2><div class="cols"><div><h3>Risk language</h3>${q(d.tone.risk, 'risk')}</div><div><h3>Positive developments</h3>${q(d.tone.growth, 'growth')}</div></div></div>`;

  if (d.llm) h += `<div class="panel"><h2>AI commentary</h2><p class="ai">${esc(d.llm)}</p></div>`;
  if (d.llm_error) h += `<div class="err">${esc(d.llm_error)}</div>`;
  show(h);
}
