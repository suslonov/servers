#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sshtunnel
from enum import Enum
import MySQLdb
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import itertools
from pyfinance.options import BSM

from db_cvx import DBPoints

class crypto_currencies(Enum):
    BTC = "BTC"
    ETH = "ETH"
    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))

CONSTANT_VOLATILITY = 0.9
RISK_FREE = 0.01
EXPIRATION_HOUR = 8
MIN_TERM = 35
MAX_TERM = 90
DOWN_LIMIT = -0.6
UP_LIMIT = 1.3
FEE = 0.0003

rsynergy1_mysql = {"ssh_host": "crowd.mil.r-synergy.com",
                   "ssh_port": 22,
                   "ssh_username": "toshick",
                   "ssh_pkey": "~/.ssh/id_rsa",
                   "SSH_TIMEOUT": 30.0}

rsynergy2_mysql = {"ssh_host": "ramses.mil.r-synergy.com",
                   "ssh_port": 22,
                   "ssh_username": "anton",
                   "ssh_pkey": "~/.ssh/id_rsa",
                   "SSH_TIMEOUT": 30.0}

def open_remote_port(server_def):
    db_host = server_def["ssh_host"]
    ssh_port = server_def["ssh_port"]
    ssh_username = server_def["ssh_username"]
    ssh_private_key_password=""
    ssh_pkey = server_def["ssh_pkey"]
    sshtunnel.SSH_TIMEOUT = server_def["SSH_TIMEOUT"]

    server = sshtunnel.SSHTunnelForwarder(
                (db_host, ssh_port),
                ssh_username=ssh_username,
                ssh_private_key_password=ssh_private_key_password,
                ssh_pkey=ssh_pkey,
                remote_bind_address=('127.0.0.1', 3306))
    server.start()
    return server, server.local_bind_port

def close_remote_port(server):
    server.stop()

class DBPointsRemote(DBPoints):
    def __init__(self, server_def=rsynergy1_mysql):
        self.server_def = server_def

    def __enter__(self):
        self.server, port = open_remote_port(self.server_def)
        self.db = MySQLdb.connect(host=self.db_host, user=self.db_user, passwd=self.db_passwd, db=self.db_name, port=port)
        self.cursor = self.db.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.commit()
        self.db.close()
        close_remote_port(self.server)

######################

def IL_initial_value(ratio):
  return (2 * np.sqrt(ratio) - ratio - 1) / 2

class BS_calculator():
    def __init__(self):
        self.calls = {}
        self.puts = {}

    def black_scholes_call_price(self, volatility, K, t, S):
        if not (volatility, K, t, S) in self.calls:
            op = BSM(S0=S, K=K, T=t, r=RISK_FREE, sigma=volatility)
            value = op.value()
            self.calls[(volatility, K, t, S)] = value
            return value
        else:
            return self.calls[(volatility, K, t, S)]
    
    def black_scholes_put_price(self, volatility, K, t, S):
        if not (volatility, K, t, S) in self.puts:
            op = BSM(S0=S, K=K, T=t, r=RISK_FREE, sigma=volatility, kind="put")
            value = op.value()
            self.puts[(volatility, K, t, S)] = value
            return value
        else:
            return self.puts[(volatility, K, t, S)]
    
# corrected pyfinance IV calculation -- anton
    def black_scholes_implied_volatility(self, K, t, S, kind, value, precision=1.0e-5, iters=100):
        vol = CONSTANT_VOLATILITY
        for _ in itertools.repeat(None, iters):  # Faster than range
            opt = BSM(S0=S, K=K, T=t, r=RISK_FREE, sigma=vol, kind=("call" if (kind=="C" or kind=="call") else "put"))
            diff = value - opt.value()
            if abs(diff) < precision:
                return vol
            vol = vol + diff / opt.vega()
        return vol

    def black_scholes_vega(self, volatility, K, t, S, kind):
        op = BSM(S0=S, K=K, T=t, r=RISK_FREE, sigma=volatility, kind=("call" if kind=="C" else "put"))
        return op.summary()["Vega"]/100

    def black_scholes_summary(self, volatility, K, t, S, kind):
        op = BSM(S0=S, K=K, T=t, r=RISK_FREE, sigma=volatility, kind=("call" if kind=="C" else "put"))
        return op.summary()

BSC = BS_calculator()

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

def payout_put(strike, price):
    return (strike - price) if price < strike else 0

def payout_call(strike, price):
    return (price - strike) if price > strike else 0

def contract_payout(contract, p, metadata):
    strike = metadata.loc[contract]['strike']
    contract_type = metadata.loc[contract, "contract_type"]
    if contract_type == "C":
        return payout_call(strike, p)
    else:
        return payout_put(strike, p)

def contract_BS_price(contract, p, term_end, metadata):
    strike = metadata.loc[contract]['strike']
    vol = metadata.loc[contract, 'min_vol']
    t = (metadata.loc[contract, 'expiration_date'] - term_end).total_seconds() / (365 * 24 * 60 * 60)
    contract_type = metadata.loc[contract, "contract_type"]
    
    if contract_type == "C":
        return BSC.black_scholes_call_price(vol, strike, t, p)
    else:
        return BSC.black_scholes_put_price(vol, strike, t, p)

