"""Build the startup investor chart and package the publication charts.
Requires matplotlib; uses only the public local directory and financing ledgers.
"""
import collections
import itertools
import json
from pathlib import Path
import zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
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


def finish(fig,name):
    fig.savefig(OUT/name)
    plt.close(fig); FILES.append(name)


def strip_axes(ax):
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(length=0,labelcolor=MUTED)


# 2. Financing-stage composition within each primary sector.
STAGE_ORDER=['种子 / 天使轮','Pre-A','A 轮','B 轮','C 轮','D 轮及以后','Pre-IPO']
MATRIX=[[0]*len(STAGE_ORDER) for _ in ORDER]
for row in ROWS:
    group='D 轮及以后' if row['stage'] in ['D 轮','E 轮','F 轮'] else row['stage']
    MATRIX[ORDER.index(row['sector'])][STAGE_ORDER.index(group)]+=1
assert sum(map(sum,MATRIX))==TOTAL
METRICS['stageSectorMatrix']={'rows':ORDER,'columns':STAGE_ORDER,'counts':MATRIX}
# 3. Co-occurrence of the most frequent technology labels; no causal edges.
TOP_TAGS=[name for name,_ in list(DATA['tags'].items())[:8]]
PAIR_COUNTS=collections.Counter(pair for row in ROWS for pair in itertools.combinations(sorted(set(row['tags'])&set(TOP_TAGS)),2))
EDGES=sorted(((pair,value) for pair,value in PAIR_COUNTS.items() if value>=2),key=lambda item:(-item[1],item[0]))
METRICS['tagPairs']=[{'tags':list(pair),'companies':value} for pair,value in EDGES]
# 4. District presence, deduplicated within district; one company can appear twice.
REGIONS=collections.Counter(region for row in ROWS for region in row['regions'])
LOCATED=sum(bool(row['regions']) for row in ROWS)
METRICS['districts']={'companiesWithRegion':LOCATED,'counts':dict(REGIONS.most_common())}
# 5. Investors in the selected named-round records; unknown names are not guessed.
INVESTORS=collections.Counter(investor for row in ROWS for investor in row['investors'])
WITH_INVESTORS=sum(bool(row['investors']) for row in ROWS)
METRICS['investors']={'companiesWithNames':WITH_INVESTORS,'counts':dict(INVESTORS.most_common())}
fig=canvas('投资机构覆盖的创业公司 TOP 12',f'{WITH_INVESTORS} 家有本轮投资方记录')
ax=fig.add_axes([.24,.22,.56,.56]);items=INVESTORS.most_common(12);names,values=zip(*items)
ax.barh(range(len(names)),values,color=BLUE,height=.55);ax.set_yticks(range(len(names)),names,fontsize=11,color=INK);ax.invert_yaxis();ax.set_xlim(0,max(values)*1.08);ax.set_xticks([]);strip_axes(ax)
for i,value in enumerate(values):ax.text(1.045,i,f'{value} 家',transform=ax.get_yaxis_transform(),va='center',fontsize=11,color=INK)
finish(fig,'startup-investor-coverage.png')

# 6. Directory recruitment links; this is explicitly not a live-job count.
RECRUIT={sector:{'withEntry':sum(row['hasRecruit'] for row in ROWS if row['sector']==sector),'total':SECTORS[sector]} for sector in ORDER}
WITH_RECRUIT=sum(row['hasRecruit'] for row in ROWS)
METRICS['recruitment']={'withEntry':WITH_RECRUIT,'bySector':RECRUIT}
assert sum(item['withEntry'] for item in RECRUIT.values())==WITH_RECRUIT
(ROOT/'docs/chart-data-2026.json').write_text(json.dumps(METRICS,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
all_files=['stage-overview-2026.png',*FILES]
with zipfile.ZipFile(OUT/'beijing-startup-charts.zip','w',compression=zipfile.ZIP_DEFLATED) as bundle:
    for name in all_files:bundle.write(OUT/name,name)
with zipfile.ZipFile(OUT/'beijing-company-charts.zip','w',compression=zipfile.ZIP_DEFLATED) as bundle:
    for name in ['beijing-company-overview.png','beijing-directory-districts.png','beijing-directory-sectors.png','beijing-directory-pairs.png',*all_files]:
        bundle.write(OUT/name,name)
assert sum(sum(row) for row in MATRIX)==TOTAL
print(json.dumps({'newCharts':len(FILES),'bundledImages':len(all_files),'locatedCompanies':LOCATED,'districtCounts':dict(REGIONS),'investorSample':WITH_INVESTORS,'recruitmentEntries':WITH_RECRUIT,'sectors':dict(SECTORS)},ensure_ascii=False))
