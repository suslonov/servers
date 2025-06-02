#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sshtunnel
import MySQLdb
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pyfinance.options import BSM

from db_cvx import DBPoints

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
    
    def black_scholes_implied_volatility(self, K, t, S, kind, value):
        op = BSM(S0=S, K=K, T=t, r=RISK_FREE, sigma=CONSTANT_VOLATILITY, kind=("call" if kind=="C" else "put"))
        return op.implied_vol(value=value)

BSC = BS_calculator()

def generate_no_hedge():
    return {"type":"no_hedge"}

def generate_strangles(one_date_contracts, underlying_price):
    for i1, p1 in enumerate(one_date_contracts.index):
        if one_date_contracts.loc[p1, "contract_type"] != "P":
            continue
        if one_date_contracts.loc[p1, "strike"] >= underlying_price.iloc[0][p1]:
            break
        for c1 in one_date_contracts.index[i1+1:]:
            if one_date_contracts.loc[c1, "contract_type"] != "C":
                continue
            if one_date_contracts.loc[c1, "strike"] <= underlying_price.iloc[0][c1]:
                continue
            yield {"type":"strangle", "put1": p1, "call1": c1}

def generate_condors(one_date_contracts, underlying_price):
    for i1, p2 in enumerate(one_date_contracts.index):
        if one_date_contracts.loc[p2, "contract_type"] != "P":
            continue
        if one_date_contracts.loc[p2, "strike"] >= underlying_price.iloc[0][p2]:
            break
        for i2, p1 in enumerate(one_date_contracts.index[i1+1:]):
            if one_date_contracts.loc[p1, "contract_type"] != "P":
                continue
            if one_date_contracts.loc[p1, "strike"] >= underlying_price.iloc[0][p1]:
                break
            if one_date_contracts.loc[p2, "strike"] >= one_date_contracts.loc[p1, "strike"]:
                break
            for i3, c1 in enumerate(one_date_contracts.index[i1+i2+2:]):
                if one_date_contracts.loc[c1, "contract_type"] != "C":
                    continue
                if one_date_contracts.loc[c1, "strike"] <= underlying_price.iloc[0][c1]:
                    continue
                for c2 in one_date_contracts.index[i1+i2+i3+3:]:
                    if one_date_contracts.loc[c2, "contract_type"] != "C":
                        continue
                    if one_date_contracts.loc[c2, "strike"] <= underlying_price.iloc[0][c2]:
                        continue
                    if one_date_contracts.loc[c2, "strike"] <= one_date_contracts.loc[c1, "strike"]:
                        continue

                    yield {"type":"condor", "put1": p1, "call1": c1, "put2": p2, "call2": c2}

def generate_condors_left(one_date_contracts, underlying_price):
    for i1, p2 in enumerate(one_date_contracts.index):
        if one_date_contracts.loc[p2, "contract_type"] != "P":
            continue
        if one_date_contracts.loc[p2, "strike"] >= underlying_price.iloc[0][p2]:
            break
        for i2, p1 in enumerate(one_date_contracts.index[i1+1:]):
            if one_date_contracts.loc[p1, "contract_type"] != "P":
                continue
            if one_date_contracts.loc[p1, "strike"] >= underlying_price.iloc[0][p1]:
                break
            if one_date_contracts.loc[p2, "strike"] >= one_date_contracts.loc[p1, "strike"]:
                break
            for c1 in one_date_contracts.index[i1+i2+2:]:
                if one_date_contracts.loc[c1, "contract_type"] != "C":
                    continue
                if one_date_contracts.loc[c1, "strike"] <= underlying_price.iloc[0][c1]:
                    continue
                yield {"type":"condor_left", "put1": p1, "call1": c1, "put2": p2}