MMC = [None, 0]
def maximin(r, l):
# there should be linear programming. Fuck linear programming.
    mmc = MMC[0]
    mmc[0] = np.min([a * mmc.index / MMC[1] + b for a, b in zip(r, l)], axis=0)
    best_point = mmc[0].idxmax()
    best = mmc.iloc[best_point, 0]
    return best, best_point / MMC[1]


def is_expiration_good(expiration_date, min_expiration_date, time_point, term, to_expiration=False):
    if to_expiration:
        return (expiration_date - time_point).days >= term and (min_expiration_date is None or expiration_date < min_expiration_date)
    else:
        min_term = max(MIN_TERM, int(term * 1.1))
        max_term = max(MAX_TERM, int(term * 3.1))
        return (expiration_date - time_point).days >= min_term and (expiration_date - time_point).days <= max_term

def get_trend(df):
    df.fillna(method="ffill", inplace=True)
    df.fillna(method="bfill", inplace=True)
    df0 = df.iloc[-1].loc[np.isnan(df.iloc[-1])].to_frame()
    df0.columns = [0]
    df.dropna(axis=1, inplace=True)
    df_linear = np.polyfit(np.arange(0, len(df.index)), df, 1)
    return pd.concat([pd.DataFrame((df_linear[1, :] + df_linear[0, :] * (len(df.index)-1)).reshape(1, df.shape[1]),
                      columns=df.columns), df0.T], axis=1)

def set_dict_point(d, time_point, element, value):
    if not time_point in d:
        d[time_point] = {}
    d[time_point][element] = value

def load_data(points=10, term=30, strike_range=1.0): # ETH only

    d2 = datetime.utcnow()
    d1 = d2 - timedelta(minutes=points*2)
    with DBPointsRemote() as db:
        dp_list = db.get_raw_data_points_from_db(d1, d2)

    ask_price = {c: {} for c in crypto_currencies.values()}
    bid_price = {c: {} for c in crypto_currencies.values()}
    mid_price = {c: {} for c in crypto_currencies.values()}
    metadata = {c: {} for c in crypto_currencies.values()}
    rate_start = {c: None for c in crypto_currencies.values()}
    last_time_point = None
    good_expirations = None

    with DBPointsRemote() as db:
        for i in dp_list[:-11:-1]:
            time_point = i[0]
            ts = time_point
            if last_time_point is None:
                last_time_point = time_point
            btc, eth, options_data_btc, options_data_eth = db.get_raw_data_from_db(ts)
            options_data = {"BTC": options_data_btc, "ETH": options_data_eth}
            rate_start = {'BTC': btc, 'ETH': eth}
            for c in crypto_currencies.values():
                if good_expirations is None:
                    good_expirations = set()
                    min_expiration_date = None
                    for tick in options_data[c]:
                        instrument_descr = tick['instrument_name'].split('-')
                        expiration_date = datetime.strptime(instrument_descr[1], '%d%b%y') + pd.Timedelta(EXPIRATION_HOUR, "h")
                        if not expiration_date in good_expirations and is_expiration_good(expiration_date, min_expiration_date, time_point, term):
                            good_expirations.add(expiration_date)
                            if min_expiration_date is None or expiration_date < min_expiration_date:
                                min_expiration_date = expiration_date
    
                for tick in options_data[c]:
                    if not tick['ask_price'] or not tick['bid_price'] or not tick['mid_price']:
                        continue
                    instrument_descr = tick['instrument_name'].split('-')
                    expiration_date = datetime.strptime(instrument_descr[1], '%d%b%y') + pd.Timedelta(EXPIRATION_HOUR, "h")
                    strike = float(instrument_descr[2])
                    rate = rate_start[c]
                    if strike < rate * ( 1 - strike_range) or strike > rate * ( 1 + strike_range):
                        continue
                    if expiration_date in good_expirations:
                        if not tick['instrument_name'] in metadata:
                            metadata[tick['instrument_name']] = {'currency': c,
                                                                 'expiration_date': expiration_date,
                                                                 'strike': strike,
                                                                 'contract_type': instrument_descr[-1]}
                        set_dict_point(ask_price[c], time_point, tick['instrument_name'], tick['ask_price'] * rate_start[c])
                        set_dict_point(bid_price[c], time_point, tick['instrument_name'], tick['bid_price'] * rate_start[c])
                        set_dict_point(mid_price[c], time_point, tick['instrument_name'], tick['mid_price'] * rate_start[c])
                        t = (expiration_date - time_point).total_seconds() / (365 * 24 * 60 * 60)
                        metadata[tick['instrument_name']]["term"] = t
                        metadata[tick['instrument_name']]["implied_vol"] = BSC.black_scholes_implied_volatility(strike, t, rate_start[c], instrument_descr[-1], tick['mid_price'] * rate_start[c])
                        op = BSC.black_scholes_summary(metadata[tick['instrument_name']]["implied_vol"], strike, t, rate_start[c], instrument_descr[-1])
                        metadata[tick['instrument_name']]["Vega"] = op["Vega"]/100
                        metadata[tick['instrument_name']]["Delta"] = op["Delta"]

    for c in crypto_currencies.values():
        ask_price[c] = get_trend(pd.DataFrame.from_dict(ask_price[c], orient='index'))
        bid_price[c] = get_trend(pd.DataFrame.from_dict(bid_price[c], orient='index'))
        mid_price[c] = get_trend(pd.DataFrame.from_dict(mid_price[c], orient='index'))

    metadata = pd.DataFrame.from_dict(metadata, orient='index')

    return rate_start, good_expirations, last_time_point, ask_price, bid_price, mid_price, metadata

