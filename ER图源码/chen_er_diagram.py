# -*- coding: utf-8 -*-
"""校园医务室数据库 E-R 图（陈氏记法）渲染脚本。

记法说明：
    矩形  = 实体          椭圆 = 属性（主键加下划线）
    菱形  = 联系          连线上的 1 / N = 联系基数
    双线矩形 / 双线菱形 = 弱实体及其弱联系

用法：
    python chen_er_diagram.py                # 完整版：画出全部属性
    python chen_er_diagram.py --simple       # 简版：只画主键、候选键与外键
    python chen_er_diagram.py --dpi 300      # 指定分辨率

输出（与脚本同目录）：
    ER图_Chen记法.png / .svg          完整版
    ER图_Chen记法_简版.png / .svg     简版
"""

import argparse
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
from matplotlib.lines import Line2D                                # noqa: E402
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon    # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False

# ------------------------------------------------------------------ 配色
ENT_FC, ENT_EC = "#E8F1FB", "#2F6BB0"
REL_FC, REL_EC = "#FDF3D8", "#C08A2E"
ATTR_FC, ATTR_EC = "#F7F9FC", "#8A94A6"
CARD_COLOR = "#B03030"
LINE_COLOR = "#4A4A4A"
WEAK_COLOR = "#95A5A6"

# ------------------------------------------------------------------ 尺寸
ENT_W, ENT_H = 5.8, 2.0        # 实体矩形
REL_W, REL_H = 3.4, 1.8        # 联系菱形
ATTR_W, ATTR_H = 3.2, 1.15     # 属性椭圆
CANVAS = (0, 90, -2, 44)       # xmin, xmax, ymin, ymax

# ------------------------------------------------------------------ 实体
# pos: 矩形中心；attrs: (属性名, 键标记, 极角°, 极径)
# 键标记：PK 主键（下划线）、UK 候选键、FK 外键、"" 普通属性
ENTITIES = {
    "科室": dict(en="department", pos=(12, 31), attrs=[
        ("DE_no", "PK", 230, 5.5),
        ("DE_name", "UK", 310, 5.5),
    ]),
    "医生": dict(en="doctor", pos=(33, 31), attrs=[
        ("D_no", "PK", 60, 6.2),
        ("D_name", "UK", 90, 6.2),
        ("D_sex", "", 120, 6.2),
        ("D_age", "", 210, 6.2),
        ("D_Title", "", 240, 6.2),
        ("D_Department", "FK", 300, 6.2),
        ("D_password", "", 330, 6.2),
    ]),
    "排班": dict(en="schedule", pos=(56, 31), attrs=[
        ("id", "PK", 200, 5.8),
        ("DE_name", "FK", 235, 5.8),
        ("D_name", "FK", 270, 5.8),
        ("D_title", "", 305, 5.8),
        ("visit_date", "", 340, 5.8),
        ("remaining", "", 30, 5.8),
    ]),
    "患者": dict(en="patient", pos=(12, 12), attrs=[
        ("P_no", "PK", 60, 6.2),
        ("P_name", "", 90, 6.2),
        ("P_sex", "", 120, 6.2),
        ("P_age", "", 240, 6.2),
        ("P_phonenumber", "UK", 270, 6.2),
        ("P_password", "", 300, 6.2),
    ]),
    "挂号": dict(en="registration", pos=(33, 12), attrs=[
        ("id", "PK", 120, 6.8),
        ("patient_id", "FK", 150, 6.8),
        ("D_name", "FK", 200, 6.8),
        ("D_title", "", 230, 6.8),
        ("DE_name", "", 260, 6.8),
        ("visit_date", "", 290, 6.8),
        ("medical_record", "", 320, 6.8),
        ("price", "", 350, 6.8),
    ]),
    "处方": dict(en="prescription", pos=(56, 12), attrs=[
        ("id", "PK", 60, 5.5),
        ("registration_id", "FK", 100, 5.5),
        ("create_time", "", 140, 5.5),
    ]),
    "药品": dict(en="medicine", pos=(78, 22), attrs=[
        ("med_id", "PK", 45, 5.5),
        ("med_name", "UK", 90, 5.5),
        ("stock_quantity", "", 135, 5.5),
        ("unit_price", "", 180, 5.5),
    ]),
    "处方明细": dict(en="prescription_detail", pos=(78, 7), weak=True, attrs=[
        ("id", "PK", 205, 7.2),
        ("prescription_id", "FK", 235, 7.2),
        ("med_id", "FK", 265, 7.2),
        ("med_name", "", 295, 7.2),
        ("unit_price", "", 325, 7.2),
        ("quantity", "", 355, 7.2),
    ]),
}

