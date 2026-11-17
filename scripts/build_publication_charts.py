"""Render the Beijing directory overview and startup financing charts."""
import csv
import json
from html import escape
from itertools import combinations
from math import ceil, cos, radians, sin
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from build_startup_statistics import build
from beijing_job_rules import normtitle, keyurl

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

from chart_style import INK, MUTED, PAPER, PALETTE, page

def frame(title, bounds):
    fig = page(title)
    ax = fig.add_axes(bounds, facecolor=PAPER)
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
fig, ax = frame("北京雇主类型分布",[.07,.055,.86,.80])
for y,(label,rows) in enumerate(ordered_groups):
    value = len(rows)
    ax.text(0,y-.19,label,fontsize=15,va="bottom",color=INK)
    ax.plot([0,value],[y+.12,y+.12],lw=4,color=PALETTE[0],solid_capstyle="round")
    ax.text(1,y-.19,f"{value/total:.1%}",transform=ax.get_yaxis_transform(),
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
fig = page("北京 AI 公司地址分布")
ax = fig.add_axes([.22,.48,.56,.42])
colors = PALETTE
wedges,_ = ax.pie([n for _,n in parts],colors=colors,startangle=90,counterclock=False,
                   wedgeprops={"edgecolor":PAPER,"linewidth":.8})
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
    fig.text(left+.386,y,f"{count/region_total:.1%}",ha="right",color=INK,fontsize=12)
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
with (ROOT/"docs/beijing-jd-sample.csv").open(encoding="utf-8-sig",newline="") as source:
    jobs = list(csv.DictReader(source))
covered_ids = {j["目录ID"] for j in jobs}
assert covered_ids <= {c["id"] for c in companies}
roles = ["算法", "工程", "产品", "运营"]
assert all(j["方向"] in roles for j in jobs)

employer = lambda j: "liblib" if j["目录ID"] == "lovart" else j["目录ID"]
assert len({(employer(j), keyurl(j["详情"]), normtitle(j["岗位"])) for j in jobs}) == len(jobs)
covered = len({employer(j) for j in jobs})
groups_by_role = {r: [j for j in jobs if j["方向"] == r] for r in roles}
counts = {r: (len(js), len({employer(j) for j in js})) for r, js in groups_by_role.items()}
shares = [counts[role][0] / len(jobs) for role in roles]
fig = page("北京 AI 岗位方向占比")
ax = fig.add_axes([.068, .072, .864, .789])
ax.set(xlim=(0, 1), ylim=(0, 1))
ax.axis("off")
role_colors = ["#825441", "#47665e", "#dfbc95", "#b9c7bc"]
lower_height = sum(shares[2:])
for indices, bottom, height in [((0, 1), lower_height, sum(shares[:2])), ((2, 3), 0, lower_height)]:
    left = 0
    for i in indices:
        width = shares[i] / height
        ax.add_patch(Rectangle((left, bottom), width, height, fc=role_colors[i], ec=PAPER, lw=2))
        color = PAPER if i < 2 else INK
        ax.text(left + .031, bottom + height * .61, roles[i], color=color, va="center", fontsize=17)
        ax.text(left + .029, bottom + height * (.48 if i < 2 else .29), f"{shares[i]:.1%}",
                color=color, va="center", fontsize=25 if i < 2 else 18, weight="bold")
        left += width
save(fig,"beijing-job-directions.png")
md = ["# 北京 AI 岗位", "", f"目录共 {total} 个条目。本次收录 {covered} 家雇主的 {len(jobs):,} 条北京 AI 职位记录。更新于 2026 年 11 月 17 日。", "",
      "![北京 AI 岗位方向](images/beijing-job-directions.png)", "",
      "| 方向 | 岗位数 | 雇主数 |", "| --- | ---: | ---: |"]
for role, (n, employers) in counts.items():
    md.append(f"| [{role}](#{role}) | {n:,} | {employers} |")
md += ["","[全部岗位明细](beijing-jd-sample.csv) · [307 家核查记录](beijing-employer-audit.csv) · [同文重复](beijing-jd-reposts.csv) · [改写合并](beijing-jd-rewrite-merges.csv) · [待核记录](beijing-jd-rewrite-pending.csv)","",
       "工作地点须明确包含北京。先采用官网职位，再用 Ivyea 和 Offer 岛补充。优先按招聘编号合并；同一雇主下，名称相同或近似且主要职责文本一致的重复发布合并。改写公告按团队、核心职责及招聘对象复核；待核记录仍计入。缺少可辨认编号时按同一雇主的同名岗位合并。雇主可以跨方向出现，招聘人数不计入岗位数。未找到可确认岗位的雇主保留在核查记录中。",""]
for role, js in groups_by_role.items():
    md += [f"## {role}", ""]
    path = f"beijing-jobs-{roles.index(role)+1}.html"
    names = {c["id"]: c["name"] for c in companies}
    html = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>北京 AI {role}岗位</title>",
            "<style>body{max-width:46rem;margin:2rem auto;padding:0 1rem;background:#fbf8f1;color:#373c36;font:1rem/1.6 system-ui,sans-serif}h1{font-size:1.6rem}summary{cursor:pointer;padding:.65rem 0}details{border-top:1px solid #ddd5c8}li{margin:.65rem 0}a{color:#784b3b}ul{padding-left:1.3rem}</style>",
            f"<h1>北京 AI {role}岗位</h1><p>{len(js):,} 个岗位 · {counts[role][1]} 家雇主</p>"]
    by_employer = {}
    for job in js:
        by_employer.setdefault(employer(job), []).append(job)
    for cid, postings in sorted(by_employer.items(),key=lambda pair:(-len(pair[1]),names[pair[0]])):
        html.append(f"<details><summary>{escape(names[cid])} · {len(postings)}</summary><ul>")
        for job in postings:
            html.append(f'<li><a href="{escape(job["详情"], quote=True)}">{escape(job["岗位"])}</a></li>')
        html.append("</ul></details>")
    html.append("</html>")
    (ROOT/"docs"/path).write_text("\n".join(html),encoding="utf8")
    md += [f"[查看全部 {len(js):,} 个{role}岗位](https://ningsiyuan1024.github.io/ai-company-map/docs/{path})",""]
