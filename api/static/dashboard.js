"use strict";
const $=id=>document.getElementById(id);
const price=new Intl.NumberFormat('pl-PL',{maximumFractionDigits:0});
const percent=new Intl.NumberFormat('pl-PL',{minimumFractionDigits:1,maximumFractionDigits:1});
let market='secondary',current=null,request=null,catalogData=null;
function quarter(q){const [year,n]=q.split('Q');return `${['I','II','III','IV'][Number(n)-1]} kw. ${year}`;}
function ordinal(q){const [y,n]=q.split('Q').map(Number);return y*4+n-1;}
function signed(value){return `${value>0?'+':''}${percent.format(value)}%`;}
function error(message){$('error').textContent=message;$('error').hidden=false;}
function renderChart(data){
 const points=[{q:data.known_price_quarter,value:data.known_price_pln_m2,known:true},...data.forecasts.map(r=>({q:r.target_quarter,value:r.prediction_pln_m2,known:false}))];
 const w=1000,h=290,left=73,right=29,top=26,bottom=48,plotW=w-left-right,plotH=h-top-bottom;
 const values=points.map(p=>p.value),minValue=Math.min(...values),maxValue=Math.max(...values),span=Math.max(maxValue-minValue,maxValue*.06);
 const low=Math.max(0,minValue-span*.4),high=maxValue+span*.4;
 const minQ=ordinal(points[0].q),maxQ=ordinal(points.at(-1).q);
 points.forEach(p=>{p.x=left+(ordinal(p.q)-minQ)/(maxQ-minQ)*plotW;p.y=top+(high-p.value)/(high-low)*plotH;});
 let svg=`<svg viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#4b8e7e" stop-opacity=".14"/><stop offset="100%" stop-color="#4b8e7e" stop-opacity="0"/></linearGradient></defs>`;
 for(let i=0;i<5;i++){const y=top+i*plotH/4;const val=high-i*(high-low)/4;svg+=`<line x1="${left}" y1="${y}" x2="${w-right}" y2="${y}" stroke="#e8eee3" stroke-dasharray="3 5"/><text x="${left-15}" y="${y+4}" text-anchor="end" fill="#97a28f" font-size="11" font-family="Segoe UI,Arial,sans-serif">${price.format(val)}</text>`;}
 const predicted=points.slice(1),path=predicted.map((p,i)=>`${i?'L':'M'} ${p.x} ${p.y}`).join(' ');
 svg+=`<path d="${path} L ${predicted.at(-1).x} ${top+plotH} L ${predicted[0].x} ${top+plotH} Z" fill="url(#fill)"/><line x1="${points[0].x}" y1="${points[0].y}" x2="${points[1].x}" y2="${points[1].y}" stroke="#a4b4a4" stroke-width="1.7" stroke-dasharray="5 5"/><path d="${path}" fill="none" stroke="#377e6e" stroke-width="2.5" stroke-linejoin="round"/>`;
 for(const [i,p]of points.entries()){
  const name=`${quarter(p.q)}: ${price.format(p.value)} zł/m²${p.known?' — ostatni odczyt':i===1?' — nowcast':' — prognoza'}`;
  svg+=`<circle cx="${p.x}" cy="${p.y}" r="${p.known?4:4.5}" fill="${p.known?'#9cae9c':'#fff'}" stroke="${p.known?'#9cae9c':'#377e6e'}" stroke-width="2"><title>${name}</title></circle><text x="${p.x}" y="${h-19}" text-anchor="middle" fill="#8b9985" font-size="11" font-family="Segoe UI,Arial,sans-serif">${p.q.replace('Q',' · Q')}</text>`;
 }
 svg+='</svg>';$('chart').innerHTML=svg;
 $('chart').setAttribute('aria-label',`Ścieżka cen: ostatni odczyt ${price.format(points[0].value)} zł za metr kwadratowy, prognoza na ${quarter(points.at(-1).q)}: ${price.format(points.at(-1).value)} zł za metr kwadratowy. Szczegóły w tabeli poniżej.`);
}
function render(data){
 current=data;const first=data.forecasts[0],last=data.forecasts.at(-1),change=(last.prediction_pln_m2/data.known_price_pln_m2-1)*100;
 $('known').textContent=price.format(data.known_price_pln_m2);$('known-quarter').textContent=quarter(data.known_price_quarter);
 $('first').textContent=price.format(first.prediction_pln_m2);$('first-quarter').textContent=quarter(first.target_quarter);
 $('last').textContent=price.format(last.prediction_pln_m2);$('last-quarter').textContent=quarter(last.target_quarter);$('change').textContent=signed(change);
 $('change').title='Zmiana względem ostatniej znanej ceny, nie stopa zwrotu w jednym kwartale.';
 $('chart-title').textContent=`${data.area} · rynek ${data.market==='secondary'?'wtórny':'pierwotny'}`;
 $('chart-description').textContent=`${quarter(last.target_quarter)}: ${signed(change)} względem odczytu z ${quarter(data.known_price_quarter)}. Wartości dotyczą średniej ceny transakcyjnej w mieście.`;
 $('forecast-table').replaceChildren();
 for(const row of data.forecasts){const tr=document.createElement('tr');for(const [i,value]of [quarter(row.target_quarter),price.format(row.prediction_pln_m2),signed((row.prediction_pln_m2/data.known_price_pln_m2-1)*100),row.horizon===0?'Nowcast':'Prognoza'].entries()){const td=document.createElement('td');if(i===3){const tag=document.createElement('span');tag.className='type-tag';tag.textContent=value;td.append(tag);}else td.textContent=value;tr.append(td);}$('forecast-table').append(tr);}
 renderChart(data);$('download').disabled=false;
}
async function update(){
 if(!catalogData)return;if(request)request.abort();const controller=new AbortController();request=controller;
 $('results').classList.add('loading');$('results').setAttribute('aria-busy','true');$('download').disabled=true;$('error').hidden=true;
 try{const response=await fetch('/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({area:$('city').value,market}),signal:controller.signal});if(!response.ok)throw Error('request');const data=await response.json();if(request===controller)render(data);}catch(e){if(e.name!=='AbortError')error('Nie udało się pobrać prognozy. Sprawdź, czy serwer działa, i ponownie wybierz miasto.');}finally{if(request===controller){$('results').classList.remove('loading');$('results').setAttribute('aria-busy','false');}}
}
$('city').addEventListener('change',update);
document.querySelectorAll('[data-market]').forEach(button=>button.addEventListener('click',()=>{market=button.dataset.market;document.querySelectorAll('[data-market]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));update();}));
$('download').addEventListener('click',()=>{if(!current)return;const rows=[['Miasto','Rynek','Kwartał','Cena PLN/m2','Zmiana od znanej ceny %'],...current.forecasts.map(r=>[current.area,current.market==='primary'?'pierwotny':'wtórny',r.target_quarter,r.prediction_pln_m2.toFixed(2).replace('.',','),((r.prediction_pln_m2/current.known_price_pln_m2-1)*100).toFixed(2).replace('.',',')])];const csv='\ufeff'+rows.map(row=>row.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(';')).join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=`prognoza_${current.area}_${current.market}.csv`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
(async()=>{try{const response=await fetch('/catalog');if(!response.ok)throw Error('catalog');catalogData=await response.json();$('city').replaceChildren();for(const area of catalogData.areas){const option=document.createElement('option');option.value=area;option.textContent=area;$('city').append(option);}$('city').value=catalogData.areas.includes('Warszawa')?'Warszawa':catalogData.areas[0];$('city').disabled=false;$('city-count').textContent=catalogData.areas.length;$('reference').textContent=quarter(catalogData.reference_origin);$('issued').textContent=catalogData.generated.split('-').reverse().join('.');$('model-error').textContent=percent.format(catalogData.evaluation.model_mape)+'%';$('baseline-error').textContent=percent.format(catalogData.evaluation.baseline_mape)+'%';$('evaluation-period').textContent=`Ocena końca ścieżki · origin ${catalogData.evaluation.origin} → cel ${catalogData.evaluation.target}`;await update();}catch(e){error('Nie udało się wczytać panelu. Sprawdź działanie serwera i odśwież stronę.');$('results').setAttribute('aria-busy','false');}})();
