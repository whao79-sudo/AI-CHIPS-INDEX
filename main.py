#!/usr/bin/env python3
import pandas as pd, numpy as np, requests, yaml, os, sys
from datetime import datetime
from pathlib import Path

class IndexGenerator:
    def __init__(self, cp="config.yaml"):
        self.cfg=self._load(cp); self.stocks=self.cfg["stocks"]
        self.out=Path(self.cfg["output"]["dir"])
    def _load(self,cp):
        if os.path.exists(cp):
            with open(cp,encoding="utf-8") as f: return yaml.safe_load(f)
        return {"stocks":[{"name":"中际旭创","code":"sz300308"},{"name":"新易盛","code":"sz300502"},{"name":"天孚通信","code":"sz300394"},{"name":"海光信息","code":"sh688041"},{"name":"寒武纪","code":"sh688256"},{"name":"龙芯中科","code":"sh688047"},{"name":"工业富联","code":"sh601138"},{"name":"浪潮信息","code":"sz000977"},{"name":"中科曙光","code":"sh603019"},{"name":"香农芯创","code":"sz300475"},{"name":"佰维存储","code":"sh688525"},{"name":"德明利","code":"sz001309"},{"name":"江波龙","code":"sz301308"},{"name":"兆易创新","code":"sh603986"}],"index":{"base_date":"2024-01-02","base_value":1000},"output":{"dir":"./output","start_date":"2024-01-01","end_date":None}}

    def fetch_one(self,code,t=15):
        u=f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={code}&scale=240&ma=no&datalen=1000"
        try:
            r=requests.get(u,timeout=t,headers={"User-Agent":"Mozilla/5.0"}); r.raise_for_status(); d=r.json()
            if not d: return None
            df=pd.DataFrame(d).rename(columns={"day":"date","open":"open","high":"high","low":"low","close":"close","volume":"volume"})
            for c in ["open","high","low","close","volume"]: df[c]=pd.to_numeric(df[c],errors='coerce')
            df["code"]=code; df["amount"]=df["volume"]*df["close"]
            return df[["date","code","open","high","low","close","volume","amount"]]
        except: print(f"Fail: {code}"); return None

    def fetch(self,sd=None,ed=None):
        if not sd: sd=self.cfg["output"].get("start_date","2024-01-01")
        if not ed: ed=datetime.now().strftime("%Y-%m-%d")
        all_df=[self.fetch_one(s["code"]) for s in self.stocks]
        all_df=[d for d in all_df if d is not None]
        if not all_df: return None
        df=pd.concat(all_df,ignore_index=True)
        return df[(df["date"]>=sd)&(df["date"]<=ed)]

    def calc(self,df):
        df=df.copy(); df["date"]=pd.to_datetime(df["date"]); df=df.sort_values(["code","date"])
        d=df.groupby(df["date"].dt.strftime("%Y-%m-%d")).agg({"open":"mean","high":"mean","low":"mean","close":"mean"}).reset_index().rename(columns={"date":"ds"})
        if len(d)==0: return None
        b=self.cfg["index"]["base_value"]
        d["index_value"]=(d["close"]/d["close"].iloc[0]*b).round(2)
        d["daily_return"]=(d["index_value"].pct_change(fill_method=None)*100).round(2)
        d["cumulative_return"]=((d["index_value"]/b-1)*100).round(2)
        d.loc[0,["daily_return","cumulative_return"]]=0
        s=b/d["close"].iloc[0]
        for c in ["open","high","low","close"]: d[c]=(d[c]*s).round(2)
        return d.rename(columns={"ds":"date"})

    def gen_html(self,df,t="AI CHIP INDEX"):
        d=df["date"].tolist(); o=df["open"].tolist(); h=df["high"].tolist(); l=df["low"].tolist(); c=df["close"].tolist()
        def sma(d,p): return [sum(d[i-p+1:i+1])/p if i>=p-1 else None for i in range(len(d))]
        def ema(d,p):
            r=[]; m=2/(p+1); v=d[0]
            for i in range(len(d)):
                if i<p-1: r.append(None)
                elif i==p-1: v=sum(d[:p])/p; r.append(v)
                else: v=(d[i]-v)*m+v; r.append(v)
            return r
        def hhv(d,p): return [max(d[i-p+1:i+1]) if i>=p-1 else None for i in range(len(d))]
        def llv(d,p): return [min(d[i-p+1:i+1]) if i>=p-1 else None for i in range(len(d))]
        h9,h26,h52=hhv(h,9),hhv(h,26),hhv(h,52); l9,l26,l52=llv(l,9),llv(l,26),llv(l,52)
        skA=[(a+b)/2 if a and b else None for a,b in zip([(x+y)/2 for x,y in zip(h9,l9)],[(x+y)/2 for x,y in zip(h26,l26)])]
        skB=[(x+y)/2 if x and y else None for x,y in zip(h52,l52)]
        em5=ema(c,5); m50=sma(c,50); m100=sma(c,100)
        sig=[]
        for i in range(1,len(skA)):
            if all([skA[i],skB[i],skA[i-1],skB[i-1]]):
                if skA[i-1]<=skB[i-1]and skA[i]>skB[i]: sig.append({"x":d[i],"y":h[i]*1.002,"t":"buy"})
                if skB[i-1]<=skA[i-1]and skB[i]>skA[i]: sig.append({"x":d[i],"y":l[i]*0.998,"t":"sell"})
        r=f'{df["index_value"].iloc[-1]:.2f}'; cr=f'{df["cumulative_return"].iloc[-1]:.2f}%'; n=len(df); st=d[0]
        tr=[f'{{x:{d},close:{c},open:{o},high:{h},low:{l},type:"candlestick",name:"K线",increasing:{{line:{{color:"#FF0000"}}}},decreasing:{{line:{{color:"#00FF00"}}}}}}',
            f'{{x:{d},y:{skA},mode:"lines",name:"云A",line:{{color:"#2F4F4F"}}}}',
            f'{{x:{d},y:{skB},mode:"lines",name:"云B",line:{{color:"#8B4513"}}}}',
            f'{{x:{d},y:{em5},mode:"lines",name:"EMA5",line:{{color:"#FFF"}}}}',
            f'{{x:{d},y:{m50},mode:"lines",name:"MA50",line:{{color:"#0F0"}}}}',
            f'{{x:{d},y:{m100},mode:"lines",name:"MA100",line:{{color:"#F00",width:2}}}}']
        for s in sig:
            tr.append(f'{{x:[{s["x"]}],y:[{s["y"]}],mode:"markers",type:"scatter",name:{"金叉" if s["t"]=="buy" else "死叉"},marker:{{symbol:{"triangle-up" if s["t"]=="buy" else "triangle-down"},size:15,color:{"#F00" if s["t"]=="buy" else "#0F0"}}}}}')
        return f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>{t}</title>
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
Plotly.newPlot("chart",[{",".join(tr)}],{{title:"{t}",plot_bgcolor:"#16213e",paper_bgcolor:"#16213e",font:{{color:"#eee"}},xaxis:{{title:"日期",gridcolor:"#333",tickangle:-45}},yaxis:{{title:"指数点位",gridcolor:"#333"}},legend:{{bgcolor:"rgba(0,0,0,0.5)"}}}},{{responsive:true,displayModeBar:true}});
</script></body></html>'''

    def save(self,sdf,idf):
        self.out.mkdir(parents=True,exist_ok=True)
        sdf.to_csv(self.out/"AI_CHIP_INDEX_stocks.csv",index=False,encoding="utf-8-sig")
        idf.to_csv(self.out/"AI_CHIP_INDEX_detail.csv",index=False,encoding="utf-8-sig")
        idf[["date","index_value"]].to_csv(self.out/"AI_CHIP_INDEX.csv",index=False,encoding="utf-8-sig")
        with open(self.out/"AI_CHIP_INDEX_kline.html","w",encoding="utf-8") as f: f.write(self.gen_html(idf))
        print("Saved.")

    def run(self):
        s=self.fetch(); i=self.calc(s)
        if i is not None: self.save(s,i); print(f"Done. Latest: {i['index_value'].iloc[-1]:.2f}, {i['cumulative_return'].iloc[-1]:.2f}%")

if __name__=="__main__":
    g=IndexGenerator()
    if len(sys.argv)>1 and sys.argv[1]=="chart":
        s=pd.read_csv(g.out/"AI_CHIP_INDEX_stocks.csv",encoding="utf-8-sig")
        g.save(s,g.calc(s))
    else: g.run()