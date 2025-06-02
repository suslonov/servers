#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import pytz
import pandas as pd
import numpy as np
import json

from gvol_feed import crypto_currencies, GvolFeed
from db_cvx2 import DBPoints2

RISK_FREE_RATE = 0

def T_for_dates(t, e):
    y1 = datetime.fromtimestamp(t).year
    y2 = datetime.fromtimestamp(e).year
    if y1 == y2:
        return (e - t)/((datetime(y1,12,31) - datetime(y1,1,1)).days + 1)/24/60/60
    else:
        return (e - datetime(y2,1,1, tzinfo=pytz.timezone('UTC')).timestamp())/((datetime(y2,12,31) - datetime(y2,1,1)).days + 1)/24/60/60 + \
               (datetime(y2,1,1, tzinfo=pytz.timezone('UTC')).timestamp() - t)/((datetime(y1,12,31) - datetime(y1,1,1)).days + 1)/24/60/60

def get_underlying_price(calls, puts, e):
    mid = calls.loc[~np.isnan(calls["mid_price"])][["strike", "mid_price"]]
    mid.set_index("strike", inplace=True)
    mid.rename(columns={"mid_price": "mid_price_call"}, inplace=True)
    mid["mid_price"] = np.nan
    mid_update = puts.loc[~np.isnan(puts["mid_price"])][["strike", "mid_price"]]
    mid_update.set_index("strike", inplace=True)
    mid.update(mid_update)
    mid.rename(columns={"mid_price": "mid_price_put"}, inplace=True)
    mid["diff"] = abs(mid["mid_price_call"] - mid["mid_price_put"])
    at_the_money = mid["diff"].idxmin()
    T_sec = (int(calls.loc[calls["strike"] == at_the_money, "date"].values[0]) + int(puts.loc[puts["strike"] == at_the_money, "date"].values[0])) / 2000
    T = T_for_dates(T_sec, e)
    return at_the_money + np.exp(RISK_FREE_RATE * T) * (mid.loc[at_the_money, "mid_price_call"] - mid.loc[at_the_money, "mid_price_put"])

def one_sigma4(e, calls, puts, F, t):
    if len(calls) == 0 or len(puts) == 0:
        return None

    T = T_for_dates(t, e)
    S = 0
    K0c = 0
    compare_list = [calls.loc[c, "mid_price"] if calls.loc[c, "mid_price"] else 0 for c in calls.index]
    for (i, c) in enumerate(calls.index):
        if calls.loc[c, "strike"] > F:
            prev_max = 0
            if i > 0:
                prev_max = max(compare_list[max((0, i-10)):i])
            if i > 3 and prev_max != 0 and calls.loc[c, "mid_price"] > 2 * prev_max:
                continue
            if i == 0:
                dK = calls.loc[calls.index[i+1], "strike"] - calls.loc[c, "strike"]
            elif i == len(calls) - 1:
                dK = calls.loc[c, "strike"] - calls.loc[calls.index[i-1], "strike"]
            else:
                dK = (calls.loc[calls.index[i+1], "strike"] - calls.loc[calls.index[i-1], "strike"])/2
            S += dK * calls.loc[c, "mid_price"] / (calls.loc[c, "strike"]**2)
        else:
            K0c = calls.loc[c, "strike"]

    K0p = 0
    compare_list = [puts.loc[p, "mid_price"] if puts.loc[p, "mid_price"] else 0 for p in puts.index]
    for (i, p) in enumerate(puts.index):
        if puts.loc[p, "strike"] < F:
            prev_max = 0
            if i > 0:
                prev_max = max(compare_list[max((0, i-10)):i])
            if i > 3 and prev_max != 0 and puts.loc[p, "mid_price"] > 2 * prev_max:
                continue
            if i == 0:
                dK = puts.loc[p, "strike"] - puts.loc[puts.index[i+1], "strike"]
            elif i == len(puts) - 1:
                dK = puts.loc[puts.index[i-1], "strike"] - puts.loc[p, "strike"]
            else:
                dK = (puts.loc[puts.index[i-1], "strike"] - puts.loc[puts.index[i+1], "strike"])/2
            S += dK * puts.loc[p, "mid_price"] / (puts.loc[p, "strike"]**2)
        else:
            K0p = puts.loc[p, "strike"]

    K0 = (K0c + K0p)/2
    if S <= 0:
        return None
    else:
        return (2 * np.exp(RISK_FREE_RATE * T) * S - (F / K0-1)**2) / T

