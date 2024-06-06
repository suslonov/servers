#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import random
from flask import Flask, render_template, request, flash, make_response, send_file

import requests
from hashlib import md5
import MySQLdb
import json
import tempfile
import math
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from utils import Proto_Load_TS_Data, Proto_Load_TS_Alg, Proto_Save_TS_Data
 
application = Flask(__name__)
application.secret_key = 'random string'
sub_path = "/"
img_path = "/www/ts/img"
file_path = "algs.py"
db = MySQLdb.connect(host="localhost", user="ts", passwd="ts_proto", db="ts_proto")
db.set_character_set('utf8')
mycur = db.cursor()
mycur.execute('SET NAMES utf8;')
mycur.execute('SET CHARACTER SET utf8;')
mycur.execute('SET character_set_connection=utf8;')
i = mycur.execute("""select * from t_countries""")
countries = mycur.fetchall()

@application.route(sub_path, methods = ['POST', 'GET'])
def home_page_ts():
    with open("server_parameters.json") as f:
        server_parameters = json.load(f)
    
    if request.method == 'POST':
        result = request.form
        algname = result.get('algname')

        if result.get('HistogramButton'):
            return hist_page_ts(algname)

        rowslist, userid, algs, _ = Proto_Load_TS_Data()
        sessionid = result.get('sessionid')
        if not sessionid:
            sessionstr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr) + str(datetime.datetime.now()) + str(round(random.random()*1000000, 0))
            sessionid = md5(sessionstr.encode("utf8")).hexdigest()

        userid = result.get('user_id')

        re = {}
        re_data = {}
        for r in rowslist:
            re[r[1]] = result.get("row_"+r[1])
            str_result = result.get("row_"+r[1])
            if r[1] == "Comment":
                continue
            if str_result:
                if r[2] == 0 or r[2] == 2 or r[2] == 6:
                    re_data[r[1]] = str_result
                elif r[2] == 1:
                    if str_result:
                        re_data[r[1]] = True
                    else:
                        re_data[r[1]] = False
                elif r[2] == 3:
                    re_data[r[1]] = int(str_result.replace(',',''))
                elif r[2] == 4:
                    re_data[r[1]] = float(str_result.replace(',',''))
                elif r[2] == 5:
                    re_data[r[1]] = str_result
                else:
                    re_data[r[1]] = str_result

        re_data["Algorithm"] = algname
        re_data["user_ID"] = sessionid[0:5]

        url = server_parameters["URLS"][algname]
        headers = {'Content-Type': "application/json"}
        res = requests.put(url, headers=headers, json=re_data)
        if res.status_code != 200:
            trustscore = "[Error status = " + str(res.status_code) + "]"
        else:
            trustscore = res.json()["TS"]

        if re:
            Proto_Save_TS_Data(sessionid, userid, rowslist, re, algname, trustscore)

        resp = make_response(render_template('home-page-ts.html', sub_path=sub_path, userid=userid, sessionid=sessionid, row_list=rowslist, algs=algs, algname=algname, ts=trustscore, re=re, countries=countries))
        resp.set_cookie('SessionID', sessionid)
        return resp
    else:
        sessionid = request.cookies.get('SessionID')
        algname = ''
        if not sessionid:
            sessionstr = request.environ.get('HTTP_X_REAL_IP', request.remote_addr) + str(datetime.datetime.now()) + str(round(random.random()*1000000, 0))
            sessionid = md5(sessionstr.encode("utf8")).hexdigest()
            rowslist, userid, algs, re = Proto_Load_TS_Data()
        else:
            rowslist, userid, algs, re = Proto_Load_TS_Data(0, sessionid)

        resp = make_response(render_template('home-page-ts.html', sub_path=sub_path, userid=userid, sessionid=sessionid, row_list=rowslist, algs=algs, algname=algname, re=re, countries=countries))
        resp.set_cookie('SessionID', sessionid)
        return resp

@application.route('/sid/<sid>', methods = ['GET'])
def home_page_ts_sid(sid):
    sessionid = sid
    rowslist, userid, algs, re = Proto_Load_TS_Data(0, sessionid)
    resp = make_response(render_template('home-page-ts.html', sub_path=sub_path, userid=userid, sessionid=sessionid, row_list=rowslist, algs=algs, re=re, countries=countries))
    resp.set_cookie('SessionID', sessionid)
    return resp