def generate_condors_right(one_date_contracts, underlying_price):
    for i1, p1 in enumerate(one_date_contracts.index):
        if one_date_contracts.loc[p1, "contract_type"] != "P":
            continue
        if one_date_contracts.loc[p1, "strike"] >= underlying_price.iloc[0][p1]:
            break
        for i2, c1 in enumerate(one_date_contracts.index[i1+1:]):
            if one_date_contracts.loc[c1, "contract_type"] != "C":
                continue
            if one_date_contracts.loc[c1, "strike"] <= underlying_price.iloc[0][c1]:
                continue
            for c2 in one_date_contracts.index[i1+i2+2:]:
                if one_date_contracts.loc[c2, "contract_type"] != "C":
                    continue
                if one_date_contracts.loc[c2, "strike"] <= underlying_price.iloc[0][c2]:
                    continue
                if one_date_contracts.loc[c2, "strike"] <= one_date_contracts.loc[c1, "strike"]:
                    continue
                yield {"type":"condor_right", "put1": p1, "call1": c1, "call2": c2}

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

def plan_forecasts(price, plan, term_end, ask_price, bid_price, metadata, to_expiration=False):
    ratio = plan['ratio'] if plan['type'] != 'no_hedge' else 1
    prices = [price * (1 + DOWN_LIMIT), price * (1 + UP_LIMIT)]
    start_prices = {}

    for row in plan:
        if row in ['call', 'put', 'call1', 'put1']:
            prices.append(metadata.loc[plan[row]]['strike'])
            start_prices[plan[row]] = -ask_price[plan[row]].iloc[0] * price
        elif row in ['call2', 'put2']:
            prices.append(metadata.loc[plan[row]]['strike'])
            start_prices[plan[row]] = bid_price[plan[row]].iloc[0] * price
    prices.sort()

    forecasts = {}
    for row in plan:
        if row in ['call', 'put', 'call1', 'put1']:
            forecasts[plan[row]] = {}
            for p in prices:
                if to_expiration:
                    forecasts[plan[row]][round(p, 2)] = round(contract_payout(plan[row], p, metadata), 4)
                else:
                    forecasts[plan[row]][round(p, 2)] = round(contract_BS_price(plan[row], p, term_end, metadata), 4)
        elif row in ['call2', 'put2']:
            forecasts[plan[row]] = {}
            for p in prices:
                if to_expiration:
                    forecasts[plan[row]][round(p, 2)] = -round(contract_payout(plan[row], p, metadata), 4)
                else:
                    forecasts[plan[row]][round(p, 2)] = -round(contract_BS_price(plan[row], p, term_end, metadata), 4)
    forecasts['il'] = {}
    forecasts['saldo'] = {}
    for p in prices:
        round_p = round(p, 2)
        forecasts['il'][round_p] = round(IL_initial_value(p / price) * price, 4)
        saldo = 0
        for contract in forecasts:
            if contract == 'il':
                saldo += forecasts['il'][round_p]
            elif contract != 'saldo':
                saldo += (start_prices[contract] + forecasts[contract][round_p] - (0 if to_expiration else FEE * p) - FEE * price) * ratio
        forecasts['saldo'][round_p] = round(saldo, 2)
    return forecasts

MMC = [None, 0]
def maximin(r, l):
# there should be linear programming. Fuck linear programming.
    mmc = MMC[0]
    mmc[0] = np.min([a * mmc.index / MMC[1] + b for a, b in zip(r, l)], axis=0)
    best_point = mmc[0].idxmax()
    best = mmc.iloc[best_point, 0]
    return best, best_point / MMC[1]
    
def eval_no_hedge(v, price, term_end, metadata, ask_price, bid_price, ratio, no_hedge, fit_ratio, amount, to_expiration=False):
    p = price * (1 + DOWN_LIMIT)
    i1 = IL_initial_value(p / price) * price
    
    p = price * (1 + UP_LIMIT)
    i2 = IL_initial_value(p / price) * price

    return min(i1, i2)

