// Presentation only. Python is the single source for scientific calculations.
const $ = selector => document.querySelector(selector);
const state = {rows: [], research: null, summary: {}, quality: {}, page: 0, editing: null, request: 0};
const fmt = (value, digits = 0) => value == null ? '—' : Number(value).toLocaleString('en-US', {maximumFractionDigits: digits});
const iso = value => String(value).slice(0, 10);
const escapeHtml = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[character]));

async function request(path, options = {}) {
  const response = await fetch(path, {...options, headers: {'Content-Type': 'application/json', ...options.headers}});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
function error(message) { $('#error').textContent = message; $('#error').classList.toggle('hidden', !message); }
async function refresh() {
  const sequence = ++state.request;
  $('#loading').classList.remove('hidden');
  $('#apply').disabled = true;
  try {
    const params = new URLSearchParams();
    if ($('#start').value) params.set('start', $('#start').value);
    if ($('#end').value) params.set('end', $('#end').value);
    const [data, research] = await Promise.all([request(`/api/observations?${params}`), request('/api/research')]);
    if (sequence !== state.request) return;
    Object.assign(state, {rows: data.observations, summary: data.summary, quality: data.quality, research, page: 0});
    error(''); render();
  } catch (err) { if (sequence === state.request) error(err.message); }
  finally { if (sequence === state.request) { $('#loading').classList.add('hidden'); $('#apply').disabled = false; } }
}
function changeView(view) {
  document.querySelectorAll('.view').forEach(element => element.classList.toggle('hidden', element.id !== view));
  document.querySelectorAll('.nav').forEach(button => button.classList.toggle('active', button.dataset.view === view));
  $('#page-name').textContent = document.querySelector(`[data-view="${view}"] span`).textContent;
  $('#filters').classList.toggle('hidden', ['models','methods'].includes(view));
}
function card(label, value, caption) { return `<div class="kpi"><div class="stripe"></div><div class="tag">${label}</div><div class="value">${value}</div><div class="caption">${caption}</div></div>`; }

// Every observation is plotted against its actual calendar timestamp. SVG titles
// provide a hover readout, and the explorer provides a downloadable numeric view.
function chart(target, rows, series, options = {}) {
  const box = $(target);
  if (!rows.length) { box.innerHTML = '<div class="chart-empty">No observations in this range.</div>'; return; }
  const dates = rows.map(row => new Date(iso(row.date) + 'T00:00:00Z').getTime());
  const valid = rows.flatMap(row => series.map(s => row[s.key])).filter(value => value != null && Number.isFinite(Number(value)));
  if (!valid.length) { box.innerHTML = '<div class="chart-empty">More observations are needed for this rolling window.</div>'; return; }
  let low = Math.min(0, ...valid), high = Math.max(0, ...valid);
  if (high === low) high = low + 1;
  const span = high - low; high += span * .07; if (low < 0) low -= span * .07;
  const begin = Math.min(...dates), end = Math.max(...dates);
  const x = value => 62 + (end === begin ? .5 : (value - begin)/(end-begin)) * 664;
  const y = value => 240 - (value-low)/(high-low)*190;
  const ticks = [0,1,2,3,4].map(i => {
    const value = low + (high-low)*i/4, vertical = y(value);
    return `<line x1="62" x2="726" y1="${vertical}" y2="${vertical}" stroke="#e9edf3"/><text x="52" y="${vertical+4}" text-anchor="end" class="axis-label">${fmt(value, options.decimals || 0)}</text>`;
  }).join('');
  const labels = [0,.5,1].map(fraction => {
    const time = begin + (end-begin)*fraction;
    return `<text x="${62 + fraction*664}" y="266" text-anchor="${fraction===0?'start':fraction===1?'end':'middle'}" class="axis-label">${new Date(time).toISOString().slice(0,10)}</text>`;
  }).join('');
  const legend = series.map((s,i) => `<circle cx="${64+i*195}" cy="18" r="4" fill="${s.color}"/><text x="${75+i*195}" y="22" class="legend-label">${s.label}</text>`).join('');
  const lines = series.map(s => {
    let path = '', connected = false, dots = '';
    rows.forEach((row,i) => {
      const value = row[s.key];
      if (value == null || !Number.isFinite(Number(value))) {connected=false; return;}
      const px = x(dates[i]), py = y(value);
      path += `${connected ? 'L' : 'M'}${px.toFixed(2)},${py.toFixed(2)} `; connected=true;
      dots += `<circle class="data-point" cx="${px}" cy="${py}" r="4" fill="${s.color}"><title>${iso(row.date)} · ${s.label}: ${fmt(value,2)}</title></circle>`;
    });
    return `<path d="${path}" fill="none" stroke="${s.color}" stroke-width="2" vector-effect="non-scaling-stroke" ${s.dash?'stroke-dasharray="5 4"':''}/>${dots}`;
  }).join('');
  const zero = low < 0 ? `<line x1="62" x2="726" y1="${y(0)}" y2="${y(0)}" stroke="#8494aa" stroke-dasharray="3 4"/>` : '';
  box.innerHTML = `<svg viewBox="0 0 760 280" role="img" aria-label="${series.map(s=>s.label).join(', ')} over actual reporting dates">${ticks}${zero}${legend}${lines}${labels}</svg>`;
}
function currentFeatures() {
  const dates = new Set(state.rows.map(row=>row.date));
  return state.research.observations.filter(row=>dates.has(iso(row.date)));
}
function renderOverview() {
  const r=state.research, s=state.summary;
  $('#coverage').textContent = `${r.source_audit.valid_rows} SOURCE OBSERVATIONS · ${r.source_audit.first_date} — ${r.source_audit.last_date}`;
  $('#source-status').textContent = r.matches_source ? '✓ WORKING DATA MATCHES SOURCE' : 'WORKING COPY MODIFIED';
  $('#workspace-warning').classList.toggle('hidden', r.matches_source);
  $('#workspace-warning').textContent = 'This working database differs from the supplied CSV. Dashboard results reflect your edits; the submitted report and notebook describe the original source.';
  $('#filter-count').textContent = `${fmt(s.count)} selected observations`;
  $('#asof').textContent = s.count ? `LATEST SELECTED · ${s.last_date}` : 'EMPTY RANGE';
  if (s.count) {
    const calendar = Math.round((Date.parse(s.last_date)-Date.parse(s.first_date))/86400000)+1;
    $('#kpis').innerHTML = card('Latest total load', fmt(s.latest.total_load), `${s.last_date} · CBP + HHS census`)
      + card('Observed-date coverage', fmt(100*s.count/calendar,1)+'%', `${fmt(s.count)} of ${fmt(calendar)} calendar dates in range`)
      + card('Net HHS flow', (s.average_net_flow>0?'+':'')+fmt(s.average_net_flow,1), `Mean per observation · trailing ${s.recent_window}`)
      + card('Discharge offset', fmt(s.aggregate_offset_ratio,3)+'×', `Aggregate ratio · trailing ${s.recent_window}`);
  } else $('#kpis').innerHTML='';
  chart('#load-chart', currentFeatures(), [{key:'total_load',label:'Total reported load',color:'#ce8248'},{key:'load_mean7',label:'7-observation mean',color:'#4b6b94',dash:true}]);
  const years = {};
  state.rows.forEach(row=>{const y=row.date.slice(0,4); (years[y] ||= []).push(row.total_load);});
  const means = Object.entries(years).map(([year,values])=>({year,count:values.length,mean:values.reduce((a,b)=>a+b,0)/values.length}));
  const max = Math.max(1,...means.map(row=>row.mean));
  $('#year-comparison').innerHTML = means.map(row=>`<div class="year-row"><div><strong>${row.year}</strong><span>${fmt(row.mean)} children</span></div><div class="bar-track"><div style="width:${row.mean/max*100}%"></div></div><small>${row.count} reported observations</small></div>`).join('') || 'No observations.';
  const m=r.models, selected=m.available?m.scores.find(row=>row.model===m.selected_model):null;
  $('#findings').innerHTML = `<article class="finding"><span>01 / LONG-TERM CHANGE</span><h3>${fmt(r.summary.change_from_peak_pct,1)}% from observed peak</h3><p>Full history: ${fmt(r.summary.latest_load)} at the latest source date versus ${fmt(r.summary.peak_load)} on ${r.summary.peak_date}.</p></article><article class="finding"><span>02 / MISSINGNESS MATTERS</span><h3>${fmt(r.summary.unobserved_days)} unobserved dates</h3><p>Full coverage is ${fmt(r.summary.coverage_pct,1)}%. Reporting gaps stay visible throughout analysis and target construction.</p></article><article class="finding"><span>03 / EVALUATED PREDICTION</span><h3>${m.available?fmt(selected.test.mae,1)+' children MAE':'Insufficient model data'}</h3><p>${m.available?`${m.selected_model} was selected on validation; its test improvement versus persistence is ${fmt(m.test_skill_vs_persistence_pct,1)}%.`:'More exact seven-day pairs are required.'}</p></article>`;
  const months={}; state.rows.forEach(row=>{const key=row.date.slice(0,7);(months[key] ||= []).push(row);});
  const monthly=Object.entries(months).map(([month,rows])=>({date:month+'-01',hhs_mean:rows.reduce((a,b)=>a+b.hhs_care,0)/rows.length,cbp_mean:rows.reduce((a,b)=>a+b.cbp_custody,0)/rows.length}));
  chart('#monthly-chart',monthly,[{key:'hhs_mean',label:'HHS care',color:'#4b6b94'},{key:'cbp_mean',label:'CBP custody',color:'#ce8248'}]);
}
function renderFlows() {
  const rows=currentFeatures();
  chart('#transfer-chart', rows,[{key:'transfers',label:'Transfers out',color:'#ce8248'},{key:'discharges',label:'Discharges',color:'#4b8b87'}]);
  chart('#flow-chart',rows,[{key:'net_flow',label:'Net flow proxy',color:'#6e7faa'},{key:'net_mean7',label:'7-observation mean',color:'#ce8248'}]);
  chart('#volatility-chart',rows,[{key:'volatility14',label:'Normalized volatility (%)',color:'#8b77aa'}],{decimals:1});
  $('#sensitivity').innerHTML = `<table class="compact"><thead><tr><th>Rule</th><th>Flagged</th><th>Eligible</th><th>Share</th></tr></thead><tbody>${state.research.sensitivity.map(row=>`<tr><td>${row.rule}</td><td>${row.flagged}</td><td>${row.eligible}</td><td>${fmt(row.share_pct,1)}%</td></tr>`).join('')}</tbody></table>`;
  const s=state.research.summary;
  $('#stress-note').innerHTML=`<p><strong>Threshold diagnostic:</strong> ${s.high_relative_stress_rows} of ${s.eligible_stress_rows} eligible full-dataset observations meet at least three of four prior-history relative-stress components. A rule that rarely triggers requires validation before any operational use.</p>`;
}
function renderModels() {
  const m=state.research.models;
  if (!m.available) {$('#model-content').innerHTML=`<div class="notice">${m.reason}</div>`;return;}
  const s=m.scores.find(row=>row.model===m.selected_model), f=m.forecast, split=m.split;
  $('#model-content').innerHTML=`<div class="kpis">${card('Validation-selected model',m.selected_model,'Fixed candidates · chosen by validation MAE')}${card('Untouched test MAE',fmt(s.test.mae,2),'Mean absolute error in children')}${card('Gain over persistence',fmt(m.test_skill_vs_persistence_pct,1)+'%','Test MAE reduction · negative means worse')}${card('Test target pairs',fmt(split.test_pairs),'Observed target exactly 7 calendar days later')}</div>
  <article class="panel split-panel"><h3>Chronological evaluation</h3><p>Boundaries use 70% / 15% / 15% of the original observation sequence. Pairs crossing a boundary are excluded.</p><div class="split-bar"><div><strong>TRAIN</strong><span>${split.train_pairs} pairs</span></div><div><strong>VALIDATION</strong><span>${split.validation_pairs} pairs</span></div><div><strong>TEST</strong><span>${split.test_pairs} pairs</span></div></div><div class="split-labels"><span>Training targets through ${split.train_last_target}</span><span>Validation from ${split.validation_start}</span><span>Test origins from ${split.test_start}</span></div></article>
  <div class="grid-two equal lower"><article class="panel table-panel"><div class="panel-heading"><h3>Every candidate, every score</h3><p>Lower MAE is better. Test scores are reported after selection.</p></div><div class="table-scroll"><table><thead><tr><th>Model</th><th>Validation MAE</th><th>Test MAE</th><th>Test RMSE</th></tr></thead><tbody>${m.scores.map(row=>`<tr class="${row.model===m.selected_model?'selected-model':''}"><td>${row.model}${row.model===m.selected_model?' ✓':''}</td><td>${fmt(row.validation.mae,2)}</td><td>${fmt(row.test.mae,2)}</td><td>${fmt(row.test.rmse,2)}</td></tr>`).join('')}</tbody></table></div></article><article class="panel insight"><span class="signal">INTERPRETING THE EXPERIMENT</span><strong>Complexity has to earn its place.</strong><p>The selected ${m.selected_model.toLowerCase()} uses only information available at each origin. All candidates face the same exact-date target pairs. The test period represents one historical regime.</p><div class="note">No random split. Training transformations fit only on training rows. Model choice uses validation, never the test score.</div></article></div>
  <article class="panel lower"><h3>Held-out predictions against reported HHS care</h3><p>Model and baseline predictions were made seven days before each target date.</p><div id="test-chart" class="chart"></div></article>
  <div class="grid-two equal lower"><article class="panel forecast-card"><span class="section-kicker">HISTORICAL FORWARD ESTIMATE</span><h3>${fmt(f.estimate)} children in HHS care</h3><p>Target ${f.date} · origin ${f.origin}</p><div class="forecast-range">${fmt(f.error_reference_low)} – ${fmt(f.error_reference_high)}<small>Estimate ± 90th percentile of absolute validation error</small></div><p>This is a reference error range, not a calibrated confidence interval. The target is beyond the supplied source cutoff; it is not a forecast for today's date.</p></article><article class="panel prose"><h3>Features and limitations</h3><p>Current census and flows, previous census, 7/14-observation means, 14-observation standard deviation, net flow, elapsed gaps, and a 14-observation calendar-time slope.</p><p>Exact-date target availability can bias the evaluated sample. Nearby forecasts overlap. Structural changes can invalidate historical performance. No causal or facility-capacity claims are made.</p><p>The selected model is ${m.selected_model}; predictive performance is described by errors, not a misleading percentage “accuracy”.</p></article></div>`;
  chart('#test-chart',m.test_predictions,[{key:'actual',label:'Actual HHS care',color:'#203a5d'},{key:'selected',label:'Selected model',color:'#ce8248'},{key:'persistence',label:'Persistence baseline',color:'#65a49f',dash:true}]);
}
function renderQuality() {
  const r=state.research,q=state.quality,a=r.source_audit;
  $('#quality-cards').innerHTML=[['Selected observations',q.observations],['Unobserved dates in range',q.unobserved_calendar_days],['Gaps longer than one day',q.reporting_gaps],['Transfers > custody flags',q.transfers_above_custody]].map(([label,value])=>`<div class="quality-card"><span>${label}</span><strong>${fmt(value)}</strong><p>Selected date range</p></div>`).join('');
  const years=[...new Set(r.monthly.map(row=>iso(row.date).slice(0,4)))];
  const headings=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  $('#coverage-grid').innerHTML=`<div class="calendar-row calendar-head"><strong>YEAR</strong>${headings.map(h=>`<span>${h}</span>`).join('')}</div>`+years.map(year=>`<div class="calendar-row"><strong>${year}</strong>${headings.map((_,i)=>{const month=year+'-'+String(i+1).padStart(2,'0');const cell=r.monthly.find(row=>iso(row.date).startsWith(month));return cell?`<span style="background:rgba(75,139,135,${.12+cell.coverage_pct*.006})" title="${month}: ${cell.observations} observed dates; ${fmt(cell.coverage_pct,1)}% of calendar month">${cell.observations}</span>`:'<span>—</span>';}).join('')}</div>`).join('')+'<p class="chart-foot">Full working dataset. Cell values count observed dates; hover for calendar-month coverage.</p>';
  $('#audit-details').innerHTML=`<dl class="audit-list"><dt>Physical source rows</dt><dd>${a.source_rows}</dd><dt>Wholly blank rows removed</dt><dd>${a.blank_rows_removed}</dd><dt>Valid source observations</dt><dd>${a.valid_rows}</dd><dt>Duplicate source dates</dt><dd>${a.duplicate_dates}</dd></dl><p>Source SHA-256</p><code class="hash">${a.sha256}</code>`;
  const fields=['cbp_intake','cbp_custody','transfers','hhs_care','discharges','net_flow'];
  const labels=['Intake','Custody','Transfers','HHS care','Discharges','Net flow'];
  $('#correlation').innerHTML=`<div class="table-scroll"><table><thead><tr><th></th>${labels.map(l=>`<th>${l}</th>`).join('')}</tr></thead><tbody>${fields.map((x,i)=>`<tr><th>${labels[i]}</th>${fields.map(y=>{const value=r.correlations.find(c=>c.x===x&&c.y===y).value;const color=value==null?'transparent':value>=0?`rgba(75,139,135,${Math.abs(value)*.3})`:`rgba(206,130,72,${Math.abs(value)*.3})`;return `<td style="background:${color}">${fmt(value,2)}</td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function visibleRows(){return state.rows.filter(row=>row.date.includes($('#search').value.trim())).reverse();}
function renderTable(){const rows=visibleRows(),size=12,pages=Math.max(1,Math.ceil(rows.length/size));state.page=Math.min(state.page,pages-1);$('#table-body').innerHTML=rows.slice(state.page*size,(state.page+1)*size).map(row=>`<tr><td>${row.date}</td>${['cbp_intake','cbp_custody','transfers','hhs_care','discharges','total_load','net_flow'].map(key=>`<td>${fmt(row[key])}</td>`).join('')}<td><button class="row-action" data-action="edit" data-id="${row.id}">Edit</button><button class="row-action danger" data-action="delete" data-id="${row.id}">Delete</button></td></tr>`).join('')||'<tr><td colspan="9">No matching observations.</td></tr>';$('#table-info').textContent=`${rows.length} records · page ${state.page+1} of ${pages}`;$('#prev').disabled=state.page===0;$('#next').disabled=state.page>=pages-1;}
function render(){renderOverview();renderFlows();renderModels();renderQuality();renderTable();}
function openEditor(row=null){state.editing=row?.id??null;$('#record-form').reset();$('#form-error').textContent='';$('#dialog-title').textContent=row?`Edit ${row.date}`:'Add observation';if(row)for(const field of ['date','cbp_intake','cbp_custody','transfers','hhs_care','discharges'])$('#record-form').elements[field].value=row[field];$('#editor').showModal();}
async function saveRecord(event){event.preventDefault();const form=$('#record-form'),button=form.querySelector('[type="submit"]');const payload={date:form.elements.date.value};for(const field of ['cbp_intake','cbp_custody','transfers','hhs_care','discharges'])payload[field]=Number(form.elements[field].value);button.disabled=true;try{await request(state.editing?`/api/observations/${state.editing}`:'/api/observations',{method:state.editing?'PUT':'POST',body:JSON.stringify(payload)});$('#editor').close();await refresh();}catch(err){$('#form-error').textContent=err.message;}finally{button.disabled=false;}}
function downloadCsv(){const fields=['date','cbp_intake','cbp_custody','transfers','hhs_care','discharges','total_load','net_flow'];const csv=[fields.join(','),...visibleRows().map(row=>fields.map(f=>row[f]).join(','))].join('\r\n');const link=document.createElement('a');link.href=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));link.download='uac_filtered_observations.csv';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);}

document.querySelectorAll('.nav').forEach(button=>button.addEventListener('click',()=>changeView(button.dataset.view)));
$('#apply').addEventListener('click',refresh);$('#reset').addEventListener('click',()=>{$('#start').value='';$('#end').value='';refresh();});
$('#search').addEventListener('input',()=>{state.page=0;renderTable();});$('#prev').addEventListener('click',()=>{state.page--;renderTable();});$('#next').addEventListener('click',()=>{state.page++;renderTable();});
$('#add').addEventListener('click',()=>openEditor());$('#close').addEventListener('click',()=>$('#editor').close());$('#cancel').addEventListener('click',()=>$('#editor').close());$('#record-form').addEventListener('submit',saveRecord);$('#download').addEventListener('click',downloadCsv);
$('#table-body').addEventListener('click',async event=>{const button=event.target.closest('button[data-action]');if(!button)return;const row=state.rows.find(item=>item.id===Number(button.dataset.id));if(button.dataset.action==='edit')return openEditor(row);if(!confirm(`Delete ${row.date} from the working database?`))return;try{await request(`/api/observations/${row.id}`,{method:'DELETE'});await refresh();}catch(err){error(err.message);}});
request('/api/health').then(()=>{$('#health').textContent='API connected';refresh();}).catch(err=>{$('#health').textContent='API unavailable';error(err.message);$('#loading').classList.add('hidden');});