(ROOT/"docs/JOBS.md").write_text("\n".join(md),encoding="utf8")
ordered = ranked(sectors)
main_sectors = ordered[:8] + [("其他赛道", sum(value for _, value in ordered[8:]))]
assert sum(value for _, value in main_sectors) == total

# Allocate a hundred dots by largest remainder; labels use unrounded counts.
fig, ax = frame("北京 AI 公司主营赛道",[.07,.46,.86,.41])
dots = [count * 100 // total for _, count in main_sectors]
for i in sorted(range(len(dots)), key=lambda i: -(main_sectors[i][1]*100 % total))[:100-sum(dots)]:
    dots[i] += 1
offset = 0
for n, color in zip(dots, colors):
    for index in range(offset, offset+n):
        y,x = divmod(index, 10)
        ax.add_patch(plt.Circle((x+.5,y+.5),.4,color=color,lw=0))
    offset += n
assert offset == 100
ax.set(xlim=(0,10),ylim=(10,0),aspect="equal")
ax.axis("off")
for i,((label,count),color) in enumerate(zip(main_sectors,colors)):
    col,row = divmod(i,5)
    x,y = .07+col*.48,.405-row*.071
    fig.text(x,y,"●",color=color,fontsize=13)
    fig.text(x+.035,y,label,fontsize=10.5,color=INK)
    fig.text(x+.424,y,f"{count/total:.1%}",fontsize=11,weight="bold",ha="right",color=INK)
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
    ax.scatter([i*.072+.008 for i in range(n)],[y+.69]*n,s=24,color=PALETTE[1],lw=0,clip_on=False)
save(fig,"beijing-directory-pairs.png")

stages = ["种子 / 天使轮", "Pre-A", *[f"{letter} 轮" for letter in "ABCDEF"], "Pre-IPO"]
values = [stats["stage"].get(stage,0) for stage in stages]
assert sum(values) == stats["total"]
fig, ax = frame("北京创业公司融资阶段",[.07,.06,.86,.80])
for y,(label,n) in enumerate(zip(stages,values)):
    share = n / stats["total"]
    ax.text(0,y,label,fontsize=14,va="center",color=INK)
    ax.plot([.33,.33+share*2.25],[y,y],lw=4,color=PALETTE[1],solid_capstyle="round")
    ax.text(.99,y,f"{share:.1%}",ha="right",va="center",fontsize=16,weight="bold",color=INK)
ax.set(xlim=(0,1),ylim=(len(stages)-.35,-.65))
ax.axis("off")
save(fig,"stage-overview-2026.png")