def eval_strangle(v, price, term_end, metadata, ask_price, bid_price, ratio, no_hedge, fit_ratio, amount, to_expiration=False):
    put1 = v['put1']
    put1_strike = metadata.loc[put1]['strike']
    put1_price = ask_price[put1][0] * price
    call1 = v['call1']
    call1_strike = metadata.loc[call1]['strike']
    call1_price = ask_price[call1][0] * price
    vol = metadata.loc[put1, "min_vol"]    
    t = (metadata.loc[put1, 'expiration_date'] - term_end).total_seconds() / (365 * 24 * 60 * 60)

    p = price * (1 + DOWN_LIMIT)
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - FEE * p * 2
    r1 = - put1_price - call1_price + bs - FEE * price * 2
    i1 = IL_initial_value(p / price) * price
    
    p = put1_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - FEE * p * 2
    r2 = - put1_price - call1_price + bs - FEE * price * 2
    i2 = IL_initial_value(p / price) * price

    p = call1_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - FEE * p * 2
    r3 = - put1_price - call1_price + bs - FEE * price * 2
    i3 = IL_initial_value(p / price) * price

    p = price * (1 + UP_LIMIT)
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - FEE * p * 2
    r4 = - put1_price - call1_price + bs - FEE * price * 2
    i4 = IL_initial_value(p / price) * price

    if np.isnan([r1, r2, r3, r4]).any():
        v["ratio"] = 0
        return np.nan
    if fit_ratio and not no_hedge:
        max_steps_contracts = int(amount/price)
        MMC[0] = pd.DataFrame(np.zeros(max_steps_contracts+1), index = np.arange(max_steps_contracts+1))
        MMC[1] = max_steps_contracts
        r, ratio = maximin([r1, r2, r3, r4], [i1, i2, i3, i4])
        v["ratio"] = ratio
        return r
    else:
        if no_hedge:
            v["ratio"] = 1
            return min(r1, r2, r3, r4)
        else:
            v["ratio"] = ratio
            return min(r1 * ratio + i1, r2 * ratio + i2, r3 * ratio + i3, r4 * ratio + i4)

def eval_condor_right(v, price, term_end, metadata, ask_price, bid_price, ratio, no_hedge, fit_ratio, amount, to_expiration=False):
    put1 = v['put1']
    put1_strike = metadata.loc[put1]['strike']
    put1_price = ask_price[put1][0] * price
    call1 = v['call1']
    call1_strike = metadata.loc[call1]['strike']
    call1_price = ask_price[call1][0] * price
    call2 = v['call2']
    call2_strike = metadata.loc[call2]['strike']
    call2_price = bid_price[call2][0] * price
    vol = metadata.loc[put1, "min_vol"]    
    t = (metadata.loc[put1, 'expiration_date'] - term_end).total_seconds() / (365 * 24 * 60 * 60)
   
    p = price * (1 + DOWN_LIMIT)
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 3
    r1 = - put1_price - call1_price + call2_price + bs - FEE * price * 3
    i1 = IL_initial_value(p / price) * price
    
    p = put1_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 3
    r2 = - put1_price - call1_price + call2_price + bs - FEE * price * 3
    i2 = IL_initial_value(p / price) * price
    
    p = call1_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 3
    r4 = - put1_price - call1_price + call2_price + bs - FEE * price * 3
    i4 = IL_initial_value(p / price) * price
    
    p = call2_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 3
    r5 = - put1_price - call1_price + call2_price + bs - FEE * price * 3
    i5 = IL_initial_value(p / price) * price
    
    p = price * (1 + UP_LIMIT)
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 3
    r6 = - put1_price - call1_price + call2_price + bs - FEE * price * 3
    i6 = IL_initial_value(p / price) * price
    
    if np.isnan([r1, r2, r4, r5, r6]).any():
        v["ratio"] = 0
        return np.nan
    if fit_ratio and not no_hedge:
        max_steps_contracts = int(amount/price)
        MMC[0] = pd.DataFrame(np.zeros(max_steps_contracts+1), index = np.arange(max_steps_contracts+1))
        MMC[1] = max_steps_contracts
        r, ratio = maximin([r1, r2, r4, r5, r6], [i1, i2, i4, i5, i6])
        v["ratio"] = ratio
        return r
    else:
        if no_hedge:
            v["ratio"] = 1
            return min(r1, r2, r4, r5, r6)
        else:
            v["ratio"] = ratio
            return min(r1 * ratio + i1, r2 * ratio + i2, r4 * ratio + i4, r5 * ratio + i5, r6 * ratio + i6)

