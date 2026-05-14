#!/usr/bin/env python3
"""
SVG K线图渲染 - 纯 SVG 静态图（无交互手势，但手机缩放由浏览器原生支持）
优点：颜色逻辑写在 Python 端，绝对正确，不存在 JS 绘制 bug
"""
from datetime import datetime


def _n(val):
    """None 转为 'null'"""
    return "null" if val is None else f"{val:.1f}"


def gen_kline_html(df, ind, title, stocks_list):
    ds = df["date"].tolist()
    op = df["open"].tolist()
    hi = df["high"].tolist()
    lo = df["low"].tolist()
    cl = df["close"].tolist()
    lt = df.iloc[-1]
    n = len(ds)

    sn = "、".join([s["name"] for s in stocks_list])
    lv = int(lt["index_value"])
    cr = round(lt["cumulative_return"], 2)
    last_date = ds[-1]
    last_close = round(cl[-1], 1)
    last_change = round(cl[-1] - op[-1], 1)
    last_change_pct = round((cl[-1] - op[-1]) / op[-1] * 100, 2)
    is_up = cl[-1] >= op[-1]

    # ========== 计算绘图空间 ==========
    pd_l = 50  # 左
    pd_r = 15  # 右
    pd_t = 15  # 上
    pd_b = 30  # 下（放日期）
    pw = 1000  # 绘图宽
    ph = 500   # 绘图高
    W = pw + pd_l + pd_r
    H = ph + pd_t + pd_b

    mn = min(lo)
    mx = max(hi)
    rg = mx - mn or 1

    def yp(v):
        return f"{pd_t + ph - (v - mn) / rg * ph:.1f}"

    def xp(i):
        return f"{pd_l + (i / (n - 1)) * pw:.1f}"

    # ========== CSS ==========
    css = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#050518;color:#ddd;font-family:Arial,sans-serif;padding:5px;text-align:center}}
