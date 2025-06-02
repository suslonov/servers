#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import MySQLdb

class DBPoints2(object):
    db_host="127.0.0.1"
    db_user="cvix_test"
    db_passwd="cvix_test"
    db_name="cvix_test"

    def __enter__(self):
        self.db = MySQLdb.connect(host=self.db_host, user=self.db_user, passwd=self.db_passwd, db=self.db_name)
        self.cursor = self.db.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.commit()
        self.db.close()


    def get_last_marketcap_from_db(self):
        s1 = """SELECT point, market_cap_btc, market_cap_eth FROM market_caps ORDER by point DESC LIMIT 1"""
        i = self.cursor.execute(s1)
        if i > 0:
            r = self.cursor.fetchone()
            return r
        else:
            return None

    def add_marketcap_to_db(self, point, market_cap_btc, market_cap_eth):
        s2 = """INSERT INTO market_caps (point, market_cap_btc, market_cap_eth) VALUES (%s, %s, %s)"""
        self.cursor.execute(s2, (point, market_cap_btc, market_cap_eth))

    def get_marketcap_from_db(self, point):
        s2 = 'SELECT market_cap_btc, market_cap_eth from market_caps where point = "'+ str(point) +'"'
        self.cursor.execute(s2)
        (market_cap_btc, market_cap_eth) = self.cursor.fetchone()
        return market_cap_btc, market_cap_eth

    def get_marketcaps_from_db(self, point):
        s2 = 'SELECT point, market_cap_btc, market_cap_eth from market_caps where point >= "'+ str(point) +'"'
        self.cursor.execute(s2)
        l = self.cursor.fetchall()
        return l
    
    def get_last_marketcap_till_from_db(self, point):
        s2 = 'select point, market_cap_btc, market_cap_eth from market_caps where point = (select max(point) point from market_caps where point <= "'+ str(point) +'")'
        self.cursor.execute(s2)
        (point, market_cap_btc, market_cap_eth) = self.cursor.fetchone()
        return market_cap_btc, market_cap_eth


    def add_point_to_db(self, ver, point, cvi_data):
        s2 = """INSERT INTO cvi_instant_""" + ver + """ (point, cvi_data) VALUES (%s, %s)"""
        return self.cursor.execute(s2, (point, cvi_data))

    # def update_minute_point_in_db(self, ver, minute_point, cvix_point, cvix, ema1, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth):
    #     s2 = 'UPDATE cvix_minutes_' + ver + ' SET cvix_btc = %s, cvix_eth = %s, cvix = %s, ema1 = %s, ema_btc = %s, ema_eth = %s, previous_point = "'+ str(previous_point) +'", previous_point_btc = "'+ str(previous_point_btc) +'", previous_point_eth = "'+ str(previous_point_eth) +'" WHERE minute_point = "'+ str(minute_point) +'"'
    #     return self.cursor.execute(s2, (cvix_point[0], cvix_point[1], cvix, ema1, ema_btc, ema_eth))

    # def delete_minute_point_from_db(self, ver, ddd):
    #     s2 = 'DELETE FROM cvix_minutes_' + ver + ' WHERE minute_point = "' + ddd + '"'
    #     return self.cursor.execute(s2)

    def get_minutes_from_db(self, ver, frequency, n):
        # if frequency == 'day':
        #     s1 = "SELECT c1.* FROM cvix_minutes_" + ver + " c1 INNER JOIN (SELECT max(minute_point) minute_point, CAST(minute_point AS date) day_point FROM cvix_minutes_" + ver + " group by day_point) c2 ON c1.minute_point = c2.minute_point ORDER BY c1.minute_point DESC LIMIT " + str(n)
        # elif frequency == 'hour':
        #     s1 = 'SELECT * FROM cvix_minutes_' + ver + ' WHERE minute(minute_point)=0 and minute_point >= DATE_ADD(NOW(), INTERVAL (-' + str(n) + '-4) hour) ORDER by minute_point'
        # elif frequency == '20min':
        #     s1 ='SELECT c1.* FROM cvix_minutes_' + ver + ' c1 INNER JOIN (SELECT max(minute_point) minute_point, DATE_ADD(DATE_ADD(minute_point, INTERVAL -second(minute_point) second), INTERVAL (-minute(minute_point) + CASE minute(minute_point) WHEN 0 THEN 0 ELSE ((minute(minute_point)-1) div 20 + 1)*20 END) minute) minute_point1 FROM cvix_minutes_' + ver + ' WHERE minute_point >= DATE_ADD(NOW(), INTERVAL (-20*' + str(n) + '-200) minute) GROUP BY minute_point1) c2 ON c1.minute_point = c2.minute_point;'
        # else:
        s1 = "SELECT * FROM cvi_instant_" + ver + " ORDER by point DESC LIMIT " + str(n)
        self.cursor.execute(s1)
        l = list(self.cursor.fetchall())
        return l

    def get_last_minute_from_db(self, ver):
        s1 = "SELECT * FROM cvi_instant_" + ver + " ORDER by point DESC LIMIT 1"
        if not self.cursor.execute(s1):
            return None
        l = list(self.cursor.fetchone())
        return l
    
    def get_last_minute_till_from_db(self, ver, point):
        s2 = 'select * from cvi_instant_' + ver + ' where point = (select max(point) point from cvi_instant_' + ver + ' where point <= "'+ str(point) +'")'
        self.cursor.execute(s2)
        return self.cursor.fetchone()

    def get_minute_from_db(self, ver, point):
        s5 = 'SELECT * from cvi_instant_' + ver + ' WHERE point = "'+ str(point) +'"'
        i = self.cursor.execute(s5)
        if i == 0:
            return None
        else:
            return self.cursor.fetchone()

    def get_minutes_from_db_all(self, ver):
        s5 = "SELECT * from cvi_instant_" + ver
        self.cursor.execute(s5)
        l = list(self.cursor.fetchall())
        return l

    # def get_changes_from_db_all(self, ver, curr=None):
    #     s5 = "SELECT * FROM cvix_minutes_" + ver + " WHERE minute_point=previous_point" + ('_eth' if curr == 'ETH' else '_btc' if  curr == 'BTC' else '')
    #     self.cursor.execute(s5)
    #     l = list(self.cursor.fetchall())
    #     return l

    # def get_changes_from_db(self, ver, n, curr=None):
    #     s1 = "SELECT * FROM cvix_minutes_" + ver + " WHERE minute_point=previous_point" + ('_eth' if curr == 'ETH' else '_btc' if  curr == 'BTC' else '') + " ORDER by minute_point DESC LIMIT " + str(n)
    #     self.cursor.execute(s1)
    #     l = list(self.cursor.fetchall())
    #     return l

