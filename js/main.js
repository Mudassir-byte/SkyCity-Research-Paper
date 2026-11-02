const D=window.PAPER_DATA,$=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const RM=matchMedia('(prefers-reduced-motion:reduce)').matches,C={'In-Store':'#14b8a6','Uber Eats':'#ec4899','DoorDash':'#818cf8','Self-Delivery':'#4facfe'},CH=Object.keys(C),SEG=['Full-service','Cafe','QSR','Ghost Kitchen'];
const F={p0:v=>(v*100).toFixed(0)+'%',p1:v=>(v*100).toFixed(1)+'%',p2:v=>(v*100).toFixed(2)+'%',m:v=>(v<0?'-':'')+'$'+(Math.abs(v)/1e6).toFixed(2)+'M',d:v=>'$'+Math.round(Math.abs(v)).toLocaleString('en-US'),i:v=>Math.round(v).toLocaleString('en-US'),n:v=>(v/1e6).toFixed(2)+'M'};
const get=(o,p)=>p.split('.').reduce((a,k)=>a&&a[k],o),S={metric:'orders',view:'total',hm:'share',sort:'aggDel'};
$$('[data-b]').forEach(e=>{const[p,f]=e.dataset.b.split('|');e.textContent=F[f](get(D,p))});
/* animation helpers */
const tween=(el,to,f,ms=900)=>{if(RM){el.textContent=f(to);return}const t0=performance.now();(function s(t){const k=Math.min(1,(t-t0)/ms),e=1-Math.pow(1-k,3);el.textContent=f(to*e);k<1&&requestAnimationFrame(s)})(t0)};
const grow=el=>requestAnimationFrame(()=>requestAnimationFrame(()=>$$('[data-w]',el).forEach(f=>f.style.width=f.dataset.w+'%')));
const rows=(el,items,max)=>{el.innerHTML=items.map(i=>`<div class="row"><span class="lb">${i.l}</span><div class="tr" title="${i.l}: ${i.t}"><i style="background:${i.c}" data-w="${Math.max(0,i.v/max*100)}"></i></div><b>${i.t}</b></div>`).join('');grow(el)};
/* section 3: channels + donuts */
const donut=(el,vals,cols)=>{const R=48,L=2*Math.PI*R;if(!el.firstChild)el.innerHTML=`<svg viewBox="0 0 120 120" role="img" aria-label="Donut chart">${[0,1,2,3].map(()=>`<circle cx="60" cy="60" r="${R}" fill="none" stroke-width="16" stroke-dasharray="0 ${L}" transform="rotate(-90 60 60)"/>`).join('')}</svg>`;let a=0;$$('circle',el).forEach((c,i)=>{const l=(vals[i]||0)*L;c.setAttribute('stroke',cols[i]||'none');c.setAttribute('stroke-dasharray',`${Math.max(0,l-1.5)} ${L}`);c.setAttribute('stroke-dashoffset',-a);a+=l})};
const chans=()=>S.view==='total'?CH:CH.slice(1),share=(k,chs)=>{const t=chs.reduce((s,c)=>s+D.channels[c][k],0);return chs.map(c=>D.channels[c][k]/t)};
function drawCh(){const chs=chans(),m=S.metric;let v;if(m==='margin')v=chs.map(c=>D.channels[c].margin);else v=share(m==='orders'?'orders':m,chs);
 rows($('#chBars'),chs.map((c,i)=>({l:c,v:v[i],c:C[c],t:F.p1(v[i])})),m==='margin'?.3:Math.max(...v)*1.05);
 donut($('#dOrd'),share('orders',chs),chs.map(c=>C[c]));donut($('#dPro'),share('profit',chs),chs.map(c=>C[c]))}
