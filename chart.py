#!/usr/bin/env python3
"""Canvas K线图渲染 - 支持日线/周线切换"""
from datetime import datetime
import json


def gen_kline_html(df, ind, title, stocks_list, wdf=None, w_ind=None):
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
        "ema5": ind["ema5"], "ma50": ind["ma50"],
        "ma100": ind["ma100"], "ub2": ind["ub2"], "lb2": ind["lb2"],
        "dif": ind["dif"], "dea": ind["dea"], "macd": ind["macd"],
    }

    # 周线数据
    w_data = None
    if wdf is not None and w_ind is not None:
        w_data = {
            "ds": wdf["date"].tolist(),
            "op": wdf["open"].tolist(),
            "hi": wdf["high"].tolist(),
            "lo": wdf["low"].tolist(),
            "cl": wdf["close"].tolist(),
            "sa_": w_ind["sa_"], "sb_": w_ind["sb_"],
            "tenkan": w_ind["tenkan"], "kijun": w_ind["kijun"],
            "boll": w_ind["boll"], "ub": w_ind["ub"], "lb": w_ind["lb"],
            "ma300": w_ind["ma300"], "ub1": w_ind["ub1"], "lb1": w_ind["lb1"],
            "ema5": w_ind["ema5"], "ma50": w_ind["ma50"],
            "ma100": w_ind["ma100"], "ub2": w_ind["ub2"], "lb2": w_ind["lb2"],
            "dif": w_ind["dif"], "dea": w_ind["dea"], "macd": w_ind["macd"],
        }

    data_json = json.dumps(data)
    w_data_json = json.dumps(w_data) if w_data else "null"
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
.pb{{text-align:center;margin:3px 0;line-height:1}}
.pbtn{{display:inline-block;padding:2px 10px;margin:0 2px;font-size:11px;border:1px solid #555;border-radius:4px;color:#888;background:transparent;cursor:pointer}}
.pbtn.act{{border-color:#00d4ff;color:#00d4ff;background:rgba(0,212,255,0.1)}}
@media(min-width:768px){{
  body{{padding:15px 30px}}
  h1{{font-size:24px}}
}}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="pb">
<span class="pbtn act" id="pbtn_day" onclick="switchPeriod(false)">日线</span>
<span class="pbtn" id="pbtn_week" onclick="switchPeriod(true)">周线</span>
</div>
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
<span style="border-left:3px solid #fff;color:#fff">DIF</span>
<span style="border-left:3px solid #ffd700;color:#ffd700">DEA</span>
<span style="color:#f44">MACD+</span>
<span style="color:#00c853">MACD-</span>
</div>
<div class="cwrap">
<canvas id="kc"></canvas>
</div>
<script>
(function(){{
var D_DAY = {data_json};
var D_WEEK = {w_data_json};
var isWeek = false;
var D;

function getData(){{ return isWeek ? D_WEEK : D_DAY; }}

function switchPeriod(week){{
  isWeek = week;
  D = getData();
  // 切换后reset视角
  document.getElementById("pbtn_day").className = week ? "pbtn" : "pbtn act";
  document.getElementById("pbtn_week").className = week ? "pbtn act" : "pbtn";
  var n = D.ds.length;
  scale = n / 60;
  offset = n - 60;
  isInit = true; // 触发一次初始缩放
  resize();
}}
// 挂到全局以便 onclick 调用
window.switchPeriod = switchPeriod;

var c = document.getElementById("kc");
var ctx = c.getContext("2d");

var W, H;
var pd=25, pd_b=8, scale=1, offset=0, isInit=true;
var MAIN_RATIO = 0.7; // 主图占70%，MACD占30%
var INITIAL_VIS = 60;

function resize(){{
  D = getData();
  var n = D.ds.length;
  var r = c.parentElement.getBoundingClientRect();
  W = r.width;
  H = Math.max(350, Math.min(W * 0.7, window.innerHeight * 0.85));
  c.width = W * devicePixelRatio;
  c.height = H * devicePixelRatio;
  c.style.width = W + "px";
  c.style.height = H + "px";
  ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
  if(isInit){{
    scale = n / INITIAL_VIS;
    offset = n - INITIAL_VIS;
    isInit = false;
  }}
  draw();
}}

function clamp(v,lo,hi){{return v<lo?lo:v>hi?hi:v}}

function draw(){{
  D = getData();
  var n = D.ds.length;
  ctx.clearRect(0,0,W,H);
  if(n<2) return;

  var pw = W - pd - pd;
  var ph1 = (H - pd - pd_b) * MAIN_RATIO;  // 主图
  var ph2 = (H - pd - pd_b) * (1 - MAIN_RATIO) - 30; // MACD副图（中间30px分隔）
  var gapY = pd + ph1 + 15; // 分隔线位置
  var macdY0 = gapY + 15;   // MACD绘图区起始

  var visN = Math.max(10, Math.floor(n / scale));
  var i0 = Math.floor(offset);
  if(i0 < 0) i0 = 0;
  if(i0 > n - visN) i0 = n - visN;
  var i1 = Math.min(i0 + visN, n);

  function xp(i){{ return pd + (i-i0)/(i1-i0)*pw }}

  // ========== 主图 ==========
  var mn1 = 1e9, mx1 = -1e9;
  for(var i=i0;i<i1;i++){{
    if(D.lo[i] < mn1) mn1 = D.lo[i];
    if(D.hi[i] > mx1) mx1 = D.hi[i];
  }}
  var rg1 = mx1 - mn1 || 1;
  function yp1(v){{ return pd + ph1 - (v-mn1)/rg1*ph1 }}

  // 主图网格
  ctx.strokeStyle = "#222";
  ctx.lineWidth = 0.5;
  for(var g=0;g<5;g++){{
    var yy = pd + g*ph1/4;
    ctx.beginPath(); ctx.moveTo(pd,yy); ctx.lineTo(pd+pw,yy); ctx.stroke();
    ctx.fillStyle = "#666";
    ctx.font = "7px Arial";
    ctx.textAlign = "end";
    ctx.fillText(Math.round(mn1 + (1-g/4)*rg1), pd-2, yy+3);
  }}

  function poly1(arr, color, w, dash){{
    ctx.strokeStyle = color;
    ctx.lineWidth = w;
    ctx.setLineDash(dash ? [3,2] : []);
    ctx.beginPath();
    var started = false;
    for(var i=i0;i<i1;i++){{
      if(arr[i]==null){{ started=false; continue; }}
      var xx = xp(i), yy = yp1(arr[i]);
      if(!started){{ ctx.moveTo(xx,yy); started=true; }}
      else ctx.lineTo(xx,yy);
    }}
    ctx.stroke();
    ctx.setLineDash([]);
  }}

  function fillCloud1(d1, d2, color){{
    ctx.fillStyle = color;
    ctx.beginPath();
    for(var i=i0;i<i1;i++){{
      if(d1[i]==null||d2[i]==null) continue;
      ctx.lineTo(xp(i), yp1(d1[i]));
    }}
    for(var i=i1-1;i>=i0;i--){{
      if(d1[i]==null||d2[i]==null) continue;
      ctx.lineTo(xp(i), yp1(d2[i]));
    }}
    ctx.closePath();
    ctx.fill();
  }}

  // 主图框 clip — 防止指标跑出绘图区
  ctx.save();
  ctx.beginPath();
  ctx.rect(pd, pd, pw, ph1);
  ctx.clip();

  // 云层
  for(var i=i0;i<i1;i++){{
    var j=i;
    while(j<i1 && D.sa_[j]!=null && D.sb_[j]!=null) j++;
    if(j>i){{
      var bullish = D.sa_[i] >= D.sb_[i];
      fillCloud1(D.sa_, D.sb_, bullish ? "rgba(255,107,53,0.18)" : "rgba(42,111,156,0.18)");
    }}
    i=j;
  }}

  poly1(D.sa_, "#ff6b35", 1.2);
  poly1(D.sb_, "#2a6f9c", 1.2);
  poly1(D.ub, "#aa843e", 0.5, true);
  poly1(D.lb, "#aa843e", 0.5, true);
  poly1(D.boll, "#aa843e", 1);
  poly1(D.ma300, "#ffd700", 1.5);
  poly1(D.ub1, "#ffd700", 0.5, true);
  poly1(D.lb1, "#ffd700", 0.5, true);
  poly1(D.ub2, "#666", 0.5, true);
  poly1(D.lb2, "#666", 0.5, true);
  poly1(D.ema5, "#fff", 1.2);
  poly1(D.ma50, "#0f0", 1.2);
  poly1(D.ma100, "#f44", 1.5);

  // K线
  var cw2 = Math.max(1, Math.min(8, pw/(i1-i0)-1));
  var hw2 = cw2/2;
  for(var i=i0;i<i1;i++){{
    var x = xp(i);
    var col = D.op[i] < D.cl[i] ? "#ff4444" : "#00c853";
    ctx.strokeStyle = col;
    ctx.lineWidth = 0.8;
    ctx.beginPath(); ctx.moveTo(x,yp1(D.hi[i])); ctx.lineTo(x,yp1(D.lo[i])); ctx.stroke();
    ctx.fillStyle = col;
    ctx.fillRect(x-hw2, Math.min(yp1(D.op[i]),yp1(D.cl[i])), cw2, Math.max(1, Math.abs(yp1(D.cl[i])-yp1(D.op[i]))));
  }}

  // 信号
  ctx.font = "12px Arial";
  ctx.textAlign = "center";
  for(var i=Math.max(1,i0);i<i1;i++){{
    if(D.sa_[i]==null||D.sb_[i]==null||D.sa_[i-1]==null||D.sb_[i-1]==null) continue;
    if(D.sa_[i-1]<=D.sb_[i-1]&&D.sa_[i]>D.sb_[i])
      {{ctx.fillStyle="#ff6b35"; ctx.fillText("▲", xp(i), yp1(D.hi[i])-2);}}
    if(D.sa_[i-1]>=D.sb_[i-1]&&D.sa_[i]<D.sb_[i])
      {{ctx.fillStyle="#2a6f9c"; ctx.fillText("▼", xp(i), yp1(D.lo[i])+12);}}
  }}

  // 主图边框（在 clip 之后画）
  ctx.restore();
  ctx.strokeStyle = "#333";
  ctx.lineWidth = 1;
  ctx.setLineDash([]);
  ctx.strokeRect(pd, pd, pw, ph1);

  // ========== 分隔线 + MACD 标签 ==========
  ctx.strokeStyle = "#333";
  ctx.lineWidth = 0.5;
  ctx.beginPath(); ctx.moveTo(pd, gapY); ctx.lineTo(pd+pw, gapY); ctx.stroke();
  ctx.fillStyle = "#888";
  ctx.font = "9px Arial";
  ctx.textAlign = "left";
  ctx.fillText("MACD(12,26,9)", pd+4, gapY+11);

  // ========== MACD 副图 ==========
  // 找 dif/DEA/MACD 的范围 + 额外 padding
  var mn2 = 0, mx2 = 0;
  var hasMacd = false;
  for(var i=i0;i<i1;i++){{
    if(D.macd[i]==null) continue;
    hasMacd = true;
    if(D.macd[i] < mn2) mn2 = D.macd[i];
    if(D.macd[i] > mx2) mx2 = D.macd[i];
    if(D.dif[i] < mn2) mn2 = D.dif[i];
    if(D.dif[i] > mx2) mx2 = D.dif[i];
    if(D.dea[i] < mn2) mn2 = D.dea[i];
    if(D.dea[i] > mx2) mx2 = D.dea[i];
  }}
  if(!hasMacd) {{ mn2 = -10; mx2 = 10; }}
  var padding2 = Math.max(Math.abs(mx2 - mn2) * 0.15, Math.abs(mx2 - mn2) * 0.15 || 1);
  mn2 -= padding2; mx2 += padding2;
  var rg2 = mx2 - mn2 || 1;
  // y 值严格限制在副图框内
  function yp2(v){{ return Math.max(macdY0, Math.min(macdY0 + ph2, macdY0 + ph2 - (v-mn2)/rg2*ph2)); }}

  // 裁剪区 — 确保 MACD 内容不超出副图框
  ctx.save();
  ctx.beginPath();
  ctx.rect(pd, macdY0, pw, ph2);
  ctx.clip();

  // MACD网格
  ctx.strokeStyle = "#222";
  ctx.lineWidth = 0.5;
  ctx.beginPath(); ctx.moveTo(pd, yp2(0)); ctx.lineTo(pd+pw, yp2(0)); ctx.stroke();

  // MACD柱
  for(var i=i0;i<i1;i++){{
    if(D.macd[i]==null) continue;
    var x = xp(i);
    var y0 = yp2(0);
    var yv = yp2(D.macd[i]);
    var col = D.macd[i] >= 0 ? "#f44" : "#00c853";
    ctx.fillStyle = col;
    ctx.fillRect(x-hw2*0.6, Math.min(y0, yv), cw2*0.6, Math.max(0.5, Math.abs(yv-y0)));
  }}

  // MACD 线 — 单独用 poly2（使用 yp2）
  function poly2(arr, color, w, dash){{
    ctx.strokeStyle = color;
    ctx.lineWidth = w;
    ctx.setLineDash(dash ? [3,2] : []);
    ctx.beginPath();
    var started = false;
    for(var i=i0;i<i1;i++){{
      if(arr[i]==null){{ started=false; continue; }}
      var xx = xp(i), yy = yp2(arr[i]);
      if(!started){{ ctx.moveTo(xx,yy); started=true; }}
      else ctx.lineTo(xx,yy);
    }}
    ctx.stroke();
    ctx.setLineDash([]);
  }}
  poly2(D.dif, "#fff", 1);
  poly2(D.dea, "#ffd700", 1, true);

  // MACD 刻度
  ctx.fillStyle = "#666";
  ctx.font = "7px Arial";
  ctx.textAlign = "end";
  ctx.fillText(mx2.toFixed(1), pd-2, yp2(mx2)+3);
  ctx.fillText(mn2.toFixed(1), pd-2, yp2(mn2)+3);

  // MACD 边框（在 clip 之后画边框，确保线条清晰）
  ctx.restore();
  ctx.strokeStyle = "#333";
  ctx.lineWidth = 1;
  ctx.strokeRect(pd, macdY0, pw, ph2);

  // ========== 共享日期轴（放在MACD下方） ==========
  ctx.fillStyle = "#999";
  ctx.textAlign = "center";
  var visDays = i1 - i0;
  var labelW = 38;
  var labelStep = Math.max(1, Math.floor(labelW * visDays / pw));
  var lastYearShown = "";
  for(var i=i0;i<i1;i+=labelStep){{
    var dateStr = D.ds[i];
    var parts = dateStr.split("-");
    var mmdd = parts[1] + parts[2];
    var yyyy = parts[0];
    var xx = xp(i);
    ctx.font = "7px Arial";
    var dateY = macdY0 + ph2 + 12;
    ctx.fillText(mmdd, xx, dateY);
    if(yyyy !== lastYearShown){{
      ctx.fillText(yyyy, xx, dateY + 10);
      lastYearShown = yyyy;
    }}
  }}
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