def eval_condor_left(v, price, term_end, metadata, ask_price, bid_price, ratio, no_hedge, fit_ratio, amount, to_expiration=False):
    put1 = v['put1']
    put1_strike = metadata.loc[put1]['strike']
    put1_price = ask_price[put1][0] * price
    put2 = v['put2']
    put2_strike = metadata.loc[put2]['strike']
    put2_price = bid_price[put2][0] * price
    call1 = v['call1']
    call1_strike = metadata.loc[call1]['strike']
    call1_price = ask_price[call1][0] * price
    vol = metadata.loc[put1, "min_vol"]    
    t = (metadata.loc[put1, 'expiration_date'] - term_end).total_seconds() / (365 * 24 * 60 * 60)
   
    p = price * (1 + DOWN_LIMIT)
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - FEE * p * 3
    r1 = - put1_price - call1_price + put2_price + bs - FEE * price * 3
    i1 = IL_initial_value(p / price) * price
    
    p = put1_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - FEE * p * 3
    r2 = - put1_price - call1_price + put2_price + bs - FEE * price * 3
    i2 = IL_initial_value(p / price) * price
    
    p = put2_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - FEE * p * 3
    r3 = - put1_price - call1_price + put2_price + bs - FEE * price * 3
    i3 = IL_initial_value(p / price) * price
    
    p = call1_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - FEE * p * 3
    r4 = - put1_price - call1_price + put2_price + bs - FEE * price * 3
    i4 = IL_initial_value(p / price) * price
    
    p = price * (1 + UP_LIMIT)
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - FEE * p * 3
    r6 = - put1_price - call1_price + put2_price + bs - FEE * price * 3
    i6 = IL_initial_value(p / price) * price
    
    if np.isnan([r1, r2, r3, r4, r6]).any():
        v["ratio"] = 0
        return np.nan
    if fit_ratio and not no_hedge:
        max_steps_contracts = int(amount/price)
        MMC[0] = pd.DataFrame(np.zeros(max_steps_contracts+1), index = np.arange(max_steps_contracts+1))
        MMC[1] = max_steps_contracts
        r, ratio = maximin([r1, r2, r3, r4, r6], [i1, i2, i3, i4, i6])
        v["ratio"] = ratio
        return r
    else:
        if no_hedge:
            v["ratio"] = 1
            return min(r1, r2, r3, r4, r6)
        else:
            v["ratio"] = ratio
            return min(r1 * ratio + i1, r2 * ratio + i2, r3 * ratio + i3, r4 * ratio + i4, r6 * ratio + i6)