/* section 4: heatmap + growth */
function drawHeat(){const sub=Object.keys(D.subregions),sh=S.hm==='share';$('#heat').innerHTML='<tr><th></th>'+CH.map(c=>`<th style="color:${C[c]}">${c}</th>`).join('')+'</tr>'+sub.map(s=>`<tr><th>${s}</th>${CH.map(c=>{const v=D.subregions[s][sh?'share':'margin'][c],a=sh?v/.45:Math.min(1,Math.abs(v)/.3);return `<td style="background:rgba(${sh?'99,102,241':v<0?'245,87,108':'20,184,166'},${(.12+a*.75).toFixed(2)})" title="${s} · ${c}">${F.p1(v)}</td>`}).join('')}</tr>`).join('')}
function drawGrow(){const m=+$('#months').value;$('#mo').textContent=m;const sub=Object.keys(D.subregions);rows($('#grow'),sub.map(s=>{const p=D.subregions[s].proj,ix=p[m]/p[0]*100;return{l:s,v:ix,c:ix>=100?'#14b8a6':'#ec4899',t:`${ix.toFixed(0)} · ${F.i(p[m])}`}}),190)}
/* section 5: cuisine + segments */
function drawCuis(){const a=[...D.cuisines].sort((x,y)=>y[S.sort]-x[S.sort]);$('#cuis').innerHTML=a.map(c=>`<div class="row"><span class="lb">${c.name}</span><div class="tr" title="${c.name}: ${F.p0(c.aggDel)} aggregators, ${F.p0(c.sdDel)} self-delivery"><i style="background:#ec4899" data-w="${c.aggDel*100}"></i><i style="background:#4facfe" data-w="${c.sdDel*100}"></i></div><b>${F.p0(c.aggDel)}</b></div>`).join('');grow($('#cuis'))}
function drawSegs(){$('#segs').innerHTML=SEG.map(s=>{const g=D.segments[s];return `<div class="card"><h3>${s}</h3><p>${F.i(g.venues)} venues · ${g.tier2} lose on both apps</p>${CH.map(c=>{const v=g.margin[c],z=28.57,w=Math.abs(v)/.7*100,l=v>=0?z:z-w;return `<div class="row" style="grid-template-columns:20px 1fr 52px;margin:.35rem 0"><span class="lb" style="color:${C[c]}">●</span><div class="tr dv"><i style="background:${C[c]};left:${l}%" data-w="${w}"></i></div><b>${F.p1(v)}</b></div>`}).join('')}</div>`}).join('');grow($('#segs'))}
/* section 6: risk */
function drawRisk(){const a=+$('#comb').value,b=+$('#sing').value;$('#o1').textContent=F.p0(a);$('#o2').textContent=F.p0(b);const n=SEG.map(()=>[0,0,0,0]);let t1=0,t2=0,bo=0;
 D.venueRows.forEach(([s,adi,sm,t])=>{const k=adi>=a||sm>=b;n[s][t?(k?3:2):(k?1:0)]++;t1+=k;t2+=t;bo+=k&&t});
 $('#rk').innerHTML=[['Tier 1 · concentration',t1,'var(--g-ocean)'],['Tier 2 · loss on both apps',t2,'var(--g-sunset)'],['Both tiers',bo,'var(--g-sunset)'],['Venues in scope',D.venues,'var(--g-aurora)']].map(([l,v,g])=>`<div class="kpi" style="--accent-g:${g}"><div class="l">${l}</div><div class="v">${F.i(v)}</div><div class="s">${(v/D.venues*100).toFixed(1)}% of venues</div></div>`).join('');
 const col=['#14b8a6','#818cf8','#f5576c','#ec4899'];$('#rseg').innerHTML=SEG.map((s,i)=>{const T=n[i].reduce((x,y)=>x+y,0);return `<div class="r"><span>${s}</span><div class="tr" title="${n[i].join(' / ')}">${n[i].map((v,j)=>`<i style="background:${col[j]};width:${v/T*100}%"></i>`).join('')}</div><b>${F.i(T)}</b></div>`}).join('')}
/* section 7: simulator */
let last=0;function drawSim(){const s=+$('#shift').value/100,cp=+$('#cap').value,t=$('#tgt').value,sm=D.sim,key=t==='Self-Delivery'?'Self-Delivery':'In-Store';
 const g=s*sm.G[key]+(cp<.33?(1-s)*sm.caps[cp.toFixed(2)]:0);$('#p1').textContent=Math.round(s*100)+'%';$('#p3').textContent=cp<.33?F.p0(cp):'none';
 $('#r0').textContent=F.m(sm.base);tween($('#r1'),sm.base+g,F.m,500);tween($('#r2'),g,v=>(v>=0?'+':'')+F.m(v),500);$('#r3').textContent=`${(g/sm.base*100).toFixed(1)}% · ${F.i(s*sm.aggOrders)} orders moved`}
/* static lists */
$('#checks').innerHTML=D.checks.map(c=>`<li class="${c[1]?'':'bad'}">${c[0]}</li>`).join('');
$('#anoms').innerHTML=D.anomalies.map(a=>`<details><summary><b>${a[0]}</b> ${a[1]}</summary><p>${a[2]}</p><p><b>Resolution:</b> ${a[3]}</p></details>`).join('');
$('#nav').innerHTML=$$('section').map(s=>`<a href="#${s.id}">${s.querySelector('h2').textContent.replace(/^\d+\.\s*/,'')}</a>`).join('');
/* wiring */
$$('.seg').forEach(g=>g.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;$$('button',g).forEach(x=>x.setAttribute('aria-pressed',x===b));S[g.dataset.k]=b.dataset.v;({metric:drawCh,view:drawCh,hm:drawHeat,sort:drawCuis})[g.dataset.k]()}));
$('#months').oninput=drawGrow;['comb','sing'].forEach(i=>$('#'+i).oninput=drawRisk);['shift','tgt','cap'].forEach(i=>$('#'+i).oninput=drawSim);
$('#comb').value=D.risk.defaults[0];$('#sing').value=D.risk.defaults[1];
const draw={s3:drawCh,s4:()=>{drawHeat();drawGrow()},s5:()=>{drawCuis();drawSegs()},s6:drawRisk,s7:drawSim};
const io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;const el=e.target;el.classList.add('in');(draw[el.id]||(()=>{}))();$$('[data-c]',el).forEach(c=>{const[p,f]=c.dataset.c.split('|');tween(c,get(D,p),F[f])});io.unobserve(el)}),{threshold:.12});
$$('.rv').forEach(e=>io.observe(e));
const spy=new IntersectionObserver(es=>es.forEach(e=>e.isIntersecting&&$$('#nav a').forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id))),{rootMargin:'-40% 0px -55% 0px'});$$('section').forEach(s=>spy.observe(s));
addEventListener('scroll',()=>$('#bar').style.width=scrollY/(document.documentElement.scrollHeight-innerHeight)*100+'%',{passive:true});