def find_best_cvi_hedge(amount, term, strike_range):
    rate_start, good_expirations, time_point, ask_price, bid_price, mid_price, metadata = load_data(term=term, strike_range=strike_range)
    if amount <= 0:
        return None, None, None, None, None

    plans = []
    for c in crypto_currencies.values():
        for expiration in metadata.groupby(["expiration_date"]).count().index:
            one_date = metadata.loc[(metadata["expiration_date"] == expiration) & (metadata["currency"] == c)].sort_values(["strike", "contract_type"])
            plans.extend([v for v in generate_straddles(one_date, c)])
            plans.extend([v for v in generate_strangles(one_date, c)])
            plans.extend([v for v in generate_guts(one_date, c)])

    plans_df = pd.DataFrame.from_records(plans)
    for c in crypto_currencies.values():
        plans_df.loc[plans_df["currency"] == c, "price_put"] = ask_price[c].T.loc[plans_df.loc[plans_df["currency"] == c, "put"]].values
        plans_df.loc[plans_df["currency"] == c, "price_call"] = ask_price[c].T.loc[plans_df.loc[plans_df["currency"] == c, "call"]].values
        plans_df.loc[plans_df["currency"] == c, "Vega_put"] = metadata.loc[plans_df.loc[plans_df["currency"] == c, "put"], "Vega"].values
        plans_df.loc[plans_df["currency"] == c, "Vega_call"] = metadata.loc[plans_df.loc[plans_df["currency"] == c, "call"], "Vega"].values
        plans_df.loc[plans_df["currency"] == c, "Delta_put"] = metadata.loc[plans_df.loc[plans_df["currency"] == c, "put"], "Delta"].values
        plans_df.loc[plans_df["currency"] == c, "Delta_call"] = metadata.loc[plans_df.loc[plans_df["currency"] == c, "call"], "Delta"].values
    plans_df["price"] = plans_df["price_put"]/plans_df["Vega_put"] + plans_df["price_call"]/plans_df["Vega_call"]
    plans_df["min_vega"] = plans_df[["Vega_put", "Vega_call"]].min(axis=1)
    plans_df["closest"] = (metadata.loc[plans_df["put"], "expiration_date"] == min(good_expirations)).values
    plans_df.dropna(inplace=True)

    best_strategies = plans_df.loc[plans_df.groupby(["currency"])["price"].idxmin()].set_index(["currency"])
    max_Vega_strategies = plans_df.loc[plans_df.groupby(["currency"])["min_vega"].idxmax()].set_index(["currency"])
    plans_df_closest = plans_df.loc[plans_df["closest"]]
    best_strategies_closest = plans_df_closest.loc[plans_df_closest.groupby(["currency"])["price"].idxmin()].set_index(["currency"])
    max_Vega_strategies_closest = plans_df_closest.loc[plans_df_closest.groupby(["currency"])["min_vega"].idxmax()].set_index(["currency"])

    return best_strategies, max_Vega_strategies, best_strategies_closest, max_Vega_strategies_closest, rate_start

def funding_fee(cvi):
    return round(min(0.1, 0.1 * np.power(1/2, (cvi-50)/5) + 0.003), 4) if cvi <= 150 else 0.002

def load_ff(term):
    with DBPointsRemote() as db:
        cvi_list = db.get_last_minute_from_db("v003")
        cvi = round(cvi_list[4], 4)
        cvi_ff = funding_fee(cvi)
        cvi_ff_amount = cvi_ff * term * 24
        # cvi_average_list = db.get_average_from_db("v003")
        # cvi_avg = round(cvi_average_list[0], 4)
        cvi_avg = 85.75
        cvi_avg_ff = funding_fee(cvi_avg)
        cvi_avg_ff_amount = cvi_avg_ff * term * 24
    return {"cvi": cvi, "cvi_avg": cvi_avg, "cvi_ff": cvi_ff, "cvi_avg_ff": cvi_avg_ff, "cvi_ff_amount": cvi_ff_amount, "cvi_avg_ff_amount": cvi_avg_ff_amount}

def prepare_best_cvi_hedge(amount, term, strike_range=1.0):
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
    best_strategies, rate_start, funding_fee = prepare_best_cvi_hedge(amount, term, strike_range)
    
    print(best_strategies)
