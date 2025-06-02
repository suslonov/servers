#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import math
import time
import pytz

from db_cvx import DBPoints
from crypto_exchange_reader import crypto_currencies, Coinmarketcap, DeribitExchangeReader

KEEP_RAW_DATA = True
RISK_FREE_RATE = 0
MARK_PRICE_DEVIATION_THRESHOLD = 1

SMOOTHING_EMA_1 = 0.1
MIN_SMOOTHING_EMA_1 = 0.01
SMOOTHING_EMA_2 = 0.2
RENEW_TIME = 3600
RENEW_TRESHOLD = 0.05

ORACLE_THRESHOLD = 0.01
RENEW_PERIOD = 1200
DEVIATION_THRESHOLD = 0.11
SMOOTHING_FACTOR_B = 0.31

ORACLE_THRESHOLD_1 = 0.02
RENEW_PERIOD_1 = 3600
DEVIATION_THRESHOLD_1 = 0.11
SMOOTHING_FACTOR_B_1 = 0.22

ORACLE_THRESHOLD_2 = 0.05
RENEW_PERIOD_2 = 3600
DEVIATION_THRESHOLD_2 = 0.11
SMOOTHING_FACTOR_B_2 = 0.22

ORACLE_THRESHOLD_5 = 0.01
RENEW_PERIOD_5 = 300
DEVIATION_THRESHOLD_5 = 0.2
SMOOTHING_FACTOR_B_5 = 0.4
MIN_SMOOTHING_FACTOR_5 = 0.04

ORACLE_THRESHOLD_3 = 0.025
RENEW_PERIOD_3 = 1800
DEVIATION_THRESHOLD_3 = 0.15
SMOOTHING_FACTOR_B_3 = 0.4
MIN_SMOOTHING_FACTOR_3 = 0.08

ORACLE_THRESHOLD_6 = 0.01
RENEW_PERIOD_6 = 600
DEVIATION_THRESHOLD_6 = 0.2
SMOOTHING_FACTOR_B_6 = 0.4
MIN_SMOOTHING_FACTOR_6 = 0.04

def instrument_older_than_hour(instrument_name, one_hour_before, instruments_for_currency):
    for i in instruments_for_currency:
        if instrument_name == i['instrument_name']:
            if one_hour_before > i['creation_timestamp']:
                return True
            else:
                return False
    return False

def extract_option_datesV003(currency, options_data, instruments_for_currency, now_date):
    call_contracts = {}
    put_contracts = {}
    one_hour_before = int((pytz.timezone('UTC').localize(now_date).timestamp()-3600)*1000)

    for tick in options_data:
        if instrument_older_than_hour(tick['instrument_name'], one_hour_before, instruments_for_currency):
            instrument_descr = tick['instrument_name'].split('-')
            expiration_date = datetime.strptime(instrument_descr[1], '%d%b%y')
            if expiration_date.weekday() == 4:# good option matures on Fridays
                if instrument_descr[-1] == "C":
                    contracts = call_contracts
                else:
                    contracts = put_contracts
                strike = instrument_descr[2]
                if tick['mid_price'] and tick['mark_price'] and abs(tick['mid_price'] - tick['mark_price'])/tick['mark_price'] > MARK_PRICE_DEVIATION_THRESHOLD:
                    tick['mid_price'] = tick['mark_price']
                if not expiration_date in contracts:
                    contracts[expiration_date] = [(int(strike), tick['mid_price'], tick['underlying_price'])]
                else:
                    contracts[expiration_date].append((int(strike), tick['mid_price'], tick['underlying_price']))

    e30 = now_date + timedelta(days=30) - timedelta(hours=DeribitExchangeReader.expiration_hour)
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
        expirations.append(int(pytz.timezone('UTC').localize(e).timestamp()) + 3600 * DeribitExchangeReader.expiration_hour)
        selected_calls.append(call_contracts[e])
        selected_puts.append(put_contracts[e])

    return (expirations, selected_calls, selected_puts, currency)

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

def one_sigma4(e, calls, puts, curr, now_time):
    T = T_for_dates(now_time, e)
    S = 0
    K0c = 0
    compare_list = [c[1] if c[1] else 0 for c in calls]   # <<< changed
    for (i,c) in enumerate(calls):
        if c[0] > c[2]:
            if c[1] is None:
                continue
            prev_max = max(compare_list[max((0, i-10)):i])   # <<< changed
            if i > 3 and prev_max != 0 and c[1] > 2 * prev_max:   # <<< changed
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
    compare_list = [p[1] if p[1] else 0 for p in puts]     # <<< changed
    for (i,p) in enumerate(puts):
        if p[0] < p[2]:
            if p[1] is None:
                continue
            prev_max = max(compare_list[max((0, i-10)):i])   # <<< changed
            if i > 3 and prev_max != 0 and p[1] > 2 * prev_max:   # <<< changed
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

