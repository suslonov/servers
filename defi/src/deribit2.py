#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import math
import time
import pytz

from db_cvx import db_points
from crypto_exchanges import crypto_currencies, coinmarketcap, deribit_exchange

KEEP_RAW_DATA = True
SMOOTHING_EMA_1 = 0.1
MIN_SMOOTHING_EMA_1 = 0.01
SMOOTHING_EMA_2 = 0.2
RENEW_TIME = 3600
RENEW_TRESHOLD = 0.05
RISK_FREE_RATE = 0

def instrument_older_than_hour(instrument_name, one_hour_before, instruments_for_currency):
    for i in instruments_for_currency:
        if instrument_name == i['instrument_name']:
            if one_hour_before > i['creation_timestamp']:
                return True
            else:
                return False
    return False


def extract_two_datesV001(currency, options_data, now_date):
    call_contracts = {}
    put_contracts = {}

    for tick in options_data:
        instrument_descr = tick['instrument_name'].split('-')
        expiration_date = datetime.strptime(instrument_descr[1], '%d%b%y').date()
        if expiration_date.weekday() == 4:# good options matures on Fridays
            if instrument_descr[-1] == "C":
                contracts = call_contracts
            else:
                contracts = put_contracts
            strike = instrument_descr[2]
            if not expiration_date in contracts:
                contracts[expiration_date] = [(int(strike), tick['mid_price'], tick['underlying_price'])]
            else:
                contracts[expiration_date].append((int(strike), tick['mid_price'], tick['underlying_price']))

    e30 = now_date.date() + timedelta(days=30)
    e_list = []
    e_higher = 0
    e_lower = 0

    for e in call_contracts:
        if e < e30:
            if e_lower == 0 or e_lower < e:
                e_lower = e
        elif e > e30:
            if e_higher == 0 or e_higher > e:
                e_higher = e
    if e_lower:
        e_list.append(e_lower)
    if e_higher:
        e_list.append(e_higher)

    expirations = []
    selected_calls = []
    selected_puts = []
    e_list.sort()
    for e in e_list:
        expirations.append(e)
        selected_calls.append(call_contracts[e])
        selected_puts.append(put_contracts[e])

    return (expirations, selected_calls, selected_puts, currency)


def extract_option_datesV003(currency, options_data, instruments_for_currency, now_date):
    call_contracts = {}
    put_contracts = {}
    one_hour_before = int((pytz.timezone('UTC').localize(now_date).timestamp()-3600)*1000)

    for tick in options_data:
        if instrument_older_than_hour(tick['instrument_name'], one_hour_before, instruments_for_currency):
            instrument_descr = tick['instrument_name'].split('-')
            expiration_date = datetime.strptime(instrument_descr[1], '%d%b%y')
            if expiration_date.weekday() == 4:# good options matures on Fridays
                if instrument_descr[-1] == "C":
                    contracts = call_contracts
                else:
                    contracts = put_contracts
                strike = instrument_descr[2]
                if not expiration_date in contracts:
                    contracts[expiration_date] = [(int(strike), tick['mid_price'], tick['underlying_price'])]
                else:
                    contracts[expiration_date].append((int(strike), tick['mid_price'], tick['underlying_price']))

    e30 = now_date + timedelta(days=30) - timedelta(hours=deribit_exchange.expiration_hour)
    e_list = []
    e_higher = 0
    e_lower = 0
    for e in call_contracts:
        if e <= e30:
            if e_lower == 0 or e_lower < e:
                e_lower = e
        elif e > e30:
            if e_higher == 0 or e_higher > e:
                e_higher = e
    if e_lower:
        e_list.append(e_lower)
    if e_higher:
        e_list.append(e_higher)

    expirations = []
    selected_calls = []
    selected_puts = []
    e_list.sort()
    for e in e_list:
        expirations.append(int(pytz.timezone('UTC').localize(e).timestamp()) + 3600 * deribit_exchange.expiration_hour)
        selected_calls.append(call_contracts[e])
        selected_puts.append(put_contracts[e])

    return (expirations, selected_calls, selected_puts, currency)

def get_option_datesV001(exchange, now_date):
    return [extract_two_datesV001(curr, od, now_date) for (curr, od) in zip(exchange.currency, exchange.option_data)]

def get_option_datesV003(exchange, now_date):
    return [extract_option_datesV003(curr, od, i, now_date) for (curr, i, od) in zip(exchange.currency, exchange.instruments, exchange.option_data)]

