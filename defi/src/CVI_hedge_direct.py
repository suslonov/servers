#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import asyncio
import json
import websockets
from enum import Enum
from datetime import datetime
import numpy as np
import pandas as pd
import pytz

from crypto_exchange_reader import crypto_currencies, DeribitExchangeReader

# import nest_asyncio
# nest_asyncio.apply()

UTC = pytz.timezone('UTC')
MIN_TERM = 35
MAX_TERM = 90
EXPIRATION_HOUR = 8

class DeribitExchangeReaderTickers(DeribitExchangeReader):
    url_ticker = "https://www.deribit.com/api/v2/public/ticker?instrument_name={}"

    def get_ticker_html(self, instrument_name):
        url = self.url_ticker.format(instrument_name)
        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            print("error getting options from Deribit", res.status_code)
            print(res.json())
            return None

        d = res.json()
        return d["result"]

    async def get_tickers_socket(self, instrument_name_list):
        results = {}
        not_get = []
######### switching 2 lines below should improve performance, but does not work at some servers (???)
        for id_i, i in enumerate(instrument_name_list):
            async with websockets.connect('wss://www.deribit.com/ws/api/v2') as websocket:
######### 
                msg = json.dumps({"jsonrpc" : "2.0",
                       "id" : 8106 + id_i,
                       "method" : "public/ticker",
                       "params" : {"instrument_name" : i}})
                await websocket.send(msg)
                response = await websocket.recv()
                d = json.loads(response)
                if not "result" in d:
                    not_get.append(i)
                    # print("error for an instrument", msg)
                    # if "error" in d:
                    #     print(d["error"])
                else:
                    results[i] = d["result"]
        return results, not_get

def is_expiration_good(expiration_date, min_expiration_date, time_point, term, to_expiration=False):
    if to_expiration:
        return (expiration_date - time_point).days >= term and (min_expiration_date is None or expiration_date < min_expiration_date)
    else:
        min_term = max(MIN_TERM, int(term * 1.1))
        max_term = max(MAX_TERM, int(term * 3.1))
        return (expiration_date - time_point).days >= min_term and (expiration_date - time_point).days <= max_term

def load_data(term=30, strike_range=1.0):
    exchange = DeribitExchangeReaderTickers()
    time_point = datetime.utcnow()
    rate_start = {c.value: exchange.get_currency(c) for c in crypto_currencies}
    instruments = {c.value: exchange.get_instruments_data(c) for c in crypto_currencies}

    to_request = {}
    good_expirations = set()
    min_expiration_date = None

    for c in rate_start:
        for i in instruments[c]:
            expiration_date = datetime.fromtimestamp(i["expiration_timestamp"]/1000, tz=UTC).replace(tzinfo=None) + pd.Timedelta(EXPIRATION_HOUR, "h")
            if is_expiration_good(expiration_date, min_expiration_date, time_point, term):
                if not expiration_date in good_expirations:
                    good_expirations.add(expiration_date)
                    if min_expiration_date is None or expiration_date < min_expiration_date:
                        min_expiration_date = expiration_date
                i["expiration_date"] = expiration_date
                t = (expiration_date - time_point).total_seconds() / (365 * 24 * 60 * 60)
                i["term"] = t
                to_request[i["instrument_name"]] = i

    tickers, not_get =  asyncio.get_event_loop().run_until_complete(exchange.get_tickers_socket(list(to_request.keys())))
    for i in not_get:
        tickers[i] = exchange.get_ticker_html(i)
   
    options_data = {}
    for i in tickers:
        t = tickers[i]
        if t['open_interest'] == 0.0 or t['best_bid_amount'] == 0 or t['best_ask_price'] == 0 or t['best_ask_amount'] == 0 or t['greeks']['vega'] == 0 or t['greeks']['delta'] == 0:
            continue
        rate = rate_start[to_request[i]["base_currency"]]
        if to_request[i]["strike"] < rate * ( 1 - strike_range) or to_request[i]["strike"] > rate * ( 1 + strike_range):
            continue
        t["expiration_date"] = to_request[i]["expiration_date"]
        t["term"] = to_request[i]["term"]
        t["strike"] = to_request[i]["strike"]
        t["currency"] = to_request[i]["base_currency"]
        t["contract_type"] = "C" if to_request[i]["option_type"] == "call" else "P"
        t["Vega"] = t["greeks"]["vega"]
        t["Delta"] = t["greeks"]["delta"]
        options_data[i] = t

    return pd.DataFrame.from_records(options_data).T, rate_start, good_expirations

