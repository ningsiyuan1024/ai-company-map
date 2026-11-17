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

def frame(title, bounds):
    fig = plt.figure(figsize=(8, 6), dpi=180)
    fig.text(.055, .91, title, fontsize=22, weight="bold", color=INK)
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
fig, ax = frame(f"北京 {total} 家雇主类型分布",[.31,.08,.59,.75])
for y,(label,rows) in enumerate(ordered_groups):
    ax.barh(y,len(rows),height=.54,color="#4254aa")
    ax.annotate(str(len(rows)),(len(rows),y),xytext=(5,0),textcoords="offset points",va="center",color=INK,fontsize=13)
ax.set_yticks(range(len(groups)),[label for label,_ in ordered_groups],fontsize=12)
ax.set_xticks([])
ax.invert_yaxis()
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
fig, ax = frame("北京 AI 公司地址分布",[.025,.15,.57,.60])
colors = ["#4557a6","#77a7db","#ef946c","#79bbb1","#9377b8","#e2ae59","#65a2ba",
          "#c388ae","#8eac75","#b09ac9","#e8ad9e","#7c92b4","#9bafa8"]
wedges,_ = ax.pie([n for _,n in parts],colors=colors,startangle=90,counterclock=False,
                   wedgeprops={"edgecolor":"white","linewidth":.8})
for i,(label,count) in enumerate(parts):
    y = .81-i*(.71/max(1,len(parts)-1))
    fig.text(.585,y,"●",color=wedges[i].get_facecolor(),fontsize=13)
    fig.text(.625,y,label.replace("北京经济技术开发区","北京经开区"),color=INK,fontsize=12)
    fig.text(.95,y,f"{count}  ·  {count/region_total:.1%}",ha="right",color=INK,fontsize=12)
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

fig, ax = frame("北京 AI 公司主营赛道", [.05,.06,.90,.76])
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
fig, ax = frame("北京 AI 公司技术方向组合", [.22,.17,.67,.65])
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
fig, ax = frame("北京创业公司融资阶段", [.08,.13,.87,.67])
ax.bar(range(len(values)),values,width=.65,color="#46768a")
for i,n in enumerate(values):
    ax.text(i,n+.55,str(n),ha="center",fontsize=14,color=INK)
ax.set_xticks(range(len(values)),["种子 /\n天使轮",*stages[1:]])
ax.set_ylim(0,max(values)*1.12)
ax.set_yticks([])
ax.axhline(0,color=MUTED,lw=1)
save(fig,"stage-overview-2026.png")