def T_for_dates(now_time, e):
    y1 = datetime.fromtimestamp(now_time).year
    y2 = datetime.fromtimestamp(e).year
    if y1 == y2:
        return (e - now_time)/((datetime(y1,12,31) - datetime(y1,1,1)).days + 1)/24/60/60
    else:
        return (e - datetime(y2,1,1, tzinfo=pytz.timezone('UTC')).timestamp())/((datetime(y2,12,31) - datetime(y2,1,1)).days + 1)/24/60/60 + \
               (datetime(y2,1,1, tzinfo=pytz.timezone('UTC')).timestamp() - now_time)/((datetime(y1,12,31) - datetime(y1,1,1)).days + 1)/24/60/60

def one_sigma1(e, calls, puts, curr, now_date):
    T = (e - now_date.date()).days/365.0
    S = 0
    K0c = 0
    for (i,c) in enumerate(calls):
        if c[0] > c[2]:
            if c[1] is None:
                continue
            F = c[2]
            if i == 0:
                dK = calls[i+1][0] - c[0]
            elif i == len(calls) - 1:
                dK = c[0] - calls[i-1][0]
            else:
                dK = (calls[i+1][0] - calls[i-1][0])/2
            S += dK*c[1]*curr/(c[0]**2)
        else:
            K0c = c[0]

    K0p = 0
    for (i,p) in enumerate(puts):
        if p[0] < p[2]:
            if p[1] is None:
                continue
            F = p[2]
            if i == 0:
                dK = p[0] - puts[i+1][0]
            elif i == len(puts) - 1:
                dK = puts[i-1][0] - p[0]
            else:
                dK = (puts[i-1][0] - puts[i+1][0])/2
            S += dK*p[1]*curr/(p[0]**2)
        else:
            K0p = p[0]

    K0 = (K0c + K0p)/2
    return (2*math.exp(RISK_FREE_RATE*T)*S - (F/K0-1)**2)/T

def one_sigma3(e, calls, puts, curr, now_time):
    T = T_for_dates(now_time, e)
    S = 0
    K0c = 0
    for (i,c) in enumerate(calls):
        if c[0] > c[2]:
            if c[1] is None:
                continue
            F = c[2]
            if i == 0:
                dK = calls[i+1][0] - c[0]
            elif i == len(calls) - 1:
                dK = c[0] - calls[i-1][0]
            else:
                dK = (calls[i+1][0] - calls[i-1][0])/2
            S += dK*c[1]/(c[0]**2)
        else:
            K0c = c[0]

    K0p = 0
    for (i,p) in enumerate(puts):
        if p[0] < p[2]:
            if p[1] is None:
                continue
            F = p[2]
            if i == 0:
                dK = p[0] - puts[i+1][0]
            elif i == len(puts) - 1:
                dK = puts[i-1][0] - p[0]
            else:
                dK = (puts[i-1][0] - puts[i+1][0])/2
            S += dK*p[1]/(p[0]**2)
        else:
            K0p = p[0]

    K0 = (K0c + K0p)/2
    if S <= 0:
        return None
    else:
        return (2*math.exp(RISK_FREE_RATE*T)*S*curr - (F/K0-1)**2)/T


def weighted_sigma1(sigmas, now_date):
    tm = 60*60*24*30
    t1 = (sigmas[0][0] - now_date.date()).days*60*60*24
    t2 = (sigmas[1][0] - now_date.date()).days*60*60*24
    return (t1*(t2-tm)*sigmas[0][1] - t2*(t1-tm)*sigmas[0][1])/(t2-t1)/tm


def weighted_sigma3(sigmas, now_time):
    tm = 60*60*24*30
    if len(sigmas) == 1:
        return None
    ST = 0
    count_s = 0
    for (e, s) in sigmas:
        if not s is None:
            ST += abs(e - now_time - tm)
            count_s += 1

    weighted = 0
    for (e, s) in sigmas:
        if not s is None:
            weighted += (ST - abs(e - now_time - tm))*(e - now_time)*s

    if count_s <= 1:
        return None
    else:
        return weighted/ST/tm/(count_s - 1)

def calc_CVIX_V001(exchange, now_date):
    d = get_option_datesV001(exchange, now_date)
    cvix_list_by_currency = []
    for data_by_currency in d:
        (expirations, calls, puts, curr) = data_by_currency
        for c in calls:
            c.sort()
        for p in puts:
            p.sort()
            p.reverse()
        s = weighted_sigma1([(e, one_sigma1(e, c, p, curr, now_date)) for (e, c, p) in zip(expirations, calls, puts)], now_date)
        cvix_list_by_currency.append(math.sqrt(s)*100)

    return cvix_list_by_currency