def calc_CVIX_V004(exchange, now_date):
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
        s = weighted_sigma3([(e, one_sigma4(e, c, p, curr, now_time)) for (e, c, p) in zip(expirations, calls, puts)], now_time)
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

def calc_EMA4(ema, time_point, cvi_value, now_date):
    MIN_SMOOTHING_FACTOR = SMOOTHING_FACTOR_B / 10
    if ema is None or time_point is None:
        ema = cvi_value
        time_point = now_date
    else:
        time_delta = (now_date - time_point).seconds + round((now_date - time_point).microseconds/1000000)

        if abs(cvi_value/ema - 1) < DEVIATION_THRESHOLD:
            smoothing_factor = MIN_SMOOTHING_FACTOR + SMOOTHING_FACTOR_B * min(time_delta, RENEW_PERIOD) / RENEW_PERIOD
        else:
            smoothing_factor = MIN_SMOOTHING_FACTOR

        ema_candidate = cvi_value * smoothing_factor + ema * (1 - smoothing_factor)
        if time_delta > RENEW_PERIOD or abs((ema_candidate - ema)/ema) > ORACLE_THRESHOLD:
            ema = ema_candidate
            time_point = now_date
    return ema, time_point

def calc_EMA41(ema, time_point, cvi_value, now_date):
    MIN_SMOOTHING_FACTOR = SMOOTHING_FACTOR_B_1 / 10
    if ema is None or time_point is None:
        ema = cvi_value
        time_point = now_date
    else:
        time_delta = (now_date - time_point).seconds + round((now_date - time_point).microseconds/1000000)

        if abs(cvi_value/ema - 1) < DEVIATION_THRESHOLD_1:
            smoothing_factor = MIN_SMOOTHING_FACTOR + SMOOTHING_FACTOR_B_1 * min(time_delta, RENEW_PERIOD_1) / RENEW_PERIOD_1
        else:
            smoothing_factor = MIN_SMOOTHING_FACTOR

        ema_candidate = cvi_value * smoothing_factor + ema * (1 - smoothing_factor)
        if time_delta > RENEW_PERIOD_1 or abs((ema_candidate - ema)/ema) > ORACLE_THRESHOLD_1:
            ema = ema_candidate
            time_point = now_date
    return ema, time_point

def calc_EMA42(ema, time_point, cvi_value, now_date):
    MIN_SMOOTHING_FACTOR = SMOOTHING_FACTOR_B_2 / 10
    if ema is None or time_point is None:
        ema = cvi_value
        time_point = now_date
    else:
        time_delta = (now_date - time_point).seconds + round((now_date - time_point).microseconds/1000000)

        if abs(cvi_value/ema - 1) < DEVIATION_THRESHOLD_2:
            smoothing_factor = MIN_SMOOTHING_FACTOR + SMOOTHING_FACTOR_B_2 * min(time_delta, RENEW_PERIOD_2) / RENEW_PERIOD_2
        else:
            smoothing_factor = MIN_SMOOTHING_FACTOR

        ema_candidate = cvi_value * smoothing_factor + ema * (1 - smoothing_factor)
        if time_delta > RENEW_PERIOD_2 or abs((ema_candidate - ema)/ema) > ORACLE_THRESHOLD_2:
            ema = ema_candidate
            time_point = now_date
    return ema, time_point

def calc_EMA43(ema, time_point, cvi_value, now_date):
    if ema is None or time_point is None:
        ema = cvi_value
        time_point = now_date
    else:
        time_delta = (now_date - time_point).seconds + round((now_date - time_point).microseconds/1000000)

        if abs(cvi_value/ema - 1) < DEVIATION_THRESHOLD_3:
            smoothing_factor = MIN_SMOOTHING_FACTOR_3 + SMOOTHING_FACTOR_B_3 * min(time_delta, RENEW_PERIOD_3) / RENEW_PERIOD_3
        else:
            smoothing_factor = MIN_SMOOTHING_FACTOR_3

        ema_candidate = cvi_value * smoothing_factor + ema * (1 - smoothing_factor)
        if time_delta > RENEW_PERIOD_3 or abs((ema_candidate - ema)/ema) > ORACLE_THRESHOLD_3:
            ema = ema_candidate
            time_point = now_date
    return ema, time_point