def generate_strangles(one_date_contracts, c):
    for i1, p1 in enumerate(one_date_contracts.index):
        if one_date_contracts.loc[p1, "contract_type"] != "P":
            continue
        for c1 in one_date_contracts.index[i1+1:]:
            if one_date_contracts.loc[c1, "contract_type"] != "C":
                continue
            yield {"type":"strangle", "put": p1, "call": c1, "currency": c}

def generate_straddles(one_date_contracts, c):
    for i1, c1 in enumerate(one_date_contracts.index):
        if one_date_contracts.loc[c1, "contract_type"] != "C":
            continue
        if i1+1 >= len(one_date_contracts.index):
            continue
        p1 = one_date_contracts.index[i1+1]
        if one_date_contracts.loc[p1, "contract_type"] != "P":
            continue
        if one_date_contracts.loc[c1, "strike"] == one_date_contracts.loc[p1, "strike"]:
            yield {"type":"straddle", "put": p1, "call": c1, "currency": c}

def generate_guts(one_date_contracts, c):
    for i1, c1 in enumerate(one_date_contracts.index):
        if one_date_contracts.loc[c1, "contract_type"] != "C":
            continue
        for p1 in one_date_contracts.index[i1+1:]:
            if one_date_contracts.loc[p1, "contract_type"] != "P":
                continue
            if one_date_contracts.loc[c1, "strike"] != one_date_contracts.loc[p1, "strike"]:
                yield {"type":"guts", "put": p1, "call": c1, "currency": c}

def find_best_cvi_hedge(amount, term, strike_range):
    if amount <= 0:
        return None, None, None, None, None
    df_options_data, rate_start, good_expirations = load_data(term=30, strike_range=strike_range)

    plans = []
    for c in crypto_currencies.values():
        for expiration in df_options_data.groupby(["expiration_date"]).count().index:
            one_date = df_options_data.loc[(df_options_data["expiration_date"] == expiration) & (df_options_data["currency"] == c)].sort_values(["strike", "contract_type"])
            plans.extend([v for v in generate_straddles(one_date, c)])
            plans.extend([v for v in generate_strangles(one_date, c)])
            plans.extend([v for v in generate_guts(one_date, c)])

    plans_df = pd.DataFrame.from_records(plans)
    for c in crypto_currencies.values():
        plans_df.loc[plans_df["currency"] == c, "price_put"] = (df_options_data.loc[plans_df.loc[plans_df["currency"] == c, "put"], "best_ask_price"] * rate_start[c]).values
        plans_df.loc[plans_df["currency"] == c, "price_call"] = (df_options_data.loc[plans_df.loc[plans_df["currency"] == c, "call"], "best_ask_price"] * rate_start[c]).values

        plans_df.loc[plans_df["currency"] == c, "Vega_put"] = df_options_data.loc[plans_df.loc[plans_df["currency"] == c, "put"], "Vega"].values
        plans_df.loc[plans_df["currency"] == c, "Vega_call"] = df_options_data.loc[plans_df.loc[plans_df["currency"] == c, "call"], "Vega"].values
        plans_df.loc[plans_df["currency"] == c, "Delta_put"] = df_options_data.loc[plans_df.loc[plans_df["currency"] == c, "put"], "Delta"].values
        plans_df.loc[plans_df["currency"] == c, "Delta_call"] = df_options_data.loc[plans_df.loc[plans_df["currency"] == c, "call"], "Delta"].values
    plans_df["price"] = plans_df["price_put"]/plans_df["Vega_put"] + plans_df["price_call"]/plans_df["Vega_call"]
    plans_df["min_vega"] = plans_df[["Vega_put", "Vega_call"]].min(axis=1)
    plans_df["closest"] = (df_options_data.loc[plans_df["put"], "expiration_date"] == min(good_expirations)).values
    plans_df.dropna(inplace=True)

    plans_df['idx'] = plans_df.index
    plans_df.sort_values(["price"],inplace=True)
    best_strategies = plans_df.loc[plans_df.groupby(["currency"])["idx"].first()].set_index(["currency"])
    plans_df_closest = plans_df.loc[plans_df["closest"]]
    best_strategies_closest = plans_df_closest.loc[plans_df_closest.groupby(["currency"])["idx"].first()].set_index(["currency"])

    plans_df.sort_values(["min_vega"],inplace=True)
    max_Vega_strategies = plans_df.loc[plans_df.groupby(["currency"])["idx"].last()].set_index(["currency"])
    plans_df_closest = plans_df.loc[plans_df["closest"]]
    max_Vega_strategies_closest = plans_df_closest.loc[plans_df_closest.groupby(["currency"])["idx"].last()].set_index(["currency"])

    return best_strategies, max_Vega_strategies, best_strategies_closest, max_Vega_strategies_closest, rate_start