# ------------------------------------------------------------------ 联系
# 规则：菱形放在两实体之间；1 标注在靠“一”端，N 标注在靠“多”端
RELATIONSHIPS = [
    dict(name="拥有", a="科室", b="医生", pos=(22.5, 31), weak=False),
    dict(name="出诊", a="医生", b="排班", pos=(44.5, 31), weak=False),
    dict(name="接诊", a="医生", b="挂号", pos=(33, 21.5), weak=False),
    dict(name="挂号", a="患者", b="挂号", pos=(22.5, 12), weak=False),
    dict(name="开具", a="挂号", b="处方", pos=(44.5, 12), weak=False),
    dict(name="包含", a="处方", b="处方明细", pos=(67, 9.5), weak=True),
    dict(name="引用", a="药品", b="处方明细", pos=(78, 14.5), weak=False),
]

# 科室 → 排班 的联系需要绕行，单独用折线绘制，避免穿过医生
DETOUR = dict(name="发布", a="科室", b="排班", y=39.0, diamond=(34, 39.0))


# ------------------------------------------------------------------ 工具函数
def rect_edge(cx, cy, w, h, tx, ty, pad=0.0):
    """求矩形中心指向 (tx,ty) 的射线与矩形边界的交点。"""
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (w / 2 + pad) / abs(dx) if dx else float("inf")
    sy = (h / 2 + pad) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def diamond(cx, cy, name, weak=False):
    pts = [(cx - REL_W / 2, cy), (cx, cy + REL_H / 2),
           (cx + REL_W / 2, cy), (cx, cy - REL_H / 2)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=REL_FC,
                         edgecolor=REL_EC, linewidth=1.8, zorder=4))
    if weak:                                   # 弱联系：里面再套一圈
        k = 0.78
        inner = [(cx - REL_W / 2 * k, cy), (cx, cy + REL_H / 2 * k),
                 (cx + REL_W / 2 * k, cy), (cx, cy - REL_H / 2 * k)]
        ax.add_patch(Polygon(inner, closed=True, facecolor="none",
                             edgecolor=REL_EC, linewidth=1.2, zorder=5))
    ax.text(cx, cy, name, ha="center", va="center", fontsize=12,
            fontweight="bold", color="#7A5310", zorder=6)


def connect(p1, p2, card1=None, card2=None):
    """画连线并在两端附近标注基数。"""
    ax.add_line(Line2D([p1[0], p2[0]], [p1[1], p2[1]],
                       color=LINE_COLOR, linewidth=1.6, zorder=1))
    for p, q, card in ((p1, p2, card1), (p2, p1, card2)):
        if not card:
            continue
        t = 0.30
        x = p[0] + (q[0] - p[0]) * t
        y = p[1] + (q[1] - p[1]) * t
        ax.text(x, y + 0.45, card, ha="center", va="center", fontsize=13,
                fontweight="bold", color=CARD_COLOR, zorder=7,
                bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                          edgecolor="none", alpha=0.85))


def polyline(points, card1=None, card2=None, diamond_at=None, name=None, weak=False):
    """折线路径的联系（用于需要绕行的“发布”）。"""
    ax.add_line(Line2D([p[0] for p in points], [p[1] for p in points],
                       color=LINE_COLOR, linewidth=1.6, zorder=1))
    if diamond_at:
        diamond(diamond_at[0], diamond_at[1], name, weak)
    if card1:
        ax.text(points[0][0] + 0.5, points[0][1] + 0.5, card1, fontsize=13,
                fontweight="bold", color=CARD_COLOR, ha="center", va="center",
                zorder=7, bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                                    edgecolor="none", alpha=0.85))
    if card2:
        ax.text(points[-1][0] - 0.5, points[-1][1] - 0.5, card2, fontsize=13,
                fontweight="bold", color=CARD_COLOR, ha="center", va="center",
                zorder=7, bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                                    edgecolor="none", alpha=0.85))


