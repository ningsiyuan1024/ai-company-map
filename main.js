'use strict';
(() => {
 const $=id=>document.getElementById(id);
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const p = new URLSearchParams(location.search);
 const catalog = window.DINQ_CATALOG;
 const city = Object.hasOwn(catalog,p.get('city')) ? p.get('city') : 'beijing';
 const {name:cityName,records:companies,date,source} = catalog[city];
 const unique = values => [...new Set(values.filter(Boolean))];
 if(city==='beijing'){
   const districts='东城区 西城区 朝阳区 丰台区 石景山区 海淀区 门头沟区 房山区 通州区 顺义区 昌平区 大兴区 怀柔区 平谷区 密云区 延庆区 北京经济技术开发区'.split(' ');
   for(const company of companies){
     for(const location of company.locations){
       if(!location.district) location.district=districts.find(name=>location.address?.includes(name));
     }
   }
 }
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
 $('coverage').textContent=`目录共 ${companies.length} 家公司 · ${companies.flatMap(c=>c.sites).length} 个地理参考点。`;
 const finance = c => city==='beijing' ? window.BEIJING_FINANCE_2026?.records[c.id] : null;
 const events = c => {
   if(city!=='beijing')return window.FUNDING_EVENTS[c.id]||[];
   const f=finance(c)?.financing;
   if(!f||finance(c).listing)return [];
   return [[f.date,f.round,f.investorNames||[],f.url]];
 };
 const roundGroup = e => {
   const round=e[1];
   if(round.startsWith('Pre-A'))return 'Pre-A';
   if(round.startsWith('Pre-IPO'))return 'Pre-IPO';
   if(round.startsWith('种子'))return '种子';
   if(round.startsWith('天使'))return '天使';
   return /^[A-H]/.test(round)?round[0]+'轮':'其他融资';
 };
 const cityEvents = companies.flatMap(events);
 const setupFilter = (key,label,choices) => {
   state[key]=choices.includes(p.get(key)) ? p.get(key) : '';
   $(key).hidden=!choices.length;
   $(key).innerHTML=options([['',label],...choices.map(v=>[v,v])],state[key]);
   $(key).onchange=()=>{state[key]=$(key).value;state.selected=null;render({fitMap:true});};
 };
 setupFilter('round','融资记录',unique(cityEvents.map(roundGroup)).sort());
 setupFilter('investor','投资机构',unique(cityEvents.flatMap(e=>e[2])).sort((a,b)=>a.localeCompare(b,'zh')));
 const matchesEvent = e => (!state.round||roundGroup(e)===state.round)&&(!state.investor||e[2].includes(state.investor));
 const matchesFunding = c => (!state.round&&!state.investor)||events(c).some(matchesEvent);
 const eventLabel = e => e[0]+' · '+e[1]+' · '+e[2].join('、');
 const visibleSites = c => c.sites.filter(site=>state.region==='全部'||site.region===state.region);
 const activeSite = c => c.sites[state.site];
 const closeIcon='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>', arrow='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>', pin='<svg viewBox="0 0 32 40" aria-hidden="true"><path fill="currentColor" stroke="#fff" stroke-width="2" d="M16 38C12 31 3 23 3 15a13 13 0 0 1 26 0c0 8-9 16-13 23Z"/><circle cx="16" cy="15" r="4.5" fill="#fff"/></svg>';
 const markers=new Map(), reduced=matchMedia('(prefers-reduced-motion:reduce)').matches;
 let map=null,tiles=null,loadedTiles=0,failedTiles=0,loadTimer=null;
 const filtered = () => companies.filter(c => matchesFunding(c) && (state.region==='全部'||regions(c).includes(state.region)) &&
   [c.name,...events(c).map(eventLabel),...c.aliases,c.category,...c.tags,...c.locations.flatMap(l=>[l.district,l.area,l.address])].join(' ').toLowerCase().includes(state.q.trim().toLowerCase()));
 function sync(){const q=new URLSearchParams();if(city!=="beijing")q.set("city",city);for(const key of ['round','investor'])if(state[key])q.set(key,state[key]);if(state.q)q.set('q',state.q);if(state.region!=='全部')q.set('region',state.region);if(state.selected)q.set('company',state.selected);try{history.replaceState(null,'',location.pathname+(q.size?'?'+q:''));}catch{}}
 function status(message,retry=false){$('map-status').hidden=!message;$('map-status-text').textContent=message;$('retry-map').hidden=!retry;}
 function fit(){if(!map)return;const points=filtered().flatMap(c=>visibleSites(c).map(site=>[site.lat,site.lng]));if(!points.length)return;const mobile=matchMedia('(max-width:700px)').matches;map.fitBounds(points,{paddingTopLeft:mobile?[70,70]:[100,100],paddingBottomRight:mobile?[85,75]:[160,90],maxZoom:points.length===1?15:13,animate:false});}
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
 function financeDetails(c,link){
   const record=finance(c);
   if(!record||!(record.listing||record.financing||record.unicorn||record.otc))return '';
   const lines=[];
   if(record.listing){
     const l=record.listing;
     lines.push(link(l.url,record.listingScope+'已上市 · '+l.name+' · '+l.code+' · '+l.date));
   }
   if(record.otc){
     const otc=record.otc;
     lines.push(link(otc.url,'新三板挂牌 · '+otc.code+' · '+otc.date));
   }
   if(record.financing&&!record.listing){
     const f=record.financing;
     lines.push(link(f.url,f.date+' · '+f.round+' · '+f.publisher+'（来源 '+f.sourcePublished+'）'));
   }
   if(record.unicorn){
     const u=record.unicorn;
     lines.push(link(u.url,'2026胡润独角兽榜 · '+u.name+' · 2026-06-25'+(u.subsequentListing?'；另有后续上市证据':'')));
   }
   return '<details class="source-details"><summary>2026 融资与上市依据</summary><div>'+lines.map(l=>'<p>'+l+'</p>').join('')+'</div></details>';
 }
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
     ${city==='beijing'?financeDetails(c,link):(events(c).length?`<details class="source-details"><summary>融资记录 · ${esc(events(c)[0][1])}（${esc(events(c)[0][0])}）</summary><div>${events(c).map(e=>`<p>${link(e[3],eventLabel(e))}</p>`).join('')}</div></details>`:'')}<div class="actions">${link(c.recruit,c.recruitLabel,'primary')}${site?link(site.coord?'https://uri.amap.com/marker?position='+site.coord.join(',')+'&name='+encodeURIComponent(c.name):'https://www.openstreetmap.org/?mlat='+site.lat+'&mlon='+site.lng+'#map=17/'+site.lat+'/'+site.lng,'查看地图','secondary'):''}</div>
     <details class="source-details"><summary>位置与来源</summary><div>${addresses.filter(a=>site||a!==addresses[0]).map(a=>`<p>${esc(a)}</p>`).join('')}
     ${c.evidence?c.evidence.map(([label,url])=>link(url,label)).join(' '):link(source,'DINQ 城市数据')} ${link(site?.source,'点位来源')}<p>资料核对 ${esc(c.checked||date)}。实际工作地点以招聘方为准。</p></div></details>`;
   if(selector)$('site').onchange=e=>select(c.id,{siteIndex:Number(e.target.value)});
 }
 function render({fitMap=false}={}){const list=filtered();if(state.selected&&!list.some(c=>c.id===state.selected))state.selected=null;const focusId=document.activeElement?.closest?.('.company-row')?.dataset.id;$('result-count').textContent=`${list.length} 家公司`;$('clear-filters').hidden=!state.round&&!state.investor&&!state.q&&state.region==='全部';$('empty').hidden=list.length>0;$('company-list').hidden=!list.length;$('company-list').innerHTML=list.map(c=>`<button class="company-row" data-id="${c.id}" aria-label="查看 ${esc(c.name)}" aria-pressed="${state.selected===c.id}"><span class="company-initial" aria-hidden="true">${esc(Array.from(c.name)[0])}</span><span class="company-content"><strong translate="no">${esc(c.name)}</strong><small>${esc(regions(c).join(' / ')||cityName)} · ${esc(c.tags.slice(0,2).join(' / '))}</small>${finance(c)?.listing?'<small class="funding-line">'+esc(finance(c).listingScope+'已上市')+'</small>':''}${finance(c)?.unicorn?'<small class="funding-line">2026胡润独角兽榜'+(finance(c).listing?' · 已有上市证据':'')+'</small>':''}${events(c).some(matchesEvent)?`<small class="funding-line">${esc(eventLabel(events(c).find(matchesEvent)))}</small>`:''}${visibleSites(c).length?'':'<span class="pending">位置待核验</span>'}</span></button>`).join('');document.querySelectorAll('[data-region]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.region===state.region)));renderDetail();updateMarkers();sync();if(focusId)document.querySelector(`.company-row[data-id="${focusId}"]`)?.focus({preventScroll:true});if(fitMap)fit();}
 function select(id,{keyboard=false,siteIndex}={}){const c=companies.find(c=>c.id===id);if(!c)return;state.selected=id;state.site=siteIndex??c.sites.indexOf(visibleSites(c)[0]);render();const site=activeSite(c);if(map&&site){const mobile=matchMedia('(max-width:700px)').matches;map.setView([site.lat,site.lng],Math.max(map.getZoom(),14),{animate:false});if(mobile||map.getSize().x<600){const size=map.getSize();const available=Math.max(70,size.y-$('detail').getBoundingClientRect().height-40);map.panBy([0,(size.y-available)/2],{animate:false});}}if(keyboard)$('detail').focus({preventScroll:true});}
 function closeDetail(){const id=state.selected;state.selected=null;render();document.querySelector(`.company-row[data-id="${id}"]`)?.focus({preventScroll:true});}
 function reset(){for(const k of ['round','investor']){state[k]='';$(k).value='';}state.q='';state.region='全部';$('region').value='全部';state.selected=null;$('search').value='';render({fitMap:true});$('search').focus();}
 function startMap(){if(!window.L){$('map').classList.add('no-map');$('map').textContent='地图组件未能加载，公司目录仍可使用。';return;}map=L.map('map',{zoomControl:false,scrollWheelZoom:true,zoomAnimation:!reduced,fadeAnimation:!reduced,markerZoomAnimation:!reduced,minZoom:9,maxZoom:19}).setView([39.984,116.36],12);L.control.zoom({position:'topright',zoomInTitle:'放大地图',zoomOutTitle:'缩小地图'}).addTo(map);L.control.scale({position:'bottomleft',imperial:false,maxWidth:100}).addTo(map);map.attributionControl.setPrefix(false);
 if(city==='beijing'){
   if(!window.BEIJING_BASEMAP){status('北京底图未能加载，请刷新页面');return;}
   map.getContainer().classList.add('local-basemap');
   map.createPane('baseShapes');map.getPane('baseShapes').style.zIndex=200;
   map.createPane('baseLabels');map.getPane('baseLabels').style.zIndex=350;
   const data=window.BEIJING_BASEMAP;
   const canvas=L.canvas({pane:'baseShapes',padding:0.5});
   const weights={motorway:3.2,trunk:2.5,primary:1.8,secondary:1.2,tertiary:0.7};
   const features=[...data.geojson.features].sort((a,b)=>(a.properties.kind==='road')-(b.properties.kind==='road'));
   L.geoJSON({type:'FeatureCollection',features},{pane:'baseShapes',renderer:canvas,interactive:false,style:f=>{
     const p=f.properties;
     if(p.kind==='water')return {color:'#b8d4e2',weight:0,fillColor:'#c8e1eb',fillOpacity:1};
     if(p.kind==='park')return {color:'#dce7d3',weight:0,fillColor:'#dce7d3',fillOpacity:0.8};
     return {color:['motorway','trunk'].includes(p.class)?'#d5bf8b':'#c4c9cb',weight:weights[p.class],opacity:0.95};
   }}).addTo(map);
   const labelLayer=L.layerGroup().addTo(map);
   function label(text,latlng,road=false){
     L.marker(latlng,{pane:'baseLabels',interactive:false,keyboard:false,icon:L.divIcon({
       className:road?'base-label road-label':'base-label',html:esc(text),iconSize:[120,20],iconAnchor:[60,10]
     })}).addTo(labelLayer);
   }
   function labels(){
     labelLayer.clearLayers();
     const bounds=map.getBounds(),occupied=[];
     const add=(text,latlng,road)=>{
       if(!bounds.contains(latlng))return;
       const pixel=map.latLngToContainerPoint(latlng);
       if(occupied.some(p=>Math.abs(p.x-pixel.x)<105&&Math.abs(p.y-pixel.y)<32))return;
       occupied.push(pixel);label(text,latlng,road);
     };
     data.places.forEach(p=>add(p.name,p.coord,false));
     if(map.getZoom()<12)return;
     const names=new Set();
     for(const f of data.geojson.features){
       const p=f.properties;
       if(p.kind!=='road'||!p.name||names.has(p.name))continue;
       if(map.getZoom()<14&&!['motorway','trunk','primary'].includes(p.class))continue;
       const line=f.geometry.coordinates[0],mid=line[Math.floor(line.length/2)];
       if(bounds.contains([mid[1],mid[0]])){names.add(p.name);add(p.name,[mid[1],mid[0]],true);}
     }
   }
   map.on('moveend zoomend',labels);labels();
   map.attributionControl.addAttribution('© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> · <a href="./MAP-DATA-LICENSE.md" target="_blank">北京道路参考底图</a>');
 }else{
 tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,maxNativeZoom:19,attribution:'© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>',referrerPolicy:'strict-origin-when-cross-origin',keepBuffer:1,updateWhenIdle:true});tiles.on('tileload',()=>{loadedTiles++;if(loadedTiles){clearTimeout(loadTimer);status('');}});tiles.on('tileerror',()=>{failedTiles++;if(failedTiles>=4&&!loadedTiles)status('底图暂时无法连接',true);});tiles.addTo(map);
 }

 for(const c of companies){
   c.sites.forEach((site,i)=>{
     const marker=L.marker([site.lat,site.lng],{icon:icon(c,i),keyboard:false,title:c.name}).bindTooltip(esc(c.name),{direction:'top',offset:[0,-36],className:'company-label'});
     marker.on('click',()=>select(c.id,{siteIndex:i}));
     markers.set(c.id+':'+i,{marker,c,site,i});
   });
 }
 updateMarkers();
 $('map').addEventListener('keydown',e=>{const b=e.target.closest('[data-company]');if(b&&(e.key==='Enter'||e.key===' ')){e.preventDefault();select(b.dataset.company,{keyboard:true,siteIndex:Number(b.dataset.site)});}});fit();if(city!=='beijing')loadTimer=setTimeout(()=>{if(!loadedTiles)status('底图暂时无法连接',true);},12000);if(location.protocol==='file:')status('在线底图请通过“打开地图”启动',false);new ResizeObserver(()=>map.invalidateSize({pan:false})).observe($('map'));
 }
 $('search').value=state.q;$('search').addEventListener('input',e=>{state.q=e.target.value;render({fitMap:true});});$('company-list').addEventListener('click',e=>{const b=e.target.closest('[data-id]');if(b)select(b.dataset.id,{keyboard:e.detail===0});});$('detail').addEventListener('click',e=>{if(e.target.closest('.close-detail'))closeDetail();});$('clear-filters').addEventListener('click',reset);$('reset-search').addEventListener('click',reset);$('fit-map').addEventListener('click',fit);$('retry-map').addEventListener('click',()=>{loadedTiles=0;failedTiles=0;status('正在连接底图…');tiles?.redraw();clearTimeout(loadTimer);loadTimer=setTimeout(()=>{if(!loadedTiles)status('底图暂时无法连接',true);},12000);});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.selected)closeDetail();if(e.key==='/'&&!e.ctrlKey&&!e.metaKey&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();$('search').focus();}});render();startMap();if(state.selected)select(state.selected);
})();