def eval_condor(v, price, term_end, metadata, ask_price, bid_price, ratio, no_hedge, fit_ratio, amount, to_expiration=False):
    if not 'put2' in v:
        return eval_condor_right(v, price, term_end, metadata, ask_price, bid_price)
    if not 'call2' in v:
        return eval_condor_left(v, price, term_end, metadata, ask_price, bid_price)
    put1 = v['put1']
    put1_strike = metadata.loc[put1]['strike']
    put1_price = ask_price[put1][0] * price
    put2 = v['put2']
    put2_strike = metadata.loc[put2]['strike']
    put2_price = bid_price[put2][0] * price
    call1 = v['call1']
    call1_strike = metadata.loc[call1]['strike']
    call1_price = ask_price[call1][0] * price
    call2 = v['call2']
    call2_strike = metadata.loc[call2]['strike']
    call2_price = bid_price[call2][0] * price
    vol = metadata.loc[put1, "min_vol"]    
    t = (metadata.loc[put1, 'expiration_date'] - term_end).total_seconds() / (365 * 24 * 60 * 60)
   
    p = price * (1 + DOWN_LIMIT)
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 4
    r1 = - put1_price - call1_price + put2_price + call2_price + bs - FEE * price * 4
    i1 = IL_initial_value(p / price) * price
    
    p = put1_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 4
    r2 = - put1_price - call1_price + put2_price + call2_price + bs - FEE * price * 4
    i2 = IL_initial_value(p / price) * price
    
    p = put2_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 4
    r3 = - put1_price - call1_price + put2_price + call2_price + bs - FEE * price * 4
    i3 = IL_initial_value(p / price) * price
    
    p = call1_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 4
    r4 = - put1_price - call1_price + put2_price + call2_price + bs - FEE * price * 4
    i4 = IL_initial_value(p / price) * price
    
    p = call2_strike
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 4
    r5 = - put1_price - call1_price + put2_price + call2_price + bs - FEE * price * 4
    i5 = IL_initial_value(p / price) * price
    
    p = price * (1 + UP_LIMIT)
    if to_expiration:
        bs = payout_put(put1_strike, p) + payout_call(call1_strike, p) - payout_put(put2_strike, p) - payout_call(call2_strike, p)
    else:
        bs = BSC.black_scholes_put_price(vol, put1_strike, t, p) + BSC.black_scholes_call_price(vol, call1_strike, t, p) - BSC.black_scholes_put_price(vol, put2_strike, t, p) - BSC.black_scholes_call_price(vol, call2_strike, t, p) - FEE * p * 4
    r6 = - put1_price - call1_price + put2_price + call2_price + bs - FEE * price * 4
    i6 = IL_initial_value(p / price) * price
    
    if np.isnan([r1, r2, r3, r4, r5, r6]).any():
        v["ratio"] = 0
        return np.nan
    if fit_ratio and not no_hedge:
        max_steps_contracts = int(amount/price)
        MMC[0] = pd.DataFrame(np.zeros(max_steps_contracts+1), index = np.arange(max_steps_contracts+1))
        MMC[1] = max_steps_contracts
        r, ratio = maximin([r1, r2, r3, r4, r5, r6], [i1, i2, i3, i4, i5, i6])
        v["ratio"] = ratio
        return r
    else:
        if no_hedge:
            v["ratio"] = 1
            return min(r1, r2, r3, r4, r5, r6)
        else:
            v["ratio"] = ratio
            return min(r1 * ratio + i1, r2 * ratio + i2, r3 * ratio + i3, r4 * ratio + i4, r5 * ratio + i5, r6 * ratio + i6)

evaluation_functions = {'no_hedge': eval_no_hedge, 'strangle': eval_strangle, 'condor': eval_condor, 'condor_left': eval_condor_left, 'condor_right': eval_condor_right}

def is_expiration_good(expiration_date, min_expiration_date, time_point, term, to_expiration=False):
    if to_expiration:
        return (expiration_date - time_point).days >= term and (min_expiration_date is None or expiration_date < min_expiration_date)
    else:
        min_term = max(MIN_TERM, int(term * 1.1))
        max_term = max(MAX_TERM, int(term * 3.1))
        return (expiration_date - time_point).days >= min_term and (expiration_date - time_point).days <= max_term


