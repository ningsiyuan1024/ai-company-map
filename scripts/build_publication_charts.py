"""Render the Beijing directory overview and startup financing charts."""
import csv
import json
from itertools import combinations
from math import ceil, cos, radians, sin
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from build_startup_statistics import build

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/images"
directory = json.loads((ROOT / "skills/ai-company-match/references/companies.json").read_text(encoding="utf8"))
companies = directory["companies"]
total = len(companies)
assert total == directory["total"] == len({row["id"] for row in companies})
stats = build()
font_path = Path("C:/Windows/Fonts/msyh.ttc")
if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
fonts = {font.name for font in font_manager.fontManager.ttflist}
plt.rcParams["font.family"] = next(name for name in ("Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC") if name in fonts)

INK, MUTED, TEAL, LIGHT = "#183d40", "#52676b", "#16796e", "#cbded9"

def frame(title, bounds):
    fig = plt.figure(figsize=(6, 7.5), dpi=200)
    fig.text(.07, .935, title, fontsize=23, weight="bold", color=INK)
    ax = fig.add_axes(bounds)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0, labelcolor=INK)
    return fig, ax

def save(fig, filename):
    fig.savefig(OUT / filename)
    plt.close(fig)

tags, districts = Counter(), Counter()
aliases = {"AI Agent":"Agent", "AI Infra":"AI 基础设施", "AI4Science":"AI for Science"}
pairs = Counter()
district_names = "东城区 西城区 朝阳区 丰台区 石景山区 海淀区 门头沟区 房山区 通州区 顺义区 昌平区 大兴区 怀柔区 平谷区 密云区 延庆区 北京经济技术开发区".split()
located = 0
for company in companies:
    directions = {aliases.get(tag, tag) for tag in company["tags"] if tag != "外企"}
    tags.update(directions)
    pairs.update(combinations(sorted(directions), 2))
    regions = set()
    for place in company["locations"]:
        if place["district"]:
            regions.add(place["district"])
        else:
            regions.update(name for name in district_names if name in (place["address"] or ""))
    districts.update(regions)
    located += bool(regions)

def ranked(counts):
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))

finance = json.loads((ROOT/"docs/finance-2026.json").read_text(encoding="utf8"))["records"]
startup_ids = {i for row in stats["companies"] for i in row["directoryIds"]}
large = set("bytedance alibaba tencent baidu huawei xiaomi jd meituan netease kuaishou ant xiaohongshu iflytek 360 bilibili".split())
industry = set("teleai tal tkfunds citicpress nkdpharm chinawenfa wizardquant zsquant zding joinquant lingjun qianxiang".split())

def employer_type(row):
    key = row["id"]
    if key in large:
        return "国内科技大厂"
    if "外企" in row["tags"] or row["category"] == "国际科技" or key in {"amazon","schneider-electric"}:
        return "外企"
    if row["category"] == "研究机构":
        return "研究机构"
    if key in industry:
        return "传统行业与金融机构"
    if key in startup_ids:
        return "创业公司"
    if finance[key].get("listing") or finance[key].get("otc"):
        return "其他上市与挂牌企业"
    if row["category"] in {"机器人与具身","机器人与具身智能","具身机器人","具身智能","智能硬件","汽车与智能驾驶"}:
        return "机器人与智能硬件企业"
    if row["category"] in {"算力与芯片","AI基础设施","数据中心"}:
        return "芯片与算力企业"
    return "其他科技公司与团队"

groups = {}
for row in companies:
    groups.setdefault(employer_type(row),[]).append(row)
ordered_groups = sorted(groups.items(),key=lambda item:-len(item[1]))
assert sum(len(rows) for _,rows in ordered_groups) == total
fig, ax = frame(f"北京 {total} 家雇主类型分布",[.07,.055,.86,.80])
for y,(label,rows) in enumerate(ordered_groups):
    value = len(rows)
    ax.text(0,y-.19,label,fontsize=15,va="bottom",color=INK)
    ax.barh(y+.12,value,height=.20,color="#355790")
    ax.text(1,y-.19,str(value),transform=ax.get_yaxis_transform(),
            ha="right",va="bottom",fontsize=16,weight="bold",color=INK)
ax.set_xlim(0,max(len(rows) for _,rows in ordered_groups))
ax.set_ylim(len(groups)-.5,-.7)
ax.axis("off")
save(fig,"beijing-company-overview.png")

md = ["# 北京雇主名单","","307 个公司与团队条目，每个条目归入一个主类。点击名称打开地图。",""]
for label,rows in ordered_groups:
    md.append(f"[{label}（{len(rows)}）](#{label.lower()})")
md.extend(["","创业公司按已知融资记录归类。LiblibAI 和 Lovart 在地图中各有入口；融资专题把它们算作同一家公司。施耐德电气和博世归入外企，微软亚洲研究院随微软归入外企。",""])
for label,rows in ordered_groups:
    md.extend([f"## {label}",""])
    for row in rows:
        md.append(f"- [{row['name']}]({row['directoryUrl']})")
    md.append("")
(ROOT/"docs/EMPLOYERS.md").write_text("\n".join(md),encoding="utf8")

