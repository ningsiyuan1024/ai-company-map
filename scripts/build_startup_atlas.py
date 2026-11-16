"""Build six additional startup charts and a portable PNG bundle.
Requires matplotlib; uses only the public local directory and financing ledgers.
"""
import collections
import itertools
import json
import math
from pathlib import Path
import zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap
from build_startup_statistics import build

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/images'
DATA=build(); TOTAL=DATA['total']; AS_OF=DATA['asOf'].replace('-','.')
directory=json.loads((ROOT/'skills/ai-company-match/references/companies.json').read_text(encoding='utf8'))
BY_ID={row['id']:row for row in directory['companies']}
FINANCE=json.loads((ROOT/'docs/finance-2026.json').read_text(encoding='utf8'))['records']
font_path=Path('C:/Windows/Fonts/msyh.ttc')
if font_path.exists(): font_manager.fontManager.addfont(str(font_path))
fonts={font.name for font in font_manager.fontManager.ttflist}
font=next((name for name in ['Microsoft YaHei','Noto Sans CJK SC','Source Han Sans SC'] if name in fonts),None)
if not font: raise RuntimeError('Install a supported Chinese font before rendering.')
plt.rcParams.update({'font.family':font,'axes.unicode_minus':False,'savefig.facecolor':'white'})
INK='#182b42'; MUTED='#536476'; BLUE='#426fc0'; TEAL='#278879'; GRAY='#dce3eb'
GROUP_MAP={
    '机器人与具身':'机器人与具身智能','机器人与具身智能':'机器人与具身智能','具身智能':'机器人与具身智能',
    '算力与芯片':'算力与基础设施','AI基础设施':'算力与基础设施',
    '大模型与平台':'大模型与平台','AI应用与生成':'内容与通用AI应用','AI应用':'内容与通用AI应用',
    'AI应用与企业服务':'企业与数据服务','AI数据与评测':'企业与数据服务',
    'AI应用与Agent':'Agent 产品与服务','Agent安全':'Agent 产品与服务','Agent评测':'Agent 产品与服务',
}
COLORS={'机器人与具身智能':'#426fc0','算力与基础设施':'#278879','内容与通用AI应用':'#bd724a',
        '大模型与平台':'#77649b','企业与数据服务':'#567b8f','Agent 产品与服务':'#80683f'}
INVESTOR_ALIASES={'HongShan红杉中国':'红杉中国','经纬创投':'经纬中国','Monolith砺思资本':'砺思资本'}
TAG_NAMES={'AI Infra':'AI 基础设施'}
ROWS=[]
for row in DATA['companies']:
    members=[BY_ID[id] for id in row['directoryIds']]
    sector=GROUP_MAP[members[0]['category']]
    assert all(GROUP_MAP[member['category']]==sector for member in members)
    regions=sorted({location['district'] for member in members for location in member['locations'] if location['district']})
    names=set()
    for id in row['directoryIds']:
        event=FINANCE[id]['financing']
        # Count investors only when tied to the specific round selected for the chart.
        if event and event['round']==row['round'] and event['date']==row['eventDate']:
            names.update(INVESTOR_ALIASES.get(name,name) for name in event.get('investorNames',[]) if name)
    ROWS.append({**row,'sector':sector,'regions':regions,'hasRecruit':any(member['recruitUrl'] for member in members),'investors':sorted(names)})
SECTORS=collections.Counter(row['sector'] for row in ROWS)
ORDER=[name for name,_ in SECTORS.most_common()]
assert sum(SECTORS.values())==TOTAL
METRICS={'asOf':DATA['asOf'],'sampleTotal':TOTAL,'scope':DATA['scope'],'sectorCounts':dict(SECTORS),'rows':ROWS}
FILES=[]


def canvas(title,subtitle,figsize=(12,8)):
    fig=plt.figure(figsize=figsize,dpi=180)
    fig.text(.06,.93,title,fontsize=24,weight='bold',color=INK)
    fig.text(.06,.865,subtitle,fontsize=11.5,color=MUTED)
    return fig