def load_data(points=10, term=30, to_expiration=False): # ETH only

    d2 = datetime.utcnow()
    d1 = d2 - timedelta(minutes=points*2)
    with DBPointsRemote() as db:
        dp_list = db.get_raw_data_points_from_db(d1, d2)

    ask_price = {}
    bid_price = {}
    underlying_price = {}
    metadata = {}
    rate_start = None
    last_time_point = None
    good_expirations = None

    with DBPointsRemote() as db:
        for i in dp_list[:-11:-1]:
            time_point = i[0]
            ts = time_point
            if last_time_point is None:
                last_time_point = time_point
            _, eth, _, options_data = db.get_raw_data_from_db(ts)
            if not rate_start:
                rate_start = eth
            if good_expirations is None:
                good_expirations = set()
                min_expiration_date = None
                for tick in options_data:
                    instrument_descr = tick['instrument_name'].split('-')
                    expiration_date = datetime.strptime(instrument_descr[1], '%d%b%y') + pd.Timedelta(EXPIRATION_HOUR, "h")
                    if not expiration_date in good_expirations and is_expiration_good(expiration_date, min_expiration_date, time_point, term, to_expiration):
                        good_expirations.add(expiration_date)
                        if min_expiration_date is None or expiration_date < min_expiration_date:
                            min_expiration_date = expiration_date

            for tick in options_data:
                instrument_descr = tick['instrument_name'].split('-')
                expiration_date = datetime.strptime(instrument_descr[1], '%d%b%y') + pd.Timedelta(EXPIRATION_HOUR, "h")
                if expiration_date in good_expirations:
                    strike = float(instrument_descr[2])
                    if not tick['instrument_name'] in metadata:
                        metadata[tick['instrument_name']] = {'expiration_date': expiration_date,
                                                         'strike': strike,
                                                         'contract_type': instrument_descr[-1]}
                    if not time_point in ask_price:
                        ask_price[time_point] = {}
                    if not time_point in bid_price:
                        bid_price[time_point] = {}
                    if not time_point in underlying_price:
                        underlying_price[time_point] = {}
                    ask_price[time_point][tick['instrument_name']] = tick['ask_price'] if tick['ask_price'] else np.nan
                    bid_price[time_point][tick['instrument_name']] = tick['bid_price'] if tick['bid_price'] else np.nan
                    underlying_price[time_point][tick['instrument_name']] = tick['underlying_price']
                    t = (expiration_date - time_point).total_seconds() / (365 * 24 * 60 * 60)
                    if tick['ask_price'] and abs(strike/tick['underlying_price'] - 1) < 0.1: # take close-to-money strikes only
                        metadata[tick['instrument_name']]["implied_vol"] = BSC.black_scholes_implied_volatility(strike, t, eth, instrument_descr[-1], tick['ask_price'] * eth)
                    else:
                        metadata[tick['instrument_name']]["implied_vol"] = np.nan

    ask_price = pd.DataFrame.from_dict(ask_price, orient='index')
    bid_price = pd.DataFrame.from_dict(bid_price, orient='index')
    underlying_price = pd.DataFrame.from_dict(underlying_price, orient='index')
    metadata = pd.DataFrame.from_dict(metadata, orient='index')

    ask_price.fillna(method="ffill", inplace=True)
    ask_price.fillna(method="bfill", inplace=True)
    bid_price.fillna(method="ffill", inplace=True)
    bid_price.fillna(method="bfill", inplace=True)
    ask_price0 = ask_price.iloc[-1].loc[np.isnan(ask_price.iloc[-1])].to_frame()
    bid_price0 = bid_price.iloc[-1].loc[np.isnan(bid_price.iloc[-1])].to_frame()
    ask_price0.columns = [0]
    bid_price0.columns = [0]
    ask_price.dropna(axis=1, inplace=True)
    bid_price.dropna(axis=1, inplace=True)
    ask_price_linear = np.polyfit(np.arange(0, len(ask_price.index)), ask_price, 1)
    bid_price_linear = np.polyfit(np.arange(0, len(bid_price.index)), bid_price, 1)
    underlying_price_linear = np.polyfit(np.arange(0, len(underlying_price.index)), underlying_price, 1)
    ask_price = pd.DataFrame((ask_price_linear[1, :] + ask_price_linear[0, :] * (len(ask_price.index)-1)).reshape(1, ask_price.shape[1]), columns=ask_price.columns)
    bid_price = pd.DataFrame((bid_price_linear[1, :] + bid_price_linear[0, :] * (len(bid_price.index)-1)).reshape(1, bid_price.shape[1]), columns=bid_price.columns)
    underlying_price = pd.DataFrame((underlying_price_linear[1, :] + underlying_price_linear[0, :] * (len(underlying_price.index)-1)).reshape(1, underlying_price.shape[1]), columns=underlying_price.columns)
    ask_price = pd.concat([ask_price, ask_price0.T], axis=1)
    bid_price = pd.concat([bid_price, bid_price0.T], axis=1)

    return rate_start, good_expirations, last_time_point, ask_price, bid_price, underlying_price, metadata

