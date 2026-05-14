#!/usr/bin/env python3
"""SVG K线图渲染模块"""
from datetime import datetime


def gen_kline_html(df, ind, title, stocks_list):
    """生成包含所有指标线的SVG K线图HTML"""
    ds = df["date"].tolist()
    op = df["open"].tolist()
    hi = df["high"].tolist()
    lo = df["low"].tolist()
    cl = df["close"].tolist()
    lt = df.iloc[-1]
    n = len(ds)

    W = 1400
    H = 660
    pd_ = 80
    pw = W - 2 * pd_
    ph = H - 2 * pd_
    mv = min(lo)
    xv = max(hi)
    rg = xv - mv or 1

    def yp(v):
        return pd_ + ph - (v - mv) / rg * ph

    cw = max(2, min(12, pw // n - 1))
    hw = max(1, cw // 2)

    def xp(i):
        return pd_ + i * pw // (n - 1 if n > 1 else 1)

    def poly(d, color, w, dash=""):
        pts = []
        for i in range(n):
            if d[i] is None:
                continue
            pts.append("{},{}".format(xp(i), yp(d[i])))
        if not pts:
            return ""
        attr = 'stroke-dasharray="4,3"' if dash else ""
        return '<polyline points="{}" fill="none" stroke="{}" stroke-width="{}" {}/>'.format(
            " ".join(pts), color, w, attr
        )

    def fill_area(d1, d2, color):
        pts = []
        for i in range(n):
            if d1[i] is None or d2[i] is None:
                continue
            pts.append("{},{}".format(xp(i), yp(d1[i])))
        for i in range(n - 1, -1, -1):
            if d1[i] is None or d2[i] is None:
                continue
            pts.append("{},{}".format(xp(i), yp(d2[i])))
        if not pts:
            return ""
        return '<polygon points="{}" fill="{}" opacity="0.12"/>'.format(
            " ".join(pts), color
        )

    gs = ""
    sg = ""
    xt = ""

    # 网格
    for i in range(5):
        yy = pd_ + i * ph // 4
        v = mv + (1 - i / 4) * rg
        gs += '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="#222" stroke-width="0.5"/>'.format(
            pd_, yy, pd_ + pw, yy
        )
        gs += '<text x="{}" y="{}" fill="#666" font-size="11" text-anchor="end">{:.0f}</text>'.format(
            pd_ - 5, yy + 4, v
        )

    # 云层
    sg += fill_area(ind["sa_"], ind["sb_"], "#2f4f4f")
    sg += fill_area(ind["sb_"], ind["sa_"], "#8b4513")
    sg += poly(ind["sa_"], "#2f4f4f", 1)
    sg += poly(ind["sb_"], "#8b4513", 1)
    # BOLL20
    sg += poly(ind["ub"], "#aa843e", 0.5, "dash")
    sg += poly(ind["lb"], "#aa843e", 0.5, "dash")
    sg += poly(ind["boll"], "#aa843e", 1)
    # MA300
    sg += poly(ind["ma300"], "#ffd700", 2)
    sg += poly(ind["ub1"], "#ffd700", 0.5, "dash")
    sg += poly(ind["lb1"], "#ffd700", 0.5, "dash")
    sg += poly(ind["ub1a"], "#4682b4", 1, "dash")
    sg += poly(ind["lb1a"], "#4682b4", 1, "dash")
    # MA100布林
    sg += poly(ind["ub2"], "#888", 0.5, "dash")
    sg += poly(ind["lb2"], "#888", 0.5, "dash")
    # 均线
    sg += poly(ind["ema5"], "#fff", 1.5)
    sg += poly(ind["ma50"], "#0f0", 1.5)
    sg += poly(ind["ma100"], "#f44", 2)

    # K线
    for i in range(n):
        x = xp(i)
        y_op = yp(op[i])
        y_hi = yp(hi[i])
        y_lo = yp(lo[i])
        y_cl = yp(cl[i])
        c = "#ff4444" if op[i] < cl[i] else "#00c853"
        sg += '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1.5"/>'.format(
            x, y_hi, x, y_lo, c
        )
        sg += '<rect x="{}" y="{}" width="{}" height="{}" fill="{}" rx="1"/>'.format(
            x - hw, min(y_op, y_cl), cw, abs(y_cl - y_op) + 1, c
        )

    # 交叉信号
    sa_ = ind["sa_"]
    sb_ = ind["sb_"]
    for i in range(1, n):
        if sa_[i] is not None and sb_[i] is not None and sa_[i-1] is not None and sb_[i-1] is not None:
            if sa_[i-1] <= sb_[i-1] and sa_[i] > sb_[i]:
                sg += '<text x="{}" y="{}" fill="#f44" font-size="20" text-anchor="middle" dominant-baseline="bottom">▲</text>'.format(
                    xp(i), yp(hi[i]) - 2
                )
            if sa_[i-1] >= sb_[i-1] and sa_[i] < sb_[i]:
                sg += '<text x="{}" y="{}" fill="#0f0" font-size="20" text-anchor="middle" dominant-baseline="top">▼</text>'.format(
                    xp(i), yp(lo[i]) + 2
                )

    # 时间轴
    for i in range(n):
        if i % 60 == 0 or i == n - 1:
            xt += '<text x="{}" y="{}" fill="#666" font-size="10" text-anchor="middle">{}</text>'.format(
                xp(i), pd_ + ph + 20, ds[i]
            )

    box = '<rect x="{}" y="{}" width="{}" height="{}" fill="none" stroke="#444" stroke-width="1"/>'.format(
        pd_, pd_, pw, ph
    )
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" style="width:100%;height:auto;max-width:{}px">{}{}{}</svg>'.format(
        W, H, W, gs + box, sg, xt
    )

    # 统计数据
    stats = ""
    for l, v in [
        ("最新点位", str(lt["index_value"])),
        ("累计涨幅", str(lt["cumulative_return"]) + "%"),
        ("交易日", str(n)),
        ("起始日", ds[0]),
    ]:
        stats += '<div class="stat"><div class="v">{}</div><div class="l">{}</div></div>'.format(v, l)

    sn = "、".join([s["name"] for s in stocks_list])

    html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>''' + title + '''</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#050518;color:#ddd;font-family:Arial,sans-serif;padding:10px}
h1{text-align:center;color:#00d4ff;font-size:20px;margin:10px 0}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0 auto 12px;max-width:500px}
.stat{background:#0d0d28;padding:12px;border-radius:8px;text-align:center}
.stat .v{font-size:22px;color:#00d4ff;font-weight:bold}
.stat .l{font-size:11px;color:#888;margin-top:3px}
.cwrap{background:#0d0d28;border-radius:8px;padding:10px;overflow-x:auto}
.leg{text-align:center;margin:6px 0 10px;font-size:11px;line-height:1.7}
.leg span{display:inline-block;padding:0 6px;border-radius:2px;margin:0 3px}
.info{text-align:center;margin:8px 0;font-size:11px;color:#555;line-height:1.6}
@media(min-width:768px){
  body{padding:20px 40px}
  h1{font-size:28px}
  .stats{grid-template-columns:1fr 1fr 1fr 1fr;max-width:none}
  .stat .v{font-size:28px}
}
</style>
</head>
<body>
<h1>''' + title + '''</h1>
<div class="stats">''' + stats + '''</div>
<div class="leg">
<span style="border-left:3px solid #2f4f4f;color:#2f4f4f">先行A</span>
<span style="border-left:3px solid #8b4513;color:#8b4513">先行B</span>
<span style="border-left:3px solid #aa843e;color:#aa843e">BOL20</span>
<span style="border-left:3px solid #ffd700;color:#ffd700">MA300</span>
<span style="border-left:3px solid #4682b4;color:#4682b4">±1SD300</span>
<span style="border-left:3px solid #fff;color:#fff">EMA5</span>
<span style="border-left:3px solid #0f0">MA50</span>
<span style="border-left:3px solid #f44;color:#f44">MA100</span>
<span style="color:#ff4444">▲金叉</span>
<span style="color:#0f0">▼死叉</span>
</div>
<div class="cwrap">''' + svg + '''</div>
<div class="info">成分股（等权重）：''' + sn + ''' | Cloud+Ichimoku+Bollinger | ''' + datetime.now().strftime("%Y-%m-%d %H:%M") + '''</div>
</body>
</html>'''
    return html