parts = ranked(districts)
assert set(districts) <= set(district_names)
region_total = sum(districts.values())
# Mobile layout: label the largest share directly and reserve full-width rows for small slices.
fig = plt.figure(figsize=(6,7.5),dpi=200)
fig.text(.07,.935,"北京 AI 公司地址分布",fontsize=23,weight="bold",color=INK)
ax = fig.add_axes([.22,.48,.56,.42])
colors = ["#355790","#72a5d2","#dc8768","#68aaa2","#a381b4","#d5ad63","#76a4ae",
          "#b986a2","#93aa7e","#a395ba","#dba899","#8299b2","#9dafac"]
wedges,_ = ax.pie([n for _,n in parts],colors=colors,startangle=90,counterclock=False,
                   wedgeprops={"edgecolor":"white","linewidth":.8})
name,count = parts[0]
angle = radians((wedges[0].theta1 + wedges[0].theta2)/2)
ax.text(.46*cos(angle),.46*sin(angle),f"{name}\n{count/region_total:.1%}",
        ha="center",va="center",fontsize=15,weight="bold",color="white")
rows_per_column = ceil(len(parts)/2)
for i,(label,count) in enumerate(parts):
    column,row = divmod(i,rows_per_column)
    left = .065 + column*.49
    y = .425-row*.055
    fig.text(left,y,"●",color=wedges[i].get_facecolor(),fontsize=11)
    fig.text(left+.035,y,label.replace("北京经济技术开发区","北京经开区"),color=INK,fontsize=12)
    fig.text(left+.292,y,str(count),ha="right",color=INK,fontsize=12,weight="bold")
    fig.text(left+.386,y,f"{count/region_total:.1%}",ha="right",color=MUTED,fontsize=10)
save(fig,"beijing-directory-districts.png")
print(f"districts: {located} records, {region_total} presences, {len(parts)} regions")
with (ROOT / "docs/company-directions.csv").open(encoding="utf-8-sig", newline="") as source:
    classifications = {row["id"]: row for row in csv.DictReader(source)}
assert classifications.keys() == {company["id"] for company in companies}
sectors = Counter()
for company in companies:
    record = classifications[company["id"]]
    assert record["原分类"] == company["category"]
    sectors[record["合并分类"]] += 1
ordered = ranked(sectors)
main_sectors = ordered[:8] + [("其他赛道", sum(value for _, value in ordered[8:]))]
assert sum(value for _, value in main_sectors) == total

# One square per directory entry; the final row may be partial.
fig, ax = frame("北京 AI 公司主营赛道",[.07,.46,.86,.41])
columns = 24
offset = 0
for (label,count),color in zip(main_sectors,colors):
    for index in range(offset,offset+count):
        y,x = divmod(index,columns)
        ax.add_patch(plt.Rectangle((x,y),.87,.87,color=color,lw=0))
    offset += count
assert offset == total
ax.set(xlim=(0,columns),ylim=(ceil(total/columns),0),aspect="equal")
ax.axis("off")
for i,((label,count),color) in enumerate(zip(main_sectors,colors)):
    col,row = divmod(i,5)
    x,y = .07+col*.48,.405-row*.071
    fig.text(x,y,"■",color=color,fontsize=13)
    fig.text(x+.035,y,label,fontsize=12,color=INK)
    fig.text(x+.405,y,str(count),fontsize=13,weight="bold",ha="right",color=INK)
save(fig,"beijing-directory-sectors.png")

# A sparse set of pairs reads naturally as two aligned labels and a shared count.
cutoff = 4
common = [(pair,n) for pair,n in ranked(pairs) if n>=cutoff]
fig, ax = frame("北京 AI 公司技术方向组合",[.07,.07,.86,.80])
ax.set(xlim=(0,1),ylim=(len(common),0))
ax.axis("off")
for y,((left,right),n) in enumerate(common):
    ax.text(0,y+.34,left,fontsize=14,va="center",color=INK)
    ax.text(.38,y+.34,"+",fontsize=12,va="center",color=MUTED)
    ax.text(.46,y+.34,right,fontsize=14,va="center",color=INK)
    ax.text(1,y+.34,f"{n} 家",fontsize=15,weight="bold",va="center",ha="right",color=INK)
    ax.barh(y+.67,n/common[0][1],height=.09,color="#72a5d2")
save(fig,"beijing-directory-pairs.png")

stages = ["种子 / 天使轮", "Pre-A", *[f"{letter} 轮" for letter in "ABCDEF"], "Pre-IPO"]
values = [stats["stage"].get(stage,0) for stage in stages]
assert sum(values) == stats["total"]
fig, ax = frame("北京创业公司融资阶段", [.085,.12,.84,.73])
ax.bar(range(len(values)),values,width=.68,color="#355790")
for i,n in enumerate(values):
    ax.text(i,n+.55,str(n),ha="center",fontsize=15,weight="bold",color=INK)
ax.set_xticks(range(len(values)),["种子 /\n天使","Pre-A","A轮","B轮","C轮","D轮","E轮","F轮","Pre-\nIPO"],fontsize=12)
ax.set_ylim(0,max(values)*1.12)
ax.set_yticks([])
ax.axhline(0,color=MUTED,lw=1)
save(fig,"stage-overview-2026.png")
