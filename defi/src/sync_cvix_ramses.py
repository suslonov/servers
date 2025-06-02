#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sshtunnel
import MySQLdb
from datetime import datetime, timedelta
import time

from db_cvx import DBPoints
from deribit3 import deribit_main

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
    def __init__(self, server_def):
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

def main():
    time.sleep(30)

    l1 = []
    l2 = []
    REQUEST_DEPTH = 10
    t1 = datetime.utcnow()
    try:
        with DBPointsRemote(rsynergy1_mysql) as db1:
#            with db_points_remote(rsynergy2_mysql) as db2:
            with DBPoints() as db2:
                l1 = db1.get_minutes_from_db('v003', 'minute', REQUEST_DEPTH)
                # print(l1[0][0], t1)
                if l1[0][0].replace(second=0) < t1.replace(second=0, microsecond=0):
                    raise  ValueError('no record at the head server for this minute ' + str(t1) + " last sec= " + str(l1[0][0]))
                l2 = db2.get_minutes_from_db('v003', 'minute', REQUEST_DEPTH)
                ii = 0
                while l1[ii][0].replace(second=0) > l2[0][0].replace(second=0) and ii < REQUEST_DEPTH:
                    ii += 1
                if ii < 1:
                    return
                
                # print("Depth=", ii)

                l004 = db1.get_minutes_from_db('v004', 'minute', ii)
                l0041 = db1.get_minutes_from_db('v0041', 'minute', ii)
                l0042 = db1.get_minutes_from_db('v0042', 'minute', ii)
                l0043 = db1.get_minutes_from_db('v0043', 'minute', ii)
                l0045 = db1.get_minutes_from_db('v0045', 'minute', ii)
                l0046 = db1.get_minutes_from_db('v0046', 'minute', ii)
                market_caps = db1.get_last_marketcap_from_db()
    
                if datetime.utcnow() - t1 > timedelta(minutes=1):
                    raise ValueError('getting the data from the main server gets too long')
    
                market_caps2 = db2.get_last_marketcap_from_db()
                if market_caps[0] > market_caps2[0]:
                    db2.add_marketcap_to_db(market_caps[0], market_caps[1], market_caps[2])

                for i in range(ii-1, -1, -1):
                    db2.add_minute_point_to_db("v003", l1[i][0], (l1[i][1], l1[i][2]), l1[i][3], l1[i][4], l1[i][5], l1[i][6], l1[i][7], l1[i][8], l1[i][9])
                    db2.add_minute_point_to_db("v004", l004[i][0], (l004[i][1], l004[i][2]), l004[i][3], l004[i][4], l004[i][5], l004[i][6], l004[i][7], l004[i][8], l004[i][9])
                    db2.add_minute_point_to_db("v0041", l0041[i][0], (l0041[i][1], l0041[i][2]), l0041[i][3], l0041[i][4], l0041[i][5], l0041[i][6], l0041[i][7], l0041[i][8], l0041[i][9])
                    db2.add_minute_point_to_db("v0042", l0042[i][0], (l0042[i][1], l0042[i][2]), l0042[i][3], l0042[i][4], l0042[i][5], l0042[i][6], l0042[i][7], l0042[i][8], l0042[i][9])
                    db2.add_minute_point_to_db("v0043", l0043[i][0], (l0043[i][1], l0043[i][2]), l0043[i][3], l0043[i][4], l0043[i][5], l0043[i][6], l0043[i][7], l0043[i][8], l0043[i][9])
                    db2.add_minute_point_to_db("v0045", l0045[i][0], (l0045[i][1], l0045[i][2]), l0045[i][3], l0045[i][4], l0045[i][5], l0045[i][6], l0045[i][7], l0045[i][8], l0045[i][9])
                    db2.add_minute_point_to_db("v0046", l0046[i][0], (l0046[i][1], l0046[i][2]), l0046[i][3], l0046[i][4], l0046[i][5], l0046[i][6], l0046[i][7], l0046[i][8], l0046[i][9])
    
                # for i in range(ii-1, -1, -1):
                #     btc, eth, r_b, r_e = db1.get_raw_data_from_db(l1[i][0])
                #     db2.add_raw_data_to_db(l1[i][0], (btc, eth), (r_b, r_e))
    except Exception as e:
        print(e, flush=True)
        deribit_main()

if __name__ == '__main__':
    main()



# while True:
#     time.sleep(2)
#     t1 = datetime.utcnow()
#     with DBPointsRemote(rsynergy1_mysql) as db1:
#         db1.cursor.execute("SELECT max(minute_point) FROM cvix_minutes_v003")
#         l1 = list(db1.cursor.fetchone())
#         if l1[0].replace(second=0) < t1.replace(second=0, microsecond=0):
#             print('no record at the head server for this minute ' + str(t1) + " last sec= " + str(l1[0]))
