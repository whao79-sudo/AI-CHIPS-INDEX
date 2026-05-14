#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Chip Index Generator - Standalone Version
"""

import pandas as pd
import numpy as np
import requests
import yaml
import os
import sys
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
                {"name": "中际旭创", "code": "sz300308"},
                {"name": "新易盛", "code": "sz300502"},
                {"name": "天孚通信", "code": "sz300394"},
                {"name": "海光信息", "code": "sh688041"},
                {"name": "寒武纪", "code": "sh688256"},
                {"name": "龙芯中科", "code": "sh688047"},
                {"name": "工业富联", "code": "sh601138"},
                {"name": "浪潮信息", "code": "sz000977"},
                {"name": "中科曙光", "code": "sh603019"},
                {"name": "香农芯创", "code": "sz300475"},
                {"name": "佰维存储", "code": "sh688525"},
                {"name": "德明利", "code": "sz001309"},
                {"name": "江波龙", "code": "sz301308"},
                {"name": "兆易创新", "code": "sh603986"},
            ],
            "index": {"base_date": "2024-01-02", "base_value": 1000.0},
            "output": {"dir": "./output", "start_date": "2024-01-01", "end_date": None},
        }

    def fetch_stock_data(self, code, timeout=15):
        url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={}&scale=240&ma=no&datalen=1000".format(code)
        try:
            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            })
            response.raise_for_status()
            data = response.json()
            if not data:
                return None
            df = pd.DataFrame(data)
            df = df.rename(columns={
                "day": "date", "open": "open", "high": "high",
                "low": "low", "close": "close", "volume": "volume"
            })
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df["code"] = code
            df["amount"] = df["volume"] * df["close"]
            return df[["date", "code", "open", "high", "low", "close", "volume", "amount"]]
        except Exception as e:
            print("Fail {}: {}".format(code, e))
            return None

    def fetch_data(self, start_date=None, end_date=None):
        print("Fetching {} stocks...".format(len(self.stocks)))
        if start_date is None:
            start_date = self.config["output"].get("start_date", "2024-01-01")
        if end_date is None:
            end_date = self.config["output"].get("end_date")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        all_stocks_df = []
        for i, stock in enumerate(self.stocks, 1):
            print("  [{}/{}] {} ({})...".format(i, len(self.stocks), stock['name'], stock['code']), end=" ", flush=True)
            df = self.fetch_stock_data(stock["code"])
            if df is not None and len(df) > 0:
                df["name"] = stock["name"]
                all_stocks_df.append(df)
                print("OK {} rows".format(len(df)))
            else:
                print("NO DATA")

        if not all_stocks_df:
            return None

        stocks_df = pd.concat(all_stocks_df, ignore_index=True)
        stocks_df = stocks_df[(stocks_df["date"] >= start_date) & (stocks_df["date"] <= end_date)]
        print("Total: {} rows".format(len(stocks_df)))
        return stocks_df

    def calculate_index(self, stocks_df):
        print("Calculating index...")
        stocks_df = stocks_df.copy()
        stocks_df["date"] = pd.to_datetime(stocks_df["date"])
        stocks_df = stocks_df.sort_values(["code", "date"])

        daily_ohlc = stocks_df.groupby(stocks_df["date"].dt.strftime("%Y-%m-%d")).agg({
            "open": "mean", "high": "mean", "low": "mean", "close": "mean"
        }).reset_index()
        daily_ohlc.rename(columns={"date": "date_str"}, inplace=True)

        if len(daily_ohlc) == 0:
            return None

        base_close = daily_ohlc["close"].iloc[0]
        base_value = self.index_config["base_value"]
        daily_ohlc["index_value"] = (daily_ohlc["close"] / base_close * base_value).round(2)
        daily_ohlc["daily_return"] = (daily_ohlc["index_value"].pct_change(fill_method=None) * 100).round(2)
        daily_ohlc["cumulative_return"] = ((daily_ohlc["index_value"] / base_value - 1) * 100).round(2)
        daily_ohlc.loc[0, "daily_return"] = 0.0
        daily_ohlc.loc[0, "cumulative_return"] = 0.0

        scale = base_value / daily_ohlc["close"].iloc[0]
        daily_ohlc["open"] = (daily_ohlc["open"] * scale).round(2)
        daily_ohlc["high"] = (daily_ohlc["high"] * scale).round(2)
        daily_ohlc["low"] = (daily_ohlc["low"] * scale).round(2)
        daily_ohlc["close"] = (daily_ohlc["close"] * scale).round(2)

        return daily_ohlc.rename(columns={"date_str": "date"})

    def generate_kline_html(self, df, title="AI CHIP INDEX"):
        dates = df["date"].tolist()
        opens = df["open"].tolist()
        highs = df["high"].tolist()
        lows = df["low"].tolist()
        closes = df["close"].tolist()

        def sma(data, period):
            result = []
            for i in range(len(data)):
                if i < period - 1:
                    result.append(None)
                else:
                    result.append(sum(data[i-period+1:i+1]) / period)
            return result

        def ema(data, period):
            result = []
            multiplier = 2 / (period + 1)
            ema_val = data[0]
            for i in range(len(data)):
                if i < period - 1:
                    result.append(None)
                elif i == period - 1:
                    ema_val = sum(data[:period]) / period
                    result.append(ema_val)
                else:
                    ema_val = (data[i] - ema_val) * multiplier + ema_val
                    result.append(ema_val)
            return result

        def hhv(data, period):
            result = []
            for i in range(len(data)):
                if i < period - 1:
                    result.append(None)
                else:
                    result.append(max(data[i-period+1:i+1]))
            return result

        def llv(data, period):
            result = []
            for i in range(len(data)):
                if i < period - 1:
                    result.append(None)
                else:
                    result.append(min(data[i-period+1:i+1]))
            return result

        high9 = hhv(highs, 9); low9 = llv(lows, 9)
        high26 = hhv(highs, 26); low26 = llv(lows, 26)
        high52 = hhv(highs, 52); low52 = llv(lows, 52)

        tenkan = [(h + l) / 2 if h is not None and l is not None else None for h, l in zip(high9, low9)]
        kijun = [(h + l) / 2 if h is not None and l is not None else None for h, l in zip(high26, low26)]
        senkouA = [(t + k) / 2 if t is not None and k is not None else None for t, k in zip(tenkan, kijun)]
        senkouB = [(h + l) / 2 if h is not None and l is not None else None for h, l in zip(high52, low52)]

        ma20 = sma(closes, 20)
        ma300 = sma(closes, 300)
        ema5 = ema(closes, 5)
        ma50 = sma(closes, 50)
        ma100 = sma(closes, 100)

        crossSignals = []
        for i in range(1, len(senkouA)):
            if senkouA[i] and senkouB[i] and senkouA[i-1] and senkouB[i-1]:
                if senkouA[i-1] <= senkouB[i-1] and senkouA[i] > senkouB[i]:
                    crossSignals.append({"x": dates[i], "y": highs[i] * 1.002, "type": "buy"})
                if senkouB[i-1] <= senkouA[i-1] and senkouB[i] > senkouA[i]:
                    crossSignals.append({"x": dates[i], "y": lows[i] * 0.998, "type": "sell"})

        # 用 JSON 格式传递数据，避免 JavaScript 转义问题
        import json
        dates_json = json.dumps(dates)
        opens_json = json.dumps(opens)
        highs_json = json.dumps(highs)
        lows_json = json.dumps(lows)
        closes_json = json.dumps(closes)
        senkouA_json = json.dumps(senkouA)
        senkouB_json = json.dumps(senkouB)
        ema5_json = json.dumps(ema5)
        ma50_json = json.dumps(ma50)
        ma100_json = json.dumps(ma100)
        sig_json = json.dumps(crossSignals)

        latest_close = df["index_value"].iloc[-1]
        cum_return = df["cumulative_return"].iloc[-1]
        num_days = len(df)
        start_date = dates[0]

        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>""" + title + """</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a2e; color: #eee; margin: 0; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { text-align: center; color: #00d4ff; }
        #chart { width: 100%; height: 700px; background: #16213e; border-radius: 10px; }
        .stats { display: flex; justify-content: space-around; margin: 20px 0; }
        .stat { background: #16213e; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 24px; color: #00d4ff; }
        .stat-label { font-size: 12px; color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI CHIP INDEX</h1>
        <div class="stats">
            <div class="stat"><div class="stat-value">""" + str(latest_close) + """</div><div class="stat-label">最新点位</div></div>
            <div class="stat"><div class="stat-value">""" + str(cum_return) + """%</div><div class="stat-label">累计涨幅</div></div>
            <div class="stat"><div class="stat-value">""" + str(num_days) + """</div><div class="stat-label">交易日</div></div>
            <div class="stat"><div class="stat-value">""" + start_date + """</div><div class="stat-label">起始日期</div></div>
        </div>
        <div id="chart"></div>
    </div>
    <script>
        var dates = """ + dates_json + """;
        var opens = """ + opens_json + """;
        var highs = """ + highs_json + """;
        var lows = """ + lows_json + """;
        var closes = """ + closes_json + """;
        var senkouA = """ + senkouA_json + """;
        var senkouB = """ + senkouB_json + """;
        var ema5 = """ + ema5_json + """;
        var ma50 = """ + ma50_json + """;
        var ma100 = """ + ma100_json + """;
        var sig = """ + sig_json + """;

        var traces = [
            {x: dates, close: closes, open: opens, high: highs, low: lows, type: 'candlestick', name: 'K线',
              increasing: {line: {color: '#FF0000'}}, decreasing: {line: {color: '#00FF00'}}},
            {x: dates, y: senkouA, mode: 'lines', name: '云A', line: {color: '#2F4F4F'}},
            {x: dates, y: senkouB, mode: 'lines', name: '云B', line: {color: '#8B4513'}},
            {x: dates, y: ema5, mode: 'lines', name: 'EMA5', line: {color: '#FFFFFF'}},
            {x: dates, y: ma50, mode: 'lines', name: 'MA50', line: {color: '#00FF00'}},
            {x: dates, y: ma100, mode: 'lines', name: 'MA100', line: {color: '#FF0000', width: 2}}
        ];

        sig.forEach(function(s) {
            var nm = (s.type === 'buy') ? '金叉' : '死叉';
            var sy = (s.type === 'buy') ? 'triangle-up' : 'triangle-down';
            var cl = (s.type === 'buy') ? '#FF0000' : '#00FF00';
            traces.push({x: [s.x], y: [s.y], mode: 'markers', type: 'scatter', name: nm,
                marker: {symbol: sy, size: 15, color: cl}});
        });

        var layout = {
            title: 'AI CHIP INDEX', plot_bgcolor: '#16213e', paper_bgcolor: '#16213e',
            font: {color: '#eee'}, xaxis: {title: '日期', gridcolor: '#333', tickangle: -45},
            yaxis: {title: '指数点位', gridcolor: '#333'}, legend: {bgcolor: 'rgba(0,0,0,0.5)'}
        };

        Plotly.newPlot('chart', traces, layout, {responsive: true, displayModeBar: true});
    </script>
</body>
</html>"""

        return html

    def save_data(self, stocks_df, index_df):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stocks_df.to_csv(self.output_dir / "AI_CHIP_INDEX_stocks.csv", index=False, encoding="utf-8-sig")
        index_df.to_csv(self.output_dir / "AI_CHIP_INDEX_detail.csv", index=False, encoding="utf-8-sig")
        index_df[["date", "index_value"]].to_csv(self.output_dir / "AI_CHIP_INDEX.csv", index=False, encoding="utf-8-sig")
        title = self.config["output"].get("chart_title", "AI CHIP INDEX")
        html = self.generate_kline_html(index_df, title)
        with open(self.output_dir / "AI_CHIP_INDEX_kline.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved all files")

    def run_all(self):
        stocks_df = self.fetch_data()
        if stocks_df is None:
            return
        index_df = self.calculate_index(stocks_df)
        if index_df is None:
            return
        self.save_data(stocks_df, index_df)
        print("Done! Latest: {:.2f}, Return: {:.2f}%".format(index_df['index_value'].iloc[-1], index_df['cumulative_return'].iloc[-1]))


if __name__ == "__main__":
    g = IndexGenerator()
    if len(sys.argv) > 1 and sys.argv[1] == "chart":
        s = pd.read_csv(g.output_dir / "AI_CHIP_INDEX_stocks.csv", encoding="utf-8-sig")
        g.save_data(s, g.calculate_index(s))
    else:
        g.run_all()