def funding_fee(cvi):
    return round(min(0.1, 0.1 * np.power(1/2, (cvi-50)/5) + 0.003), 4) if cvi <= 150 else 0.002

def load_ff(term):
    
    res = requests.get("http://defi.r-synergy.com/V003/cvijson", {'Content-Type': "application/json"})
    if res.status_code != 200:
        print("error getting CVI", res.status_code)
        print(res.json())
        return {}

    d = res.json()
    cvi = round(d['cvi-ema'], 4)
    cvi_ff = funding_fee(cvi)
    cvi_ff_amount = cvi_ff * term *24
    cvi_avg = 85.75  # ! hardcoded average
    cvi_avg_ff = funding_fee(cvi_avg)
    cvi_avg_ff_amount = cvi_avg_ff * term *24
    return {"cvi": cvi, "cvi_avg": cvi_avg, "cvi_ff": cvi_ff, "cvi_avg_ff": cvi_avg_ff, "cvi_ff_amount": cvi_ff_amount, "cvi_avg_ff_amount": cvi_avg_ff_amount}

def prepare_best_cvi_hedge_direct(amount, term, strike_range=1.0):
    best_strategies, max_Vega_strategies, best_strategies_closest, max_Vega_strategies_closest, rate_start = find_best_cvi_hedge(amount, term, strike_range)
    if best_strategies is None:
        return {}, {}

    all_best_strategies = {}
    # for s, s_name in zip([max_Vega_strategies, max_Vega_strategies_closest, best_strategies, best_strategies_closest],
    #              ["Best Vega (and delta-neutral) strategy", "Best Vega strategy for the closest expiration after the term", "Best price strategy",  "Best price strategy for the closest expiration after the term"]):
    for s, s_name in zip([max_Vega_strategies, best_strategies],
                 ["Best Vega (and delta-neutral) strategy", "Best price strategy"]):
        best_s = {}
        for c in crypto_currencies.values():
            best_s[c] = [{"type": s.loc[c, "type"],
                                       "contract": s.loc[c, "put"],
                                       "Vega": s.loc[c, "Vega_put"],
                                       "Delta": s.loc[c, "Delta_put"],
                                       "price": s.loc[c, "price_put"],
                                       "Ncontracts": amount / rate_start[c] / s.loc[c, "Vega_put"] * np.sqrt(term/365)/2},
                                      {"type": "total delta = {:.9f}".format((s.loc[c, "Delta_put"] / rate_start[c] / s.loc[c, "Vega_put"] + 
                                                                         s.loc[c, "Delta_call"] / rate_start[c] / s.loc[c, "Vega_call"])/
                                                                               (1 / rate_start[c] / s.loc[c, "Vega_put"] + 1 / rate_start[c] / s.loc[c, "Vega_call"])),
                                       "contract": s.loc[c, "call"],
                                       "Vega": s.loc[c, "Vega_call"],
                                       "Delta": s.loc[c, "Delta_call"],
                                       "price": s.loc[c, "price_call"],
                                       "Ncontracts": amount / rate_start[c] / s.loc[c, "Vega_call"] * np.sqrt(term/365)/2}]
        all_best_strategies[s_name] = best_s
    return all_best_strategies, rate_start, load_ff(term)

def test():
    amount = 1000000
    term = 30
    strike_range = 0.2
######
    # best_strategies, max_Vega_strategies, best_strategies_closest, max_Vega_strategies_closest, rate_start = find_best_cvi_hedge(amount, term)
######

######
    t0= datetime.now()
    best_strategies, rate_start, funding_fee = prepare_best_cvi_hedge_direct(amount, term, strike_range)
    print(datetime.now()-t0)

    print(best_strategies)