def find_best_plan(amount, ratios, no_hedge, fit_ratio, term):
    rate_start, good_expirations, time_point, ask_price, bid_price, underlying_price, metadata = load_data(term=term)
    if amount/rate_start < 1 and amount != 0:
        return {}, 0, [], 0
    term_end = time_point + timedelta(days=term)

    plans = {}
    metadata['min_vol'] = np.nan
    for expiration in metadata.groupby(["expiration_date"]).count().index:
        one_date = metadata.loc[metadata["expiration_date"] == expiration].sort_values(["strike"])
        plans["no_hedge"] = [generate_no_hedge()]
        plans["strangle"] = [v for v in generate_strangles(one_date, underlying_price)]
        plans["condor"] = [v for v in generate_condors(one_date, underlying_price)]
        plans["condor_left"] = [v for v in generate_condors_left(one_date, underlying_price)]
        plans["condor_right"] = [v for v in generate_condors_right(one_date, underlying_price)]
        metadata.loc[metadata["expiration_date"] == expiration, "min_vol"] = metadata.loc[metadata["expiration_date"] == expiration, "implied_vol"].min()

    BSC.calls = {}
    BSC.puts = {}
    best_plan = {'no_hedge': None, 'strangle': None, 'condor': None, 'condor_left': None, 'condor_right': None}
    best_plan_forecast = {'no_hedge': None, 'strangle': None, 'condor': None, 'condor_left': None, 'condor_right': None}
    for plan_type in plans:
        for v in plans[plan_type]:
            plan_forecast = evaluation_functions[plan_type](v, rate_start, term_end, metadata, 
                                                        ask_price, bid_price, ratios[plan_type] if plan_type != 'no_hedge' else 1, 
                                                        no_hedge, fit_ratio, amount if amount != 0 else rate_start * 1000)
            if best_plan_forecast[plan_type] is None or best_plan_forecast[plan_type] < plan_forecast:
                best_plan_forecast[plan_type] = plan_forecast
                best_plan[plan_type] = v

    best_strategies = []
    for plan_type in best_plan:
        strategy_contracts = []
        plan_price = 0
        forecasts = plan_forecasts(rate_start, best_plan[plan_type], term_end, ask_price, bid_price, metadata)
        for row in best_plan[plan_type]:
            if row in ['call', 'put', 'call1', 'put1']:
                price = ask_price[best_plan[plan_type][row]].iloc[0] * rate_start
                plan_price += (price + FEE * rate_start) * best_plan[plan_type]['ratio']
                strategy_contracts.append(('buy', best_plan[plan_type][row], round(price, 2), forecasts[best_plan[plan_type][row]]))
            elif row in ['call2', 'put2']:
                price = bid_price[best_plan[plan_type][row]].iloc[0] * rate_start
                plan_price += (-price + FEE * rate_start) * best_plan[plan_type]['ratio']
                strategy_contracts.append(('sell', best_plan[plan_type][row], round(price, 2), forecasts[best_plan[plan_type][row]]))
        strategy_contracts.append(("", 'il', "", forecasts['il']))
        strategy_contracts.append(("", 'saldo', "", forecasts['saldo']))
        if 'ratio' in best_plan[plan_type]:
            strategy_contracts.append(("", 'ratio', round(best_plan[plan_type]['ratio'], 3), ""))
        best_strategies.append((round(best_plan_forecast[plan_type], 4), plan_type, strategy_contracts, round(plan_price, 2)))
    best_strategies.sort(reverse=True)

    return best_strategies, rate_start, (int(amount/rate_start * best_plan[best_strategies[0][1]]['ratio']) if amount !=0 else 0), 0