def weighted_sigma(sigmas, t):
    tm = 60*60*24*30
    if len(sigmas) == 1:
        return None
    ST = 0
    count_s = 0
    for (e, s) in sigmas:
        if not s is None:
            ST += abs(e - t - tm)
            count_s += 1

    weighted = 0
    for (e, s) in sigmas:
        if not s is None:
            weighted += (ST - abs(e - t - tm))*(e - t)*s

    if count_s <= 1:
        return None
    else:
        return weighted/ST/tm/(count_s - 1)

def calc_cvi_v4(df_options, now_time):
    now_plus_30 = (datetime.now() + timedelta(days=30)).timestamp()
    
    try:
        next_e = df_options.loc[df_options["expiration"] >= now_plus_30, "expiration"].min()
        next_calls = df_options.loc[(df_options["expiration"] == next_e) & (df_options["putCall"] == "C")].sort_values(["strike"])
        next_puts = df_options.loc[(df_options["expiration"] == next_e) & (df_options["putCall"] == "P")].sort_values(["strike"], ascending=False)
        next_underlying_price = get_underlying_price(next_calls, next_puts, next_e)
        next_sigma = one_sigma4(next_e, next_calls.loc[~np.isnan(next_calls["mid_price"])][["strike", "mid_price"]],
                                next_puts.loc[~np.isnan(next_puts["mid_price"])][["strike", "mid_price"]], next_underlying_price, now_time)
        
        prev_e = df_options.loc[df_options["expiration"] <= now_plus_30, "expiration"].max()
        prev_calls = df_options.loc[(df_options["expiration"] == prev_e) & (df_options["putCall"] == "C")].sort_values(["strike"])
        prev_puts = df_options.loc[(df_options["expiration"] == prev_e) & (df_options["putCall"] == "P")].sort_values(["strike"], ascending=False)
        prev_underlying_price = get_underlying_price(prev_calls, prev_puts, prev_e)
        prev_sigma = one_sigma4(prev_e, prev_calls.loc[~np.isnan(prev_calls["mid_price"])][["strike", "mid_price"]],
                                prev_puts.loc[~np.isnan(prev_puts["mid_price"])][["strike", "mid_price"]], prev_underlying_price, now_time)
    except:
        return None

    if next_sigma is None or prev_sigma is None or next_sigma < 0 or prev_sigma < 0:
        return None
    
    s = weighted_sigma([(prev_e, prev_sigma), (next_e, next_sigma)], now_time)
    return np.sqrt(s) * 100

def gvol_main():
    now_date = datetime.utcnow()
    now_time = int(now_date.timestamp()//60)*60
    exchanges_gvol = {}
    for e_name in ['deribit', 'bitcom', 'okex', 'delta', 'ledgerx']:
        try:
            exchange = GvolFeed(e_name)
            exchange.request_exchange(now_date)
            exchanges_gvol[e_name] = exchange
        except:
            pass
    
    exchanges_cvi = {}
    for e_name in exchanges_gvol:
        exchanges_cvi[e_name] = {}
    
        for c in crypto_currencies:
            df_options = exchanges_gvol[e_name].option_data[c.value]
            if len(df_options) > 0:
                exchanges_cvi[e_name][c.value] = calc_cvi_v4(df_options, now_time)
    
    with DBPoints2() as db:
        db.add_point_to_db("v004", now_date, json.dumps(exchanges_cvi))

if __name__ == '__main__':
    gvol_main()
