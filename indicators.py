#!/usr/bin/env python3
"""指标计算模块 - 一目均衡 + 布林带 + 多均线"""
import numpy as np


def calc_indicators(cl, hi, lo):
"""计算所有指标，返回字典"""
n = len(cl)

# 一目均衡
tenkan = []
kijun = []
for i in range(n):
tenkan.append((hi[i] + lo[i]) / 2 if i >= 8 else None)
kijun.append((max(hi[max(0,i-25):i+1]) + min(lo[max(0,i-25):i+1])) / 2 if i >= 25 else None)
sa_ = [(tenkan[i] + kijun[i]) / 2 if tenkan[i] is not None and kijun[i] is not None else None for i in range(n)]
sb_ = [(max(hi[max(0,i-51):i+1]) + min(lo[max(0,i-51):i+1])) / 2 if i >= 51 else None for i in range(n)]

# SMA
def sma(d, p):
r = []
t = 0.0
for i in range(n):
t += d[i]
if i >= p:
t -= d[i-p]
r.append(round(t / min(p, i+1), 2) if i >= p-1 else None)
return r

# EMA
def ema_(d, p):
r = []
f = 2 / (p + 1)
for i in range(n):
if i == 0:
r.append(d[0])
else:
r.append(round(d[i] * f + (1 - f) * r[-1], 2))
return r

boll = sma(cl, 20)
ma50 = sma(cl, 50)
ma100 = sma(cl, 100)
ma300 = sma(cl, 300)
ema5 = ema_(cl, 5)

def std(d, p):
return [round(float(np.std(d[max(0,i-p+1):i+1])), 2) if i >= p-1 else None for i in range(n)]

s20 = std(cl, 20)
s100 = std(cl, 100)
s300 = std(cl, 300)

ub = [round(boll[i] + 2 * s20[i], 2) if boll[i] is not None else None for i in range(n)]
lb = [round(boll[i] - 2 * s20[i], 2) if boll[i] is not None else None for i in range(n)]
ub1 = [round(ma300[i] + 2 * s300[i], 2) if ma300[i] is not None else None for i in range(n)]
lb1 = [round(ma300[i] - 2 * s300[i], 2) if ma300[i] is not None else None for i in range(n)]
ub1a = [round(ma300[i] + s300[i], 2) if ma300[i] is not None else None for i in range(n)]
lb1a = [round(ma300[i] - s300[i], 2) if ma300[i] is not None else None for i in range(n)]
ub2 = [round(ma100[i] + 2 * s100[i], 2) if ma100[i] is not None else None for i in range(n)]
lb2 = [round(ma100[i] - 2 * s100[i], 2) if ma100[i] is not None else None for i in range(n)]

return {
"tenkan": tenkan, "kijun": kijun, "sa_": sa_, "sb_": sb_,
"boll": boll, "ub": ub, "lb": lb,
"ma300": ma300, "ub1": ub1, "lb1": lb1, "ub1a": ub1a, "lb1a": lb1a,
"ema5": ema5, "ma50": ma50, "ma100": ma100, "ub2": ub2, "lb2": lb2,
}