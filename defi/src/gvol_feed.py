#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    https://docs-lite.gvol.io/#e43c9ad3-a512-4532-8ecf-3a2d5116f9dd
    Exchange: Deribit, Bitcom, Okex, Delta, LedgerX
"""

import requests
import pandas as pd
import numpy as np
from enum import Enum
class crypto_currencies(Enum):
    BTC = "BTC"
    ETH = "ETH"
    SOL = "SOL"

HEADERS_TEMPLATE = {'Content-Type': "application/json", 'gvol-lite-plus': '', 'accept': '*/*'}
KEY_FILE = 'gvol.sec'
URL = "https://app.pinkswantrading.com/graphql"
GRAPHQL_PARAMS_TEMPLATE = {"query": "query UtilityRealtimeOptionbook($exchange: ExchangeEnumType)" +
" {\n  UtilityRealtimeOptionbook:" +
" genericUtilityRealtimeOptionbook(exchange: $exchange)" +
" {\n   date\n" +
"   instrumentName\n" +
"   currency\n" +
"   expiration\n" +
"   strike\n" +
"   putCall\n" +
# "   isAtm\n" +
# "   oi\n" +
"   bestBidPrice\n" +
"   bestAskPrice\n" +
"   usdBid\n" +
"   usdAsk\n" +
# "   bidIV\n" +
# "   markIv\n" +
# "   askIv\n" +
"   indexPrice\n" +
# "   underlyingPrice\n" +
"}}\n",
"variables":{}}

FIAT_PRICING = {'deribit': False, 'bitcom': False, 'okex': False, 'delta': True, 'ledgerx': False}

class GvolFeed(object):

    def __init__(self, exchange):
        self.exchange = exchange
        try:
            with open(KEY_FILE, 'r') as f:
                k = f.readline()
            key = k.strip('\n')
        except:
            key = ""
        self.headers = HEADERS_TEMPLATE
        self.headers['gvol-lite-plus'] = key
        self.params = GRAPHQL_PARAMS_TEMPLATE.copy()
        self.params['variables'] = {"exchange": exchange}

    def get_exchange_data(self):
        res = requests.get(URL, json=self.params, headers=self.headers)

        if res.status_code != 200:
            print("error getting options from gvol for", self.exchange, res.status_code, res.text)
            return None
        json_data = res.json()
        if len(json_data) == 0 or len(json_data["data"]["UtilityRealtimeOptionbook"]) == 0 :
            print("error getting options from gvol for", self.exchange, res.status_code, res.text)
        return pd.DataFrame(res.json()["data"]["UtilityRealtimeOptionbook"])

    def request_exchange(self, now_date):
        exchange_data = self.get_exchange_data()
        exchange_data["expiration"] = pd.to_numeric(exchange_data["expiration"])//1000
        if FIAT_PRICING[self.exchange]:
            exchange_data["mid_price"] = (exchange_data["bestAskPrice"] + exchange_data["bestBidPrice"])/2
            exchange_data.loc[(exchange_data["bestAskPrice"] == 0) | (exchange_data["bestBidPrice"] == 0), "mid_price"] = np.nan
        else:
            exchange_data["mid_price"] = (exchange_data["usdAsk"] + exchange_data["usdBid"])/2
            exchange_data.loc[(exchange_data["usdAsk"] == 0) | (exchange_data["usdBid"] == 0), "mid_price"] = np.nan

        self.option_data = {c.value: exchange_data.loc[exchange_data['currency'] == c.value] for c in crypto_currencies}