def calc_EMA45(ema, time_point, cvi_value, now_date):
    if ema is None or time_point is None:
        ema = cvi_value
        time_point = now_date
    else:
        time_delta = (now_date - time_point).seconds + round((now_date - time_point).microseconds/1000000)

        if abs(cvi_value/ema - 1) < DEVIATION_THRESHOLD_5:
            smoothing_factor = MIN_SMOOTHING_FACTOR_5 + SMOOTHING_FACTOR_B_5 * min(time_delta, RENEW_PERIOD_5) / RENEW_PERIOD_5
        else:
            smoothing_factor = MIN_SMOOTHING_FACTOR_5

        ema_candidate = cvi_value * smoothing_factor + ema * (1 - smoothing_factor)
        if time_delta > RENEW_PERIOD_5 or abs((cvi_value - ema)/ema) > ORACLE_THRESHOLD_5:
            ema = ema_candidate
            time_point = now_date
    return ema, time_point

def calc_EMA46(ema, time_point, cvi_value, now_date):
    if ema is None or time_point is None:
        ema = cvi_value
        time_point = now_date
    else:
        time_delta = (now_date - time_point).seconds + round((now_date - time_point).microseconds/1000000)

        if abs(cvi_value/ema - 1) < DEVIATION_THRESHOLD_6:
            smoothing_factor = MIN_SMOOTHING_FACTOR_6 + SMOOTHING_FACTOR_B_6 * min(time_delta, RENEW_PERIOD_6) / RENEW_PERIOD_6
        else:
            smoothing_factor = MIN_SMOOTHING_FACTOR_6

        ema_candidate = cvi_value * smoothing_factor + ema * (1 - smoothing_factor)
        if time_delta > RENEW_PERIOD_6 or abs((cvi_value - ema)/ema) > ORACLE_THRESHOLD_6:
            ema = ema_candidate
            time_point = now_date
    return ema, time_point