def finish(fig,name,note):
    fig.text(.06,.09,note,fontsize=9.5,color=MUTED)
    fig.text(.06,.04,f'北京 AI 公司地图  |  已披露轮次创业样本 {TOTAL} 家  |  {AS_OF}',fontsize=9.5,color=MUTED)
    fig.savefig(OUT/name)
    plt.close(fig); FILES.append(name)


def strip_axes(ax):
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(length=0,labelcolor=MUTED)


# 1. Mutually exclusive primary sectors, sized by company count.
fig=canvas('北京 AI 创业公司主营赛道', '按主营方向归类，每家公司计一次；矩形面积对应公司数量。')
ax=fig.add_axes([.06,.19,.88,.60]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')

def partition(items,x,y,w,h):
    if len(items)==1:
        name,value=items[0]
        ax.add_patch(plt.Rectangle((x,y),w,h,facecolor=COLORS[name],edgecolor='white',linewidth=4))
        fontsize=16 if value>=10 else 11
        label=name.replace('机器人与具身智能','机器人与\n具身智能').replace('算力与基础设施','算力与\n基础设施').replace('Agent 产品与服务','Agent 产品\n与服务').replace('企业与数据服务','企业与\n数据服务')
        if h<.22: label=name
        ax.text(x+w/2,y+h/2+min(.035,h*.10),label,ha='center',va='center',fontsize=fontsize,color='white',weight='bold')
        ax.text(x+w/2,y+h/2-min(.07,h*.28),f'{value} 家 · {value/TOTAL:.1%}',ha='center',va='center',fontsize=fontsize-2,color='white')
        return
    total=sum(value for _,value in items)
    split=min(range(1,len(items)),key=lambda n:abs(sum(v for _,v in items[:n])-total/2))
    ratio=sum(v for _,v in items[:split])/total
    if w>=h:
        partition(items[:split],x,y,w*ratio,h);partition(items[split:],x+w*ratio,y,w*(1-ratio),h)
    else:
        partition(items[:split],x,y,w,h*ratio);partition(items[split:],x,y+h*ratio,w,h*(1-ratio))
partition(SECTORS.most_common(),0,0,1,1)
finish(fig,'startup-sector-treemap.png','主营赛道为互斥分类；原始近义类别合并。技术方向标签另行统计。')

# 2. Financing-stage composition within each primary sector.
STAGE_ORDER=['种子 / 天使轮','Pre-A','A 轮','B 轮','C 轮','D 轮及以后','Pre-IPO']
MATRIX=[[0]*len(STAGE_ORDER) for _ in ORDER]
for row in ROWS:
    group='D 轮及以后' if row['stage'] in ['D 轮','E 轮','F 轮'] else row['stage']
    MATRIX[ORDER.index(row['sector'])][STAGE_ORDER.index(group)]+=1
assert sum(map(sum,MATRIX))==TOTAL
METRICS['stageSectorMatrix']={'rows':ORDER,'columns':STAGE_ORDER,'counts':MATRIX}
fig=canvas('创业赛道与融资阶段', '每格为公司数量；颜色越深，样本公司越多。')
ax=fig.add_axes([.235,.25,.65,.51])
cmap=LinearSegmentedColormap.from_list('report_blue',['#f1f5fa',BLUE])
image=ax.imshow(MATRIX,cmap=cmap,aspect='auto',vmin=0)
ax.set_yticks(range(len(ORDER)),[f'{name}  {SECTORS[name]}' for name in ORDER],fontsize=11,color=INK)
ax.set_xticks(range(len(STAGE_ORDER)),['种子 /\n天使轮','Pre-A','A 轮','B 轮','C 轮','D 轮\n及以后','Pre-IPO'],fontsize=10,color=INK)
ax.tick_params(length=0,pad=10)
maxval=max(max(row) for row in MATRIX)
for i,values in enumerate(MATRIX):
    for j,value in enumerate(values):
        ax.text(j,i,str(value) if value else '—',ha='center',va='center',fontsize=14,color='white' if value>maxval*.57 else INK if value else '#a3aebc')
for spine in ax.spines.values(): spine.set_visible(False)
finish(fig,'startup-sector-stage-matrix.png','D 轮及以后合并 D / E / F 轮；Pre-IPO 单列。同行为同一主营赛道。')

# 3. Co-occurrence of the most frequent technology labels; no causal edges.
TOP_TAGS=[name for name,_ in list(DATA['tags'].items())[:8]]
PAIR_COUNTS=collections.Counter(pair for row in ROWS for pair in itertools.combinations(sorted(set(row['tags'])&set(TOP_TAGS)),2))
EDGES=sorted(((pair,value) for pair,value in PAIR_COUNTS.items() if value>=2),key=lambda item:(-item[1],item[0]))
METRICS['tagPairs']=[{'tags':list(pair),'companies':value} for pair,value in EDGES]
fig=canvas('同公司技术方向组合', '观察方向之间的交叉：节点为方向标签，连线为同时具备两个标签的公司。')
ax=fig.add_axes([.055,.17,.57,.61]);ax.set_aspect('equal');ax.axis('off');ax.set_xlim(-1.52,1.52);ax.set_ylim(-1.5,1.5)
positions={tag:(math.cos(math.pi/2+2*math.pi*i/len(TOP_TAGS)),math.sin(math.pi/2+2*math.pi*i/len(TOP_TAGS))) for i,tag in enumerate(TOP_TAGS)}
for (left,right),value in EDGES:
    a,b=positions[left],positions[right]
    ax.plot([a[0],b[0]],[a[1],b[1]],color='#a7bdcf',linewidth=value*.85,alpha=.75,zorder=1)
for tag,(x,y) in positions.items():
    count=DATA['tags'][tag]
    ax.scatter(x,y,s=430+count*80,color=TEAL if tag in ['具身智能','世界模型','人形机器人','VLA'] else BLUE,edgecolors='white',linewidth=2,zorder=3)
    ax.text(x,y,str(count),ha='center',va='center',fontsize=13,color='white',weight='bold',zorder=4)
    horizontal='right' if x<-.9 else 'left' if x>.9 else 'center'
    ax.text(x*1.25,y*1.27,TAG_NAMES.get(tag,tag),ha=horizontal,va='center',fontsize=10.5,color=INK)
fig.text(.66,.745,'方向组合',fontsize=12,weight='bold',color=INK)
fig.text(.92,.745,'公司数',fontsize=11,color=MUTED,ha='right')
for i,(pair,value) in enumerate(EDGES):
    y=.69-i*.052
    fig.text(.66,y,' + '.join(TAG_NAMES.get(tag,tag) for tag in pair),fontsize=10,color=INK)
    fig.text(.92,y,str(value),fontsize=11,color=INK,ha='right')
finish(fig,'startup-technology-combinations.png','仅展示前 8 个标签中同现不少于 2 家的组合；连线不表示技术依赖或岗位需求。')

# 4. District presence, deduplicated within district; one company can appear twice.
REGIONS=collections.Counter(region for row in ROWS for region in row['regions'])
LOCATED=sum(bool(row['regions']) for row in ROWS)
METRICS['districts']={'companiesWithRegion':LOCATED,'counts':dict(REGIONS.most_common())}
fig=canvas('北京创业公司公开地址分布',f'{LOCATED} 家样本公司有区县或经开区地址信息；按公司在各区域出现次数统计。')
ax=fig.add_axes([.23,.22,.57,.56]); items=REGIONS.most_common();names,values=zip(*items)
ax.hlines(range(len(names)),0,values,color='#e5ebf3',linewidth=8)
ax.scatter(values,range(len(names)),s=[160 if v<10 else 260 for v in values],color=BLUE,zorder=3)
ax.set_yticks(range(len(names)),names,fontsize=12,color=INK);ax.invert_yaxis();ax.set_xlim(0,max(values)*1.12);ax.set_xticks([]);strip_axes(ax)
for i,value in enumerate(values):ax.text(1.04,i,f'{value} 家',transform=ax.get_yaxis_transform(),va='center',fontsize=12,color=INK)
finish(fig,'startup-beijing-districts.png','同一公司可有多个区域地址；公开联系或办公地址不代表具体岗位工作地点。')

# 5. Investors in the selected named-round records; unknown names are not guessed.
INVESTORS=collections.Counter(investor for row in ROWS for investor in row['investors'])
WITH_INVESTORS=sum(bool(row['investors']) for row in ROWS)
METRICS['investors']={'companiesWithNames':WITH_INVESTORS,'counts':dict(INVESTORS.most_common())}
fig=canvas('投资机构覆盖的创业公司 TOP 12',f'基于 {WITH_INVESTORS} 家已收录投资机构名称的具名融资记录；按参与公司数排序。')
ax=fig.add_axes([.24,.22,.56,.56]);items=INVESTORS.most_common(12);names,values=zip(*items)
ax.barh(range(len(names)),values,color=BLUE,height=.55);ax.set_yticks(range(len(names)),names,fontsize=11,color=INK);ax.invert_yaxis();ax.set_xlim(0,max(values)*1.08);ax.set_xticks([]);strip_axes(ax)
for i,value in enumerate(values):ax.text(1.045,i,f'{value} 家',transform=ax.get_yaxis_transform(),va='center',fontsize=11,color=INK)
finish(fig,'startup-investor-coverage.png','一家可对应多家机构；仅代表样本已收录记录，不是机构完整投资组合或质量排名。')

# 6. Directory recruitment links; this is explicitly not a live-job count.
RECRUIT={sector:{'withEntry':sum(row['hasRecruit'] for row in ROWS if row['sector']==sector),'total':SECTORS[sector]} for sector in ORDER}
WITH_RECRUIT=sum(row['hasRecruit'] for row in ROWS)
METRICS['recruitment']={'withEntry':WITH_RECRUIT,'bySector':RECRUIT}
assert sum(item['withEntry'] for item in RECRUIT.values())==WITH_RECRUIT
fig=canvas('各创业赛道的招聘入口收录',f'样本中 {WITH_RECRUIT} 家公司已收录招聘入口，占 {WITH_RECRUIT/TOTAL:.1%}。')
ax=fig.add_axes([.235,.25,.59,.49])
for i,sector in enumerate(ORDER):
    total=RECRUIT[sector]['total'];value=RECRUIT[sector]['withEntry'];ratio=value/total
    ax.barh(i,ratio*100,color=TEAL,height=.55)
    ax.barh(i,(1-ratio)*100,left=ratio*100,color=GRAY,height=.55)
    ax.text(1.03,i,f'{value} / {total} 家',transform=ax.get_yaxis_transform(),va='center',fontsize=11,color=INK)
    if value:ax.text(ratio*50,i,f'{ratio:.0%}',ha='center',va='center',fontsize=11,color='white',weight='bold')
ax.set_yticks(range(len(ORDER)),ORDER,fontsize=11,color=INK);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xticks([]);strip_axes(ax)
fig.patches.extend([plt.Rectangle((.235,.77),.012,.012,transform=fig.transFigure,color=TEAL),plt.Rectangle((.42,.77),.012,.012,transform=fig.transFigure,color=GRAY)])
fig.text(.253,.768,'已收录入口',fontsize=10,color=MUTED);fig.text(.438,.768,'尚未收录入口',fontsize=10,color=MUTED)
finish(fig,'startup-recruitment-coverage.png','入口来自目录快照（2026.11.14）；有入口不等于当前有岗位，未收录不等于没有招聘。')

(ROOT/'docs/chart-data-2026.json').write_text(json.dumps(METRICS,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
all_files=['stage-overview-2026.png','direction-tags.png','beijing-company-overview.png',*FILES]
with zipfile.ZipFile(OUT/'beijing-startup-charts.zip','w',compression=zipfile.ZIP_DEFLATED) as bundle:
    for name in all_files:bundle.write(OUT/name,name)
assert sum(sum(row) for row in MATRIX)==TOTAL
print(json.dumps({'newCharts':len(FILES),'bundledImages':len(all_files),'locatedCompanies':LOCATED,'districtCounts':dict(REGIONS),'investorSample':WITH_INVESTORS,'recruitmentEntries':WITH_RECRUIT,'sectors':dict(SECTORS)},ensure_ascii=False))
