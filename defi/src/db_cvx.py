# -*- coding: utf-8 -*-

import pickle
import zlib
import MySQLdb

class DBPoints(object):
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

    def add_raw_data_to_db(self, point, curr, raw_data):
        s5 = """INSERT INTO raw_data_jan (point, btc, eth, raw_data, raw_data_eth) VALUES (%s, %s, %s, _binary "%s", _binary "%s")"""
        self.cursor.execute(s5, (point, curr[0], curr[1], zlib.compress(pickle.dumps(raw_data[0])), zlib.compress(pickle.dumps(raw_data[1]))))

    def get_raw_data_points_from_db(self, point1, point2):
        s5 = 'SELECT point from raw_data_jan where point >= "' + str(point1) + '" and point < "' + str(point2) + '"'
        self.cursor.execute(s5)
        l = list(self.cursor.fetchall())
        return l

    def get_raw_data_from_db(self, point):
        s5 = 'SELECT btc, eth, raw_data, raw_data_eth from raw_data_jan where point = "'+ str(point) +'"'
        self.cursor.execute(s5)
        (btc, eth, r_b, r_e) = self.cursor.fetchone()
        return btc, eth, pickle.loads(zlib.decompress(r_b[1:-1])), pickle.loads(zlib.decompress(r_e[1:-1]))

    def add_raw_data_from_db_no_compress(self, point, btc, eth, r_b, r_e):
        s5 = """INSERT INTO raw_data_jan (point, btc, eth, raw_data, raw_data_eth) VALUES (%s, %s, %s, _binary "%s", _binary "%s")"""
        self.cursor.execute(s5, (point, btc, eth, r_b, r_e))

    def get_raw_data_points_from_db_old(self, table, point1, point2):
        s5 = 'SELECT point from ' + table + ' where point >= "' + str(point1) + '" and point < "' + str(point2) + '"'
        self.cursor.execute(s5)
        l = list(self.cursor.fetchall())
        return l

    def get_raw_data_from_db_no_decompress(self, table, point):
        s5 = 'SELECT btc, eth, raw_data, raw_data_eth from ' + table + ' where point = "'+ str(point) +'"'
        self.cursor.execute(s5)
        (btc, eth, r_b, r_e) = self.cursor.fetchone()
        return btc, eth, r_b, r_e

    def add_minute_point_to_db(self, ver, minute_point, cvix_point, cvix, ema1, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth):
        s2 = """INSERT INTO cvix_minutes_""" + ver + """ (minute_point, cvix_btc, cvix_eth, cvix, ema1, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        return self.cursor.execute(s2, (minute_point, cvix_point[0], cvix_point[1], cvix, ema1, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth))

    def update_minute_point_in_db(self, ver, minute_point, cvix_point, cvix, ema1, ema_btc, ema_eth, previous_point, previous_point_btc, previous_point_eth):
        s2 = 'UPDATE cvix_minutes_' + ver + ' SET cvix_btc = %s, cvix_eth = %s, cvix = %s, ema1 = %s, ema_btc = %s, ema_eth = %s, previous_point = "'+ str(previous_point) +'", previous_point_btc = "'+ str(previous_point_btc) +'", previous_point_eth = "'+ str(previous_point_eth) +'" WHERE minute_point = "'+ str(minute_point) +'"'
        return self.cursor.execute(s2, (cvix_point[0], cvix_point[1], cvix, ema1, ema_btc, ema_eth))

    def delete_minute_point_from_db(self, ver, ddd):
        s2 = 'DELETE FROM cvix_minutes_' + ver + ' WHERE minute_point = "' + ddd + '"'
        return self.cursor.execute(s2)

    def get_minutes_from_db(self, ver, frequency, N):
        if frequency == 'day':
            s1 = "SELECT c1.* FROM cvix_minutes_" + ver + " c1 INNER JOIN (SELECT max(minute_point) minute_point, CAST(minute_point AS date) day_point FROM cvix_minutes_" + ver + " group by day_point) c2 ON c1.minute_point = c2.minute_point ORDER BY c1.minute_point DESC LIMIT " + str(N)
        elif frequency == 'hour':
            s1 = 'SELECT * FROM cvix_minutes_' + ver + ' WHERE minute(minute_point)=0 and minute_point >= DATE_ADD(NOW(), INTERVAL (-' + str(N) + '-4) hour) ORDER by minute_point'
        elif frequency == '20min':
            s1 ='SELECT c1.* FROM cvix_minutes_' + ver + ' c1 INNER JOIN (SELECT max(minute_point) minute_point, DATE_ADD(DATE_ADD(minute_point, INTERVAL -second(minute_point) second), INTERVAL (-minute(minute_point) + CASE minute(minute_point) WHEN 0 THEN 0 ELSE ((minute(minute_point)-1) div 20 + 1)*20 END) minute) minute_point1 FROM cvix_minutes_' + ver + ' WHERE minute_point >= DATE_ADD(NOW(), INTERVAL (-20*' + str(N) + '-200) minute) GROUP BY minute_point1) c2 ON c1.minute_point = c2.minute_point;'
        else:
            s1 = "SELECT * FROM cvix_minutes_" + ver + " ORDER by minute_point DESC LIMIT " + str(N)
        self.cursor.execute(s1)
        l = list(self.cursor.fetchall())
        return l

    def get_last_minute_from_db(self, ver):
        s1 = "SELECT * FROM cvix_minutes_" + ver + " ORDER by minute_point DESC LIMIT 1"
        if not self.cursor.execute(s1):
            return None
        l = list(self.cursor.fetchone())
        return l
    
    def get_average_from_db(self, ver):
        s1 = "SELECT avg(ema1), avg(ema_btc), avg(ema_eth) FROM cvix_minutes_" + ver
        if not self.cursor.execute(s1):
            return None
        l = list(self.cursor.fetchone())
        return l

    def get_last_minute_till_from_db(self, ver, minute_point):
        s2 = 'select * from cvix_minutes_' + ver + ' where minute_point = (select max(minute_point) minute_point from cvix_minutes_' + ver + ' where minute_point <= "'+ str(minute_point) +'")'
        self.cursor.execute(s2)
        return self.cursor.fetchone()

    def get_minute_from_db(self, ver, minute_point):
        s5 = 'SELECT * from cvix_minutes_' + ver + ' WHERE minute_point = "'+ str(minute_point) +'"'
        i = self.cursor.execute(s5)
        if i == 0:
            return None
        else:
            return self.cursor.fetchone()

    def get_minutes_from_db_all(self, ver):
        s5 = "SELECT * from cvix_minutes_" + ver
        self.cursor.execute(s5)
        l = list(self.cursor.fetchall())
        return l

    def get_changes_from_db_all(self, ver, curr=None):
        s5 = "SELECT * FROM cvix_minutes_" + ver + " WHERE minute_point=previous_point" + ('_eth' if curr == 'ETH' else '_btc' if  curr == 'BTC' else '')
        self.cursor.execute(s5)
        l = list(self.cursor.fetchall())
        return l

    def get_changes_from_db(self, ver, n, curr=None):
        s1 = "SELECT * FROM cvix_minutes_" + ver + " WHERE minute_point=previous_point" + ('_eth' if curr == 'ETH' else '_btc' if  curr == 'BTC' else '') + " ORDER by minute_point DESC LIMIT " + str(n)
        self.cursor.execute(s1)
        l = list(self.cursor.fetchall())
        return l

