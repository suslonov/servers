#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import json
import pandas as pd

from db_cvx import DBPoints
from db_cvx2 import DBPoints2

MAX_ETHVOL_OLD = 218
MAX_ETHVOL = 220

def filter_eth_only(l):
    return [(ll[0], min(ll[2], MAX_ETHVOL_OLD if datetime(2021, 11, 1) > ll[0] else MAX_ETHVOL), 
             min(ll[6], MAX_ETHVOL_OLD if datetime(2021, 11, 1) > ll[0] else MAX_ETHVOL), ll[9]) for ll in l]

def cvi_chart_page(ver, currency=None):
    with DBPoints() as db:
        l = db.get_minutes_from_db(ver, "hour", 1000)
    # the list is in the reverse order !
    if len(l) == 0:
        return 0, l
    else:
        if currency is None:
            chart_values_btc = [('new Date('+str(ll[0].year)+", "+str(ll[0].month-1)+", "+str(ll[0].day)+", "+str(ll[0].hour)+", "+str(ll[0].minute)+", 0)", ll[1], ll[5] if ll[5] else 'null') for ll in l[-1000:] if ll[1]]
            chart_values_eth = [('new Date('+str(ll[0].year)+", "+str(ll[0].month-1)+", "+str(ll[0].day)+", "+str(ll[0].hour)+", "+str(ll[0].minute)+", 0)", ll[2], ll[6] if ll[6] else 'null') for ll in l[-1000:] if ll[2]]
            chart_values = [('new Date('+str(ll[0].year)+", "+str(ll[0].month-1)+", "+str(ll[0].day)+", "+str(ll[0].hour)+", "+str(ll[0].minute)+", 0)", ll[3], ll[4] if ll[4] else 'null') for ll in l[-1000:] if ll[3]]
            return l[-1][1], l[-1][2], l[-1][3], l[-1][4], l[-1][5], l[-1][6], chart_values_btc, chart_values_eth, chart_values
        elif currency == "ETH": # temporary one-currency solution
            chart_values_eth = [('new Date('+str(ll[0].year)+", "+str(ll[0].month-1)+", "+str(ll[0].day)+", "+str(ll[0].hour)+", "+str(ll[0].minute)+", 0)", 
                                 ll[1], ll[2] if ll[2] else 'null') for ll in filter_eth_only(l[-1000:]) if ll[1]]
            return l[-1][2], l[-1][6], chart_values_eth
        else:
            return 0, l


def cvix_last(ver, currency=None):
    with DBPoints() as db:
        cvix = db.get_minutes_from_db(ver, "minute", 1)
    if currency is None:
        return cvix[0]
    else:
        return filter_eth_only(cvix)[0]

def cvix_1000(ver, frequency="minute", currency=None):
    with DBPoints() as db:
        cvix_list = db.get_minutes_from_db(ver, frequency, 1000)
    if frequency == "hour":
        cvix_list.sort()
    if currency is None:
        return cvix_list
    else:
        return filter_eth_only(cvix_list)

