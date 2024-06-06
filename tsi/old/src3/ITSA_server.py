# encoding: utf-8

import sys
import json
import os
import sys, os.path
if (sys.version.find('anaconda') != -1) or (sys.version.find('Continuum') != -1):
    anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                     '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                     '/home/anton/anaconda3/lib/python3.6/site-packages']
    sys.path = anaconda_path + sys.path
from OPTS import parameters as parms
from OPTS import ITSA_operation as itsa
from flask import Flask, request, jsonify, Response, render_template

if (sys.version.find('anaconda') != -1) or (sys.version.find('Continuum') != -1):
    anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                     '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                     '/home/anton/anaconda3/lib/python3.6/site-packages']
    sys.path = anaconda_path + sys.path
 
application = Flask(__name__)
itsa_port = parms.itsa_server_port # 8022
tsua_port = parms.tsua_server_port # 8020

@application.route("/onboard_assign_TS", methods=["PUT"])
def onboard_assign_TS():
    with open("default_onboard.json") as f:
        default_attributes = json.load(f)
    api_request = request.get_json()

    # if 'Algorithm' in api_request:
    #     if api_request['Algorithm'] == 'ITSA_A2':
    #         sys.path.append(os.path.abspath('../../ts/src'))
    #         from algs import Calculate_TS
    #         TS = Calculate_TS(api_request, api_request['Algorithm'])
    #         return jsonify({"TS":TS})


    # override with incoming values
    # default_attributes = {**default_attributes, **api_request} - does not work with Python3.4
    for k,v in api_request.items():
        default_attributes[k] = v 
    tsua_user_info = itsa.compute_ITSA_pass_TSUA_info(default_attributes,peek=False)

    return jsonify(tsua_user_info)


@application.route("/get_itsa_values", methods=["PUT"])
def itsa_values():
    userid = request.get_json()["user_ID"]  
    #print(userid)
    itsa_values = itsa.itsa_value_db.read_usr_parms_from_db(userid)
    return jsonify(itsa_values)


if __name__ == '__main__':
    # application.run(host='0.0.0.0', debug=False, port=1020)
    application.run(host='0.0.0.0', debug=False, port=itsa_port)
