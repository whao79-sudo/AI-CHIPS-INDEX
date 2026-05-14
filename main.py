#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chip Index - Chart.js K线图版
"""
import pandas as pd, numpy as np, requests, yaml, os, sys, json
from datetime import datetime
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
            if not data: return None
            df = pd.DataFrame(data).rename(columns={"day":"date","open":"open","high":"high","low":"low","close":"close","volume":"volume"})
            for c in ["open","high","low","close","volume"]: df[c] = pd.to_numeric(df[c], errors='coerce')
            df["code"]=code; df["amount"]=df["volume"]*df["close"]
            return df[["date","code","open","high","low","close","volume","amount"]]
        except Exception as e:
            print("Fail {}: {}".format(code, e)); return None

    def fetch_data(self, start_date=None, end_date=None):
        if not start_date: start_date = self.config["output"].get("start_date","2024-01-01")
        if not end_date: end_date = datetime.now().strftime("%Y-%m-%d")
        print("Fetching {} stocks...".format(len(self.stocks)))
        all_df = []
        for i,s in enumerate(self.stocks,1):
            print("  [{}/{}] {} ({})...".format(i,len(self.stocks),s['name'],s['code']))
            df = self.fetch_stock_data(s["code"])
            if df is not None and len(df)>0: df["name"]=s["name"]; all_df.append(df)
        if not all_df: return None
        df = pd.concat(all_df, ignore_index=True)
        return df[(df["date"]>=start_date)&(df["date"]<=end_date)]

    def calculate_index(self, stocks_df):
        stocks_df = stocks_df.copy(); stocks_df["date"]=pd.to_datetime(stocks_df["date"])
        stocks_df = stocks_df.sort_values(["code","date"])
        d = stocks_df.groupby(stocks_df["date"].dt.strftime("%Y-%m-%d")).agg({"open":"mean","high":"mean","low":"mean","close":"mean"}).reset_index().rename(columns={"date":"ds"})
        if len(d)==0: return None
        b = self.index_config["base_value"]
        d["index_value"] = (d["close"]/d["close"].iloc[0]*b).round(2)
        d["daily_return"] = (d["index_value"].pct_change(fill_method=None)*100).round(2)
        d["cumulative_return"] = ((d["index_value"]/b-1)*100).round(2)
        d.loc[0,["daily_return","cumulative_return"]] = 0.0
        s = b/d["close"].iloc[0]
        for c in ["open","high","low","close"]: d[c] = (d[c]*s).round(2)
        return d.rename(columns={"ds":"date"})

    def gen_html(self, df, title="AI CHIP INDEX"):
        def ema(data, period):
            result = []; m = 2/(period+1); ema_val = data[0]
            for i in range(len(data)):
                if i < period-1: result.append(None)
                elif i == period-1:
                    ema_val = sum(data[:period])/period; result.append(round(ema_val,2))
                else:
                    ema_val = (data[i]-ema_val)*m+ema_val; result.append(round(ema_val,2))
            return result
        def sma(data, period):
            result = []
            for i in range(len(data)):
                if i < period-1: result.append(None)
                else: result.append(round(sum(data[i-period+1:i+1])/period,2))
            return result

        closes = [float(x) for x in df["close"]]
        dates = [str(x) for x in df["date"]]
        opens = [float(x) for x in df["open"]]
        highs = [float(x) for x in df["high"]]
        lows = [float(x) for x in df["low"]]
        values = [float(x) for x in df["index_value"]]
        cret = [float(x) for x in df["cumulative_return"]]

        c5 = ema(closes,5)
        c50 = sma(closes,50)
        c100 = sma(closes,100)
        latest = df.iloc[-1]

        dj = json.dumps({"dates":dates,"o":opens,"h":highs,"l":lows,"c":closes,"v":values,"r":cret,"ma5":c5,"ma50":c50,"ma100":c100})

        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>""" + title + """</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-chart-financial@0.1.0/dist/chartjs-chart-financial.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f23;color:#e0e0e0;font-family:Arial,sans-serif;padding:10px}
h1{text-align:center;color:#00d4ff;font-size:20px;margin:10px 0}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
.stat{background:#1a1a3e;padding:12px;border-radius:8px;text-align:center}
.stat .v{font-size:22px;color:#00d4ff;font-weight:bold}
.stat .l{font-size:11px;color:#888;margin-top:3px}
#chart-wrap{background:#1a1a3e;border-radius:8px;padding:10px;margin-bottom:10px}
#chart{width:100%;height:500px}
.info{text-align:center;margin-top:8px;font-size:11px;color:#666}
</style>
</head>
<body>
<h1>""" + title + """</h1>
<div class="stats">
<div class="stat"><div class="v">""" + str(latest["index_value"]) + """</div><div class="l">最新点位</div></div>
<div class="stat"><div class="v">""" + str(latest["cumulative_return"]) + """%</div><div class="l">累计涨幅</div></div>
<div class="stat"><div class="v">""" + str(len(df)) + """</div><div class="l">交易日</div></div>
<div class="stat"><div class="v">""" + df["date"].iloc[0] + """</div><div class="l">起始日期</div></div>
</div>
<div id="chart-wrap"><div id="chart"><canvas id="cv"></canvas></div></div>
<div class="info">成分股：中际旭创、新易盛、天孚通信、海光信息、寒武纪、龙芯中科、工业富联、浪潮信息、中科曙光、香农芯创、佰维存储、德明利、江波龙、兆易创新 | 等权重 | """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</div>
<script>
var DATA=""" + dj + """;
var d=DATA.dates.map(function(x,i){return{x:x,o:DATA.o[i],h:DATA.h[i],l:DATA.l[i],c:DATA.c[i]}});
var ctx=document.getElementById("cv").getContext("2d");
var chart=new Chart(ctx,{
type:"candlestick",
data:{
  datasets:[
    {label:"K线",data:d,color:{up:"#ff4444",down:"#00c853",unchanged:"#888"},borderColor:{up:"#ff4444",down:"#00c853",unchanged:"#888"},bar:{_data:null}},
  ]
},
options:{
  responsive:true,maintainAspectRatio:false,
  parsing:{xAxisKey:"x",yAxisKey:"c"},
  scales:{
    x:{type:"time",time:{parser:"yyyy-MM-dd",tooltipFormat:"yyyy-MM-dd",unit:"month"},ticks:{color:"#888"},grid:{color:"#222"},adapters:{date:{}}},
    y:{beginAtZero:false,ticks:{color:"#888"},grid:{color:"#222"}}
  },
  plugins:{
    legend:{labels:{color:"#ddd"}},
    tooltip:{enabled:true,mode:"index",intersect:false}
  }
}
});
// 等 chartjs-chart-financial 注册后加均线
setTimeout(function(){
  var cData=chart.data;
  cData.datasets.push({label:"EMA5",data:DATA.dates.map(function(x,i){return{x:x,y:DATA.ma5[i]}}),type:"line",borderColor:"#fff",pointRadius:0,borderWidth:1.5,fill:false});
  cData.datasets.push({label:"MA50",data:DATA.dates.map(function(x,i){return{x:x,y:DATA.ma50[i]}}),type:"line",borderColor:"#00ff00",pointRadius:0,borderWidth:1.5,fill:false});
  cData.datasets.push({label:"MA100",data:DATA.dates.map(function(x,i){return{x:x,y:DATA.ma100[i]}}),type:"line",borderColor:"#ff4444",pointRadius:0,borderWidth:2,fill:false});
  chart.update();
},500);
</script>
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