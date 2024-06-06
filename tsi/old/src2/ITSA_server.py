# encoding: utf-8

import os
import sys, os.path
if (sys.version.find('anaconda') != -1) or (sys.version.find('Continuum') != -1):
    anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                     '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                     '/home/anton/anaconda3/lib/python3.6/site-packages']
    sys.path = anaconda_path + sys.path
import json
import requests
from OPTS import parameters as parms
from OPTS import KYC_ITSA_operation as itsa
from flask import Flask, request, jsonify, Response, render_template

application = Flask(__name__)
kyc_port = parms.kyc_server_port # 8000
tsua_port = parms.tsua_server_port # 8020

@application.route("/onboard_assign_TS", methods=["PUT"])
def onboard_assign_TS():
    with open("default_onboard.json") as f:
        default_attributes = json.load(f)
    api_request = request.get_json()
    #print(api_request)
    # override with incoming values
    # default_attributes = {**default_attributes, **api_request} - does not work with Python3.4
    for k,v in api_request.items():
        default_attributes[k] = v 
    message, tsua_user_info = itsa.on_board(default_attributes,peek=False)
    # Update TSUA database from onboarding data
    tsua_url = "http://0.0.0.0:{:4d}".format(int(tsua_port))
    requests.put(url = tsua_url + "/insert_update_user", json = tsua_user_info).json()
    return jsonify({"user_ID":tsua_user_info["user_ID"], "TS":tsua_user_info["TS"]})
    #return jsonify(message)


@application.route("/get_aml_kyc_values", methods=["PUT"])
def aml_kyc_values():
    userid = request.get_json()["user_ID"]  
    #print(userid)
    kyc_values = itsa.aml_kyc_db.read_usr_parms_from_db(userid)
    return jsonify(kyc_values)


if __name__ == '__main__':
    # application.run(host='0.0.0.0', debug=False, port=1020)
    application.run(host='0.0.0.0', debug=False, port=kyc_port)
