#!/usr/bin/env python3
"""Canvas K线图渲染 - 支持缩放平移"""
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

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#050518;color:#ddd;font-family:Arial,sans-serif;padding:10px;overflow:hidden;touch-action:none}}
h1{{text-align:center;color:#00d4ff;font-size:20px;margin:10px 0}}
.stats{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0 auto 12px;max-width:500px}}
.stat{{background:#0d0d28;padding:12px;border-radius:8px;text-align:center}}
.stat .v{{font-size:22px;color:#00d4ff;font-weight:bold}}
.stat .l{{font-size:11px;color:#888;margin-top:3px}}
.cwrap{{background:#0d0d28;border-radius:8px;padding:5px;width:100%;height:auto}}
canvas{{display:block;width:100%;height:auto;touch-action:none}}
.leg{{text-align:center;margin:6px 0;font-size:10px;line-height:1.6}}
.leg span{{display:inline-block;padding:0 4px;margin:0 2px;border-radius:2px}}
.info{{text-align:center;margin:6px 0;font-size:10px;color:#555;line-height:1.5}}
@media(min-width:768px){{
  body{{padding:20px 40px}}
  h1{{font-size:28px}}
  .stats{{grid-template-columns:1fr 1fr 1fr 1fr;max-width:none}}
  .stat .v{{font-size:28px}}
}}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="stats">
<div class="stat"><div class="v">{lv}</div><div class="l">最新点位</div></div>
<div class="stat"><div class="v">{cr}%</div><div class="l">累计涨幅</div></div>
<div class="stat"><div class="v">{n}</div><div class="l">交易日</div></div>
<div class="stat"><div class="v">{ds[0]}</div><div class="l">起始日</div></div>
</div>
<div class="leg">
<span style="border-left:3px solid #ff6b35;color:#ff6b35">先行A</span>
<span style="border-left:3px solid #2a6f9c;color:#2a6f9c">先行B</span>
<span style="border-left:3px solid #aa843e;color:#aa843e">BOL20</span>
<span style="border-left:3px solid #ffd700;color:#ffd700">MA300</span>
<span style="border-left:3px solid #4682b4;color:#4682b4">±1SD300</span>
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
var pd=60, scale=1, offset=0;

function resize(){{
  var r = c.parentElement.getBoundingClientRect();
  W = r.width;
  // 竖屏取75%高度，横屏取85%
  H = window.innerWidth > window.innerHeight
    ? window.innerHeight * 0.85
    : window.innerHeight * 0.75;
  c.width = W * devicePixelRatio;
  c.height = H * devicePixelRatio;
  c.style.width = W + "px";
  c.style.height = H + "px";
  ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
  draw();
}}

function clamp(v,lo,hi){{return v<lo?lo:v>hi?hi:v}}

function draw(){{
  ctx.clearRect(0,0,W,H);
  if(n<2) return;

  var pw = W - 2*pd;
  var ph = H - 2*pd;
  var visN = Math.max(10, Math.floor(n / scale));
  var i0 = Math.floor(clamp(offset, 0, n - visN));
  var i1 = Math.min(i0 + visN, n);

  // 价格范围
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
    ctx.font = "10px Arial";
    ctx.textAlign = "end";
    ctx.fillText(Math.round(mn + (1-g/4)*rg), pd-5, yy+4);
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
    var started = false;
    for(var i=i0;i<i1;i++){{
      if(d1[i]==null||d2[i]==null){{ started=false; continue; }}
      var xx = xp(i), yy = yp(d1[i]);
      if(!started){{ ctx.moveTo(xx,yy); started=true; }}
      else ctx.lineTo(xx,yy);
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
        ? "rgba(255,107,53,0.22)"
        : "rgba(42,111,156,0.22)", i, j);
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
  poly(D.ub1a, "#4682b4", 1, true);
  poly(D.lb1a, "#4682b4", 1, true);
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
  ctx.font = "16px Arial";
  ctx.textAlign = "center";
  for(var i=Math.max(1,i0);i<i1;i++){{
    if(D.sa_[i]==null||D.sb_[i]==null||D.sa_[i-1]==null||D.sb_[i-1]==null) continue;
    if(D.sa_[i-1]<=D.sb_[i-1]&&D.sa_[i]>D.sb_[i]){{
      ctx.fillStyle = "#ff6b35";
      ctx.fillText("▲", xp(i), yp(D.hi[i])-2);
    }}
    if(D.sa_[i-1]>=D.sb_[i-1]&&D.sa_[i]<D.sb_[i]){{
      ctx.fillStyle = "#2a6f9c";
      ctx.fillText("▼", xp(i), yp(D.lo[i])+14);
    }}
  }}

  // 时间轴 - 动态间隔防重叠
  ctx.fillStyle = "#888";
  ctx.font = "10px Arial";
  ctx.textAlign = "center";
  var visDays = i1 - i0;
  // 屏幕宽度上一行日期大概占35px，算间隔
  var labelW = 60;
  var labelStep = Math.max(1, Math.floor(labelW * visDays / pw));
  for(var i=i0;i<i1;i+=labelStep){{
    ctx.fillText(D.ds[i], xp(i), pd+ph+15);
  }}

  // 边框
  ctx.strokeStyle = "#555";
  ctx.lineWidth = 1;
  ctx.setLineDash([]);
  ctx.strokeRect(pd, pd, pw, ph);
}}

// 触摸
var isDragging = false;
var dragStartX = 0, dragStartOff = 0;

c.addEventListener("touchstart", function(e){{
  e.preventDefault();
  var t = e.touches;
  if(t.length==1){{
    isDragging = true;
    dragStartX = t[0].clientX;
    dragStartOff = offset;
  }} else if(t.length==2){{
    isDragging = false;
    lastDist = Math.hypot(t[0].clientX-t[1].clientX, t[0].clientY-t[1].clientY);
    lastCX = (t[0].clientX+t[1].clientX)/2;
  }}
}}, {{passive:false}});

c.addEventListener("touchmove", function(e){{
  e.preventDefault();
  var t = e.touches;
  if(t.length==1 && isDragging){{
    var dx = (t[0].clientX - dragStartX) / W;
    offset = dragStartOff - dx * n / scale;
    offset = clamp(offset, 0, n - n/scale);
    draw();
  }} else if(t.length==2){{
    var dist = Math.hypot(t[0].clientX-t[1].clientX, t[0].clientY-t[1].clientY);
    var s = dist / (lastDist||1);
    var cx = (t[0].clientX+t[1].clientX)/2;
    var cxRatio = cx / W;
    var oldScale = scale;
    scale = clamp(scale * s, 1, 50);
    s = scale / oldScale;
    var centerIdx = offset + cxRatio * n / oldScale;
    offset = centerIdx - cxRatio * n / scale;
    offset = clamp(offset, 0, n - n/scale);
    lastDist = dist;
    draw();
  }}
}}, {{passive:false}});

c.addEventListener("touchend", function(e){{ isDragging=false; }});

// 鼠标滚轮
c.addEventListener("wheel", function(e){{
  e.preventDefault();
  var r = c.getBoundingClientRect();
  var cx = (e.clientX - r.left) / W;
  var oldScale = scale;
  scale = clamp(scale * (1 - e.deltaY*0.001), 1, 50);
  var s = scale / oldScale;
  var centerIdx = offset + cx * n / oldScale;
  offset = centerIdx - cx * n / scale;
  offset = clamp(offset, 0, n - n/scale);
  draw();
}}, {{passive:false}});

// 鼠标拖拽
c.addEventListener("mousedown", function(e){{
  isDragging = true;
  dragStartX = e.clientX;
  dragStartOff = offset;
}});
window.addEventListener("mousemove", function(e){{
  if(!isDragging) return;
  var dx = (e.clientX - dragStartX) / W;
  offset = dragStartOff - dx * n / scale;
  offset = clamp(offset, 0, n - n/scale);
  draw();
}});
window.addEventListener("mouseup", function(){{ isDragging=false; }});

window.addEventListener("resize", resize);
resize();

}})();
</script>
<div class="info">成分股（等权重）：{sn} | Cloud+Ichimoku+Bollinger | {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
</body>
</html>'''
    return html
