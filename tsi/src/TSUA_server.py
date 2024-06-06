# encoding: utf-8

import os
import sys, os.path
if (sys.version.find('conda') != -1) or (sys.version.find('Continuum') != -1):
    anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                     '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                     '/home/anton/anaconda3/lib/python3.6/site-packages']
    sys.path = anaconda_path + sys.path
import json
from OPTS import parameters as parms
from OPTS import TSUA_operations as DB_opts
from flask import Flask, request, jsonify, Response, render_template

if (sys.version.find('anaconda') != -1) or (sys.version.find('Continuum') != -1):
    anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                     '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                     '/home/anton/anaconda3/lib/python3.6/site-packages']
    sys.path = anaconda_path + sys.path

application = Flask(__name__)
our_port = parms.tsua_server_port # 8020

@application.route("/insert_update_user", methods=["PUT"])
def insert_user_data():
    with open("default_TSUA_parms.json") as f:
        user_info = json.load(f)
    api_request = request.get_json()
    # override default values with incoming values
    for i in api_request:
        user_info[i] = api_request[i]
    user_ID = DB_opts.insert_new_user_in_db(user_info)
    return jsonify(user_ID)
#

@application.route("/new_txn_update_all_DBs", methods = ["PUT"])
def insert_txn_data():
    with open("default_txn.json") as f:
        txn = json.load(f)
    api_request = request.get_json()
    # override default values with incoming values
    for i in api_request:
        txn[i] = api_request[i]
    txn["transaction_time"]
    new_TS =  DB_opts.new_txn_update_all(txn)
    new_TS["type"] = "senders new TS"
    print(new_TS)
    return jsonify(new_TS)
#

@application.route("/check_spending_history", methods = ["PUT"])
def check_spending_history():
    user_ID = request.get_json()["user_ID"]
    #user_ID = request.get_json()
    spending_history = DB_opts.send_db.get_usr_txn_history(user_ID)
    return jsonify(spending_history)

#

@application.route("/check_receiving_history", methods = ["PUT"])
def check_receiving_history():
    user_ID = request.get_json()["user_ID"]
    #user_ID = request.get_json()
    receiving_history = DB_opts.rec_db.get_usr_txn_history(user_ID)
    return jsonify(receiving_history)

#

@application.route("/check_user_params", methods = ["PUT"])
def check_user_params():
    user_ID = request.get_json()["user_ID"]
    #user_ID = request.get_json()
    print(user_ID)
    user_parms = DB_opts.user_db.read_usr_parms_from_db(user_ID)
    return jsonify(user_parms)


if __name__ == '__main__':
    # application.run(host='0.0.0.0', debug=False, port=1020)
    application.run(host='0.0.0.0', debug=False, port=our_port)
