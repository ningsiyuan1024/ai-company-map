"""Rebuild publication charts from the public statistics. Requires matplotlib.
Run from any directory: python scripts/build_publication_charts.py
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from build_startup_statistics import build

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'images'
stats = build()
stage = stats['stage']
total = stats['total']
assert total == len(stats['companies'])

# Use an installed Chinese font; keep generated assets portable for readers.
font_path = Path('C:/Windows/Fonts/msyh.ttc')
if font_path.exists():
    font_manager.fontManager.addfont(str(font_path))
available_fonts = {font.name for font in font_manager.fontManager.ttflist}
chinese_font = next((name for name in ['Microsoft YaHei', 'Noto Sans CJK SC', 'Source Han Sans SC'] if name in available_fonts), None)
if not chinese_font:
    raise RuntimeError('Install Microsoft YaHei or Noto Sans CJK SC to render Chinese chart labels.')
plt.rcParams.update({'font.family': chinese_font,
                     'axes.unicode_minus': False, 'savefig.facecolor': 'white'})
INK, MUTED, BLUE, TEAL, GRAY = '#182b42', '#536476', '#426fc0', '#278879', '#bdc7d2'
STAGES = [
    (name, stage.get(name, 0)) for name in ['种子 / 天使轮', 'Pre-A', *[f'{letter} 轮' for letter in 'ABCDEF'], 'Pre-IPO']
]
assert sum(value for _, value in STAGES) == total
TAG_NAMES = {'AI Infra': 'AI 基础设施'}
TAGS = [(TAG_NAMES.get(name, name), value) for name, value in stats['tags'].items() if name != '外企'][:10]
assert len(TAGS) == 10 and all(0 < count <= total for _, count in TAGS)
AS_OF = stats['asOf'].replace('-', '.')


def bars(ax, items, kind, small=False):
    labels, values = zip(*items)
    fontsize = 11 if small else 13
    colors = [GRAY if name == '阶段未明确' else INK if name == '上市' else BLUE if kind == 'stage' else TEAL for name in labels]
    ax.set_axisbelow(True)
    ax.barh(range(len(items)), values, height=.53, color=colors, zorder=3)
    ax.set_yticks(range(len(items)), labels, fontsize=fontsize, color=INK)
    ax.invert_yaxis()
    upper = ((max(values) // 10) + 1) * 10
    ticks = list(range(0, upper + 1, 10))
    ax.set_xlim(0, upper)
    ax.set_xticks(ticks, [str(t) for t in ticks], fontsize=9, color=MUTED)
    ax.xaxis.grid(True, color='#e8edf3', linewidth=.8)
    ax.tick_params(axis='both', length=0, pad=8)
    for spine in ax.spines.values(): spine.set_visible(False)
    for index, value in enumerate(values):
        ax.text(1.025, index, f'{value:>3}  /  {value / total:.1%}',
                transform=ax.get_yaxis_transform(), va='center', fontsize=fontsize - 1, color=INK)
    ax.text(1.025, 1.055, '数量 / 占比', transform=ax.transAxes, color=MUTED, fontsize=9)


def single(items, kind, title, subtitle, note, filename):
    fig = plt.figure(figsize=(12, 8), dpi=180)
    fig.text(.065, .93, title, fontsize=25, color=INK, weight='bold')
    fig.text(.065, .865, subtitle, fontsize=12, color=MUTED)
    ax = fig.add_axes([.205 if kind == 'stage' else .245, .20, .59 if kind == 'stage' else .55, .59])
    bars(ax, items, kind)
    fig.text(.065, .09, note, fontsize=10, color=MUTED)
    fig.text(.065, .045, f'北京 AI 公司地图  |  {AS_OF}  |  单位：家', fontsize=10, color=MUTED)
    fig.savefig(OUT / filename)
    plt.close(fig)


single(STAGES, 'stage', '北京 AI 创业公司融资阶段', f'已披露轮次样本：{total} 家未上市创业公司',
       'A+ 等并入对应轮次；后续融资未注明轮次时，沿用已有具名轮次。', 'stage-overview-2026.png')
single(TAGS, 'tag', '北京 AI 创业公司技术方向 TOP 10', f'已披露轮次样本：{total} 家未上市创业公司 · 按方向标签覆盖数量排序',
       f'同一公司可有多个标签；占比以 {total} 家为分母，各项占比不可相加。', 'direction-tags.png')

fig = plt.figure(figsize=(16, 9.5), dpi=180)
fig.text(.055, .935, '北京 AI 创业公司概览', fontsize=31, weight='bold', color=INK)
fig.text(.055, .875, f'已披露轮次样本：{total} 家未上市创业公司  ·  {AS_OF}', fontsize=13, color=MUTED)
fig.text(.10, .795, '融资阶段', fontsize=18, color=INK, weight='bold')
fig.text(.63, .795, '技术方向 TOP 10', fontsize=18, color=INK, weight='bold')
bars(fig.add_axes([.13, .205, .275, .54]), STAGES, 'stage', small=True)
bars(fig.add_axes([.65, .205, .245, .54]), TAGS, 'tag', small=True)
fig.text(.055, .105, '阶段：A+ 等并入对应轮次；后续融资未注明轮次时，沿用已有具名轮次。', fontsize=10, color=MUTED)
fig.text(.055, .065, f'方向：同一公司可有多个标签；两图占比均以 {total} 家为分母。单位：家。', fontsize=10, color=MUTED)
fig.text(.055, .025, '北京 AI 公司地图  ·  github.com/ningsiyuan1024/ai-company-map', fontsize=10, color=MUTED)
fig.savefig(OUT / 'beijing-company-overview.png')
plt.close(fig)
print(f'Built startup charts: {total} distinct companies; stage counts sum to {total}.')