def cvix_1000_20min(ver):
    with DBPoints() as db:
        cvix_list = db.get_minutes_from_db(ver, "20min", 1000)
        cvix_list.sort()
        t = cvix_list[-1][0]
        t = t.replace(second=0) + (0 if t.minute==0 else timedelta(minutes=(-t.minute + ((t.minute-1)//20 + 1) * 20)))
        if t > datetime.utcnow():
            return cvix_list[:-1]
        else:
            return cvix_list

def cvix_changes_all(ver, curr=None):
    with DBPoints() as db:
        cvix_list = db.get_changes_from_db_all(ver, curr=curr)
    return cvix_list

def cvix_changes_N(ver, n, curr=None):
    with DBPoints() as db:
        cvix_list = db.get_changes_from_db(ver, n, curr=curr)
    return cvix_list


def ethvol_ohlc_days(ver, n):
    with DBPoints() as db:
        ethvol_list = db.get_minutes_from_db(ver, "minute", (n + 1) * 24 * 60)

    c = ['minute_point', 'cvix_btc', 'cvix_eth', 'cvix', 'ema_cvi', 'ema_btc', 'ema_eth', 'previous_point', 'previous_point_btc', 'previous_point_eth']
    df = pd.DataFrame(ethvol_list, columns=c)
    df["date"] = df["minute_point"].dt.date
    min_date_time = datetime.utcnow().date() - timedelta(days=n)

    df1 = df.groupby(["date"])["minute_point"].idxmin()
    df2 = df.groupby(["date"])["ema_eth"].idxmax()
    df3 = df.groupby(["date"])["ema_eth"].idxmin()
    df4 = df.groupby(["date"])["minute_point"].idxmax()

    df_cvi = pd.concat([df.loc[df1][["date","ema_eth"]].set_index("date")["ema_eth"].rename("open"),
                        df.loc[df2][["date","ema_eth"]].set_index("date")["ema_eth"].rename("high"),
                        df.loc[df3][["date","ema_eth"]].set_index("date")["ema_eth"].rename("low"),
                        df.loc[df4][["date","ema_eth"]].set_index("date")["ema_eth"].rename("close")], axis=1)

    return df_cvi.loc[df_cvi.index >= min_date_time].reset_index().values.tolist()

def ethvol_ohlc_hours(ver, n):
    with DBPoints() as db:
        ethvol_list = db.get_minutes_from_db(ver, "minute", (n + 1) * 60)

    c = ['minute_point', 'cvix_btc', 'cvix_eth', 'cvix', 'ema_cvi', 'ema_btc', 'ema_eth', 'previous_point', 'previous_point_btc', 'previous_point_eth']
    df = pd.DataFrame(ethvol_list, columns=c)
    df["datetime"] = df["minute_point"].apply(lambda x: datetime(x.year, x.month, x.day, x.hour))
    min_date_time = (datetime.utcnow() - timedelta(hours=n)).replace(minute=0, second=0, microsecond=0)

    df1 = df.groupby(["datetime"])["minute_point"].idxmin()
    df2 = df.groupby(["datetime"])["ema_eth"].idxmax()
    df3 = df.groupby(["datetime"])["ema_eth"].idxmin()
    df4 = df.groupby(["datetime"])["minute_point"].idxmax()

    df_cvi = pd.concat([df.loc[df1][["datetime","ema_eth"]].set_index("datetime")["ema_eth"].rename("open"),
                        df.loc[df2][["datetime","ema_eth"]].set_index("datetime")["ema_eth"].rename("high"),
                        df.loc[df3][["datetime","ema_eth"]].set_index("datetime")["ema_eth"].rename("low"),
                        df.loc[df4][["datetime","ema_eth"]].set_index("datetime")["ema_eth"].rename("close")], axis=1)

    return df_cvi.loc[df_cvi.index >= min_date_time].reset_index().values.tolist()


def gvol_instant_cvi(n=1000):
    with DBPoints2() as db:
        l = db.get_minutes_from_db("v004", "minute", n)

    j_list = []
    for ll in l:
        dd = json.loads(ll[1])
        dddict = {("", ""): ll[0]}
        for ddd in dd:
            for dddd in dd[ddd]:
                try:
                    dddict[(ddd, dddd)] = round(float(dd[ddd][dddd]), 2)
                except:
                    dddict[(ddd, dddd)] = dd[ddd][dddd]
        j_list.append(dddict)
    df = pd.DataFrame(j_list)
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    df.sort_index(axis=1, level=1, inplace=True)
    return df

    table_body = []
    for ll in l:
        dd = json.loads(ll[1])
        row_list = [ll[0]]
        for ddd in dd:
            for dddd in dd[ddd]:
                row_list.append(dd[ddd][dddd])
                
                dddict[(ddd, dddd)] = dd[ddd][dddd]
        table_body.append(row_list)

