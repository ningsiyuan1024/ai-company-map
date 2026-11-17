"""Render the Beijing directory overview and startup financing charts."""
import csv
import json
from itertools import combinations
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

def frame(title, subtitle, bounds):
    fig = plt.figure(figsize=(8, 6), dpi=180)
    fig.text(.055, .91, title, fontsize=22, weight="bold", color=INK)
    fig.text(.055, .85, subtitle, fontsize=11, color=MUTED)
    ax = fig.add_axes(bounds)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0, labelcolor=INK)
    return fig, ax

def save(fig, filename):
    fig.savefig(OUT / filename)
    plt.close(fig)

tags, districts = Counter(), Counter()
directions_by_id = {}
aliases = {"AI Agent":"Agent", "AI Infra":"AI 基础设施", "AI4Science":"AI for Science"}
pairs = Counter()
located = 0
for company in companies:
    directions = {aliases.get(tag, tag) for tag in company["tags"] if tag != "外企"}
    tags.update(directions)
    pairs.update(combinations(sorted(directions), 2))
    directions_by_id[company["id"]] = directions
    regions = {place["district"] for place in company["locations"] if place["district"]}
    districts.update(regions)
    located += bool(regions)

def ranked(counts):
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))

# Examples use the directory's own names and tags.
examples = {
    "Agent": ["baidu", "zhipu", "01ai"],
    "具身智能": ["unitree", "linkerbot", "d_robotics"],
    "AI 基础设施": ["tencent", "infinigence", "siliconflow"],
    "大语言模型": ["deepseek", "moonshot", "bytedance"],
    "世界模型": ["pony", "shengshu", "baai"],
    "多模态": ["modelbest", "stepfun", "deepwise"],
}
names_by_id = {company["id"]:company["name"] for company in companies}
fig, ax = frame("按技术方向找公司", "北京 · 六个常见方向", [.055,.07,.89,.69])
ax.set(xlim=(0,1),ylim=(6,0))
ax.axis("off")
for y,(direction, ids) in enumerate(examples.items()):
    assert all(direction in directions_by_id[i] for i in ids)
    ax.axhline(y,color=LIGHT,lw=.8)
    ax.text(.005,y+.49,direction,va="center",color=TEAL,weight="bold",fontsize=13)
    names = [names_by_id[i].split(" / ")[0] for i in ids]
    ax.text(.235,y+.49,"   ·   ".join(names),va="center",color=INK,fontsize=12)
save(fig,"beijing-company-overview.png")

ordered_districts = ranked(districts)
parts = ordered_districts[:3] + [("其他区域",sum(n for _,n in ordered_districts[3:]))]
region_total = sum(districts.values())
fig, ax = frame("北京 AI 公司地址分布",
                f"{located} 家公司与团队 · 跨区办公的公司在每个区各算一次", [.035,.08,.57,.68])
colors = ["#196c63","#497d9c","#c18550","#a8b7b3"]
wedges,_ = ax.pie([n for _,n in parts],colors=colors,startangle=90,counterclock=False,
                   wedgeprops={"edgecolor":"white","linewidth":2})
for i,(label,count) in enumerate(parts):
    y = .64-i*.126
    fig.text(.61,y,"●",color=wedges[i].get_facecolor(),fontsize=15)
    fig.text(.65,y,label.replace("北京经济技术开发区","经开区"),color=INK,fontsize=13)
    fig.text(.94,y,f"{count} · {count/region_total:.1%}",ha="right",color=INK,fontsize=12)
save(fig,"beijing-directory-districts.png")
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

# Split rectangles along the longer side, preserving the area of each category.
def tiles(items, x, y, width, height):
    if len(items) == 1:
        yield (*items[0], x, y, width, height)
        return
    weight = sum(n for _, n in items)
    cut = min(range(1, len(items)), key=lambda i: abs(sum(n for _, n in items[:i]) - weight/2))
    share = sum(n for _, n in items[:cut]) / weight
    if width >= height:
        yield from tiles(items[:cut], x, y, width*share, height)
        yield from tiles(items[cut:], x+width*share, y, width*(1-share), height)
    else:
        yield from tiles(items[:cut], x, y+height*(1-share), width, height*share)
        yield from tiles(items[cut:], x, y, width, height*(1-share))

fig, ax = frame("北京 AI 公司主营赛道", f"{total} 家公司与团队", [.05,.06,.90,.72])
palette = ["#195d57","#27786f","#376880","#57748d","#546a63","#786854","#716489","#8a624d","#5c676c"]
for tile, color in zip(tiles(main_sectors,0,0,1.65,1), palette):
    name, count, x, y, w, h = tile
    ax.add_patch(plt.Rectangle((x,y),w,h,facecolor=color,edgecolor="white",lw=2))
    label = name.replace("Agent研发与应用","Agent 研发与应用")
    if w < .33 and len(label)>5:
        label = label.replace("Agent 研发与应用","Agent\n研发与应用")
    ax.text(x+w/2,y+h/2,f"{label}\n{count}",ha="center",va="center",color="white",fontsize=15 if count>=35 else 9 if w<.21 else 11)
ax.set(xlim=(0,1.65),ylim=(0,1))
ax.axis("off")
save(fig,"beijing-directory-sectors.png")

# The neutral cells complete the grid; only co-occurrences above the threshold are shown.
cutoff = 4
common = {pair:n for pair,n in pairs.items() if n>=cutoff}
names = sorted({t for pair in common for t in pair}, key=lambda t:(-tags[t],t))
fig, ax = frame("北京 AI 公司技术方向组合", f"{total} 家公司与团队 · 同现至少 {cutoff} 家", [.22,.17,.67,.59])
for col, first in enumerate(names[:-1]):
    for row in range(col+1,len(names)):
        count = common.get(tuple(sorted((first,names[row]))))
        ax.add_patch(plt.Rectangle((col-.48,row-.48),.96,.96,color=plt.cm.BuGn(.25+.62*count/max(common.values())) if count else "#f1f4f3",lw=0))
        if count:
            ax.text(col,row,str(count),ha="center",va="center",fontsize=14,color="white" if count>=7 else INK,weight="bold")
ax.set_xticks(range(len(names)-1),names[:-1],rotation=25,ha="right")
ax.set_yticks(range(1,len(names)),names[1:])
ax.set_xlim(-.5,len(names)-1.5)
ax.set_ylim(len(names)-.5,.5)
save(fig,"beijing-directory-pairs.png")

stages = ["种子 / 天使轮", "Pre-A", *[f"{letter} 轮" for letter in "ABCDEF"], "Pre-IPO"]
values = [stats["stage"].get(stage,0) for stage in stages]
assert sum(values) == stats["total"]
fig, ax = frame("北京创业公司融资阶段", f"{stats['total']} 家创业公司", [.08,.13,.87,.61])
ax.bar(range(len(values)),values,width=.65,color="#46768a")
for i,n in enumerate(values):
    ax.text(i,n+.55,str(n),ha="center",fontsize=14,color=INK)
ax.set_xticks(range(len(values)),["种子 /\n天使轮",*stages[1:]])
ax.set_ylim(0,max(values)*1.12)
ax.set_yticks([])
ax.axhline(0,color=MUTED,lw=1)
save(fig,"stage-overview-2026.png")
