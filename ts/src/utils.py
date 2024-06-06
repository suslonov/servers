#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import MySQLdb

def countries(c, alg = 'i'):
# Based on GCI index : https://www.itu.int/dms_pub/itu-d/opb/str/D-STR-GCI.01-2017-PDF-E.pdf
    s = """select gci, block_status from t_countries where iso3 = %s"""
    try:
        i = mycur.execute(s, (c, ))
    except Exception:
        db = MySQLdb.connect(host="localhost", user="ts", passwd="ts_proto", db="ts_proto")
        db.set_character_set('utf8')
        mycur = db.cursor()
        mycur.execute('SET NAMES utf8;')
        mycur.execute('SET CHARACTER SET utf8;')
        mycur.execute('SET character_set_connection=utf8;')
        i = mycur.execute(s, (c, ))

    if i == 0: i = mycur.execute(s, ('NA', ))
    if i == 0: return 0
        
    country = mycur.fetchone()

# EU Directive 2016/1675 of 14 July 2016
    if country[1]: return -5

    if alg == 'i':
        return (country[0] - 0.925/2)*12
    else:
        return (country[0] - 0.925/2)*4
        
def Proto_Load_TS_Data(rowsonly=1, sid=''):
    s = """select * from t_rows where roworder>0 order by roworder"""
    s1 = """select optnum, rowoption from t_row_options where rowname = %s"""
    s2 = """select distinct algname from t_algs"""
    s3 = """select userid from t_sessions where sessionid = %s"""
    s40 = """select * from t_data_str where sessionid = %s"""
    s43 = """select * from t_data_int where sessionid = %s"""
    s44 = """select * from t_data_dec where sessionid = %s"""
    s45 = """select * from t_data_date where sessionid = %s"""
    s425 = """select * from t_data_text where sessionid = %s"""

#0 - string,
#1 - checkbox,
#2 - select,
#3 - integer,
#4 - decimal,
#5 - date,
#6 - country,
#25 - text

    try:
        i = mycur.execute(s)
    except Exception:
        db = MySQLdb.connect(host="localhost", user="ts", passwd="ts_proto", db="ts_proto")
        db.set_character_set('utf8')
        mycur = db.cursor()
        mycur.execute('SET NAMES utf8;')
        mycur.execute('SET CHARACTER SET utf8;')
        mycur.execute('SET character_set_connection=utf8;')
        i = mycur.execute(s)

    rowslist = []
    re = {}
    if i > 0:
        rlst = mycur.fetchall()
        
        for r in rlst:
            if r[2] == 2:
                i1 = mycur.execute(s1, (r[1],))
                if i1 > 0:
                    rowslist.append((r[0], r[1], r[2], r[3], r[4], r[5], r[6], mycur.fetchall()))
            else:
                rowslist.append(r)

    if not rowsonly:
        i = mycur.execute(s40, (sid, ))
        if i > 0:
            rd = mycur.fetchall()
            for r1 in rd:
                re[r1[2]] = r1[3]
            else:
                re[r1[2]] = ""

        i = mycur.execute(s43, (sid, ))
        if i > 0:
            rd = mycur.fetchall()
            for r1 in rd:
                if r1[3]:
                    if r1[2][0:4] != 'year':            
                        re[r1[2]] = "{:,d}".format(r1[3])
                    else: re[r1[2]] = r1[3]
                else: re[r1[2]] = ""

        i = mycur.execute(s44, (sid, ))
        if i > 0:
            rd = mycur.fetchall()
            for r1 in rd:
                if r1[3]:
                    re[r1[2]] = "{:0,.2f}".format(r1[3])
                else:
                    re[r1[2]] = ""

        i = mycur.execute(s45, (sid, ))
        if i > 0:
            rd = mycur.fetchall()
            for r1 in rd:
                re[r1[2]] = r1[3]

        i = mycur.execute(s425, (sid, ))
        if i > 0:
            rd = mycur.fetchall()
            for r1 in rd:
                re[r1[2]] = r1[3]

        i = mycur.execute(s3, (sid, ))
        if i > 0:
            ru = mycur.fetchone()
            userid = ru[0]
        else:
            userid = ''
    else:
        userid = ''

    i = mycur.execute(s2)
    algs = []
    if i > 0:
        algs = mycur.fetchall()

    return rowslist, userid, algs, re


def Proto_Load_TS_Alg(algname):
    s = """select stepname, steptype from t_algs where algname = %s order by stepnum"""

    try:
        i = mycur.execute(s, (algname, ))
    except Exception:
        db = MySQLdb.connect(host="localhost", user="ts", passwd="ts_proto", db="ts_proto")
        db.set_character_set('utf8')
        mycur = db.cursor()
        mycur.execute('SET NAMES utf8;')
        mycur.execute('SET CHARACTER SET utf8;')
        mycur.execute('SET character_set_connection=utf8;')
        i = mycur.execute(s, (algname, ))

    alg = []
    if i > 0:
        alg = mycur.fetchall()

    return alg

