#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chip Index - 首次全量，后续增量更新
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
    """Baostock 获取个股数据"""
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
            print("    Baostock err: {}".format(rs.error_code))
            bs.logout(); return
        data = []
        while rs.next(): data.append(rs.get_row_data())
        bs.logout()
        if not data: return
        df = pd.DataFrame(data, columns=["date","open","high","low","close","volume"])
        for c in ["open","high","low","close","volume"]: df[c] = pd.to_numeric(df[c], errors="coerce")
        df["code"] = code
        print("    Baostock: {} rows ({} to {})".format(len(df), start_date.strftime("%m-%d"), end_date.strftime("%m-%d")))
        return df[["date","code","open","high","low","close","volume"]]
    except Exception as e:
        print("    Baostock fail: {}".format(e))
        try: bs.logout()
        except: pass


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

        # 看有没有历史数据
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

            # 如果有历史数据：从最后日期往后拉，只取最新几天
            last_date = None
            if old is not None:
                sub = old[old["code"] == code]
                if len(sub) > 0:
                    last_date = pd.to_datetime(sub["date"]).max()

            if last_date is not None:
                # 拉最后日期的第二天到今天
                fetch_start = last_date + timedelta(days=1)
                print("  [{}/{}] {} {} incremental from {}...".format(i, len(self.stocks), name, code, last_date.strftime("%Y-%m-%d")))
                df = fetch_baostock(code, fetch_start, end_date)
            else:
                # 没有历史：全量拉
                print("  [{}/{}] {} {} full fetch...".format(i, len(self.stocks), name, code))
                df = fetch_baostock(code, start_date, end_date)

            if df is not None and len(df) > 0:
                df["name"] = name; rows.append(df)

        if not rows: print("No data!"); return
        new = pd.concat(rows, ignore_index=True)

        # 合并新旧数据，去重
        if old is not None:
            all_ = pd.concat([old, new], ignore_index=True)
            all_ = all_.sort_values("date").drop_duplicates(subset=["code","date"], keep="last")
        else:
            all_ = new

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
        s = bv / g["close"].iloc[0]
        for c in ["open","high","low","close"]: g[c] = (g[c] * s).round(2)
        return g.rename(columns={"ds":"date"})

    def gen_html(self, df, title="AI CHIP INDEX"):
        ds = df["date"].tolist(); op = df["open"].tolist(); hi = df["high"].tolist()
        lo = df["low"].tolist(); cl = df["close"].tolist(); lt = df.iloc[-1]; n = len(ds)
        def sma(d,p):
            r=[];t=0
            for i in range(len(d)):
                t+=d[i]
                if i>=p: t-=d[i-p]
                r.append(round(t/min(p,i+1),2) if i>=p-1 else None)
            return r
        m5=sma(cl,5); m50=sma(cl,50); m100=sma(cl,100)
        W=1400; H=700; pd_=80; pw=W-2*pd_; ph=H-2*pd_
        mv=min(lo); xv=max(hi); rg=xv-mv or 1
        def yp(v): return pd_+ph-(v-mv)/rg*ph
        cw=max(2,min(12,pw//n-1)); hw=max(1,cw//2)
        sg="";gs="";xt=""
        for i in range(5):
            yy=pd_+i*ph//4; v=mv+(1-i/4)*rg
            gs+='<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="#333" stroke-width="0.5"/><text x="{}" y="{}" fill="#888" font-size="11" text-anchor="end">{:.0f}</text>'.format(pd_,yy,pd_+pw,yy,pd_-5,yy+4,v)
        for i in range(n):
            x=pd_+i*pw//(n-1 if n>1 else 1)
            yo=yp(op[i]);yh=yp(hi[i]);yl=yp(lo[i]);yc=yp(cl[i])
            c="#ff4444" if op[i]<cl[i] else "#00c853"
            sg+='<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1.5"/><rect x="{}" y="{}" width="{}" height="{}" fill="{}" rx="1"/>'.format(x,yh,x,yl,c,x-hw,min(yo,yc),cw,abs(yc-yo)+1,c)
        def ln(d,c,w):
            p=[]
            for i in range(n):
                if d[i] is None: continue
                x=pd_+i*pw//(n-1 if n>1 else 1)
                p.append("{},{}".format(x,yp(d[i])))
            return '<polyline points="{}" fill="none" stroke="{}" stroke-width="{}"/>'.format(" ".join(p),c,w) if p else ""
        sg+=ln(m5,"#fff",1.5)+ln(m50,"#0f0",1.5)+ln(m100,"#f44",2)
        for i in range(n):
            if i%60==0 or i==n-1:
                x=pd_+i*pw//(n-1 if n>1 else 1)
                xt+='<text x="{}" y="{}" fill="#888" font-size="10" text-anchor="middle">{}</text>'.format(x,pd_+ph+20,ds[i])
        svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" style="width:100%;height:auto;max-width:{}px">{}{}{}</svg>'.format(W,H,W,gs+'<rect x="{}" y="{}" width="{}" height="{}" fill="none" stroke="#555" stroke-width="1"/>'.format(pd_,pd_,pw,ph),sg,xt)
        st=""
        for l,v in [("最新点位",str(lt["index_value"])),("累计涨幅",str(lt["cumulative_return"])+"%"),("交易日",str(n)),("起始日",ds[0])]:
            st+='<div class="stat"><div class="v">{}</div><div class="l">{}</div></div>'.format(v,l)
        sn="、".join([s["name"] for s in self.stocks])
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>""" + title + """</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f23;color:#e0e0e0;font-family:Arial,sans-serif;padding:10px}
h1{text-align:center;color:#00d4ff;font-size:20px;margin:10px 0}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0 auto 12px;max-width:500px}
.stat{background:#1a1a3e;padding:12px;border-radius:8px;text-align:center}
.stat .v{font-size:22px;color:#00d4ff;font-weight:bold}
.stat .l{font-size:11px;color:#888;margin-top:3px}
.cwrap{background:#1a1a3e;border-radius:8px;padding:10px;overflow-x:auto}
.leg{text-align:center;margin:6px 0 10px;font-size:12px}
.leg span{display:inline-block;margin:0 8px;padding:2px 8px;border-radius:3px}
.info{text-align:center;margin:8px 0;font-size:11px;color:#666;line-height:1.6}
@media(min-width:768px){
  body{padding:20px 40px};h1{font-size:28px}
  .stats{grid-template-columns:1fr 1fr 1fr 1fr;max-width:none}
  .stat .v{font-size:28px}
}
</style>
</head>
<body>
<h1>""" + title + """</h1>
<div class="stats">""" + st + """</div>
<div class="leg">
<span style="border-left:3px solid #fff">EMA5</span>
<span style="border-left:3px solid #0f0">MA50</span>
<span style="border-left:3px solid #f44">MA100</span>
<span style="background:#ff4444;color:#fff">阳线</span><span style="background:#00c853;color:#fff">阴线</span>
</div>
<div class="cwrap">""" + svg + """</div>
<div class="info">成分股（等权重）：""" + sn + """ | 数据源：Baostock 前复权 | """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</div>
</body>
</html>"""

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