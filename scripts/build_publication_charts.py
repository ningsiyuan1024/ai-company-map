"""Render the Beijing directory overview and startup financing charts."""
import json
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

def chart(filename, title, scope, items, subset=None, color="#327f77"):
    labels, values = zip(*items)
    fig, ax = plt.subplots(figsize=(8, 5.6), dpi=180)
    fig.subplots_adjust(left=.23, right=.87, top=.79, bottom=.06)
    fig.text(.06, .91, title, fontsize=22, weight="bold", color="#182b42")
    fig.text(.06, .845, scope, fontsize=11, color="#536476")
    ax.barh(labels, values, height=.55, color="#dbe5e9" if subset is not None else color)
    if subset is not None:
        ax.barh(labels, [subset[label] for label in labels], height=.55, color=color)
    for i, (label, value) in enumerate(items):
        text = str(value) if subset is None else f"{subset[label]} / {value}"
        ax.annotate(text, (value, i), xytext=(6, 0), textcoords="offset points", va="center", fontsize=11)
    ax.set_xlim(0, max(values)*1.04)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.tick_params(axis="y", length=0, labelsize=11)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.savefig(OUT / filename)
    plt.close(fig)

tags, linked, districts = Counter(), Counter(), Counter()
aliases = {"AI Agent":"Agent", "AI Infra":"AI 基础设施", "AI4Science":"AI for Science"}
located = 0
for company in companies:
    directions = {aliases.get(tag, tag) for tag in company["tags"] if tag != "外企"}
    tags.update(directions)
    if company["recruitUrl"]:
        linked.update(directions)
    regions = {place["district"] for place in company["locations"] if place["district"]}
    districts.update(regions)
    located += bool(regions)

def ranked(counts):
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))

entries = sum(bool(row["recruitUrl"]) for row in companies)
chart("beijing-company-overview.png", "北京 AI 公司技术方向 TOP 10",
      f"{total} 家公司与团队  ·  有招聘入口 / 该方向总数（家）", ranked(tags)[:10], linked)
chart("beijing-directory-districts.png", "北京 AI 公司公开地址分布",
      f"{located} 家有区域信息  ·  跨区分别计数（家）", ranked(districts))
stages = ["种子 / 天使轮", "Pre-A", *[f"{letter} 轮" for letter in "ABCDEF"], "Pre-IPO"]
startup_scope = f"{stats['total']} 家已披露轮次的未上市创业公司"
chart("stage-overview-2026.png", "北京创业公司融资阶段", startup_scope,
      [(s, stats["stage"].get(s, 0)) for s in stages], color="#426fc0")
chart("direction-tags.png", "北京创业公司技术方向 TOP 10", startup_scope,
      [(aliases.get(k, k), v) for k, v in ranked(stats["tags"])[:10]])
print(f"{total} directory records, {entries} recruitment entries, {located} with district information")
