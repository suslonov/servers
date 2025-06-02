
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

def load_data(term1=90, term2=15):
    exchange = DeribitExchangeReaderTickers()
    time_point = datetime.utcnow()
    rate_start = {c.value: exchange.get_currency(c) for c in crypto_currencies}
    instruments = {c.value: exchange.get_instruments_data(c) for c in crypto_currencies}

    to_request = {}
    good_expirations = set()
    min_expiration_date = None

    expirations = set()
    for c in rate_start:
        for i in instruments[c]:
            expiration_date = datetime.fromtimestamp(i["expiration_timestamp"]/1000, tz=UTC).replace(tzinfo=None) + pd.Timedelta(EXPIRATION_HOUR, "h")
            expirations.add(expiration_date)
            
    expirations = list(expirations)
    expirations.sort()
    expiration1 = expirations[0]; expiration2 = expirations[0]
    for e in expirations:
        if not (e - time_point).days >= term2:
            expiration2 = e
        if not (e - time_point).days >= term1:
            expiration1 = e
        else:
            break
            
    for c in rate_start:
        for i in instruments[c]:
            expiration_date = datetime.fromtimestamp(i["expiration_timestamp"]/1000, tz=UTC).replace(tzinfo=None) + pd.Timedelta(EXPIRATION_HOUR, "h")
            if (expiration_date == expiration1 or expiration_date == expiration2) and abs(i["strike"]-rate_start[c])/rate_start[c] < 0.3: #!!!
            
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
        t["expiration_date"] = to_request[i]["expiration_date"]
        t["term"] = to_request[i]["term"]
        t["strike"] = to_request[i]["strike"]
        t["currency"] = to_request[i]["base_currency"]
        t["contract_type"] = "C" if to_request[i]["option_type"] == "call" else "P"
        t["Vega"] = t["greeks"]["vega"]
        t["Delta"] = t["greeks"]["delta"]
        t["Theta"] = t["greeks"]["theta"]
        t["IV"] = (t["bid_iv"] + t["ask_iv"])/2
        options_data[i] = t

    return pd.DataFrame.from_records(options_data).T, rate_start, expiration1, expiration2


