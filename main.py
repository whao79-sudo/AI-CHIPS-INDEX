#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chip Index - Cloud Ichimoku + Bollinger + Multi-MA
"""
import pandas as pd, numpy as np, requests, yaml, os, sys, json
from datetime import datetime, timedelta
from pathlib import Path

HIST_CSV = "stocks_history.csv"

try:
  import baostock as bs
  HAS_BAOSTOCK = True
except:
  HAS_BAOSTOCK = False


def fetch_baostock(code, start_date, end_date):
if not HAS_BAOSTOCK: return
bs_code = "{}.{}".format(code[:2], code[2:])
try:
bs.login()
rs = bs.query_history_k_data_plus(
bs_code, "date,open,high,low,close,volume",
start_date=start_date.strftime("%Y-%m-%d"),
end_date=end_date.strftime("%Y-%m-%d"),
frequency="d", adjustflag="2"
)
if rs.error_code != "0":
print(" Baostock err: {}".format(rs.error_code))
bs.logout(); return
rows = []
while rs.next(): rows.append(rs.get_row_data())
bs.logout()
if not rows: return
df = pd.DataFrame(rows, columns=["date","open","high","low","close","volume"])
for c in ["open","high","low","close","volume"]: df[c] = pd.to_numeric(df[c], errors="coerce")
df["code"] = code
print(" Baostock: {} rows".format(len(df)))
return df[["date","code","open","high","low","close","volume"]]
except Exception as e:
print(" Baostock fail: {}".format(e))
try: bs.logout()
except: pass


def fetch_sina(code, datalen=1000):
url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={}&scale=240&ma=no&datalen={}".format(code, datalen)
try:
r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
r.raise_for_status(); data = r.json()
if not data: return
df = pd.DataFrame(data).rename(columns={"day":"date"})
for c in ["open","high","low","close","volume"]: df[c] = pd.to_numeric(df[c], errors="coerce")
df["code"] = code
return df[["date","code","open","high","low","close","volume"]]
except Exception as e:
print(" Sina fail: {}".format(e))


def smart_adjust(df):
df = df.sort_values("date").copy()
adjusted = []
for code in df["code"].unique():
sub = df[df["code"] == code].sort_values("date").copy()
sub.reset_index(drop=True, inplace=True)
adj = 1.0
for i in range(len(sub) - 1, 0, -1):
prev_c = sub.loc[i - 1, "close"]
curr_o = sub.loc[i, "open"]
if prev_c and curr_o:
gap = (curr_o - prev_c) / prev_c
if gap < -0.25:
adj *= prev_c / curr_o
if adj != 1.0:
for c in ["open","high","low","close"]:
sub.loc[i, c] = round(sub.loc[i, c] * adj, 2)
adjusted.append(sub)
return pd.concat(adjusted, ignore_index=True)


class IndexGenerator:
def __init__(self, config_path="config.yaml"):
self.config = self._load_config(config_path)
self.stocks = self.config["stocks"]
self.index_config = self.config["index"]
self.output_dir = Path(self.config["output"]["dir"])

def _load_config(self, config_path):
if os.path.exists(config_path):
with open(config_path, "r") as f: return yaml.safe_load(f)
return {
"stocks": [
{"name":"中际旭创","code":"sz300308"},{"name":"新易盛","code":"sz300502"},
{"name":"天孚通信","code":"sz300394"},{"name":"海光信息","code":"sh688041"},
{"name":"寒武纪","code":"sh688256"},{"name":"龙芯中科","code":"sh688047"},
{"name":"工业富联","code":"sh601138"},{"name":"浪潮信息","code":"sz000977"},
{"name":"中科曙光","code":"sh603019"},{"name":"香农芯创","code":"sz300475"},
{"name":"佰维存储","code":"sh688525"},{"name":"德明利","code":"sz001309"},
{"name":"江波龙","code":"sz301308"},{"name":"兆易创新","code":"sh603986"},
],
"index":{"base_date":"2024-01-02","base_value":1000.0},
"output":{"dir":"./output","start_date":"2024-01-01"},
}

def fetch_data(self):
start = self.config["output"]["start_date"]
start_date = datetime.strptime(start, "%Y-%m-%d")
end_date = datetime.now()
old = None
if os.path.exists(HIST_CSV):
try:
old = pd.read_csv(HIST_CSV)
print("Loaded {} rows from history".format(len(old)))
except: pass
print("Fetching {} stocks...".format(len(self.stocks)))
rows = []
for i, s in enumerate(self.stocks, 1):
code = s["code"]; name = s["name"]
last_date = None
if old is not None:
sub = old[old["code"] == code]
if len(sub) > 0:
last_date = pd.to_datetime(sub["date"]).max()
if last_date is not None:
fetch_start = last_date + timedelta(days=1)
print(" [{}/{}] {} {} incr from {}...".format(i, len(self.stocks), name, code, last_date.strftime("%Y-%m-%d")))
df = fetch_baostock(code, fetch_start, end_date)
if df is None:
print(" -> Sina")
df = fetch_sina(code, datalen=15)
else:
print(" [{}/{}] {} {} full...".format(i, len(self.stocks), name, code))
df = fetch_baostock(code, start_date, end_date)
if df is None:
print(" -> Sina")
df = fetch_sina(code, datalen=1000)
if df is not None and len(df) > 0:
df["name"] = name; rows.append(df)
if not rows: print("No data!"); return
new = pd.concat(rows, ignore_index=True)
if old is not None:
all_ = pd.concat([old, new], ignore_index=True)
all_ = all_.sort_values("date").drop_duplicates(subset=["code","date"], keep="last")
else: all_ = new
all_ = all_[all_["date"] >= start]
all_.to_csv(HIST_CSV, index=False, encoding="utf-8-sig")
print("Total: {} rows".format(len(all_)))
return all_

def calc_index(self, sdf):
d = sdf.copy(); d["date"] = pd.to_datetime(d["date"])
d = d.sort_values(["code","date"])
g = d.groupby(d["date"].dt.strftime("%Y-%m-%d")).agg({"open":"mean","high":"mean","low":"mean","close":"mean"}).reset_index().rename(columns={"date":"ds"})
if len(g) == 0: return
bv = self.index_config["base_value"]
g["index_value"] = (g["close"] / g["close"].iloc[0] * bv).round(2)
g["cumulative_return"] = ((g["index_value"] / bv - 1) * 100).round(2)
g.loc[0, "cumulative_return"] = 0.0
s_ = bv / g["close"].iloc[0]
for c in ["open","high","low","close"]: g[c] = (g[c] * s_).round(2)
return g.rename(columns={"ds":"date"})

def gen_html(self, df, title="AI CHIP INDEX"):
ds = df["date"].tolist(); op = df["open"].tolist(); hi = df["high"].tolist()
lo = df["low"].tolist(); cl = df["close"].tolist(); lt = df.iloc[-1]; n = len(ds)

tenkan = [(hi[i]+lo[i])/2 if i>=8 else None for i in range(n)]
kijun = [(max(hi[max(0,i-25):i+1])+min(lo[max(0,i-25):i+1]))/2 if i>=25 else None for i in range(n)]
sa_ = [(tenkan[i]+kijun[i])/2 if tenkan[i] is not None and kijun[i] is not None else None for i in range(n)]
sb_ = [(max(hi[max(0,i-51):i+1])+min(lo[max(0,i-51):i+1]))/2 if i>=51 else None for i in range(n)]

def ma(d, p):
r=[];t=0
for i in range(n):
t+=d[i]
if i>=p: t-=d[i-p]
r.append(round(t/min(p,i+1),2) if i>=p-1 else None)
return r
def ema(d,p):
r=[];f=2/(p+1)
for i in range(n):
if i==0: r.append(d[0])
else: r.append(round(d[i]*f+(1-f)*r[-1],2))
return r

boll = ma(cl,20); ma50 = ma(cl,50); ma100 = ma(cl,100); ma300 = ma(cl,300)
ema5 = ema(cl,5)

def std(d,p):
return [round(np.std(d[max(0,i-p+1):i+1]),2) if i>=p-1 else None for i in range(n)]

s20=std(cl,20); s100=std(cl,100); s300=std(cl,300)
ub = [round(boll[i]+2*s20[i],2) if boll[i] is not None else None for i in range(n)]
lb = [round(boll[i]-2*s20[i],2) if boll[i] is not None else None for i in range(n)]
ub1 = [round(ma300[i]+2*s300[i],2) if ma300[i] is not None else None for i in range(n)]
lb1 = [round(ma300[i]-2*s300[i],2) if ma300[i] is not None else None for i in range(n)]
ub1a = [round(ma300[i]+s300[i],2) if ma300[i] is not None else None for i in range(n)]
lb1a = [round(ma300[i]-s300[i],2) if ma300[i] is not None else None for i in range(n)]
ub2 = [round(ma100[i]+2*s100[i],2) if ma100[i] is not None else None for i in range(n)]
lb2 = [round(ma100[i]-2*s100[i],2) if ma100[i] is not None else None for i in range(n)]

W=1400; H=700; p_=80; pw=W-2*p_; ph=H-2*p_
mv=min(lo); xv=max(hi); rg=xv-mv or 1
def yp(v): return p_+ph-(v-mv)/rg*ph
cw=max(2,min(12,pw//n-1)); hw=max(1,cw//2)
def xp(i): return p_+i*pw//(n-1 if n>1 else 1)
def ln(d,c,w,s=""):
pts=[]
for i in range(n):
if d[i] is None: continue
pts.append("{},{}".format(xp(i),yp(d[i])))
attr="stroke-dasharray=\"4,3\"" if s else ""
return '<polyline points="{}" fill="none" stroke="{}" stroke-width="{}" {}/>'.format(" ".join(pts),c,w,attr) if pts else ""
def fill(d1,d2,c):
pts=[]
for i in range(n):
if d1[i] is None or d2[i] is None: continue
pts.append("{},{}".format(xp(i),yp(d1[i])))
for i in range(n-1,-1,-1):
if d1[i] is None or d2[i] is None: continue
pts.append("{},{}".format(xp(i),yp(d2[i])))
return '<polygon points="{}" fill="{}" opacity="0.12"/>'.format(" ".join(pts),c) if pts else ""

gs=""; sg=""; xt=""
for i in range(5):
yy=p_+i*ph//4; v=mv+(1-i/4)*rg
gs+='<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="#222" stroke-width="0.5"/><text x="{}" y="{}" fill="#666" font-size="11" text-anchor="end">{:.0f}</text>'.format(p_,yy,p_+pw,yy,p_-5,yy+4,v)

sg+=fill(sa_, sb_, "#2f4f4f")
sg+=fill(sb_, sa_, "#8b4513")
sg+=ln(sa_,"#2f4f4f",1)+ln(sb_,"#8b4513",1)
sg+=ln(ub,"#aa843e",0.5,"dash")+ln(lb,"#aa843e",0.5,"dash")+ln(boll,"#aa843e",1)
sg+=ln(ma300,"#ffd700",2)+ln(ub1,"#ffd700",0.5,"dash")+ln(lb1,"#ffd700",0.5,"dash")
sg+=ln(ub1a,"#4682b4",1,"dash")+ln(lb1a,"#4682b4",1,"dash")
sg+=ln(ub2,"#888",0.5,"dash")+ln(lb2,"#888",0.5,"dash")
sg+=ln(ema5,"#fff",1.5)+ln(ma50,"#0f0",1.5)+ln(ma100,"#f44",2)
for i in range(n):
x=xp(i)
yo=yp(op[i]);yh_=yp(hi[i]);yl=yp(lo[i]);yc=yp(cl[i])
c="#ff4444" if op[i]<cl[i] else "#00c853"
sg+='<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1.5"/><rect x="{}" y="{}" width="{}" height="{}" fill="{}" rx="1"/>'.format(x,yh_,x,yl,c,x-hw,min(yo,yc),cw,abs(yc-yo)+1,c)
for i in range(1,n):
if sa_[i] is not None and sb_[i] is not None and sa_[i-1] is not None and sb_[i-1] is not None:
if sa_[i-1]<=sb_[i-1] and sa_[i]>sb_[i]:
sg+='<text x="{}" y="{}" fill="#f44" font-size="20" text-anchor="middle" dominant-baseline="bottom">&#9650;</text>'.format(xp(i),yp(hi[i])-2)
if sa_[i-1]>=sb_[i-1] and sa_[i]<sb_[i]:
sg+='<text x="{}" y="{}" fill="#0f0" font-size="20" text-anchor="middle" dominant-baseline="top">&#9660;</text>'.format(xp(i),yp(lo[i])+2)
for i in range(n):
if i%60==0 or i==n-1:
x=xp(i); xt+='<text x="{}" y="{}" fill="#666" font-size="10" text-anchor="middle">{}</text>'.format(x,p_+ph+20,ds[i])

svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" style="width:100%;height:auto;max-width:{}px">{}{}{}</svg>'.format(W,H,W,gs+'<rect x="{}" y="{}" width="{}" height="{}" fill="none" stroke="#444" stroke-width="1"/>'.format(p_,p_,pw,ph),sg,xt)
stats=''
for l,v in [("最新点位",str(lt["index_value"])),("累计涨幅",str(lt["cumulative_return"])+"%"),("交易日",str(n)),("起始日",ds[0])]:
stats+='<div class="stat"><div class="v">{}</div><div class="l">{}</div></div>'.format(v,l)
sn="、".join([s["name"] for s in self.stocks])
return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>""" + title + """</title>
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
@media(min-width:768px){body{padding:20px 40px};h1{font-size:28px}.stats{grid-template-columns:1fr 1fr 1fr 1fr;max-width:none}.stat .v{font-size:28px}}
</style></head><body>
<h1>""" + title + """</h1>
<div class="stats">""" + stats + """</div>
<div class="leg">
<span style="border-left:3px solid #2f4f4f;color:#2f4f4f">先行A</span><span style="border-left:3px solid #8b4513;color:#8b4513">先行B</span>
<span style="border-left:3px solid #aa843e;color:#aa843e">BOL20</span><span style="border-left:3px solid #ffd700;color:#ffd700">MA300</span>
<span style="border-left:3px solid #4682b4;color:#4682b4">&#177;1SD300</span>
<span style="border-left:3px solid #fff;color:#fff">EMA5</span><span style="border-left:3px solid #0f0">MA50</span><span style="border-left:3px solid #f44;color:#f44">MA100</span>
<span style="color:#ff4444">&#9650;金叉</span><span style="color:#0f0">&#9660;死叉</span>
</div>
<div class="cwrap">""" + svg + """</div>
<div class="info">成分股（等权重）：""" + sn + """ | Cloud+Ichimoku+Bollinger | """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</div>
</body></html>"""

def save(self, sdf, idf):
self.output_dir.mkdir(parents=True, exist_ok=True)
sdf.to_csv(self.output_dir/"AI_CHIP_INDEX_stocks.csv", index=False, encoding="utf-8-sig")
idf.to_csv(self.output_dir/"AI_CHIP_INDEX_detail.csv", index=False, encoding="utf-8-sig")
idf[["date","index_value"]].to_csv(self.output_dir/"AI_CHIP_INDEX.csv", index=False, encoding="utf-8-sig")
with open(self.output_dir/"AI_CHIP_INDEX_kline.html","w",encoding="utf-8") as f:
f.write(self.gen_html(idf))
print("Saved OK")

def run(self):
s=self.fetch_data()
if s is None: print("No data"); return
i=self.calc_index(s)
if i is None: print("Calc failed"); return
self.save(s,i)
print("Done! Latest: {:.2f}, Return: {:.2f}%".format(i["index_value"].iloc[-1], i["cumulative_return"].iloc[-1]))

if __name__=="__main__":
g=IndexGenerator()
if len(sys.argv)>1 and sys.argv[1]=="chart":
s=pd.read_csv(g.output_dir/"AI_CHIP_INDEX_stocks.csv",encoding="utf-8-sig")
g.save(s,g.calc_index(s))
else: g.run()