def draw_entity(key, info, simple=False, ellipses=None):
    cx, cy = info["pos"]
    # 属性椭圆（先画，后面实体框会压在上面）
    texts = []
    for name, marker, ang, rad in info["attrs"]:
        if simple and marker not in ("PK", "UK", "FK"):
            continue
        ax_x = cx + rad * math.cos(math.radians(ang))
        ax_y = cy + rad * math.sin(math.radians(ang))
        ex, ey = rect_edge(cx, cy, ENT_W, ENT_H, ax_x, ax_y, pad=0.06)
        ax.add_line(Line2D([ex, ax_x], [ey, ax_y], color=LINE_COLOR,
                           linewidth=1.1, zorder=1))
        ell = Ellipse((ax_x, ax_y), ATTR_W, ATTR_H, facecolor=ATTR_FC,
                      edgecolor=ATTR_EC, linewidth=1.3, zorder=3)
        ax.add_patch(ell)
        t = ax.text(ax_x, ax_y, name, ha="center", va="center", fontsize=10.5,
                    color="#243044", zorder=5)
        if ellipses is not None:
            ellipses.append((t, ell))
        if marker == "PK":
            texts.append((t, ax_x, ax_y))
    # 实体矩形
    box = FancyBboxPatch((cx - ENT_W / 2, cy - ENT_H / 2), ENT_W, ENT_H,
                         boxstyle="round,pad=0.02,rounding_size=0.25",
                         facecolor=ENT_FC, edgecolor=ENT_EC, linewidth=2.2, zorder=4)
    ax.add_patch(box)
    if info.get("weak"):                       # 弱实体：双线矩形
        k = 0.16
        ax.add_patch(FancyBboxPatch((cx - ENT_W / 2 + k, cy - ENT_H / 2 + k),
                                    ENT_W - 2 * k, ENT_H - 2 * k,
                                    boxstyle="round,pad=0.02,rounding_size=0.2",
                                    facecolor="none", edgecolor=ENT_EC,
                                    linewidth=1.2, zorder=5))
    ax.text(cx, cy + 0.22, key, ha="center", va="center", fontsize=14,
            fontweight="bold", color="#12305A", zorder=6)
    ax.text(cx, cy - 0.45, info["en"], ha="center", va="center", fontsize=9.5,
            color="#5B6B7F", zorder=6)
    return texts


