"""Render the Beijing directory overview and startup financing charts."""
import csv
import json
from itertools import combinations
from math import cos, radians
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib import patheffects
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

tags, linked, districts = Counter(), Counter(), Counter()
aliases = {"AI Agent":"Agent", "AI Infra":"AI 基础设施", "AI4Science":"AI for Science"}
pairs = Counter()
located = 0
for company in companies:
    directions = {aliases.get(tag, tag) for tag in company["tags"] if tag != "外企"}
    tags.update(directions)
    pairs.update(combinations(sorted(directions), 2))
    if company["recruitUrl"]:
        linked.update(directions)
    regions = {place["district"] for place in company["locations"] if place["district"]}
    districts.update(regions)
    located += bool(regions)

def ranked(counts):
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))

entries = sum(bool(row["recruitUrl"]) for row in companies)
items = ranked(tags)[:10]
fig, ax = frame("技术方向与招聘入口", f"北京 · {total} 家公司与团队", [.20,.09,.70,.64])
for y, (name, count) in enumerate(items):
    entry_count = linked[name]
    ax.plot([entry_count, count], [y,y], color=LIGHT, lw=3, zorder=1)
    ax.scatter(entry_count,y,color=TEAL,s=60,zorder=2)
    ax.scatter(count,y,facecolors="white",edgecolors=INK,s=60,zorder=2)
    ax.annotate(str(entry_count),(entry_count,y),xytext=(-8,0),textcoords="offset points",ha="right",va="center",color=TEAL)
    ax.annotate(str(count),(count,y),xytext=(8,0),textcoords="offset points",va="center",color=INK)
ax.scatter([],[],color=TEAL,label="有招聘入口")
ax.scatter([],[],facecolors="white",edgecolors=INK,label="该方向总数")
ax.legend(loc="lower right",bbox_to_anchor=(1,1.02),ncol=2,frameon=False,handletextpad=.25)
ax.set_yticks(range(len(items)), [name for name,_ in items])
ax.set_xlim(0,max(tags.values())+4)
ax.set_xticks(range(0,max(tags.values())+1,10))
ax.set_axisbelow(True)
ax.grid(axis="x",color="#eaf0ee")
ax.invert_yaxis()
save(fig,"beijing-company-overview.png")

def district_map(counts, located):
    source = (ROOT / "beijing-basemap.js").read_text(encoding="utf8")
    basemap = json.loads(source.split("=", 1)[1].strip().rstrip(";"))
    places = {p["name"]: tuple(reversed(p["coord"])) for p in basemap["places"]}
    fig, ax = plt.subplots(figsize=(8, 7.4), dpi=180)
    fig.subplots_adjust(left=.035, right=.965, bottom=.065, top=.87)
    fig.text(.05, .939, "北京 AI 公司地址分布", fontsize=22, weight="bold", color="#182b42")
    fig.text(.05, .892, f"{located} 家有区域信息 · 圆面积为公司数", fontsize=11, color="#536476")
    fig.text(.05, .025, "底图 © OpenStreetMap contributors", fontsize=8, color="#536476")
    ax.set_facecolor("#f5f8f7")
    roads, parks, water = [], [], []
    for feature in basemap["geojson"]["features"]:
        kind = feature["properties"]["kind"]
        coords = feature["geometry"]["coordinates"]
        if kind == "road":
            roads.extend(coords)
        elif kind == "park":
            parks.append(coords[0])
        elif kind == "water":
            water.append(coords[0])
    for shapes, fill in [(parks, "#e2ebe2"), (water, "#c4dfe6")]:
        ax.add_collection(PolyCollection(shapes, facecolors=fill, edgecolors="none"))
    ax.add_collection(LineCollection(roads, colors="#d5dcdb", linewidths=.42))
    # Offsets are in print points so the dense inner-city labels stay legible.
    offsets = {"海淀区": (-12, 22), "西城区": (-8,-15), "东城区": (0,15),
               "朝阳区": (13,-2), "门头沟区": (-6,8), "石景山区": (-9,-11)}
    for district, count in counts.most_common():
        x, y = places[district]
        ax.scatter(x, y, s=count*11, color="#24796f", alpha=.78,
                   edgecolors="white", linewidths=.8, zorder=3)
        dx, dy = offsets.get(district, (7, 4))
        label = "经开区" if district == "北京经济技术开发区" else district
        ax.annotate(f"{label} {count}", (x, y), xytext=(dx,dy), textcoords="offset points",
                    ha="right" if dx < 0 else "left", va="center", fontsize=10, color="#183b38", zorder=5,
                    path_effects=[patheffects.withStroke(linewidth=3, foreground="white")])
    ax.set_aspect(1 / cos(radians(40)))
    ax.set_xlim(115.98, 116.78)
    ax.set_ylim(39.68, 40.36)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.savefig(OUT / "beijing-directory-districts.png")
    plt.close(fig)


district_map(districts, located)
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
fig, ax = frame("北京创业公司融资阶段", f"{stats['total']} 家已披露轮次的未上市创业公司", [.08,.13,.87,.61])
ax.bar(range(len(values)),values,width=.65,color="#46768a")
for i,n in enumerate(values):
    ax.text(i,n+.55,str(n),ha="center",fontsize=14,color=INK)
ax.set_xticks(range(len(values)),["种子 /\n天使轮",*stages[1:]])
ax.set_ylim(0,max(values)*1.12)
ax.set_yticks([])
ax.axhline(0,color=MUTED,lw=1)
save(fig,"stage-overview-2026.png")
