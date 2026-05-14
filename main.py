#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chip Index Generator - 纯内嵌折线图版（无需CDN）
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
            "output":{"dir":"./output","start_date":"2026-01-01","end_date":None},
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
        datas = json.dumps([{"d":r["date"],"v":r["index_value"],"o":r["open"],"h":r["high"],"l":r["low"],"c":r["close"],"r":r["cumulative_return"]} for _,r in df.iterrows()])
        latest = df.iloc[-1]
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>""" + title + """</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f23;color:#e0e0e0;font-family:Arial,sans-serif;padding:10px}
h1{text-align:center;color:#00d4ff;font-size:20px;margin:10px 0}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
.stat{background:#1a1a3e;padding:12px;border-radius:8px;text-align:center}
.stat .v{font-size:22px;color:#00d4ff;font-weight:bold}
.stat .l{font-size:11px;color:#888;margin-top:3px}
#chart{background:#1a1a3e;border-radius:8px;width:100%;height:400px;position:relative;overflow:hidden}
canvas{width:100%;height:100%}
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
<div id="chart"><canvas id="cv"></canvas></div>
<div class="info">成分股：中际旭创、新易盛、天孚通信、海光信息、寒武纪、龙芯中科、工业富联、浪潮信息、中科曙光、香农芯创、佰维存储、德明利、江波龙、兆易创新 | 等权重</div>
<script>
(function(){
var data=""" + datas + """;
var c=document.getElementById("cv");
var p=c.getContext("2d");
function resize(){
  var rect=c.parentElement.getBoundingClientRect();
  c.width=rect.width*window.devicePixelRatio||1;
  c.height=rect.height*window.devicePixelRatio||1;
  c.style.width=rect.width+"px";
  c.style.height=rect.height+"px";
  draw();
}
function draw(){
  var W=c.width,H=c.height,dpr=window.devicePixelRatio||1;
  p.clearRect(0,0,W,H);
  if(data.length<2) return;
  pad=60*dpr; pw=W-pad*2; ph=H-pad*2;
  var vs=data.map(function(x){return x.v});
  var minV=Math.min.apply(null,vs),maxV=Math.max.apply(null,vs),rangeV=maxV-minV||1;
  var lastV=vs[vs.length-1];
  p.strokeStyle="#333"; p.lineWidth=1*dpr;
  p.beginPath(); p.moveTo(pad,pad); p.lineTo(pad,pad+ph); p.lineTo(pad+pw,pad+ph); p.stroke();
  var ys=[minV,minV+rangeV*0.25,minV+rangeV*0.5,minV+rangeV*0.75,maxV];
  p.fillStyle="#666"; p.font=Math.round(11*dpr)+"px Arial"; p.textAlign="right";
  ys.forEach(function(y){
    var yy=pad+ph-(y-minV)/rangeV*ph;
    p.strokeStyle="#222"; p.beginPath(); p.moveTo(pad,yy); p.lineTo(pad+pw,yy); p.stroke();
    p.fillStyle="#888"; p.fillText(Math.round(y),pad-5*dpr,yy+4*dpr);
  });
  var colors=["#ff4444","#00c853"];
  p.lineWidth=2*dpr;
  data.forEach(function(pt,i){
    var x=pad+i/(data.length-1)*pw;
    var y=pad+ph-(pt.v-minV)/rangeV*ph;
    if(i==0){p.beginPath();p.moveTo(x,y)}else{p.lineTo(x,y)}
  });
  var grad=p.createLinearGradient(0,pad,0,pad+ph);
  grad.addColorStop(0,"rgba(0,212,255,0.4)");
  grad.addColorStop(1,"rgba(0,212,255,0.02)");
  p.strokeStyle="#00d4ff"; p.stroke();
  data.forEach(function(pt,i){
    var x=pad+i/(data.length-1)*pw;
    var y=pad+ph-(pt.v-minV)/rangeV*ph;
    if(i==data.length-1){
      p.beginPath(); p.arc(x,y,4*dpr,0,Math.PI*2); p.fillStyle="#00d4ff"; p.fill();
      p.fillStyle="#fff"; p.textAlign="left"; p.font="bold "+(12*dpr)+"px Arial";
      p.fillText(pt.v,x+8*dpr,y+4*dpr);
    }
  });
}
window.addEventListener("resize",resize);
setTimeout(function(){
  resize();
  // 美化：鼠标移动显示值
  var container=c.parentElement;
  container.addEventListener("mousemove",function(e){
    var rect=container.getBoundingClientRect();
    var mx=e.clientX-rect.left,mw=rect.width;
    var idx=Math.round((mx-pad/pw)*(data.length-1));
    idx=Math.max(0,Math.min(data.length-1,idx));
    if(rect.width==0)return;
    var pt=data[idx];
    c.style.cursor="pointer";
    draw();
    var x=pad+idx/(data.length-1)*pw;
    var minV2=Math.min.apply(null,data.map(function(x){return x.v}));
    var maxV2=Math.max.apply(null,data.map(function(x){return x.v}));
    var rangeV2=maxV2-minV2||1;
    var y=pad+ph-(pt.v-minV2)/rangeV2*ph;
    p.strokeStyle="rgba(255,255,255,0.2)";
    p.beginPath(); p.moveTo(x,pad); p.lineTo(x,pad+ph); p.stroke();
    p.fillStyle="rgba(0,0,0,0.7)";
    p.fillRect(x+8*dpr,y-20*dpr,160*dpr,50*dpr);
    p.fillStyle="#fff"; p.font=(11*dpr)+"px Arial"; p.textAlign="left";
    p.fillText("日期:"+pt.d,x+12*dpr,y-4*dpr);
    p.fillText("指数:"+pt.v,x+12*dpr,y+12*dpr);
    p.fillText("涨幅:"+pt.r+"%",x+12*dpr,y+28*dpr);
  });
  container.addEventListener("mouseleave",function(){draw();});
},100);
})();
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