# ------------------------------------------------------------------ 主流程
def build(simple=False, dpi=200):
    global ax, fig
    fig, ax = plt.subplots(figsize=(30, 15))
    ax.set_xlim(CANVAS[0], CANVAS[1])
    ax.set_ylim(CANVAS[2], CANVAS[3])
    ax.set_aspect("equal")
    ax.axis("off")

    # 1) 联系（含连线与基数）先画，实体框与菱形后画压在上面
    for rel in RELATIONSHIPS:
        a, b = ENTITIES[rel["a"]]["pos"], ENTITIES[rel["b"]]["pos"]
        rx, ry = rel["pos"]
        p1 = rect_edge(a[0], a[1], ENT_W, ENT_H, rx, ry, pad=0.02)
        p2 = rect_edge(b[0], b[1], ENT_W, ENT_H, rx, ry, pad=0.02)
        connect(p1, p2, card1="1", card2="N")
        diamond(rx, ry, rel["name"], rel["weak"])

    # 2) 需要绕行的“发布”联系
    a = ENTITIES[DETOUR["a"]]["pos"]
    b = ENTITIES[DETOUR["b"]]["pos"]
    y = DETOUR["y"]
    dx, dy = DETOUR["diamond"]
    polyline([(a[0], a[1] + ENT_H / 2), (a[0], y), (dx - REL_W / 2, y)],
             card1="1", diamond_at=None)
    ax.add_line(Line2D([dx + REL_W / 2, b[0]], [y, y], color=LINE_COLOR, linewidth=1.6, zorder=1))
    ax.add_line(Line2D([b[0], b[0]], [y, b[1] + ENT_H / 2], color=LINE_COLOR, linewidth=1.6, zorder=1))
    diamond(dx, dy, DETOUR["name"])
    ax.text(b[0] - 0.9, y - 0.7, "N", fontsize=13, fontweight="bold",
            color=CARD_COLOR, ha="center", va="center", zorder=7,
            bbox=dict(boxstyle="round,pad=0.12", facecolor="white",
                      edgecolor="none", alpha=0.85))

    # 3) 实体与属性
    pk_texts = []
    ellipses = []
    for key, info in ENTITIES.items():
        pk_texts += draw_entity(key, info, simple=simple, ellipses=ellipses)

    # 4) 按文字实际宽度把椭圆调成刚好包住属性名，再画主键下划线
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    for t, ell in ellipses:
        bb = t.get_window_extent(renderer=renderer)
        (x0, _) = inv.transform((bb.x0, bb.y0))
        (x1, _) = inv.transform((bb.x1, bb.y0))
        ell.width = max((x1 - x0) + 1.15, ATTR_W * 0.8)
        ell.height = ATTR_H
    fig.canvas.draw()
    for t, _, _ in pk_texts:
        bb = t.get_window_extent(renderer=renderer)
        (x0, y0) = inv.transform((bb.x0, bb.y0))
        (x1, _) = inv.transform((bb.x1, bb.y0))
        ax.add_line(Line2D([x0 - 0.05, x1 + 0.05], [y0 + 0.06, y0 + 0.06],
                           color="#12305A", linewidth=1.4, zorder=6))

    # 5) 图例
    lx, ly = 14, 0.4
    ax.add_patch(FancyBboxPatch((lx, ly), 19.5, 3.4,
                                boxstyle="round,pad=0.15,rounding_size=0.2",
                                facecolor="#FBFCFE", edgecolor="#D5DEEA",
                                linewidth=1.2, zorder=3))
    ax.text(lx + 0.7, ly + 2.65, "图例", fontsize=11, fontweight="bold",
            color="#12305A", zorder=5)
    ax.add_patch(FancyBboxPatch((lx + 0.7, ly + 1.55), 1.5, 0.75,
                                boxstyle="round,pad=0.02,rounding_size=0.1",
                                facecolor=ENT_FC, edgecolor=ENT_EC,
                                linewidth=1.8, zorder=4))
    ax.text(lx + 2.6, ly + 1.92, "实体", fontsize=10, va="center", zorder=5)
    ax.add_patch(Polygon([(lx + 0.7, ly + 0.55), (lx + 1.45, ly + 1.15),
                          (lx + 2.2, ly + 0.55), (lx + 1.45, ly - 0.05)],
                         closed=True, facecolor=REL_FC, edgecolor=REL_EC,
                         linewidth=1.6, zorder=4))
    ax.text(lx + 2.6, ly + 0.55, "联系", fontsize=10, va="center", zorder=5)
    ax.add_patch(Ellipse((lx + 6.2, ly + 1.9), 1.7, 0.75, facecolor=ATTR_FC,
                         edgecolor=ATTR_EC, linewidth=1.3, zorder=4))
    ax.text(lx + 7.4, ly + 1.9, "属性", fontsize=10, va="center", zorder=5)
    ax.text(lx + 6.2, ly + 0.75, "1 : N", fontsize=11, fontweight="bold",
            color=CARD_COLOR, ha="center", zorder=5)
    ax.text(lx + 7.4, ly + 0.75, "联系基数", fontsize=10, va="center", zorder=5)
    ax.text(lx + 11.4, ly + 2.3, "主键：属性名下加下划线", fontsize=10, zorder=5)
    ax.text(lx + 11.4, ly + 1.5, "双线矩形/菱形：弱实体及其弱联系", fontsize=10, zorder=5)
    ax.text(lx + 11.4, ly + 0.7, "全部联系均为 1 : N", fontsize=10, zorder=5)

    # 6) 标题
    ax.text(45, 42.6, "校园医务室数据库 E-R 图", fontsize=21, fontweight="bold",
            color="#0F2F5C", ha="center", va="center")
    ax.text(45, 41.1, "陈氏（Chen）记法：矩形=实体，椭圆=属性，菱形=联系，"
                      "连线上的 1 / N 为基数" + ("（简版：仅主键、候选键与外键）" if simple else ""),
            fontsize=11, color="#5B6B7F", ha="center", va="center")

    out = Path(__file__).resolve().parent
    stem = "ER图_Chen记法_简版" if simple else "ER图_Chen记法"
    png = out / (stem + ".png")
    svg = out / (stem + ".svg")
    fig.savefig(png, dpi=dpi, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    fig.savefig(svg, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    plt.close(fig)
    print("已生成:", png)
    print("已生成:", svg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="渲染校园医务室数据库 E-R 图")
    parser.add_argument("--simple", action="store_true", help="只画主键、候选键与外键")
    parser.add_argument("--dpi", type=int, default=200, help="PNG 分辨率，默认 200")
    args = parser.parse_args()
    build(simple=args.simple, dpi=args.dpi)
    if not args.simple:
        build(simple=True, dpi=args.dpi)
