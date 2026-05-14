#!/usr/bin/env python3
"""Canvas K线图渲染 - 初始缩放显示最近60根K线，支持缩放平移"""
from datetime import datetime
import json


def gen_kline_html(df, ind, title, stocks_list):
    ds = df["date"].tolist()
    op = df["open"].tolist()
    hi = df["high"].tolist()
    lo = df["low"].tolist()
    cl = df["close"].tolist()
    lt = df.iloc[-1]
    n = len(ds)

    sn = "、".join([s["name"] for s in stocks_list])

    data = {
        "ds": ds, "op": op, "hi": hi, "lo": lo, "cl": cl,
        "sa_": ind["sa_"], "sb_": ind["sb_"],
        "tenkan": ind["tenkan"], "kijun": ind["kijun"],
        "boll": ind["boll"], "ub": ind["ub"], "lb": ind["lb"],
        "ma300": ind["ma300"], "ub1": ind["ub1"], "lb1": ind["lb1"],
        "ub1a": ind["ub1a"], "lb1a": ind["lb1a"],
        "ema5": ind["ema5"], "ma50": ind["ma50"],
        "ma100": ind["ma100"], "ub2": ind["ub2"], "lb2": ind["lb2"],
    }
    data_json = json.dumps(data)
    lv = int(lt["index_value"])
    cr = round(lt["cumulative_return"], 2)
    last_date = ds[-1]
    last_close = round(cl[-1], 1)
    last_change = round(cl[-1] - op[-1], 1)
    last_change_pct = round((cl[-1] - op[-1]) / op[-1] * 100, 2)
    is_up = cl[-1] >= op[-1]

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#050518;color:#ddd;font-family:Arial,sans-serif;padding:5px;overflow:hidden;touch-action:none}}
h1{{text-align:center;color:#00d4ff;font-size:16px;margin:6px 0}}
.cwrap{{background:#050518;border-radius:0;padding:0;width:100%}}
canvas{{display:block;width:100%;height:auto;touch-action:none}}
.leg{{text-align:center;margin:4px 0;font-size:10px;line-height:1.5}}
.leg span{{display:inline-block;padding:0 3px;margin:0 1px;border-radius:2px;white-space:nowrap}}
.info{{text-align:center;margin:6px 0;font-size:13px;color:#aaa;line-height:1.6}}
.info b{{color:#00d4ff;font-size:15px}}
@media(min-width:768px){{
  body{{padding:15px 30px}}
  h1{{font-size:24px}}
}}
</style>
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
<div class="cwrap">
<canvas id="kc"></canvas>
</div>
<script>
(function(){{
var D = {data_json};
var n = D.ds.length;

var c = document.getElementById("kc");
var ctx = c.getContext("2d");

var W, H;
var pd=25, pd_b=42, scale=1, offset=0, isInit=true;
var INITIAL_VIS = 60; // 初始显示最近60根K线

function resize(){{
  var r = c.parentElement.getBoundingClientRect();
  W = r.width;
  H = Math.max(250, Math.min(W * 0.55, window.innerHeight * 0.7));
  c.width = W * devicePixelRatio;
  c.height = H * devicePixelRatio;
  c.style.width = W + "px";
  c.style.height = H + "px";
  ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
  // 仅在首次加载时设置初始缩放
  if(isInit){{
    scale = n / INITIAL_VIS;
    offset = n - INITIAL_VIS;
    isInit = false;
  }}
  draw();
}}

function clamp(v,lo,hi){{return v<lo?lo:v>hi?hi:v}}

function draw(){{
  ctx.clearRect(0,0,W,H);
  if(n<2) return;

  var pw = W - pd - pd;
  var ph = H - pd - pd_b;
  var visN = Math.max(10, Math.floor(n / scale));
  var i0 = Math.floor(offset);
  if(i0 < 0) i0 = 0;
  if(i0 > n - visN) i0 = n - visN;
  var i1 = Math.min(i0 + visN, n);

  var mn = 1e9, mx = -1e9;
  for(var i=i0;i<i1;i++){{
    if(D.lo[i] < mn) mn = D.lo[i];
    if(D.hi[i] > mx) mx = D.hi[i];
  }}
  var rg = mx - mn || 1;

  function yp(v){{ return pd + ph - (v-mn)/rg*ph }}
  function xp(i){{ return pd + (i-i0)/(i1-i0)*pw }}

  // 网格
  ctx.strokeStyle = "#222";
  ctx.lineWidth = 0.5;
  for(var g=0;g<5;g++){{
    var yy = pd + g*ph/4;
    ctx.beginPath(); ctx.moveTo(pd,yy); ctx.lineTo(pd+pw,yy); ctx.stroke();
    ctx.fillStyle = "#666";
    ctx.font = "8px Arial";
    ctx.textAlign = "end";
    ctx.fillText(Math.round(mn + (1-g/4)*rg), pd-2, yy+3);
  }}

  function poly(arr, color, w, dash){{
    ctx.strokeStyle = color;
    ctx.lineWidth = w;
    ctx.setLineDash(dash ? [4,3] : []);
    ctx.beginPath();
    var started = false;
    for(var i=i0;i<i1;i++){{
      if(arr[i]==null){{ started=false; continue; }}
      var xx = xp(i), yy = yp(arr[i]);
      if(!started){{ ctx.moveTo(xx,yy); started=true; }}
      else ctx.lineTo(xx,yy);
    }}
    ctx.stroke();
    ctx.setLineDash([]);
  }}

  function fillCloud(d1, d2, color){{
    ctx.fillStyle = color;
    ctx.beginPath();
    for(var i=i0;i<i1;i++){{
      if(d1[i]==null||d2[i]==null) continue;
      ctx.lineTo(xp(i), yp(d1[i]));
    }}
    for(var i=i1-1;i>=i0;i--){{
      if(d1[i]==null||d2[i]==null) continue;
      ctx.lineTo(xp(i), yp(d2[i]));
    }}
    ctx.closePath();
    ctx.fill();
  }}

  // 云层
  for(var i=i0;i<i1;i++){{
    var j=i;
    while(j<i1 && D.sa_[j]!=null && D.sb_[j]!=null) j++;
    if(j>i){{
      var bullish = D.sa_[i] >= D.sb_[i];
      fillCloud(D.sa_, D.sb_, bullish
        ? "rgba(255,107,53,0.2)" : "rgba(42,111,156,0.2)");
    }}
    i=j;
  }}

  poly(D.sa_, "#ff6b35", 1.5);
  poly(D.sb_, "#2a6f9c", 1.5);
  poly(D.ub, "#aa843e", 0.5, true);
  poly(D.lb, "#aa843e", 0.5, true);
  poly(D.boll, "#aa843e", 1);
  poly(D.ma300, "#ffd700", 2);
  poly(D.ub1, "#ffd700", 0.5, true);
  poly(D.lb1, "#ffd700", 0.5, true);
  // ±1SD300 已移除，保留 ±2SD
  poly(D.ub2, "#888", 0.5, true);
  poly(D.lb2, "#888", 0.5, true);
  poly(D.ema5, "#fff", 1.5);
  poly(D.ma50, "#0f0", 1.5);
  poly(D.ma100, "#f44", 2);

  // K线
  var cw2 = Math.max(1, Math.min(10, pw/(i1-i0)-2));
  var hw2 = cw2/2;
  for(var i=i0;i<i1;i++){{
    var x = xp(i);
    var col = D.op[i] < D.cl[i] ? "#ff4444" : "#00c853";
    ctx.strokeStyle = col;
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(x,yp(D.hi[i])); ctx.lineTo(x,yp(D.lo[i])); ctx.stroke();
    ctx.fillStyle = col;
    ctx.fillRect(x-hw2, Math.min(yp(D.op[i]),yp(D.cl[i])), cw2, Math.abs(yp(D.cl[i])-yp(D.op[i]))+1);
  }}

  // 信号
  ctx.font = "14px Arial";
  ctx.textAlign = "center";
  for(var i=Math.max(1,i0);i<i1;i++){{
    if(D.sa_[i]==null||D.sb_[i]==null||D.sa_[i-1]==null||D.sb_[i-1]==null) continue;
    if(D.sa_[i-1]<=D.sb_[i-1]&&D.sa_[i]>D.sb_[i]){{
      ctx.fillStyle = "#ff6b35";
      ctx.fillText("▲", xp(i), yp(D.hi[i])-2);
    }}
    if(D.sa_[i-1]>=D.sb_[i-1]&&D.sa_[i]<D.sb_[i]){{
      ctx.fillStyle = "#2a6f9c";
      ctx.fillText("▼", xp(i), yp(D.lo[i])+12);
    }}
  }}

  // 时间轴 — 两行：上 MMDD，下年（只在首尾和新年份）
  ctx.fillStyle = "#999";
  ctx.textAlign = "center";
  var visDays = i1 - i0;
  var labelW = 40;
  var labelStep = Math.max(1, Math.floor(labelW * visDays / pw));
  var lastYearShown = "";
  for(var i=i0;i<i1;i+=labelStep){{
    var dateStr = D.ds[i];
    var parts = dateStr.split("-");
    var mmdd = parts[1] + parts[2];
    var yyyy = parts[0];
    var xx = xp(i);
    // 上排：MMDD
    ctx.font = "8px Arial";
    ctx.fillText(mmdd, xx, pd+ph+12);
    // 下排：年份（只在变化时显示）
    if(yyyy !== lastYearShown){{
      ctx.fillText(yyyy, xx, pd+ph+24);
      lastYearShown = yyyy;
    }}
  }}

  ctx.strokeStyle = "#555";
  ctx.lineWidth = 1;
  ctx.setLineDash([]);
  ctx.strokeRect(pd, pd, pw, ph);
}}

// 触摸手势
var isDragging = false;
var dragStartX = 0, dragStartOff = 0;
var lastDist = 0;

c.addEventListener("touchstart", function(e){{
  e.preventDefault();
  var t = e.touches;
  if(t.length==1){{
    isDragging = true; dragStartX = t[0].clientX; dragStartOff = offset;
  }} else if(t.length==2){{
    isDragging = false;
    lastDist = Math.hypot(t[0].clientX-t[1].clientX, t[0].clientY-t[1].clientY);
  }}
}}, {{passive:false}});

c.addEventListener("touchmove", function(e){{
  e.preventDefault();
  var t = e.touches;
  if(t.length==1 && isDragging){{
    var dx = (t[0].clientX - dragStartX) / W;
    offset = dragStartOff - dx * n / scale;
    draw();
  }} else if(t.length==2){{
    var dist = Math.hypot(t[0].clientX-t[1].clientX, t[0].clientY-t[1].clientY);
    var s = dist / Math.max(1, lastDist);
    var cx = (t[0].clientX+t[1].clientX)/2;
    var cxRatio = cx / W;
    var oldScale = scale;
    scale = clamp(scale * s, 1, 50);
    s = scale / oldScale;
    var centerIdx = offset + cxRatio * n / oldScale;
    offset = centerIdx - cxRatio * n / scale;
    if(offset < 0) offset = 0;
    if(offset > n - n/scale) offset = n - n/scale;
    lastDist = dist;
    draw();
  }}
}}, {{passive:false}});

c.addEventListener("touchend", function(e){{ isDragging=false; }});

c.addEventListener("wheel", function(e){{
  e.preventDefault();
  var r = c.getBoundingClientRect();
  var cx = (e.clientX - r.left) / W;
  var oldScale = scale;
  scale = clamp(scale * (1 - e.deltaY*0.001), 1, 50);
  var s = scale / oldScale;
  var centerIdx = offset + cx * n / oldScale;
  offset = centerIdx - cx * n / scale;
  if(offset < 0) offset = 0;
  if(offset > n - n/scale) offset = n - n/scale;
  draw();
}}, {{passive:false}});

c.addEventListener("mousedown", function(e){{
  isDragging = true; dragStartX = e.clientX; dragStartOff = offset;
}});
window.addEventListener("mousemove", function(e){{
  if(!isDragging) return;
  var dx = (e.clientX - dragStartX) / W;
  offset = dragStartOff - dx * n / scale;
  if(offset < 0) offset = 0;
  if(offset > n - n/scale) offset = n - n/scale;
  draw();
}});
window.addEventListener("mouseup", function(){{ isDragging=false; }});

window.addEventListener("resize", resize);
resize();

}})();
</script>
<div class="info">📅 {last_date} <b>{last_close}</b> {'🔴涨' if is_up else '🟢跌'} {last_change:+.1f}({last_change_pct:+.2f}%) | 指数 {lv}({cr}%) | {sn}</div>
</body>
</html>'''
    return html