h1{{color:#00d4ff;font-size:16px;margin:6px 0}}
svg{{display:block;margin:0 auto;width:100%;height:auto;max-width:1200px}}
.leg{{text-align:center;margin:4px 0;font-size:10px;line-height:1.5}}
.leg span{{display:inline-block;padding:0 3px;margin:0 1px;border-radius:2px;white-space:nowrap}}
.info{{text-align:center;margin:4px 0;font-size:12px;color:#aaa;line-height:1.6}}
@media(min-width:768px){{body{{padding:15px 30px}}h1{{font-size:24px}}}}
"""

    # ========== SVG 元素 ==========
    elems = []

    # 背景
    elems.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#050518" rx="4"/>')
    # 绘图区背景
    elems.append(f'<rect x="{pd_l}" y="{pd_t}" width="{pw}" height="{ph}" fill="#0a0a28" rx="2"/>')

    # 网格线 + Y轴刻度
    for g in range(5):
        yy = pd_t + g * ph / 4
        val = mn + (1 - g / 4) * rg
        elems.append(f'<line x1="{pd_l}" y1="{yy:.1f}" x2="{pd_l + pw}" y2="{yy:.1f}" stroke="#2a2a40" stroke-width="0.5"/>')
        elems.append(f'<text x="{pd_l - 6}" y="{yy + 4}" fill="#888" font-size="9" text-anchor="end">{val:.0f}</text>')

    # 日期轴
    label_step = max(1, n // 12)
    for i in range(0, n, label_step):
        elems.append(
            f'<text x="{xp(i)}" y="{pd_t + ph + 18}" fill="#888" font-size="9" text-anchor="middle">{ds[i]}</text>'
        )

    # ========== 多边形辅助 ==========
    def poly_pts(arr):
        pts = []
        for i in range(n):
            if arr[i] is not None:
                pts.append(f"{xp(i)},{yp(arr[i])}")
        return " ".join(pts)

    def poly(arr, color, w, dash=False):
        pts = poly_pts(arr)
        if not pts:
            return
        dash_attr = ' stroke-dasharray="4,3"' if dash else ""
        elems.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{w}"{dash_attr}/>')

    # 云层填充
    def cloud(d1, d2, color):
        pts = []
        for i in range(n):
            if d1[i] is not None and d2[i] is not None:
                pts.append(f"{xp(i)},{yp(d1[i])}")
        for i in range(n - 1, -1, -1):
            if d1[i] is not None and d2[i] is not None:
                pts.append(f"{xp(i)},{yp(d2[i])}")
        if pts:
            elems.append(f'<polygon points="{" ".join(pts)}" fill="{color}" fill-opacity="0.2"/>')

    # 逐段云层（按金叉/死叉分割）
    i = 0
    while i < n:
        if ind["sa_"][i] is None or ind["sb_"][i] is None:
            i += 1
            continue
        j = i + 1
        while j < n and ind["sa_"][j] is not None and ind["sb_"][j] is not None:
            j += 1
        bullish = ind["sa_"][i] >= ind["sb_"][i]
        cloud_color = "rgba(255,107,53,0.18)" if bullish else "rgba(42,111,156,0.18)"
        # 这个段内直接填充
        pts_a = []
        pts_b = []
        for k in range(i, j):
            if ind["sa_"][k] is not None and ind["sb_"][k] is not None:
                pts_a.append(f"{xp(k)},{yp(ind['sa_'][k])}")
                pts_b.insert(0, f"{xp(k)},{yp(ind['sb_'][k])}")
        all_pts = pts_a + pts_b
        if all_pts:
            elems.append(f'<polygon points="{" ".join(all_pts)}" fill="{cloud_color}"/>')
        i = j

    # 指标线
    poly(ind["sa_"], "#ff6b35", 1.5)
    poly(ind["sb_"], "#2a6f9c", 1.5)
    poly(ind["ub"], "#aa843e", 0.5, True)
    poly(ind["lb"], "#aa843e", 0.5, True)
    poly(ind["boll"], "#aa843e", 1)
    poly(ind["ma300"], "#ffd700", 2)
    poly(ind["ub1"], "#ffd700", 0.5, True)
    poly(ind["lb1"], "#ffd700", 0.5, True)
    poly(ind["ub2"], "#888", 0.5, True)
    poly(ind["lb2"], "#888", 0.5, True)
    poly(ind["ema5"], "#fff", 1.5)
    poly(ind["ma50"], "#0f0", 1.5)
    poly(ind["ma100"], "#f44", 2)

    # K线
    cw = max(2, pw // n - 2)
    if cw > 15:
        cw = 15
    hw = cw / 2
    for i in range(n):
        x = float(xp(i))
        y_o = float(yp(op[i]))
        y_c = float(yp(cl[i]))
        y_h = float(yp(hi[i]))
        y_l = float(yp(lo[i]))
        is_red = op[i] < cl[i]
        col = "#ff4444" if is_red else "#00c853"
        # 影线
        elems.append(f'<line x1="{x}" y1="{y_h}" x2="{x}" y2="{y_l}" stroke="{col}" stroke-width="1"/>')
        # 实体
        body_top = min(y_o, y_c)
        body_bot = max(y_o, y_c)
        body_h = body_bot - body_top
        if body_h < 1:
            body_h = 1  # 平盘也给一条线
        elems.append(f'<rect x="{x - hw}" y="{body_top}" width="{cw}" height="{body_h}" fill="{col}" rx="0.5"/>')

    # 信号标记
    for i in range(1, n):
        sa_ = ind["sa_"]
        sb_ = ind["sb_"]
        if sa_[i] is None or sb_[i] is None or sa_[i - 1] is None or sb_[i - 1] is None:
            continue
        x = float(xp(i))
        if sa_[i - 1] <= sb_[i - 1] and sa_[i] > sb_[i]:
            elems.append(f'<text x="{x}" y="{float(yp(hi[i])) - 4}" fill="#ff6b35" font-size="14" text-anchor="middle">▲</text>')
        if sa_[i - 1] >= sb_[i - 1] and sa_[i] < sb_[i]:
            elems.append(f'<text x="{x}" y="{float(yp(lo[i])) + 14}" fill="#2a6f9c" font-size="14" text-anchor="middle">▼</text>')

    # 外框
    elems.append(f'<rect x="{pd_l}" y="{pd_t}" width="{pw}" height="{ph}" fill="none" stroke="#555" stroke-width="1" rx="2"/>')

    svg_content = "\n".join(elems)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<h1>{title}</h1>
<div class="leg">
<span style="border-left:3px solid #ff6b35;color:#ff6b35">先行A</span>
<span style="border-left:3px solid #2a6f9c;color:#2a6f9c">先行B</span>
<span style="border-left:3px solid #aa843e;color:#aa843e">BOL20</span>
<span style="border-left:3px solid #ffd700;color:#ffd700">MA300</span>
<span style="border-left:3px solid #ffd700;color:#ffd700">±2SD300</span>
<span style="border-left:3px solid #fff;color:#fff">EMA5</span>
<span style="border-left:3px solid #0f0">MA50</span>
<span style="border-left:3px solid #f44;color:#f44">MA100</span>
<span style="color:#ff6b35">▲金叉</span>
<span style="color:#2a6f9c">▼死叉</span>
</div>
<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
{svg_content}
</svg>
<div class="info">📅 {last_date} 收盘 <b style="color:#00d4ff;font-size:14px">{last_close}</b> {'🔴涨' if is_up else '🟢跌'} {last_change:+.1f}({last_change_pct:+.2f}%) | 指数 {lv}({cr}%) | {sn}</div>
</body>
</html>"""
    return html
