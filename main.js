'use strict';
(() => {
 const $=id=>document.getElementById(id);
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const p = new URLSearchParams(location.search);
 const catalog = window.DINQ_CATALOG;
 const city = Object.hasOwn(catalog,p.get('city')) ? p.get('city') : 'beijing';
 const {name:cityName,records:companies,date,source} = catalog[city];
 const unique = values => [...new Set(values.filter(Boolean))];
 const regions = c => unique(c.locations.map(l=>l.district));
 const options = (items,select) => items.map(([value,label])=>`<option value="${esc(value)}" ${value===select?'selected':''}>${esc(label)}</option>`).join('');
 const regionNames = unique(companies.flatMap(regions));
 const legacyRegion = regionNames.find(r=>r===p.get('region')||r===p.get('region')+'区');
 const state = {q:p.get('q')||'',region:legacyRegion||'全部',selected:p.get('company')==='kimi'?'moonshot':p.get('company'),site:0};
 document.title=cityName+' AI 公司地图';
 $('city').innerHTML=options(Object.entries(catalog).map(([id,c])=>[id,c.name]),city);
 $('city').onchange=()=>location.assign('?city='+encodeURIComponent($('city').value));
 $('region').innerHTML=options([['全部','全部区域'],...regionNames.map(r=>[r,r])],state.region);
 $('region').onchange=()=>{state.region=$('region').value;state.selected=null;state.site=0;render({fitMap:true});};
 $('coverage').textContent=`DINQ 快照 ${date} · ${companies.length} 家公司 · ${companies.flatMap(c=>c.sites).length} 个地理参考点。`;
 const visibleSites = c => c.sites.filter(site=>state.region==='全部'||site.region===state.region);
 const activeSite = c => c.sites[state.site];
 const closeIcon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>', arrow='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>', pin='<svg viewBox="0 0 32 40" aria-hidden="true"><path fill="currentColor" stroke="#fff" stroke-width="2" d="M16 38C12 31 3 23 3 15a13 13 0 0 1 26 0c0 8-9 16-13 23Z"/><circle cx="16" cy="15" r="4.5" fill="#fff"/></svg>';
 const markers=new Map(), reduced=matchMedia('(prefers-reduced-motion:reduce)').matches;
 let map=null,tiles=null,loadedTiles=0,failedTiles=0,loadTimer=null;
 const filtered = () => companies.filter(c => (state.region==='全部'||regions(c).includes(state.region)) &&
   [c.name,...c.aliases,c.category,...c.tags,...c.locations.flatMap(l=>[l.district,l.area,l.address])].join(' ').toLowerCase().includes(state.q.trim().toLowerCase()));
 function sync(){const q=new URLSearchParams();if(city!=="beijing")q.set("city",city);if(state.q)q.set('q',state.q);if(state.region!=='全部')q.set('region',state.region);if(state.selected)q.set('company',state.selected);try{history.replaceState(null,'',location.pathname+(q.size?'?'+q:''));}catch{}}
 function status(message,retry=false){$('map-status').hidden=!message;$('map-status-text').textContent=message;$('retry-map').hidden=!retry;}
 function fit(){if(!map)return;const points=filtered().flatMap(c=>visibleSites(c).map(site=>[site.lat,site.lng]));if(!points.length)return;const mobile=matchMedia('(max-width:700px)').matches;map.fitBounds(points,{paddingTopLeft:mobile?[70,70]:[100,100],paddingBottomRight:mobile?[85,75]:[160,90],maxZoom:points.length===1?15:13,animate:!reduced});}
 function icon(c,i){return L.divIcon({className:'map-pin',html:`<button class="pin-button" data-company="${esc(c.id)}" data-site="${i}" aria-label="查看 ${esc(c.name)}的位置" aria-pressed="${state.selected===c.id}">${pin}</button>`,iconSize:[44,44],iconAnchor:[22,41]});}
 function updateMarkers(){
   if(!map)return;
   const ids=new Set(filtered().map(c=>c.id));
   for(const {marker,c,site,i} of markers.values()){
     const visible=ids.has(c.id)&&(state.region==='全部'||site.region===state.region);
     if(!visible){if(map.hasLayer(marker))marker.remove();continue;}
     if(!map.hasLayer(marker))marker.addTo(map);
     const selected=state.selected===c.id&&state.site===i;
     marker.getElement()?.querySelector('button')?.setAttribute('aria-pressed',String(selected));
     marker.setZIndexOffset(selected?1000:0);
     if(selected)marker.openTooltip();else marker.closeTooltip();
   }
   const list=filtered();
   $('empty-map-message').hidden=!list.length||list.some(c=>visibleSites(c).length);
 }
 const precision={area:'片区参考点',campus:'园区参考点',building:'楼宇参考点'};
 const safeUrl=url=>/^https?:\/\//i.test(url||'');
 function renderDetail(){
   const c=companies.find(c=>c.id===state.selected);
   $('detail').hidden=!c;
   if(!c){$('detail').replaceChildren();return;}
   const site=activeSite(c);
   const locs=state.region==='全部'?c.locations:c.locations.filter(l=>l.district===state.region);
   const addresses=unique(locs.map(l=>l.address||l.area)).filter(a=>a!==site?.address);
   const link=(url,label,cls='')=>safeUrl(url)?`<a class="${cls}" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`:'';
   const sites=visibleSites(c);
   const selector=sites.length>1?`<select id="site" aria-label="公司地点">${options(sites.map(s=>[c.sites.indexOf(s),s.name||s.address]),state.site)}</select>`:'';
   $('detail').innerHTML=`<div class="detail-head"><h2 id="detail-name">${esc(c.name)}</h2><button class="close-detail" aria-label="关闭公司详情">${closeIcon}</button></div>
     <div class="tags">${c.tags.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>${selector}
     <p class="location-heading"><strong>${esc(site?.name||locs[0]?.area||cityName)}</strong><small>${site?(precision[site.precision]||'参考点'):'位置待核验'}</small></p>
     <p class="address">${esc(site?.address||addresses[0]||'暂无公开地址')}</p>
     <div class="actions">${link(c.recruit,c.recruitLabel,'primary')}${site?link('https://www.openstreetmap.org/?mlat='+site.lat+'&mlon='+site.lng+'#map=17/'+site.lat+'/'+site.lng,'查看地图','secondary'):''}</div>
     <details class="source-details"><summary>位置与来源</summary><div>${addresses.filter(a=>site||a!==addresses[0]).map(a=>`<p>${esc(a)}</p>`).join('')}
     ${link(source,'DINQ 城市数据')} ${link(site?.source,'点位来源')}<p>资料快照 ${esc(date)}。实际工作地点以招聘方为准。</p></div></details>`;
   if(selector)$('site').onchange=e=>select(c.id,{siteIndex:Number(e.target.value)});
 }
 function render({fitMap=false}={}){const list=filtered();if(state.selected&&!list.some(c=>c.id===state.selected))state.selected=null;const focusId=document.activeElement?.closest?.('.company-row')?.dataset.id;$('result-count').textContent=`${list.length} 家公司`;$('clear-filters').hidden=!state.q&&state.region==='全部';$('empty').hidden=list.length>0;$('company-list').hidden=!list.length;$('company-list').innerHTML=list.map(c=>`<button class="company-row" data-id="${c.id}" aria-label="查看 ${esc(c.name)}" aria-pressed="${state.selected===c.id}"><span class="company-initial" aria-hidden="true">${esc(Array.from(c.name)[0])}</span><span class="company-content"><strong translate="no">${esc(c.name)}</strong><small>${esc(regions(c).join(' / ')||cityName)} · ${esc(c.tags.slice(0,2).join(' / '))}</small>${visibleSites(c).length?'':'<span class="pending">位置待核验</span>'}</span></button>`).join('');document.querySelectorAll('[data-region]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.region===state.region)));renderDetail();updateMarkers();sync();if(focusId)document.querySelector(`.company-row[data-id="${focusId}"]`)?.focus({preventScroll:true});if(fitMap)fit();}
 function select(id,{keyboard=false,siteIndex}={}){const c=companies.find(c=>c.id===id);if(!c)return;state.selected=id;state.site=siteIndex??c.sites.indexOf(visibleSites(c)[0]);render();const site=activeSite(c);if(map&&site){const mobile=matchMedia('(max-width:700px)').matches;map.setView([site.lat,site.lng],Math.max(map.getZoom(),14),{animate:false});if(mobile||map.getSize().x<600){const size=map.getSize();const available=Math.max(70,size.y-$('detail').getBoundingClientRect().height-40);map.panBy([0,(size.y-available)/2],{animate:false});}}if(keyboard)$('detail').focus({preventScroll:true});}
 function closeDetail(){const id=state.selected;state.selected=null;render();document.querySelector(`.company-row[data-id="${id}"]`)?.focus({preventScroll:true});}
 function reset(){state.q='';state.region='全部';$('region').value='全部';state.selected=null;$('search').value='';render({fitMap:true});$('search').focus();}
 function startMap(){if(!window.L){$('map').classList.add('no-map');$('map').textContent='地图组件未能加载，公司目录仍可使用。';return;}map=L.map('map',{zoomControl:false,scrollWheelZoom:true,zoomAnimation:!reduced,fadeAnimation:!reduced,markerZoomAnimation:!reduced,minZoom:9,maxZoom:19}).setView([39.984,116.36],12);L.control.zoom({position:'topright',zoomInTitle:'放大地图',zoomOutTitle:'缩小地图'}).addTo(map);L.control.scale({position:'bottomleft',imperial:false,maxWidth:100}).addTo(map);map.attributionControl.setPrefix(false);
 tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,maxNativeZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>',referrerPolicy:'strict-origin-when-cross-origin',keepBuffer:1,updateWhenIdle:true});tiles.on('tileload',()=>{loadedTiles++;if(loadedTiles){clearTimeout(loadTimer);status('');}});tiles.on('tileerror',()=>{failedTiles++;if(failedTiles>=4&&!loadedTiles)status('底图暂时无法连接',true);});tiles.addTo(map);
 for(const c of companies){
   c.sites.forEach((site,i)=>{
     const marker=L.marker([site.lat,site.lng],{icon:icon(c,i),keyboard:false,title:c.name}).bindTooltip(esc(c.name),{direction:'top',offset:[0,-36],className:'company-label'});
     marker.on('click',()=>select(c.id,{siteIndex:i}));
     markers.set(c.id+':'+i,{marker,c,site,i});
   });
 }
 updateMarkers();
 $('map').addEventListener('keydown',e=>{const b=e.target.closest('[data-company]');if(b&&(e.key==='Enter'||e.key===' ')){e.preventDefault();select(b.dataset.company,{keyboard:true,siteIndex:Number(b.dataset.site)});}});fit();loadTimer=setTimeout(()=>{if(!loadedTiles)status('底图暂时无法连接',true);},12000);if(location.protocol==='file:')status('在线底图请通过“打开地图”启动',false);new ResizeObserver(()=>map.invalidateSize({pan:false})).observe($('map'));
 }
 $('search').value=state.q;$('search').addEventListener('input',e=>{state.q=e.target.value;render({fitMap:true});});$('company-list').addEventListener('click',e=>{const b=e.target.closest('[data-id]');if(b)select(b.dataset.id,{keyboard:e.detail===0});});$('detail').addEventListener('click',e=>{if(e.target.closest('.close-detail'))closeDetail();});$('clear-filters').addEventListener('click',reset);$('reset-search').addEventListener('click',reset);$('fit-map').addEventListener('click',fit);$('retry-map').addEventListener('click',()=>{loadedTiles=0;failedTiles=0;status('正在连接底图…');tiles?.redraw();clearTimeout(loadTimer);loadTimer=setTimeout(()=>{if(!loadedTiles)status('底图暂时无法连接',true);},12000);});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.selected)closeDetail();if(e.key==='/'&&!e.ctrlKey&&!e.metaKey&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();$('search').focus();}});render();startMap();if(state.selected)select(state.selected);
})();
