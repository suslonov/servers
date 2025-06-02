#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from enum import Enum

class crypto_currencies(Enum):
    BTC = "BTC"
    ETH = "ETH"
    # SOL = "SOL"
    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))

class Coinmarketcap(object):
    headers_template = {'Content-Type': "application/json", 'X-CMC_PRO_API_KEY': ''}
    key_file = 'coinmarketcap.sec' # free basic level is enough
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    RETRY_ATTEMPTS = 3
    
    def __init__(self):
        try:
            with open(self.key_file, 'r') as f:
                k = f.readline()
            key = k.strip('\n')
        except:
            key = ""
        self.headers = self.headers_template
        self.headers['X-CMC_PRO_API_KEY'] = key
        self.key = key

    def get_market_data(self, currencies):
        if not self.key:
            return None
        parameters = {'symbol': ','.join(currencies)}
        res = requests.get(self.url, params=parameters, headers=self.headers)
        if res.status_code != 200:
            print("error getting coinmarketcap data", res.status_code)
            print(res.json())
            return None
        d = res.json()
        return [d['data'][c]['quote']['USD']['market_cap'] for c in currencies]

class DeribitExchangeReader(object):
    headers = {'Content-Type': "application/json"}
    expiration_hour = 8
    url_currency = "https://www.deribit.com/api/v2/public/get_index_price?index_name={}_usd"
    url_options = "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency={}&kind=option"
    url_instruments = "https://www.deribit.com/api/v2/public/get_instruments?currency={}&expired=false&kind=option"
    url_DVOL = "https://www.deribit.com/api/v2/public/get_volatility_index_data?currency=BTC&end_timestamp={}&resolution=3600&start_timestamp={}"

    def get_currency(self, req_currency=crypto_currencies.BTC):
        url = self.url_currency.format(req_currency.value.lower())
        res = requests.get(url, headers=self.headers)
        if res.status_code != 200:
            print("error getting currency from Deribit", req_currency.value, res.status_code)
            print(res.json())
            return None

        c = res.json()
        # return c["result"][req_currency.value]
        return c["result"]["index_price"]

    def get_exchange_data(self, req_currency=crypto_currencies.BTC):
        url = self.url_options.format(req_currency.value)
        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            print("error getting options from Deribit", res.status_code)
            print(res.json())
            return None

        d = res.json()
        return d["result"]

    def get_instruments_data(self, req_currency=crypto_currencies.BTC):
        url = self.url_instruments.format(req_currency.value)
        res = requests.get(url, headers=self.headers)

        if res.status_code != 200:
            print("error getting instruments from Deribit", res.status_code)
            print(res.json())
            return None

        d = res.json()
        return d["result"]

    def request_exchange(self, now_date, db=None):
        self.option_data = [self.get_exchange_data(c) for c in crypto_currencies]
        self.currency = [self.get_currency(c) for c in crypto_currencies]
        self.instruments = [self.get_instruments_data(c) for c in crypto_currencies]
        if not db is None:
            db.add_raw_data_to_db(now_date, self.currency, self.option_data)

    def request_exchange_instruments(self):
        self.instruments = [self.get_instruments_data(c) for c in crypto_currencies]

    def load_from_db(self, point, db):
        c0, c1, o0, o1 = db.get_raw_data_from_db(point)
        self.option_data = [o0, o1]
        self.currency = [c0, c1]

    def clear_data(self):
        self.option_data = None
        self.currency = None
        self.instruments = None

