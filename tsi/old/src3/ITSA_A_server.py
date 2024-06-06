# encoding: utf-8

import os
import sys, os.path
if (sys.version.find('anaconda') != -1) or (sys.version.find('Continuum') != -1):
    anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                     '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                     '/home/anton/anaconda3/lib/python3.6/site-packages']
    sys.path = anaconda_path + sys.path
import json
from flask import Flask, request, jsonify, Response, render_template
sys.path.append(os.path.abspath('../../ts/src'))
from algs import Calculate_TS

application = Flask(__name__)


@application.route("/onboard_assign_TS", methods=["PUT"])
def TS_initial():
    api_request = request.get_json()
    
    TS = Calculate_TS(api_request, 'ITSA_A2')
    return jsonify({"TS":TS})

if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=False, port=1020)
    application.run()