def Proto_Save_TS_Data(sessionid, userid, rowslist, re, algname, ts):
    s1 = """DELETE FROM t_sessions WHERE sessionid = %s"""
    s20 = """DELETE FROM t_data_str WHERE sessionid = %s"""
    s23 = """DELETE FROM t_data_int WHERE sessionid = %s"""
    s24 = """DELETE FROM t_data_dec WHERE sessionid = %s"""
    s25 = """DELETE FROM t_data_date WHERE sessionid = %s"""
    s225 = """DELETE FROM t_data_text WHERE sessionid = %s"""
    s7 = """DELETE FROM t_ts WHERE sessionid = %s AND algname = %s"""
    s4 = """INSERT INTO t_sessions (sessionid, userid) VALUES (%s, %s)"""
    s50 = """INSERT INTO t_data_str (sessionid, rowname, tsstr) VALUES (%s, %s, %s)"""
    s53 = """INSERT INTO t_data_int (sessionid, rowname, tsint) VALUES (%s, %s, %s)"""
    s54 = """INSERT INTO t_data_dec (sessionid, rowname, tsdec) VALUES (%s, %s, %s)"""
    s55 = """INSERT INTO t_data_date (sessionid, rowname, tsdate) VALUES (%s, %s, %s)"""
    s525 = """INSERT INTO t_data_text (sessionid, rowname, tstext) VALUES (%s, %s, %s)"""
    s8 = """INSERT INTO t_ts (sessionid, algname, ts) VALUES (%s, %s, %s)"""
    
    try:
        mycur.execute(s1, (sessionid, ))
    except Exception:
        db = MySQLdb.connect(host="localhost", user="ts", passwd="ts_proto", db="ts_proto")
        db.set_character_set('utf8')
        mycur = db.cursor()
        mycur.execute('SET NAMES utf8;')
        mycur.execute('SET CHARACTER SET utf8;')
        mycur.execute('SET character_set_connection=utf8;')
        mycur.execute(s1, (sessionid, ))

    mycur.execute(s20, (sessionid, ))
    mycur.execute(s23, (sessionid, ))
    mycur.execute(s24, (sessionid, ))
    mycur.execute(s25, (sessionid, ))
    mycur.execute(s225, (sessionid, ))
    mycur.execute(s7, (sessionid, algname, ))
    mycur.execute(s4, (sessionid, userid))
    if algname: mycur.execute(s8, (sessionid, algname, ts))

    for r in re:
        rowl = next((row for row in rowslist if row[1] == r), None)  #find r in the rowslist using next(iterator)
#        flash(rowl,'info')
        
        if re[r]:
            rrrr = re[r]
        else:
            rrrr = None
        if rowl[2] == 0:
            mycur.execute(s50, (sessionid, r, re[r]))
        elif rowl[2] == 1:
            if re[r]:
                rrrr = 1
            else:
                rrrr = 0
            mycur.execute(s53, (sessionid, r, rrrr))
        elif rowl[2] == 2 or  rowl[2] == 6:
            mycur.execute(s50, (sessionid, r, re[r]))
        elif rowl[2] == 3:
            mycur.execute(s53, (sessionid, r, (rrrr.replace(',','') if rrrr else rrrr)))
        elif rowl[2] == 4:
            mycur.execute(s54, (sessionid, r, (rrrr.replace(',','') if rrrr else rrrr)))
        elif rowl[2] == 5:
            mycur.execute(s55, (sessionid, r, rrrr))
        else:
            mycur.execute(s525, (sessionid, r, re[r]))

    db.commit()

def Proto_Save_TS_Only(sessionid, userid, algname, ts):
    s1 = """DELETE FROM t_sessions WHERE sessionid = %s"""
    s7 = """DELETE FROM t_ts WHERE sessionid = %s AND algname = %s"""
    s4 = """INSERT INTO t_sessions (sessionid, userid) VALUES (%s, %s)"""
    s8 = """INSERT INTO t_ts (sessionid, algname, ts) VALUES (%s, %s, %s)"""
    
    try:
        mycur.execute(s1, (sessionid, ))
    except Exception:
        db = MySQLdb.connect(host="localhost", user="ts", passwd="ts_proto", db="ts_proto")
        db.set_character_set('utf8')
        mycur = db.cursor()
        mycur.execute('SET NAMES utf8;')
        mycur.execute('SET CHARACTER SET utf8;')
        mycur.execute('SET character_set_connection=utf8;')
        mycur.execute(s1, (sessionid, ))

    mycur.execute(s7, (sessionid, algname, ))
    mycur.execute(s4, (sessionid, userid))
    if algname: mycur.execute(s8, (sessionid, algname, ts))

    db.commit()

