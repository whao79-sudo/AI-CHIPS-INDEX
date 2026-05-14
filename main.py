#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chip Index - SVG K线图版（无外部依赖，手机友好）
"""
import pandas as pd, numpy as np, requests, yaml, os, sys, json
from datetime import datetime, timedelta
from pathlib import Path


class IndexGenerator:
    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)
        self.stocks = self.config["stocks"]
        self.index_config = self.config["index"]
        self.output_dir = Path(self.config["output"]["dir"])

    def _load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
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
            "output":{"dir":"./output","start_date":"2024-01-01","end_date":None},
        }

    def fetch_stock_data(self, code, timeout=15):
        url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={}&scale=240&ma=no&datalen=1000".format(code)
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
            r.raise_for_status(); data = r.json()
            if not data: return
            df = pd.DataFrame(data).rename(columns={"day":"date","open":"open","high":"high","low":"low","close":"close","volume":"volume"})
            for c in ["open","high","low","close","volume"]: df[c] = pd.to_numeric(df[c], errors='coerce')
            df["code"]=code; df["amount"]=df["volume"]*df["close"]
            return df[["date","code","open","high","low","close","volume","amount"]]
        except Exception as e:
            print("  Fail {}: {}".format(code, e))

    def fetch_data(self, start_date=None, end_date=None):
        if not start_date: start_date = self.config["output"].get("start_date","2024-01-01")
        if not end_date: end_date = datetime.now().strftime("%Y-%m-%d")
        print("Fetching {} stocks...".format(len(self.stocks)))
        all_df = []
        for i,s in enumerate(self.stocks,1):
            print("  [{}/{}] {} ({})...".format(i,len(self.stocks),s['name'],s['code']))
            df = self.fetch_stock_data(s["code"])
            if df is not None and len(df)>0: df["name"]=s["name"]; all_df.append(df)
        if not all_df: return
        df = pd.concat(all_df, ignore_index=True)
        return df[(df["date"]>=start_date)&(df["date"]<=end_date)]

    def calculate_index(self, stocks_df):
        stocks_df = stocks_df.copy(); stocks_df["date"]=pd.to_datetime(stocks_df["date"])
        stocks_df = stocks_df.sort_values(["code","date"])
        d = stocks_df.groupby(stocks_df["date"].dt.strftime("%Y-%m-%d")).agg({"open":"mean","high":"mean","low":"mean","close":"mean"}).reset_index().rename(columns={"date":"ds"})
        if len(d)==0: return
        b = self.index_config["base_value"]
        d["index_value"] = (d["close"]/d["close"].iloc[0]*b).round(2)
        d["daily_return"] = (d["index_value"].pct_change(fill_method=None)*100).round(2)
        d["cumulative_return"] = ((d["index_value"]/b-1)*100).round(2)
        d.loc[0,["daily_return","cumulative_return"]] = 0.0
        s = b/d["close"].iloc[0]
        for c in ["open","high","low","close"]: d[c] = (d[c]*s).round(2)
        return d.rename(columns={"ds":"date"})

    def gen_html(self, df, title="AI CHIP INDEX"):
        """纯 SVG K 线图"""
        dates = df["date"].tolist()
        opens = df["open"].tolist()
        highs = df["high"].tolist()
        lows = df["low"].tolist()
        closes = df["close"].tolist()
        values = df["index_value"].tolist()
        crets = df["cumulative_return"].tolist()
        latest = df.iloc[-1]

        n = len(dates)
        if n == 0: return "<html><body>No data</body></html>"

        # 计算均线
        def sma(data, p):
            r = []; total = 0
            for i in range(len(data)):
                total += data[i]
                if i >= p: total -= data[i-p]
                r.append(round(total/min(p,i+1), 2) if i >= p-1 else None)
            return r
        ma5 = sma(closes, 5); ma50 = sma(closes, 50); ma100 = sma(closes, 100)

        # SVG 尺寸
        W=1400; H=700; pad=80; pw=W-2*pad; ph=H-2*pad
        minV=min(lows); maxV=max(highs); rng=maxV-minV or 1
        def ypos(v): return pad+ph-(v-minV)/rng*ph
        candle_w = max(2, min(12, pw//n-1))
        half_w = max(1, candle_w//2)

        # 生成 K 线 SVG
        candles_svg = ""
        for i in range(n):
            x = pad + i*pw//(n-1 if n>1 else 1)
            yo = ypos(opens[i]); yh = ypos(highs[i]); yl = ypos(lows[i]); yc = ypos(closes[i])
            color = "#ff4444" if opens[i] < closes[i] else "#00c853"
            candles_svg += '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1.5"/>'.format(x,yh,x,yl,color)
            candles_svg += '<rect x="{}" y="{}" width="{}" height="{}" fill="{}" rx="1"/>'.format(x-half_w,min(yo,yc),candle_w,abs(yc-yo)+1,color)

        # 叠加均线
        def line_svg(data, color, width):
            pts = []
            for i in range(n):
                if data[i] is None: continue
                x = pad + i*pw//(n-1 if n>1 else 1)
                pts.append("{},{}".format(x,ypos(data[i])))
            if pts: return '<polyline points="{}" fill="none" stroke="{}" stroke-width="{}"/>'.format(" ".join(pts),color,width)
            return ""

        # 网格线 + Y 轴标注
        grid_svg = ""
        def add_grid(y, label):
            nonlocal grid_svg
            v = minV + (1-y/ph)*rng if ph else 0
            yy = pad + y
            grid_svg += '<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="#333" stroke-width="0.5"/>'.format(pad,yy,pad+pw,yy)
            grid_svg += '<text x="{}" y="{}" fill="#888" font-size="11" text-anchor="end">{}</text>'.format(pad-5,yy+4,round(v,0))
        for i in range(5): add_grid(i*ph//4, "")

        # X 轴时间标注（每3个月标一次）
        x_ticks = ""
        for i in range(n):
            if i % 60 == 0 or i == n-1:
                x = pad + i*pw//(n-1 if n>1 else 1)
                x_ticks += '<text x="{}" y="{}" fill="#888" font-size="10" text-anchor="middle" transform="rotate(-30,{},{})">{}</text>'.format(x,H-10,x,H-10,dates[i])

        # 统计数字
        stat_html = ""
        items = [
            ("最新点位", str(latest["index_value"])),
            ("累计涨幅", str(latest["cumulative_return"]) + "%"),
            ("交易日", str(n)),
            ("起始", dates[0]),
        ]
        for label, val in items:
            stat_html += '<div class="stat"><div class="v">{}</div><div class="l">{}</div></div>'.format(val, label)

        # 成分股名字
        stock_names = "、".join([s["name"] for s in self.stocks])

        # 生成完整 HTML
        ma5_svg = line_svg(ma5, "#ffffff", 1.5)
        ma50_svg = line_svg(ma50, "#00ff00", 1.5)
        ma100_svg = line_svg(ma100, "#ff4444", 2)

        border_svg = '<rect x="{}" y="{}" width="{}" height="{}" fill="none" stroke="#555" stroke-width="1"/>'.format(pad,pad,pw,ph)

        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" style="width:100%;height:auto;max-width:{}px">{}{}{}{}{}</svg>'.format(W,H,W,grid_svg,border_svg,candles_svg,ma5_svg+ma50_svg+ma100_svg,x_ticks)

        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>""" + title + """</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f23;color:#e0e0e0;font-family:Arial,sans-serif;padding:10px}
h1{text-align:center;color:#00d4ff;font-size:20px;margin:10px 0;letter-spacing:2px}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;max-width:500px;margin-left:auto;margin-right:auto}
.stat{background:#1a1a3e;padding:12px;border-radius:8px;text-align:center}
.stat .v{font-size:22px;color:#00d4ff;font-weight:bold}
.stat .l{font-size:11px;color:#888;margin-top:3px}
.chart-wrap{background:#1a1a3e;border-radius:8px;padding:10px;overflow-x:auto}
.legend{text-align:center;margin:6px 0 10px;font-size:12px}
.legend span{display:inline-block;margin:0 8px;padding:2px 8px;border-radius:3px}
.info{text-align:center;margin:8px 0;font-size:11px;color:#666;line-height:1.6}
@media(min-width:768px){
  body{padding:20px 40px}
  h1{font-size:28px}
  .stats{grid-template-columns:1fr 1fr 1fr 1fr;max-width:none}
  .stat .v{font-size:28px}
}
</style>
</head>
<body>
<h1>""" + title + """</h1>
<div class="stats">""" + stat_html + """</div>
<div class="legend">
<span style="border-left:3px solid #fff">EMA5</span>
<span style="border-left:3px solid #0f0">MA50</span>
<span style="border-left:3px solid #f44">MA100</span>
<span style="background:#ff4444;color:#fff">阳线</span>
<span style="background:#00c853;color:#fff">阴线</span>
</div>
<div class="chart-wrap">""" + svg + """</div>
<div class="info">成分股（等权重）：""" + stock_names + """ | 更新：""" + datetime.now().strftime("%Y-%m-%d %H:%M") + """</div>
</body>
</html>"""

    def save(self, sdf, idf):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        sdf.to_csv(self.output_dir/"AI_CHIP_INDEX_stocks.csv",index=False,encoding="utf-8-sig")
        idf.to_csv(self.output_dir/"AI_CHIP_INDEX_detail.csv",index=False,encoding="utf-8-sig")
        idf[["date","index_value"]].to_csv(self.output_dir/"AI_CHIP_INDEX.csv",index=False,encoding="utf-8-sig")
        html = self.gen_html(idf)
        with open(self.output_dir/"AI_CHIP_INDEX_kline.html","w",encoding="utf-8") as f:
            f.write(html)
        print("Saved OK")

    def run(self):
        s = self.fetch_data()
        if s is None: print("No data"); return
        i = self.calculate_index(s)
        if i is None: print("Calc failed"); return
        self.save(s,i)
        print("Done! Latest: {:.2f}, Return: {:.2f}%".format(i["index_value"].iloc[-1],i["cumulative_return"].iloc[-1]))

if __name__=="__main__":
    g = IndexGenerator()
    if len(sys.argv)>1 and sys.argv[1]=="chart":
        s = pd.read_csv(g.output_dir/"AI_CHIP_INDEX_stocks.csv", encoding="utf-8-sig")
        g.save(s, g.calculate_index(s))
    else:
        g.run()