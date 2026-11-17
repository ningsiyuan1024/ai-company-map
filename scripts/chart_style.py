"""Shared portrait format for the Beijing directory charts."""
import matplotlib.pyplot as plt
from matplotlib import font_manager

PAPER = "#fbf8f1"
INK = "#373c36"
MUTED = "#675f54"
PALETTE = [
    "#875442", "#96aaa0", "#d09c75", "#7b97a3", "#ad8895",
    "#b9a16f", "#82a5a4", "#b99a8f", "#a3ab80", "#ac9cb2",
    "#d5ad9b", "#9ba7b1", "#adb5a3",
]

def page(title):
    figure = plt.figure(figsize=(6, 7.5), dpi=200, facecolor=PAPER)
    fonts = {font.name for font in font_manager.fontManager.ttflist}
    family = next((name for name in ("SimSun", "Noto Serif CJK SC", "Source Han Serif SC") if name in fonts), plt.rcParams["font.family"])
    figure.text(.07, .925, title, fontfamily=family, fontsize=23, color=INK)
    return figure
