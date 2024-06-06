# encoding: utf-8

import sys
import json
import os, os.path
if (sys.version.find('anaconda') != -1) or (sys.version.find('Continuum') != -1):
    anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                     '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                     '/home/anton/anaconda3/lib/python3.6/site-packages']
    sys.path = anaconda_path + sys.path
from ITSA_only_OPTS import ITSA_only_operation as itsa
from ITSA_only_OPTS import parameters as parms
from flask import Flask, request, jsonify, Response, render_template
 
application = Flask(__name__)
itsa_port = parms.itsa_server_port # 8022


@application.route("/calculate_initial_TS", methods=["PUT"])
def onboard_assign_TS():
    with open("default_onboard.json") as f:
        user_attributes = json.load(f)  # load the default attributes
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
        user_attributes[k] = v 
    tsua_user_info = itsa.compute_ITSA(user_attributes)
    return jsonify(tsua_user_info)


if __name__ == '__main__':
    # application.run(host='0.0.0.0', debug=False, port=1020)
    application.run()
#    application.run(host='0.0.0.0', debug=False, port=itsa_port)