@application.route("/ts/algs")
def alg_page_ts():
    s = """select stepnum, algname, stepname, steptype from t_algs order by algname, stepnum"""

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

    algs = []
    if i > 0:
        algs = mycur.fetchall()

    with open(file_path, 'r') as f:
        code = list(f)
    with open(file_path, 'r') as f:
        c = list(len(l) for l in f)
    
    resp = make_response(render_template('algs.html', algs=algs, code=code))
    return resp

@application.route("/sidlist")
def sid_list():
    s1 = """select distinct algname from t_algs"""
    s2 = """select sessionid"""

    try:
        i = mycur.execute(s)
    except Exception:
        db = MySQLdb.connect(host="localhost", user="ts", passwd="ts_proto", db="ts_proto")
        db.set_character_set('utf8')
        mycur = db.cursor()
        mycur.execute('SET NAMES utf8;')
        mycur.execute('SET CHARACTER SET utf8;')
        mycur.execute('SET character_set_connection=utf8;')
        i = mycur.execute(s1)
    
    names = mycur.fetchall()

    row = ['sid']
    for n in names:
        row.append(n[0])
        s2 = s2 + """, min(case when algname = '""" + n[0] + """' then ts end) """ + n[0] + """ """  
    s2 = s2 + """from t_ts group by sessionid"""
    i = mycur.execute(s2)
    res = mycur.fetchall()

    ts_data = [row]
    for t1 in res:
        row = []
        for t2 in t1:
            if type(t2) == int or type(t2) == float:
                row.append("{:0,.3f}".format(t2))
            else:
                row.append(t2)
        ts_data.append(row)
    
    resp = make_response(render_template('sidlist.html', names=names, ts_data=ts_data))
    return resp

def hist_page_ts(algname):
    s = """select ts from t_ts where algname = %s"""
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

    t = mycur.fetchall()
    t1 = list(tt[0] for tt in t)
    plt.figure(1)
    plt.clf()
    if len(t1) > 100:
        bins = int(math.sqrt(len(t1)))
    else:
        bins = 10
    plt.hist(t1, bins=bins)
    plt.xlabel('Trust Score value')
    plt.ylabel('Number of users')
    ff = tempfile.NamedTemporaryFile(suffix='.png')
    f = ff.name
    plt.savefig(f)
    return send_file(f, mimetype='image/gif')   # overlaying problem !!!!

@application.route("/api_nobody_knows_it777", methods = ['POST', 'GET'])
def api_page_ts():
    s = """select id, url, api, type, req_data, reply from t_requests_log order by id desc"""
    s1 = """insert into t_requests_log (url, api, type, req_data, reply) values(%s, %s, %s, %s, %s)"""

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
    ll = mycur.fetchall()

    if request.method == 'POST':
        result = request.form
        url0 = result.get('url0')
        api0 = result.get('api0')
        type0 = result.get('type0')
        req_data = result.get('req_data')
        newflag = result.get('newflag')

        url = "http://" + url0 + "/" + api0
        headers = {'Content-Type': "application/json"}
        if type0 == "POST":
            res = requests.post(url, headers=headers, json = json.loads(req_data))
        if type0 == "GET":
            res = requests.get(url, headers=headers, json = json.loads(req_data))
        if type0 == "PUT":
            res = requests.put(url, headers=headers, json = json.loads(req_data))

        if res.status_code != 200:
            reply = "[Error status = " + str(res.status_code) + "]"
        else:
#            reply = str(res.json()).replace("'", '"')
            reply = res.text.replace('\n', ' ')

        if newflag:
            mycur.execute(s1, (url0, api0, type0, req_data, reply))
            db.commit()
            i = mycur.execute(s)
            ll = mycur.fetchall()
            newflag = 0

    else:
        url0 = ''
        api0 = ''
        type0 = ''
        req_data = ''
        reply = ''
        newflag = ''
  
    resp = make_response(render_template('requests_log.html', ll=ll, url0=url0, api0=api0, type0=type0, req_data=req_data, reply=reply, newflag=newflag))
    return resp
