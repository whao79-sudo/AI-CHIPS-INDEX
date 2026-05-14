#!/usr/bin/env python3
import pandas as pd, numpy as np, requests, yaml, os, sys
from datetime import datetime
from pathlib import Path

class IndexGenerator:
    def __init__(self, cp="config.yaml"):
        self.cfg = self._load(cp)
        self.stocks = self.cfg["stocks"]
        self.out = Path(self.cfg["output"]["dir"])

    def _load(self, cp):
        if os.path.exists(cp):
            with open(cp, encoding="utf-8") as f: return yaml.safe_load(f)
        return {"stocks": [
            {"name":"中际旭创","code":"sz300308"},{"name":"新易盛","code":"sz300502"},
            {"name":"天孚通信","code":"sz300394"},{"name":"海光信息","code":"sh688041"},
            {"name":"寒武纪","code":"sh688256"},{"name":"龙芯中科","code":"sh688047"},
            {"name":"工业富联","code":"sh601138"},{"name":"浪潮信息","code":"sz000977"},
            {"name":"中科曙光","code":"sh603019"},{"name":"香农芯创","code":"sz300475"},
            {"name":"佰维存储","code":"sh688525"},{"name":"德明利","code":"sz001309"},
            {"name":"江波龙","code":"sz301308"},{"name":"兆易创新","code":"sh603986"}
        ],"index":{"base_date":"2024-01-02","base_value":1000},"output":{"dir":"./output","start_date":"2024-01-01","end_date":None}}

    def fetch_one(self, code, t=15):
        u = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={code}&scale=240&ma=no&datalen=1000"
        try:
            r = requests.get(u, timeout=t, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            d = r.json()
            if not d: return None
            df = pd.DataFrame(d).rename(columns={"day":"date","open":"open","high":"high","low":"low","close":"close","volume":"volume"})
            for c in ["open","high","low","close","volume"]: df[c] = pd.to_numeric(df[c], errors='coerce')
            df["code"] = code; df["amount"] = df["volume"] * df["close"]
            return df[["date","code","open","high","low","close","volume","amount"]]
        except Exception as e:
            print(f"  Fail {code}: {e}"); return None

    def fetch(self, sd=None, ed=None):
        if not sd: sd = self.cfg["output"].get("start_date","2024-01-01")
        if not ed: ed = datetime.now().strftime("%Y-%m-%d")
        print(f"Fetching {len(self.stocks)} stocks from {sd} to {ed}...")
        all_df = []
        for i, s in enumerate(self.stocks, 1):
            print(f"  [{i}/{len(self.stocks)}] {s['name']} ({s['code']})...", end=" ", flush=True)
            df = self.fetch_one(s["code"])
            if df is not None:
                df["name"] = s["name"]; all_df.append(df)
                print(f"{len(df)} rows")
            else:
                print("NO DATA")
        if not all_df: return None
        df = pd.concat(all_df, ignore_index=True)
        return df[(df["date"]>=sd) & (df["date"]<=ed)]

    def calc(self, df):
        df = df.copy(); df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["code","date"])
        d = df.groupby(df["date"].dt.strftime("%Y-%m-%d")).agg({"open":"mean","high":"mean","low":"mean","close":"mean"}).reset_index().rename(columns={"date":"ds"})
        if len(d)==0: return None
        b = self.cfg["index"]["base_value"]
        d["index_value"] = (d["close"]/d["close"].iloc[0]*b).round(2)
        d["daily_return"] = (d["index_value"].pct_change(fill_method=None)*100).round(2)
        d["cumulative_return"] = ((d["index_value"]/b-1)*100).round(2)
        d.loc[0,["daily_return","cumulative_return"]] = 0.0
        s = b/d["close"].iloc[0]
        for c in ["open","high","low","close"]: d[c] = (d[c]*s).round(2)
        return d.rename(columns={"ds":"date"})

    def gen_html(self, df, title="AI CHIP INDEX"):
        dates = df["date"].tolist()
        opens = df["open"].tolist()
        highs = df["high"].tolist()
        lows = df["low"].tolist()
        closes = df["close"].tolist()
        n = len(dates)

        # 技术指标
        def sma(data, p):
            return [sum(data[i-p+1:i+1])/p if i>=p-1 else None for i in range(len(data))]
        def ema(data, p):
            r = []; m = 2/(p+1); v = data[0] if data else 0
            for i in range(len(data)):
                if i<p-1: r.append(None)
                elif i==p-1: v=sum(data[:p])/p; r.append(v)
                else: v=(data[i]-v)*m+v; r.append(v)
            return r
        def hhv(data, p):
            return [max(data[i-p+1:i+1]) if i>=p-1 else None for i in range(len(data))]
        def llv(data, p):
            return [min(data[i-p+1:i+1]) if i>=p-1 else None for i in range(len(data))]
        def safe_div(a, b):
            return (a+b)/2 if a is not None and b is not None else None

        # 云层
        h9, l9 = hhv(highs,9), llv(lows,9)
        h26, l26 = hhv(highs,26), llv(lows,26)
        h52, l52 = hhv(highs,52), llv(lows,52)
        tenkan = [safe_div(h9[i], l9[i]) for i in range(n)]
        kijun = [safe_div(h26[i], l26[i]) for i in range(n)]
        senkouA = [safe_div(tenkan[i], kijun[i]) for i in range(n)]
        senkouB = [safe_div(h52[i], l52[i]) for i in range(n)]

        # 均线
        ema5 = ema(closes,5)
        ma50 = sma(closes,50)
        ma100 = sma(closes,100)

        # 交差信号
        sig = []
        for i in range(1, n):
            if all(x is not None for x in [senkouA[i],senkouB[i],senkouA[i-1],senkouB[i-1]]):
                if senkouA[i-1]<=senkouB[i-1] and senkouA[i]>senkouB[i]:
                    sig.append({"x":dates[i],"y":highs[i]*1.002,"t":"buy"})
                if senkouB[i-1]<=senkouA[i-1] and senkouB[i]>senkouA[i]:
                    sig.append({"x":dates[i],"y":lows[i]*0.998,"t":"sell"})

        # 构建 trace
        tr = []
        tr.append(f'{{x:{dates},close:{closes},open:{opens},high:{highs},low:{lows},type:"candlestick",name:"K线",increasing:{{line:{{color:"#FF0000"}}}},decreasing:{{line:{{color:"#00FF00"}}}}}}')
        tr.append(f'{{x:{dates},y:{senkouA},mode:"lines",name:"云A",line:{{color:"#2F4F4F"}}}}')
        tr.append(f'{{x:{dates},y:{senkouB},mode:"lines",name:"云B",line:{{color:"#8B4513"}}}}')
        tr.append(f'{{x:{dates},y:{ema5},mode:"lines",name:"EMA5",line:{{color:"#FFFFFF"}}}}')
        tr.append(f'{{x:{dates},y:{ma50},mode:"lines",name:"MA50",line:{{color:"#00FF00"}}}}')
        tr.append(f'{{x:{dates},y:{ma100},mode:"lines",name:"MA100",line:{{color:"#FF0000",width:2}}}}')
        for s in sig:
            nm = "金叉" if s["t"]=="buy" else "死叉"
            sy = "triangle-up" if s["t"]=="buy" else "triangle-down"
            cl = "#FF0000" if s["t"]=="buy" else "#00FF00"
            tr.append(f'{{x:[{s["x"]}],y:[{s["y"]}],mode:"markers",type:"scatter",name:"{nm}",marker:{{symbol:"{sy}",size:15,color:"{cl}"}}}}')

        r = f'{df["index_value"].iloc[-1]:.2f}'
        cr = f'{df["cumulative_return"].iloc[-1]:.2f}%'
        st = dates[0]
        return f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>{title}</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>body{{font-family:Arial,sans-serif;background:#1a1a2e;color:#eee;margin:0;padding:20px}}
h1{{text-align:center;color:#00d4ff}}#chart{{width:100%;height:700px;background:#16213e;border-radius:10px}}
.s{{display:flex;justify-content:space-around;margin:20px 0}}
.st{{background:#16213e;padding:15px;border-radius:8px;text-align:center}}
.v{{font-size:24px;color:#00d4ff}}.l{{font-size:12px;color:#888}}</style></head><body>
<div class="s"><div class="st"><div class="v">{r}</div><div class="l">最新点位</div></div>
<div class="st"><div class="v">{cr}</div><div class="l">累计涨幅</div></div>
<div class="st"><div class="v">{n}</div><div class="l">交易日</div></div>
<div class="st"><div class="v">{st}</div><div class="l">起始日期</div></div></div>
<div id="chart"></div><script>
Plotly.newPlot("chart",[{",".join(tr)}],{{title:"{title}",plot_bgcolor:"#16213e",paper_bgcolor:"#16213e",font:{{color:"#eee"}},xaxis:{{title:"日期",gridcolor:"#333",tickangle:-45}},yaxis:{{title:"指数点位",gridcolor:"#333"}},legend:{{bgcolor:"rgba(0,0,0,0.5)"}}}},{{responsive:true,displayModeBar:true}});
</script></body></html>'''

    def save(self, sdf, idf):
        self.out.mkdir(parents=True, exist_ok=True)
        sdf.to_csv(self.out/"AI_CHIP_INDEX_stocks.csv", index=False, encoding="utf-8-sig")
        idf.to_csv(self.out/"AI_CHIP_INDEX_detail.csv", index=False, encoding="utf-8-sig")
        idf[["date","index_value"]].to_csv(self.out/"AI_CHIP_INDEX.csv", index=False, encoding="utf-8-sig")
        with open(self.out/"AI_CHIP_INDEX_kline.html","w",encoding="utf-8") as f:
            f.write(self.gen_html(idf))
        print("Saved all files.")

    def run(self):
        s = self.fetch()
        if s is None: print("No data fetched!"); return
        i = self.calc(s)
        if i is None: print("Index calculation failed!"); return
        self.save(s, i)
        print(f"Done! Latest: {i['index_value'].iloc[-1]:.2f}, Return: {i['cumulative_return'].iloc[-1]:.2f}%")

if __name__ == "__main__":
    g = IndexGenerator()
    if len(sys.argv)>1 and sys.argv[1]=="chart":
        s = pd.read_csv(g.out/"AI_CHIP_INDEX_stocks.csv", encoding="utf-8-sig")
        g.save(s, g.calc(s))
    else:
        g.run()