def deribit_main():
    now_date = datetime.utcnow()
    # now_date = datetime(2021, 5, 9, 9, 51, 1)
    exchange = DeribitExchangeReader()
    marketcap = Coinmarketcap()

    # with db_points_remote() as db:
    #     exchange.load_from_db(now_date, db)
    # exchange.request_exchange_instruments()

    with DBPoints() as db:
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
                except Exception as e:
                    print(e)
                    time.sleep(10)
            if not success:
                market_caps = db.get_last_marketcap_from_db()
                if not market_caps:
                    print("No market caps available")
                    return
                else:
                    market_caps = market_caps[1:]
            else:
                db.add_marketcap_to_db(now_date, market_caps[0], market_caps[1])
        else:
            market_caps = db.get_last_marketcap_from_db()
            if market_caps is None:
                try:
                    market_caps = marketcap.get_market_data([c.value for c in crypto_currencies])
                    db.add_marketcap_to_db(now_date, market_caps[0], market_caps[1])
                except Exception as e:
                    print(e)
                    print("No market caps available")
                    return
            else:
                market_caps = market_caps[1:]

        market_cap_all = sum(market_caps)

        cvix_minute = 0
        try:
            cvix_listV003 = calc_CVIX_V003(exchange, now_date)
            for (cvix_point, market_cap) in zip(cvix_listV003, market_caps):
                cvix_minute += cvix_point * market_cap
            cvix_minute = cvix_minute / market_cap_all

            prev_minute = db.get_last_minute_from_db('v003')
            if not prev_minute is None:
                ema, previous_point = calc_EMA(prev_minute[4], prev_minute[7], cvix_minute, now_date)
                ema_btc, previous_point_btc = calc_EMA(prev_minute[5], prev_minute[8], cvix_listV003[0], now_date)
                ema_eth, previous_point_eth = calc_EMA(prev_minute[6], prev_minute[9], cvix_listV003[1], now_date)
            else:
                ema = cvix_minute; ema_btc = cvix_listV003[0]; ema_eth = cvix_listV003[1];
                previous_point = now_date; previous_point_btc = now_date; previous_point_eth = now_date
            db.add_minute_point_to_db('v003', now_date, cvix_listV003, cvix_minute, ema, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth)
        except:
            pass

        cvix_minute = 0
        try:
            cvix_listV004 = calc_CVIX_V004(exchange, now_date)
            for (cvix_point, market_cap) in zip(cvix_listV004, market_caps):
                cvix_minute += cvix_point * market_cap
            cvix_minute = cvix_minute / market_cap_all

            prev_minute = db.get_last_minute_from_db('v004')
            if not prev_minute is None:
                ema, previous_point = calc_EMA4(prev_minute[4], prev_minute[7], cvix_minute, now_date)
                ema_btc, previous_point_btc = calc_EMA4(prev_minute[5], prev_minute[8], cvix_listV004[0], now_date)
                ema_eth, previous_point_eth = calc_EMA4(prev_minute[6], prev_minute[9], cvix_listV004[1], now_date)
            else:
                ema = cvix_minute; ema_btc = cvix_listV004[0]; ema_eth = cvix_listV004[1];
                previous_point = now_date; previous_point_btc = now_date; previous_point_eth = now_date
            db.add_minute_point_to_db("v004", now_date, cvix_listV004, cvix_minute, ema, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth)

            prev_minute = db.get_last_minute_from_db('v0041')
            if not prev_minute is None:
                ema, previous_point = calc_EMA41(prev_minute[4], prev_minute[7], cvix_minute, now_date)
                ema_btc, previous_point_btc = calc_EMA41(prev_minute[5], prev_minute[8], cvix_listV004[0], now_date)
                ema_eth, previous_point_eth = calc_EMA41(prev_minute[6], prev_minute[9], cvix_listV004[1], now_date)
            else:
                ema = cvix_minute; ema_btc = cvix_listV004[0]; ema_eth = cvix_listV004[1];
                previous_point = now_date; previous_point_btc = now_date; previous_point_eth = now_date
            db.add_minute_point_to_db("v0041", now_date, cvix_listV004, cvix_minute, ema, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth)

            prev_minute = db.get_last_minute_from_db("v0042")
            if not prev_minute is None:
                ema, previous_point = calc_EMA42(prev_minute[4], prev_minute[7], cvix_minute, now_date)
                ema_btc, previous_point_btc = calc_EMA42(prev_minute[5], prev_minute[8], cvix_listV004[0], now_date)
                ema_eth, previous_point_eth = calc_EMA42(prev_minute[6], prev_minute[9], cvix_listV004[1], now_date)
            else:
                ema = cvix_minute; ema_btc = cvix_listV004[0]; ema_eth = cvix_listV004[1];
                previous_point = now_date; previous_point_btc = now_date; previous_point_eth = now_date
            db.add_minute_point_to_db("v0042", now_date, cvix_listV004, cvix_minute, ema, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth)

            prev_minute = db.get_last_minute_from_db("v0043")
            if not prev_minute is None:
                ema, previous_point = calc_EMA43(prev_minute[4], prev_minute[7], cvix_minute, now_date)
                ema_btc, previous_point_btc = calc_EMA43(prev_minute[5], prev_minute[8], cvix_listV004[0], now_date)
                ema_eth, previous_point_eth = calc_EMA43(prev_minute[6], prev_minute[9], cvix_listV004[1], now_date)
            else:
                ema = cvix_minute; ema_btc = cvix_listV004[0]; ema_eth = cvix_listV004[1];
                previous_point = now_date; previous_point_btc = now_date; previous_point_eth = now_date
            db.add_minute_point_to_db("v0043", now_date, cvix_listV004, cvix_minute, ema, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth)

            prev_minute = db.get_last_minute_from_db("v0045")
            if not prev_minute is None:
                ema, previous_point = calc_EMA45(prev_minute[4], prev_minute[7], cvix_minute, now_date)
                ema_btc, previous_point_btc = calc_EMA45(prev_minute[5], prev_minute[8], cvix_listV004[0], now_date)
                ema_eth, previous_point_eth = calc_EMA45(prev_minute[6], prev_minute[9], cvix_listV004[1], now_date)
            else:
                ema = cvix_minute; ema_btc = cvix_listV004[0]; ema_eth = cvix_listV004[1];
                previous_point = now_date; previous_point_btc = now_date; previous_point_eth = now_date
            db.add_minute_point_to_db("v0045", now_date, cvix_listV004, cvix_minute, ema, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth)

            prev_minute = db.get_last_minute_from_db("v0046")
            if not prev_minute is None:
                ema, previous_point = calc_EMA46(prev_minute[4], prev_minute[7], cvix_minute, now_date)
                ema_btc, previous_point_btc = calc_EMA46(prev_minute[5], prev_minute[8], cvix_listV004[0], now_date)
                ema_eth, previous_point_eth = calc_EMA46(prev_minute[6], prev_minute[9], cvix_listV004[1], now_date)
            else:
                ema = cvix_minute; ema_btc = cvix_listV004[0]; ema_eth = cvix_listV004[1];
                previous_point = now_date; previous_point_btc = now_date; previous_point_eth = now_date
            db.add_minute_point_to_db("v0046", now_date, cvix_listV004, cvix_minute, ema, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth)
        except:
            pass

        exchange.clear_data()

if __name__ == '__main__':
    deribit_main()
