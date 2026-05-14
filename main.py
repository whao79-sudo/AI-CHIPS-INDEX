#!/usr/bin/env python3
import pandas as pd
import numpy as np
import requests
import yaml
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

HIST_CSV = "stocks_history.csv"

HAS_BAOSTOCK = False
try:
    import baostock as bs
    HAS_BAOSTOCK = True
except:
    pass