def calc_CVIX_V003(exchange, now_date):
    d = get_option_datesV003(exchange, now_date)
    now_time = int(pytz.timezone('UTC').localize(now_date).timestamp()//60)*60
    cvix_list_by_currency = []
    for data_by_currency in d:
        (expirations, calls, puts, curr) = data_by_currency
        for c in calls:
            c.sort()
        for p in puts:
            p.sort()
            p.reverse()
        s = weighted_sigma3([(e, one_sigma3(e, c, p, curr, now_time)) for (e, c, p) in zip(expirations, calls, puts)], now_time)
        cvix_list_by_currency.append(math.sqrt(s)*100)

    return cvix_list_by_currency

def calc_EMA(prev_ema, previous_point, cvix_minute, now_date):  # !!!
    if prev_ema is None or previous_point is None:
        ema = cvix_minute
        previous_point = now_date
    else:
        time_delta = (now_date - previous_point).seconds + round((now_date - previous_point).microseconds/1000000)
        if time_delta > RENEW_TIME or abs((cvix_minute - prev_ema)/prev_ema) > RENEW_TRESHOLD:
            smoothing_factor = MIN_SMOOTHING_EMA_1 + SMOOTHING_EMA_1 * min(time_delta, RENEW_TIME) / RENEW_TIME
            ema = cvix_minute * smoothing_factor + prev_ema * (1 - smoothing_factor)
            previous_point = now_date
        else:
            ema = prev_ema
            previous_point = previous_point
    return ema, previous_point

def main():
    now_date = datetime.utcnow()
    exchange = deribit_exchange()
    marketcap = coinmarketcap()

    with db_points() as db:
        if KEEP_RAW_DATA:
            exchange.request_exchange(now_date, db)
        else:
            exchange.request_exchange(now_date)

        if now_date.minute%10 == 0:
            success = False
            for i in range(marketcap.RETRY_ATTEMPTS):
                try:
                    market_caps = marketcap.get_market_data([c.value for c in crypto_currencies])
                    success = True
                    break
                except Exception:
                    print(Exception)
                    time.sleep(10)
            if not success:
                market_caps = db.get_last_marketcap_from_db()
                if not market_caps:
                    print("No market caps available")
                    return
            else:
                db.add_marketcap_to_db(now_date, market_caps[0], market_caps[1])
        else:
            market_caps = db.get_last_marketcap_from_db()
            if market_caps is None:
                try:
                    market_caps = marketcap.get_market_data([c.value for c in crypto_currencies])
                    db.add_marketcap_to_db(now_date, market_caps[0], market_caps[1])
                except Exception:
                    print(Exception)
                    print("No market caps available")
                    return

        market_cap_all = sum(market_caps)

        cvix_minute = 0
        try:
            cvix_listV003 = calc_CVIX_V003(exchange, now_date)
            for (cvix_point, market_cap) in zip(cvix_listV003, market_caps):
                cvix_minute += cvix_point * market_cap
            cvix_minute = cvix_minute / market_cap_all

            prev_minute = db.get_last_minute_v003_from_db()
            if not prev_minute is None:
                ema1, previous_point = calc_EMA(prev_minute[4], prev_minute[7], cvix_minute, now_date)
                ema_btc, previous_point_btc = calc_EMA(prev_minute[5], prev_minute[8], cvix_listV003[0], now_date)
                ema_eth, previous_point_eth = calc_EMA(prev_minute[6], prev_minute[9], cvix_listV003[1], now_date)
            else:
                ema1 = cvix_minute; ema_btc = cvix_listV003[0]; ema_eth = cvix_listV003[1];
                previous_point = now_date; previous_point_btc = now_date; previous_point_eth = now_date
            db.add_minute_point_v003_to_db(now_date, cvix_listV003, cvix_minute, ema1, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth)
        except:
            pass

        cvix_minute = 0
        try:
            cvix_listV001 = calc_CVIX_V001(exchange, now_date)
            for (cvix_point, market_cap) in zip(cvix_listV001, market_caps):
                cvix_minute += cvix_point * market_cap
            cvix_minute = cvix_minute / market_cap_all

            prev_minute = db.get_last_minute_v001_from_db()
            if not prev_minute is None:
                ema1, previous_point = calc_EMA(prev_minute[4], prev_minute[7], cvix_minute, now_date)
                ema_btc, previous_point_btc = calc_EMA(prev_minute[5], prev_minute[8], cvix_listV001[0], now_date)
                ema_eth, previous_point_eth = calc_EMA(prev_minute[6], prev_minute[9], cvix_listV001[1], now_date)
            else:
                ema1 = cvix_minute; ema_btc = cvix_listV001[0]; ema_eth = cvix_listV001[1];
                previous_point = now_date; previous_point_btc = now_date; previous_point_eth = now_date
            db.add_minute_point_v001_to_db(now_date, cvix_listV001, cvix_minute, ema1, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth)
        except:
            pass

        exchange.clear_data()

if __name__ == '__main__':
    main()