def CVI_hedge_vega_theta(amount=100000):
    df_options_data, rate_start, expiration1, expiration2 = load_data(term1=90, term2=15)
    
    def two_contracts(c, e):
        strike_close_up = df_options_data.loc[(df_options_data["currency"]==c)&
                                              (df_options_data["strike"]>=rate_start[c])&
                                              (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="C"), "strike"].min()
        strike_close_down = df_options_data.loc[(df_options_data["currency"]==c)&
                                                (df_options_data["strike"]<=rate_start[c])&
                                                (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="P"), "strike"].max()
        IV = (df_options_data.loc[(df_options_data["currency"]==c)&
                                              (df_options_data["strike"]==strike_close_up)&
                                              (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="C"), "IV"].values[0] +
            df_options_data.loc[(df_options_data["currency"]==c)&
                                              (df_options_data["strike"]==strike_close_down)&
                                              (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="P"), "IV"].values[0])/2
    
        range1 = IV/100/np.sqrt(52)
        
        strike_up = df_options_data.loc[(df_options_data["currency"]==c)&
                                              (df_options_data["strike"]>=rate_start[c]*(1+range1))&
                                              (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="C"), "strike"].min()
        strike_down = df_options_data.loc[(df_options_data["currency"]==c)&
                                                (df_options_data["strike"]<=rate_start[c]/(1+range1))&
                                                (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="P"), "strike"].max()
        
        call_contract = df_options_data.loc[(df_options_data["currency"]==c)&
                                              (df_options_data["strike"]==strike_up)&
                                              (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="C")].index[0]
        
        put_contract = df_options_data.loc[(df_options_data["currency"]==c)&
                                              (df_options_data["strike"]==strike_down)&
                                              (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="P")].index[0]
        call_contract_delta = df_options_data.loc[call_contract, "Delta"]
        put_contract_delta = df_options_data.loc[put_contract, "Delta"]
        
        if abs(call_contract_delta) > abs(put_contract_delta):
            for p in df_options_data.loc[(df_options_data["currency"]==c)&
                                              (df_options_data["strike"]>=strike_down)&
                                              (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="P")].index:
                if abs(call_contract_delta + put_contract_delta) < abs(call_contract_delta + df_options_data.loc[p, "Delta"]):
                    break
                else:
                    put_contract = p
                    put_contract_delta = df_options_data.loc[p, "Delta"]
        else:
            for p in df_options_data.loc[(df_options_data["currency"]==c)&
                                              (df_options_data["strike"]<=strike_up)&
                                              (df_options_data["expiration_date"]==e)&
                                              (df_options_data["contract_type"]=="C")].index[::-1]:
                if abs(call_contract_delta + put_contract_delta) < abs(df_options_data.loc[p, "Delta"] + put_contract_delta):
                    break
                else:
                    call_contract = p
                    call_contract_delta = df_options_data.loc[p, "Delta"]

        return {"call": call_contract, "put": put_contract}

    buy_contracts_eth = two_contracts("ETH", expiration1)
    sell_contracts_eth = two_contracts("ETH", expiration2)
    buy_contracts_btc = two_contracts("BTC", expiration1)
    sell_contracts_btc = two_contracts("BTC", expiration2)

    buy_vega_eth = df_options_data.loc[buy_contracts_eth["call"], "Vega"] + df_options_data.loc[buy_contracts_eth["put"], "Vega"]
    sell_vega_eth = df_options_data.loc[sell_contracts_eth["call"], "Vega"] + df_options_data.loc[sell_contracts_eth["put"], "Vega"]
    buy_vega_btc = df_options_data.loc[buy_contracts_btc["call"], "Vega"] + df_options_data.loc[buy_contracts_btc["put"], "Vega"]
    sell_vega_btc = df_options_data.loc[sell_contracts_btc["call"], "Vega"] + df_options_data.loc[sell_contracts_btc["put"], "Vega"]

    buy_delta_eth = df_options_data.loc[buy_contracts_eth["call"], "Delta"], df_options_data.loc[buy_contracts_eth["put"], "Delta"]
    sell_delta_eth = df_options_data.loc[sell_contracts_eth["call"], "Delta"], df_options_data.loc[sell_contracts_eth["put"], "Delta"]
    buy_delta_btc = df_options_data.loc[buy_contracts_btc["call"], "Delta"], df_options_data.loc[buy_contracts_btc["put"], "Delta"]
    sell_delta_btc = df_options_data.loc[sell_contracts_btc["call"], "Delta"], df_options_data.loc[sell_contracts_btc["put"], "Delta"]

    buy_theta_eth = df_options_data.loc[buy_contracts_eth["call"], "Theta"] + df_options_data.loc[buy_contracts_eth["put"], "Theta"]
    sell_theta_eth = df_options_data.loc[sell_contracts_eth["call"], "Theta"] + df_options_data.loc[sell_contracts_eth["put"], "Theta"]
    buy_theta_btc = df_options_data.loc[buy_contracts_btc["call"], "Theta"] + df_options_data.loc[buy_contracts_btc["put"], "Theta"]
    sell_theta_btc = df_options_data.loc[sell_contracts_btc["call"], "Theta"] + df_options_data.loc[sell_contracts_btc["put"], "Theta"]
    
    theta_ratio_eth = buy_theta_eth / sell_theta_eth
    theta_ratio_btc = buy_theta_btc / sell_theta_btc
    
    vega_eth_qudr = buy_vega_eth - sell_vega_eth * theta_ratio_eth
    vega_btc_qudr = buy_vega_btc - sell_vega_btc * theta_ratio_btc
    
    n_eth = amount/rate_start["ETH"]/vega_eth_qudr*100
    n_btc = amount/rate_start["BTC"]/vega_btc_qudr*100
    
    result = {"BTC":{"sell": {sell_contracts_btc["call"]: n_btc*theta_ratio_btc,
                              sell_contracts_btc["put"]: n_btc*theta_ratio_btc},
                     "buy": {buy_contracts_btc["call"]: n_btc,
                              buy_contracts_btc["put"]: n_btc}},
              "ETH":{"sell": {sell_contracts_eth["call"]: n_eth*theta_ratio_eth,
                              sell_contracts_eth["put"]: n_eth*theta_ratio_eth},
                     "buy": {buy_contracts_eth["call"]: n_eth,
                              buy_contracts_eth["put"]: n_eth}}}
    return result