def find_best_plan_to_expiration(amount, ratios, no_hedge, fit_ratio, term):
    rate_start, good_expirations, time_point, ask_price, bid_price, underlying_price, metadata = load_data(term=term, to_expiration=True)
    if amount/rate_start < 1 and amount != 0:
        return {}, 0, [], 0
    term_end = time_point + timedelta(days=term)

    plans = {}
    metadata['min_vol'] = np.nan
    for expiration in metadata.groupby(["expiration_date"]).count().index:
        one_date = metadata.loc[metadata["expiration_date"] == expiration].sort_values(["strike"])
        plans["no_hedge"] = [generate_no_hedge()]
        plans["strangle"] = [v for v in generate_strangles(one_date, underlying_price)]
        plans["condor"] = [v for v in generate_condors(one_date, underlying_price)]
        plans["condor_left"] = [v for v in generate_condors_left(one_date, underlying_price)]
        plans["condor_right"] = [v for v in generate_condors_right(one_date, underlying_price)]
        metadata.loc[metadata["expiration_date"] == expiration, "min_vol"] = metadata.loc[metadata["expiration_date"] == expiration, "implied_vol"].min()

    BSC.calls = {}
    BSC.puts = {}
    best_plan = {'no_hedge': None, 'strangle': None, 'condor': None, 'condor_left': None, 'condor_right': None}
    best_plan_forecast = {'no_hedge': None, 'strangle': None, 'condor': None, 'condor_left': None, 'condor_right': None}
    for plan_type in plans:
        for v in plans[plan_type]:
            plan_forecast = evaluation_functions[plan_type](v, rate_start, term_end, metadata, 
                                                        ask_price, bid_price, ratios[plan_type] if plan_type != 'no_hedge' else 1, 
                                                        no_hedge, fit_ratio, amount if amount != 0 else rate_start * 1000, to_expiration=True)
            if best_plan_forecast[plan_type] is None or best_plan_forecast[plan_type] < plan_forecast:
                best_plan_forecast[plan_type] = plan_forecast
                best_plan[plan_type] = v

    best_strategies = []
    for plan_type in best_plan:
        strategy_contracts = []
        plan_price = 0
        forecasts = plan_forecasts(rate_start, best_plan[plan_type], term_end, ask_price, bid_price, metadata, to_expiration=True)
        for row in best_plan[plan_type]:
            if row in ['call', 'put', 'call1', 'put1']:
                price = ask_price[best_plan[plan_type][row]].iloc[0] * rate_start
                plan_price += (price + FEE * rate_start) * best_plan[plan_type]['ratio']
                strategy_contracts.append(('buy', best_plan[plan_type][row], round(price, 2), forecasts[best_plan[plan_type][row]]))
            elif row in ['call2', 'put2']:
                price = bid_price[best_plan[plan_type][row]].iloc[0] * rate_start
                plan_price += (-price + FEE * rate_start) * best_plan[plan_type]['ratio']
                strategy_contracts.append(('sell', best_plan[plan_type][row], round(price, 2), forecasts[best_plan[plan_type][row]]))
        strategy_contracts.append(("", 'il', "", forecasts['il']))
        strategy_contracts.append(("", 'saldo', "", forecasts['saldo']))
        if 'ratio' in best_plan[plan_type]:
            strategy_contracts.append(("", 'ratio', round(best_plan[plan_type]['ratio'], 3), ""))
        best_strategies.append((round(best_plan_forecast[plan_type], 4), plan_type, strategy_contracts, round(plan_price, 2)))
    best_strategies.sort(reverse=True)

    capital_adjustment = max((list(good_expirations)[0] - time_point).days/term, 1)

    return best_strategies, rate_start, (int(amount/rate_start * best_plan[best_strategies[0][1]]['ratio']) if amount !=0 else 0), capital_adjustment


def test():
    amount = 100000
    ratios = {"strangle": 0.159, "condor": 0.166, "condor_left": 0.159, "condor_right": 0.159}
    no_hedge = False
    fit_ratio = False
    term = 30
######
    best_strategies, rate, n_contracts, capital_adjustment = find_best_plan(amount, ratios, no_hedge, fit_ratio, term)
######
    best_strategies, rate, n_contracts, capital_adjustment = find_best_plan_to_expiration(amount, ratios, no_hedge, fit_ratio, term)
######
    print(best_strategies)
    print(n_contracts)
    print(capital_adjustment)
