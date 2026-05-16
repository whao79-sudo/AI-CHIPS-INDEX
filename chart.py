#!/usr/bin/env python3
"""Canvas K线图渲染 - 支持日线/两日/周线切换 + 成交量 + 小波成交量对比"""
from datetime import datetime
import json


def gen_kline_html(df, ind, title, stocks_list, vo, macd_ratio, wdf=None, w_ind=None, d2df=None, d2_ind=None, vo_orig=None):
    ds = df["date"].tolist()
    op = df["open"].tolist()
    hi = df["high"].tolist()
    lo = df["low"].tolist()
    cl = df["close"].tolist()
    lt = df.iloc[-1]
    n = len(ds)
    mr = macd_ratio  # MACD > 0 占比列表（与日线对齐）
    vo_raw = vo_orig or vo  # 原始成交量

    sn = "、".join([s["name"] for s in stocks_list])

    data = {
        "ds": ds, "op": op, "hi": hi, "lo": lo, "cl": cl, "vo": vo, "mr": mr, "vo_raw": vo_raw,
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
        wv = wdf["volume"].tolist()
        w_data = {
            "ds": wdf["date"].tolist(),
            "op": wdf["open"].tolist(), "hi": wdf["high"].tolist(),
            "lo": wdf["low"].tolist(), "cl": wdf["close"].tolist(), "vo": wv,
            "mr": mr, "vo_raw": vo_raw,  # 多周期共享
            "sa_": w_ind["sa_"], "sb_": w_ind["sb_"],
            "tenkan": w_ind["tenkan"], "kijun": w_ind["kijun"],
            "boll": w_ind["boll"], "ub": w_ind["ub"], "lb": w_ind["lb"],
            "ma300": w_ind["ma300"], "ub1": w_ind["ub1"], "lb1": w_ind["lb1"],
            "ema5": w_ind["ema5"], "ma50": w_ind["ma50"],
            "ma100": w_ind["ma100"], "ub2": w_ind["ub2"], "lb2": w_ind["lb2"],
            "dif": w_ind["dif"], "dea": w_ind["dea"], "macd": w_ind["macd"],
        }

    # 两日线数据
    d2_data = None
    if d2df is not None and d2_ind is not None:
        d2v = d2df["volume"].tolist()
        d2_data = {
            "ds": d2df["date"].tolist(),
            "op": d2df["open"].tolist(), "hi": d2df["high"].tolist(),
            "lo": d2df["low"].tolist(), "cl": d2df["close"].tolist(), "vo": d2v,
            "mr": mr, "vo_raw": vo_raw,
            "sa_": d2_ind["sa_"], "sb_": d2_ind["sb_"],
            "tenkan": d2_ind["tenkan"], "kijun": d2_ind["kijun"],
            "boll": d2_ind["boll"], "ub": d2_ind["ub"], "lb": d2_ind["lb"],
            "ma300": d2_ind["ma300"], "ub1": d2_ind["ub1"], "lb1": d2_ind["lb1"],
            "ema5": d2_ind["ema5"], "ma50": d2_ind["ma50"],
            "ma100": d2_ind["ma100"], "ub2": d2_ind["ub2"], "lb2": d2_ind["lb2"],
            "dif": d2_ind["dif"], "dea": d2_ind["dea"], "macd": d2_ind["macd"],
        }

    data_json = json.dumps(data)
    w_data_json = json.dumps(w_data) if w_data else "null"
    d2_data_json = json.dumps(d2_data) if d2_data else "null"
    lv = int(lt["index_value"])
    cr = round(lt["cumulative_return"], 2)
    last_date = ds[-1]
    last_close = round(cl[-1], 1)
    last_change = round(cl[-1] - op[-1], 1)
    last_change_pct = round((cl[-1] - op[-1]) / op[-1] * 100, 2)
    is_up = cl[-1] >= op[-1]

    # 周线最新信息
    w_ld = ""
    w_lc = ""
    if wdf is not None and len(wdf) > 0:
        wlt = wdf.iloc[-1]
        w_ld = wlt["date"]
        w_lc = round(wlt["close"], 1)

    # 两日线最新信息
    d2_ld = ""
    d2_lc = ""
    if d2df is not None and len(d2df) > 0:
        d2lt = d2df.iloc[-1]
        d2_ld = d2lt["date"]
        d2_lc = round(d2lt["close"], 1)

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
<span class="pbtn act" id="pbtn_day" onclick="switchPeriod(0)">日线</span>
<span class="pbtn" id="pbtn_2day" onclick="switchPeriod(1)">两日</span>
<span class="pbtn" id="pbtn_week" onclick="switchPeriod(2)">周线</span>
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
<span style="border-left:3px solid #ff6600;color:#ff6600">量(小波)</span>
<span style="border-left:3px solid #aaa;color:#aaa">量(原始)</span>
</div>
<div class="cwrap">
<canvas id="kc"></canvas>
</div>
<script>
(function(){{
var D_DAY = {data_json};
var D_2DAY = {d2_data_json};
var D_WEEK = {w_data_json};
var allData = [D_DAY, D_2DAY, D_WEEK];
var periodLabels = ["dayInfo", "d2Info", "weekInfo"];
var periodBtns = ["pbtn_day", "pbtn_2day", "pbtn_week"];
var curPeriod = 0;
var D = D_DAY;

function getData(){{ return allData[curPeriod]; }}

function switchPeriod(idx){{
  if(!allData[idx]) return;
  curPeriod = idx;
  D = allData[idx];
  for(var i=0;i<3;i++){{
    document.getElementById(periodBtns[i]).className = i==idx ? "pbtn act" : "pbtn";
    document.getElementById(periodLabels[i]).style.display = i==idx ? "" : "none";
  }}
  n = D.ds.length;
  scale = n / 60;
  offset = n - 60;
  draw();
}}
window.switchPeriod = switchPeriod;

var c = document.getElementById("kc");
var ctx = c.getContext("2d");

var W, H;
var pd=25, pd_b=35, scale=1, offset=0, isInit=true, n=0;
var PIN1 = 0.55; // 主图 55%
var PIN2 = 0.20; // MACD 20%
var PIN3 = 0.17; // 量  17%
var PIN4 = 0.08; // 原始量 8%
var INITIAL_VIS = 60;
var GAP = 12;    // 子图间距

function resize(){{
  D = getData();
  n = D.ds.length;
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
  n = D.ds.length;
  ctx.clearRect(0,0,W,H);
  if(n<2) return;

  var pw = W - pd - pd;
  var avail = H - pd - pd_b - GAP - GAP - GAP; // 主图+MACD+量(小波)+量(原始) 共4子图
  var ph1 = avail * PIN1;
  var ph2 = avail * PIN2;
  var ph3 = avail * PIN3;
  var ph4 = avail * PIN4;

  // 各子图起始Y
  var y1 = pd;
  var y2 = y1 + ph1 + GAP;
  var y3 = y2 + ph2 + GAP;
  var y4 = y3 + ph3 + GAP;

  var visN = Math.max(10, Math.floor(n / scale));
  var i0 = Math.floor(offset);
  if(i0 < 0) i0 = 0;
  if(i0 > n - visN) i0 = n - visN;
  var i1 = Math.min(i0 + visN, n);

  function xp(i){{ return pd + (i-i0)/(i1-i0)*pw }}

  // ====== 主图 ======
  var mn1 = 1e9, mx1 = -1e9;
  for(var i=i0;i<i1;i++){{ if(D.lo[i] < mn1) mn1 = D.lo[i]; if(D.hi[i] > mx1) mx1 = D.hi[i]; }}
  var rg1 = mx1 - mn1 || 1;
  function yp1(v){{ return y1 + ph1 - (v-mn1)/rg1*ph1 }}

  ctx.strokeStyle = "#222"; ctx.lineWidth = 0.5;
  for(var g=0;g<5;g++){{ var yy = y1 + g*ph1/4; ctx.beginPath(); ctx.moveTo(pd,yy); ctx.lineTo(pd+pw,yy); ctx.stroke(); ctx.fillStyle="#666"; ctx.font="7px Arial"; ctx.textAlign="end"; ctx.fillText(Math.round(mn1+(1-g/4)*rg1), pd-2, yy+3); }}

  function poly1(arr,c,w,d){{ ctx.strokeStyle=c; ctx.lineWidth=w; ctx.setLineDash(d?[3,2]:[]); ctx.beginPath(); var s=false; for(var i=i0;i<i1;i++){{ if(arr[i]==null){{s=false;continue;}} var xx=xp(i),yy=yp1(arr[i]); if(!s){{ctx.moveTo(xx,yy);s=true;}}else ctx.lineTo(xx,yy); }} ctx.stroke(); ctx.setLineDash([]); }}
  function fillCloud(d1,d2,cl){{ ctx.fillStyle=cl; ctx.beginPath(); for(var i=i0;i<i1;i++){{ if(d1[i]==null||d2[i]==null) continue; ctx.lineTo(xp(i),yp1(d1[i])); }} for(var i=i1-1;i>=i0;i--){{ if(d1[i]==null||d2[i]==null) continue; ctx.lineTo(xp(i),yp1(d2[i])); }} ctx.closePath(); ctx.fill(); }}

  ctx.save(); ctx.beginPath(); ctx.rect(pd, y1, pw, ph1); ctx.clip();
  for(var i=i0;i<i1;i++){{ var j=i; while(j<i1&&D.sa_[j]!=null&&D.sb_[j]!=null) j++; if(j>i){{ var b=D.sa_[i]>=D.sb_[i]; fillCloud(D.sa_,D.sb_,b?"rgba(255,107,53,0.18)":"rgba(42,111,156,0.18)"); }} i=j; }}
  poly1(D.sa_,"#ff6b35",1.2); poly1(D.sb_,"#2a6f9c",1.2);
  poly1(D.ub,"#aa843e",0.5,true); poly1(D.lb,"#aa843e",0.5,true); poly1(D.boll,"#aa843e",1);
  poly1(D.ma300,"#ffd700",1.5); poly1(D.ub1,"#ffd700",0.5,true); poly1(D.lb1,"#ffd700",0.5,true);
  poly1(D.ub2,"#666",0.5,true); poly1(D.lb2,"#666",0.5,true);
  poly1(D.ema5,"#fff",1.2); poly1(D.ma50,"#0f0",1.2); poly1(D.ma100,"#f44",1.5);

  var cw2=Math.max(1,Math.min(8,pw/(i1-i0)-1)), hw2=cw2/2;
  for(var i=i0;i<i1;i++){{ var x=xp(i); var col=D.op[i]<D.cl[i]?"#ff4444":"#00c853"; ctx.strokeStyle=col; ctx.lineWidth=0.8; ctx.beginPath();ctx.moveTo(x,yp1(D.hi[i]));ctx.lineTo(x,yp1(D.lo[i]));ctx.stroke(); ctx.fillStyle=col; ctx.fillRect(x-hw2,Math.min(yp1(D.op[i]),yp1(D.cl[i])),cw2,Math.max(1,Math.abs(yp1(D.cl[i])-yp1(D.op[i])))); }}

  ctx.font="12px Arial"; ctx.textAlign="center";
  for(var i=Math.max(1,i0);i<i1;i++){{ if(D.sa_[i]==null||D.sb_[i]==null||D.sa_[i-1]==null||D.sb_[i-1]==null) continue; if(D.sa_[i-1]<=D.sb_[i-1]&&D.sa_[i]>D.sb_[i]){{ctx.fillStyle="#ff6b35"; ctx.fillText("▲",xp(i),yp1(D.hi[i])-2);}} if(D.sa_[i-1]>=D.sb_[i-1]&&D.sa_[i]<D.sb_[i]){{ctx.fillStyle="#2a6f9c"; ctx.fillText("▼",xp(i),yp1(D.lo[i])+12);}} }}
  ctx.restore(); ctx.strokeStyle="#333"; ctx.lineWidth=1; ctx.strokeRect(pd, y1, pw, ph1);

  // ====== MACD ======
  ctx.strokeStyle="#333"; ctx.lineWidth=0.5; ctx.beginPath(); ctx.moveTo(pd,y2-GAP/2); ctx.lineTo(pd+pw,y2-GAP/2); ctx.stroke();
  ctx.fillStyle="#888"; ctx.font="9px Arial"; ctx.textAlign="left"; ctx.fillText("MACD(12,26,9)", pd+4, y2-GAP/2+11);
  var mn2=0,mx2=0,hasM=false; for(var i=i0;i<i1;i++){{ if(D.macd[i]==null) continue; hasM=true; if(D.macd[i]<mn2)mn2=D.macd[i];if(D.macd[i]>mx2)mx2=D.macd[i];if(D.dif[i]<mn2)mn2=D.dif[i];if(D.dif[i]>mx2)mx2=D.dif[i];if(D.dea[i]<mn2)mn2=D.dea[i];if(D.dea[i]>mx2)mx2=D.dea[i]; }}
  if(!hasM){{mn2=-10;mx2=10;}} var p2=Math.max(Math.abs(mx2-mn2)*0.15,1); mn2-=p2; mx2+=p2; var rg2=mx2-mn2||1;
  function yp2(v){{return Math.max(y2,Math.min(y2+ph2,y2+ph2-(v-mn2)/rg2*ph2));}}
  ctx.save(); ctx.beginPath(); ctx.rect(pd, y2, pw, ph2); ctx.clip();
  ctx.strokeStyle="#222"; ctx.lineWidth=0.5; ctx.beginPath(); ctx.moveTo(pd,yp2(0)); ctx.lineTo(pd+pw,yp2(0)); ctx.stroke();
  for(var i=i0;i<i1;i++){{if(D.macd[i]==null)continue; var x=xp(i),y0=yp2(0),yv=yp2(D.macd[i]); ctx.fillStyle=D.macd[i]>=0?"#f44":"#00c853"; ctx.fillRect(x-hw2*0.6,Math.min(y0,yv),cw2*0.6,Math.max(0.5,Math.abs(yv-y0)));}}
  function poly2(a,c,w,d){{ctx.strokeStyle=c;ctx.lineWidth=w;ctx.setLineDash(d?[3,2]:[]);ctx.beginPath();var s=false;for(var i=i0;i<i1;i++){{if(a[i]==null){{s=false;continue;}}var xx=xp(i),yy=yp2(a[i]);if(!s){{ctx.moveTo(xx,yy);s=true;}}else ctx.lineTo(xx,yy);}}ctx.stroke();ctx.setLineDash([]);}}
  poly2(D.dif,"#fff",1); poly2(D.dea,"#ffd700",1,true);
  ctx.fillStyle="#666"; ctx.font="7px Arial"; ctx.textAlign="end"; ctx.fillText(mx2.toFixed(1),pd-2,yp2(mx2)+3); ctx.fillText(mn2.toFixed(1),pd-2,yp2(mn2)+3);
  ctx.restore(); ctx.strokeStyle="#333"; ctx.lineWidth=1; ctx.strokeRect(pd, y2, pw, ph2);

  // ====== 成交量 ======
  ctx.strokeStyle="#333"; ctx.lineWidth=0.5; ctx.beginPath(); ctx.moveTo(pd,y3-GAP/2); ctx.lineTo(pd+pw,y3-GAP/2); ctx.stroke();
  ctx.fillStyle="#888"; ctx.font="9px Arial"; ctx.textAlign="left"; ctx.fillText("VOL", pd+4, y3-GAP/2+11);

  var mn3=1e9,mx3=-1e9;
  for(var i=i0;i<i1;i++){{ if(D.vo[i]==null) continue; if(D.vo[i]<mn3)mn3=D.vo[i]; if(D.vo[i]>mx3)mx3=D.vo[i]; }}
  var rg3 = (mx3 - mn3) || 1;
  function yp3(v){{ return y3 + ph3 - (v-mn3)/rg3*ph3; }}
  ctx.save(); ctx.beginPath(); ctx.rect(pd, y3, pw, ph3); ctx.clip();
  for(var i=i0;i<i1;i++){{ if(D.vo[i]==null) continue; var x=xp(i),y0=y3+ph3,yv=yp3(D.vo[i]); var col=D.op[i]<D.cl[i]?"#ff4444":"#00c853"; ctx.fillStyle=col; ctx.fillRect(x-hw2, Math.min(y0,yv), cw2, Math.max(0.5, Math.abs(yv-y0))); }}
  ctx.fillStyle="#666"; ctx.font="7px Arial"; ctx.textAlign="end"; ctx.fillText(formatVol(mx3), pd-2, y3+9); ctx.fillText("0", pd-2, y3+ph3+3);
  ctx.restore(); ctx.strokeStyle="#333"; ctx.lineWidth=1; ctx.strokeRect(pd, y3, pw, ph3);

  // ====== 原始成交量（对比小波） ======
  ctx.strokeStyle="#333"; ctx.lineWidth=0.5; ctx.beginPath(); ctx.moveTo(pd,y4-GAP/2); ctx.lineTo(pd+pw,y4-GAP/2); ctx.stroke();
  ctx.fillStyle="#888"; ctx.font="9px Arial"; ctx.textAlign="left"; ctx.fillText("VOL(RAW)", pd+4, y4-GAP/2+11);
  var mn4=1e9,mx4=-1e9;
  for(var i=i0;i<i1;i++){{ if(D.vo_raw[i]==null) continue; if(D.vo_raw[i]<mn4)mn4=D.vo_raw[i]; if(D.vo_raw[i]>mx4)mx4=D.vo_raw[i]; }}
  var rg4 = (mx4 - mn4) || 1;
  function yp4(v){{return y4+ph4-(v-mn4)/rg4*ph4;}}
  ctx.save(); ctx.beginPath(); ctx.rect(pd, y4, pw, ph4); ctx.clip();
  for(var i=i0;i<i1;i++){{ if(D.vo_raw[i]==null) continue; var x=xp(i),y0=y4+ph4,yv=yp4(D.vo_raw[i]); var col=D.op[i]<D.cl[i]?"rgba(255,68,68,0.4)":"rgba(0,200,83,0.4)"; ctx.fillStyle=col; ctx.fillRect(x-1, Math.min(y0,yv), 3, Math.max(0.5, Math.abs(yv-y0))); }}
  ctx.fillStyle="#aaa"; ctx.font="7px Arial"; ctx.textAlign="end"; ctx.fillText(formatVol(mx4), pd-2, y4+9); ctx.fillText("0", pd-2, y4+ph4+3);
  ctx.restore(); ctx.strokeStyle="#333"; ctx.lineWidth=1; ctx.strokeRect(pd, y4, pw, ph4);

  // ====== 日期轴 ======
  ctx.fillStyle="#999"; ctx.textAlign="center";
  var labelStep=Math.max(1,Math.floor(38*(i1-i0)/pw));
  var lastYear="";
  for(var i=i0;i<i1;i+=labelStep){{ var ds=D.ds[i],p=ds.split("-"),md=p[1]+p[2],yy=p[0],xx=xp(i); ctx.font="7px Arial"; var dy=y4+ph4+10; ctx.fillText(md,xx,dy); if(yy!==lastYear){{ctx.fillText(yy,xx,dy+10);lastYear=yy;}} }}
}}

function formatVol(v){{ if(v>=1e8) return (v/1e8).toFixed(1)+"亿"; if(v>=1e4) return (v/1e4).toFixed(1)+"万"; return v.toFixed(0); }}

// touch / mouse handlers
var isDragging=false, dragStartX=0, dragStartOff=0, lastDist=0;
c.addEventListener("touchstart",function(e){{e.preventDefault();var t=e.touches;if(t.length==1){{isDragging=true;dragStartX=t[0].clientX;dragStartOff=offset;}}else if(t.length==2){{isDragging=false;lastDist=Math.hypot(t[0].clientX-t[1].clientX,t[0].clientY-t[1].clientY);}}}},{{passive:false}});
c.addEventListener("touchmove",function(e){{e.preventDefault();var t=e.touches;if(t.length==1&&isDragging){{var dx=(t[0].clientX-dragStartX)/W;offset=dragStartOff-dx*n/scale;draw();}}else if(t.length==2){{var dist=Math.hypot(t[0].clientX-t[1].clientX,t[0].clientY-t[1].clientY);var s=dist/Math.max(1,lastDist);var cx=(t[0].clientX+t[1].clientX)/2;var cr=cx/W;var os=scale;scale=clamp(scale*s,1,50);s=scale/os;var ci=offset+cr*n/os;offset=ci-cr*n/scale;if(offset<0)offset=0;if(offset>n-n/scale)offset=n-n/scale;lastDist=dist;draw();}}}},{{passive:false}});
c.addEventListener("touchend",function(e){{isDragging=false;}});
c.addEventListener("wheel",function(e){{e.preventDefault();var r=c.getBoundingClientRect();var cx=(e.clientX-r.left)/W;var os=scale;scale=clamp(scale*(1-e.deltaY*0.001),1,50);var s=scale/os;var ci=offset+cx*n/os;offset=ci-cx*n/scale;if(offset<0)offset=0;if(offset>n-n/scale)offset=n-n/scale;draw();}},{{passive:false}});
c.addEventListener("mousedown",function(e){{isDragging=true;dragStartX=e.clientX;dragStartOff=offset;}});
window.addEventListener("mousemove",function(e){{if(!isDragging)return;var dx=(e.clientX-dragStartX)/W;offset=dragStartOff-dx*n/scale;if(offset<0)offset=0;if(offset>n-n/scale)offset=n-n/scale;draw();}});
window.addEventListener("mouseup",function(){{isDragging=false;}});
window.addEventListener("resize",resize);
resize();

}})();
</script>
<div class="info" id="dayInfo">📅 {last_date} <b>{last_close}</b> {'🔴涨' if is_up else '🟢跌'} {last_change:+.1f}({last_change_pct:+.2f}%) | 指数 {lv}({cr}%) | {sn}</div>
<div class="info" id="d2Info" style="display:none">📅 {d2_ld} <b>{d2_lc}</b>（两日）| {sn}</div>
<div class="info" id="weekInfo" style="display:none">📅 {w_ld} <b>{w_lc}</b>（周线）| {sn}</div>
</body>
</html>'''
    return html
