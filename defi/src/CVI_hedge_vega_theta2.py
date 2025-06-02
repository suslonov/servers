
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

def load_data(term1=35):
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
    expiration1 = min([(abs((e - time_point).days - term1), e) for e in expirations])[1]
    
    for c in rate_start:
        for i in instruments[c]:
            expiration_date = datetime.fromtimestamp(i["expiration_timestamp"]/1000, tz=UTC).replace(tzinfo=None) + pd.Timedelta(EXPIRATION_HOUR, "h")
            if expiration_date == expiration1 and abs(i["strike"]-rate_start[c])/rate_start[c] < 0.3: #!!!
            
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
        t["currency"] = to_request[i]["base_currency"]
        t["contract_type"] = "C" if to_request[i]["option_type"] == "call" else "P"
        t["Vega"] = t["greeks"]["vega"]
        t["Delta"] = t["greeks"]["delta"]
        t["Theta"] = t["greeks"]["theta"]
        t["IV"] = (t["bid_iv"] + t["ask_iv"])/2
        options_data[i] = t

    return pd.DataFrame.from_records(options_data).T, rate_start, pd.Timestamp(time_point), pd.Timestamp(expiration1)


def find_pair_n(i0, j0, df_calls, df_puts, t, rate):
    i = i0
    j = j0
    (delta_i0, vega_i0, theta_i0) = df_calls.iloc[i][["Delta", "Vega", "Theta"]]
    (delta_j0, vega_j0, theta_j0) = df_puts.iloc[j][["Delta", "Vega", "Theta"]]
    final = False
    while True:
        i += 1
        try:
            (delta_i, vega_i, theta_i) = df_calls.iloc[i][["Delta", "Vega", "Theta"]]
            if abs(abs(delta_i0) - abs(delta_j0)) > abs(abs(delta_i) - abs(delta_j0)):
                delta_i0 = delta_i
                vega_i0 = vega_i
                final = False
                continue
            else:
                i -= 1
                final = True
        except:
            i -= 1
            break
        j -= 1
        try:
            (delta_j, vega_j, theta_j) = df_puts.iloc[j][["Delta", "Vega", "Theta"]]
            if abs(abs(delta_i0) - abs(delta_j0)) > abs(abs(delta_i0) - abs(delta_j)):
                delta_j0 = delta_j
                vega_j0 = vega_j
                final = False
                continue
            else:
                j += 1
                if final:
                    break
        except:
            j += 1
            break

    price = df_calls.iloc[i]["best_ask_price"] + df_puts.iloc[j]["best_ask_price"]
    spread = df_calls.iloc[i]["best_ask_price"] - df_calls.iloc[i]["best_bid_price"] + df_puts.iloc[j]["best_ask_price"] - df_puts.iloc[j]["best_bid_price"]
    return i, j, delta_i0 + delta_j0, vega_i0 + vega_j0, theta_i0 + theta_j0, price, spread

def CVI_hedge_vega_theta2(cvi, amount=100000, for_json=True):
    df_options_data, rate_start, d, e = load_data(term1=35)
    t = (e - d + pd.Timedelta(EXPIRATION_HOUR, "h")).total_seconds() / (365 * 24 * 60 * 60)

    df_options_data[["currency", "expiration", "strike", "type"]] = df_options_data["instrument_name"].str.split('-', expand=True)
    df_options_data["strike"] = np.int64(df_options_data["strike"])
    df_options_data.sort_values(["strike"], inplace=True)
    df = df_options_data.loc[(df_options_data["expiration"] == e.strftime("%d%b%y").upper()) & ~pd.isnull(df_options_data["best_ask_price"]) & ~pd.isnull(df_options_data["best_bid_price"])]
    results = {}
    for curr in ["BTC", "ETH"]:
        _results = []
        rate = rate_start[curr]
        df_calls = df.loc[(df["type"] == "C") & (df["strike"] >= rate) & (df["currency"] >= curr)]
        df_puts = df.loc[(df["type"] == "P") & (df["strike"] <= rate) & (df["currency"] >= curr)]
        if len(df_calls) == 0 or len(df_puts) == 0:
            continue
    

        compare = []
        i_call = 0; i_put = len(df_puts) - 1
        # i0 = 0; j0 = len(df_puts) - 1
        while True:
            i_call, i_put, delta, vega, theta, price, spread = find_pair_n(i_call,
                                                                    i_put,
                                                                    df_calls,
                                                                    df_puts,
                                                                    t,
                                                                    rate)
            # print(i_call, i_put, delta, vega, price, spread)
            if not pd.isnull(vega):
                compare.append((vega/(spread/price), i_call, i_put, delta, vega, theta, price,
                                df_calls.iloc[i_call]["strike"] - df_puts.iloc[i_put]["strike"]))
            i_call = i_call + 1
            i_put = i_put - 1
            if i_call > len(df_calls) - 1 or i_put < 0:
                break

        for strangle in compare:
            if for_json:
                res = {"start": d,
                       "currency": curr,
                       "rate_start": rate,
                       "expiration": e,
                       "call": df_calls.iloc[strangle[1]]["instrument_name"],
                       "put": df_puts.iloc[strangle[2]]["instrument_name"],
                       "delta": strangle[3],
                       "vega": strangle[4],
                       "theta": strangle[5],
                       "price_per_contract": strangle[6],
                       "width": int(strangle[7]),
                       "N_contracts": amount/strangle[4]/cvi[curr],
                       "funding_fee_rate": -strangle[5]/strangle[4]/cvi[curr],
                       }
            else:
                res = {"expiration": e,
                       "call": df_calls.iloc[strangle[1]]["instrument_name"],
                       "put": df_puts.iloc[strangle[2]]["instrument_name"],
                       "delta": "{:.4f}".format(strangle[3]),
                       "vega": "{:.4f}".format(strangle[4]),
                       "theta": "{:.4f}".format(strangle[5]),
                       "price_per_contract": "{:.4f}".format(strangle[6]),
                       "width": int(strangle[7]),
                       "N_contracts":"{:.1f}".format(amount/strangle[4]/cvi[curr]),
                       "funding_fee_rate": "{:.4f}".format(-strangle[5]/strangle[4]/cvi[curr]),
                       }
                
            _results.append(res)
        results[curr] = _results

    return results
