#!/usr/bin/env python3
"""AI Chip Index - 主程序"""
import pandas as pd
import requests
import yaml
import os
import sys
import importlib
import baostock as bs
from datetime import datetime, timedelta
from pathlib import Path
from indicators import calc_indicators
from chart import gen_kline_html

HIST_CSV = "stocks_history.csv"
HAS_BAOSTOCK = True


def fetch_baostock(code, start_date, end_date):
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
            print("    Baostock err:", rs.error_code)
            bs.logout()
            return None
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        bs.logout()
        if not rows:
            return None
        df = pd.DataFrame(rows, columns=["date", "open", "high", "low", "close", "volume"])
        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["code"] = code
        print("    Baostock: {} rows".format(len(df)))
        return df[["date", "code", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        print("    Baostock fail:", e)
        try:
            bs.logout()
        except:
            pass
        return None


def fetch_sina(code, datalen=1000):
    url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={}&scale=240&ma=no&datalen={}".format(code, datalen)
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        df = pd.DataFrame(data).rename(columns={"day": "date"})
        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["code"] = code
        print("    Sina: {} rows".format(len(df)))
        return df[["date", "code", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        print("    Sina fail:", e)
        return None


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
            "output": {"dir": "./output", "start_date": "2024-01-01"},
        }

    def fetch_data(self):
        start_str = self.config["output"]["start_date"]
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.now()
        old = None
        if os.path.exists(HIST_CSV):
            try:
                old = pd.read_csv(HIST_CSV)
                print("Loaded {} rows from history".format(len(old)))
            except:
                pass
        print("Fetching {} stocks...".format(len(self.stocks)))
        rows = []
        for i, s in enumerate(self.stocks, 1):
            code = s["code"]
            name = s["name"]
            last_date = None
            if old is not None:
                sub = old[old["code"] == code]
                if len(sub) > 0:
                    last_date = pd.to_datetime(sub["date"]).max()
            if last_date is not None:
                fetch_start = last_date + timedelta(days=1)
                print("  [{}/{}] {} {} incr from {}...".format(
                    i, len(self.stocks), name, code,
                    last_date.strftime("%Y-%m-%d")))
                df = fetch_baostock(code, fetch_start, end_date)
                if df is None or len(df) == 0:
                    print("  -> fallback Sina")
                    df = fetch_sina(code, datalen=15)
            else:
                print("  [{}/{}] {} {} full...".format(
                    i, len(self.stocks), name, code))
                df = fetch_baostock(code, start_date, end_date)
                if df is None or len(df) == 0:
                    print("  -> fallback Sina")
                    df = fetch_sina(code, datalen=1000)
            if df is not None and len(df) > 0:
                df["name"] = name
                rows.append(df)
        if not rows:
            print("No data!")
            return None
        new = pd.concat(rows, ignore_index=True)
        if old is not None:
            all_ = pd.concat([old, new], ignore_index=True)
            all_ = all_.sort_values("date").drop_duplicates(
                subset=["code", "date"], keep="last")
        else:
            all_ = new
        all_ = all_[all_["date"] >= start_str]
        all_.to_csv(HIST_CSV, index=False, encoding="utf-8-sig")
        print("Total: {} rows".format(len(all_)))
        return all_

    def calc_index(self, sdf):
        d = sdf.copy()
        d["date"] = pd.to_datetime(d["date"])
        d = d.sort_values(["code", "date"])
        g = d.groupby(d["date"].dt.strftime("%Y-%m-%d")).agg(
            {"open": "mean", "high": "mean",
             "low": "mean", "close": "mean"}
        ).reset_index().rename(columns={"date": "ds"})
        if len(g) == 0:
            return None
        bv = self.index_config["base_value"]
        first_close = g["close"].iloc[0]
        g["index_value"] = (g["close"] / first_close * bv).round(2)
        g["cumulative_return"] = ((g["index_value"] / bv - 1) * 100).round(2)
        g.loc[0, "cumulative_return"] = 0.0
        scale = bv / first_close
        for c in ["open", "high", "low", "close"]:
            g[c] = (g[c] * scale).round(2)
        return g.rename(columns={"ds": "date"})

    def calc_weekly_index(self, sdf):
        """按周计算 OHLC：周开=周一开盘，周高=周最高，周低=周最低，周收=周五收盘"""
        d = sdf.copy()
        d["date"] = pd.to_datetime(d["date"])
        d = d.sort_values(["code", "date"])
        # 周分组：按 ISO 周（周一开始）
        d["week"] = d["date"].dt.isocalendar().year.astype(str) + "-W" + d["date"].dt.isocalendar().week.astype(str).str.zfill(2)
        g = d.groupby("week").agg(
            {"open": "first", "high": "max",
             "low": "min", "close": "last"}
        ).reset_index()
        if len(g) == 0:
            return None
        bv = self.index_config["base_value"]
        first_close = g["close"].iloc[0]
        # 需要日期映射：取每周第一个交易日日期
        week_dates = d.groupby("week")["date"].first().reset_index(name="_dt")
        g = g.merge(week_dates, on="week", how="left")
        g["date"] = g["_dt"].dt.strftime("%Y-%m-%d")
        g["index_value"] = (g["close"] / first_close * bv).round(2)
        g["cumulative_return"] = ((g["index_value"] / bv - 1) * 100).round(2)
        g.loc[0, "cumulative_return"] = 0.0
        scale = bv / first_close
        for c in ["open", "high", "low", "close"]:
            g[c] = (g[c] * scale).round(2)
        return g[["date", "open", "high", "low", "close", "index_value", "cumulative_return"]]

    def gen_html(self, df, wdf, title="AI CHIP INDEX"):
        cl = df["close"].tolist()
        hi = df["high"].tolist()
        lo = df["low"].tolist()
        ind = calc_indicators(cl, hi, lo)
        # 周线指标
        w_ind = calc_indicators(wdf["close"].tolist(), wdf["high"].tolist(), wdf["low"].tolist()) if wdf is not None else None
        return gen_kline_html(df, ind, title, self.stocks, wdf=wdf, w_ind=w_ind)

    def save(self, sdf, idf):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        sdf.to_csv(
            self.output_dir / "AI_CHIP_INDEX_stocks.csv",
            index=False, encoding="utf-8-sig")
        idf.to_csv(
            self.output_dir / "AI_CHIP_INDEX_detail.csv",
            index=False, encoding="utf-8-sig")
        idf[["date", "index_value"]].to_csv(
            self.output_dir / "AI_CHIP_INDEX.csv",
            index=False, encoding="utf-8-sig")
        # 计算周线
        wdf = self.calc_weekly_index(sdf)
        html = self.gen_html(idf, wdf)
        with open(
            self.output_dir / "AI_CHIP_INDEX_kline.html",
            "w", encoding="utf-8") as f:
            f.write(html)
        with open("index.htm", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved OK (root index.htm too)")

    def run(self):
        s = self.fetch_data()
        if s is None:
            print("No data")
            return
        i = self.calc_index(s)
        if i is None:
            print("Calc failed")
            return
        self.save(s, i)
        print("Done! Latest: {:.2f}, Return: {:.2f}%".format(
            i["index_value"].iloc[-1],
            i["cumulative_return"].iloc[-1]))


if __name__ == "__main__":
    g = IndexGenerator()
    if len(sys.argv) > 1 and sys.argv[1] == "chart":
        s = pd.read_csv(
            g.output_dir / "AI_CHIP_INDEX_stocks.csv",
            encoding="utf-8-sig")
        idf = g.calc_index(s)
        g.save(s, idf)
    else:
        g.run()
