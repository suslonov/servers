# encoding: utf-8

import os
import sys, os.path
if (sys.version.find('anaconda') != -1) or (sys.version.find('Continuum') != -1):
    anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                     '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                     '/home/anton/anaconda3/lib/python3.6/site-packages']
    sys.path = anaconda_path + sys.path
import json
#import random
#from ITSA import calc_TS_old as ts
from ITSA import calc_ITSA as ts4
from TSUArocks import coti_rdbs_TSUA_operations as DB_opts
#import datetime
#from dateutil.relativedelta import relativedelta
from flask import Flask, request, jsonify, Response, render_template

application = Flask(__name__)

#@application.route("/")
#def home():
#    locations = [e.name for e in ts.Bad_and_Good_Locations]
#    education_level = [e.name for e in ts.Highest_education]
#    ids = [e.name for e in ts.Identification]
#    # print(ids)
#    return render_template('TS_toy_prototype.html', ids=ids, education_level=education_level, locations=locations)


#def safe_strip_time(entered_time: str):
#    years_past = 0
#    try:
#        years_past = relativedelta(datetime.date.today(),
#                                   datetime.datetime.strptime(entered_time, '%Y-%m-%d')).years
#    except Exception as e:
#        print(e)
#        years_past = 0
#    print(years_past)
#    return years_past
#
#
#@application.route("/calc_TS", methods=["POST"])
#def get_data():
#
#    # print(request.form.get("row_be_merchant"))
#    # print(request.form.get("row_id_type"))
#    # print(request.form.get("row_bank_account"))
#    # print(request.form.get("row_bank_reference"))
#    # print(request.form.get("row_family_status"))
#    # print(request.form.get("row_be_merchant"))
#    # print(request.form.get("row_income_source_declared"))
#    # print(request.form.get("row_stable_income"))
#    # print(request.form.get("row_investor"))
#    # print(request.form.get("row_education"))
#    # print(request.form.get("row_location_country"))
#    # print(request.form.get("row_was_fraud"))
#    # print(request.form.get("row_last_fraud"))
#    # print(request.form.get("row_insurance_available"))
#    # print(request.form.get("row_date_of_birth"))
#    # print(request.form.get("row_por_available"))
#    # print(request.form.get("row_cards_available"))
#    # print(request.form.get("row_credit_score"))
#    # print(request.form.get("row_driver_lic"))
#    # print(request.form.get("row_social_network"))
#    # print(request.form.get("row_site_owner"))
#    # print(request.form.get("row_confirm_phone"))
#    # print(request.form.get("row_zip_code"))
#    # print(request.form.get("row_year_founded"))
#
#    user_details = {}
#    user_details["Identification"] = ts.Identification[request.form.get(
#        "row_id_type")]
#    user_details["Bank account"] = request.form.get("row_bank_account") != ""
#    user_details["Bank reference"] = request.form.get(
#        "row_bank_reference") != ""
#    fam_stat = request.form.get("row_family_status")
#
#    if fam_stat == "Single":
#        user_details["Family status"] = ts.Family_Status.Single
#    elif fam_stat == "Married or in permanent relation":
#        user_details["Family status"] = ts.Family_Status.Married_permament_relation
#    elif fam_stat == "Raising children":
#        user_details["Family status"] = ts.Family_Status.Raising_children
#    elif fam_stat == "Have grandchildren":
#        user_details["Family status"] = ts.Family_Status.Have_grandchildren
#
#    user_details["Merchant"] = request.form.get("row_be_merchant") == "on"
#    user_details["Income source declared"] = request.form.get(
#        "row_income_source_declared") == "on"
#    user_details["Stable income"] = request.form.get(
#        "row_stable_income") == "on"
#    #
#    is_investing = request.form.get("row_investor") != ""
#    user_details["Investor"] = is_investing
#    user_details["Stake"] = 0 if not is_investing else int(request.form.get(
#        "row_investor"))
#    user_details["Education"] = ts.Highest_education[request.form.get(
#        "row_education")]
#    user_details["Location"] = ts.Bad_and_Good_Locations[request.form.get(
#        "row_location_country")]
#    user_details["No frauds"] = not (request.form.get("row_was_fraud") == "on")
#    user_details["Last fraud time"] = safe_strip_time(
#        request.form.get("row_last_fraud"))
#    user_details["Business age"] = safe_strip_time(request.form.get("row_year_founded"))
#    user_details["Insurance"] = request.form.get(
#        "row_insurance_available") == "on"
#    user_details["Age"] = safe_strip_time(
#        request.form.get("row_date_of_birth"))
#    user_details["Proof of residence"] = request.form.get(
#        "row_por_available") == "on"
#    user_details["Credit card holder"] = request.form.get(
#        "row_cards_available") == "on"
#    user_details["Credit score"] = int(request.form.get("row_credit_score")) \
#        if request.form.get("row_credit_score") != "" else 300
#    user_details["Has license"] = request.form.get("row_driver_lic") == "on"
#    user_details["No digital footprint"] = not request.form.get("row_social_network") and \
#        not request.form.get("row_site_owner")
#    user_details["Phone"] = request.form.get("row_confirm_phone") == "on"
#    user_details["ZIP code"] = False if request.form.get(
#        "row_zip_code") == "" else True
#    # print(user_details)
#
#    return render_template("result.html", result=ts.get_ts(user_details, True))


# API calls
import api_calls

# enums = {"Identification":ts.Identification, "Education":ts.Highest_education, "Location":ts.Bad_and_Good_Locations, "Family status":ts.Family_Status}

# @application.route("/get_TS_initial", methods=["PUT"])
# def TS_initial():
#     user_attributes = ts.worst_possible_user
#     api_request = request.get_json()
#     for e_label,e in enums.items():
#         if e_label in api_request:
#             api_request[e_label] = e[api_request[e_label]]
#     user_attributes = {**user_attributes, **api_request}
#     TS = ts.get_ts(user_attributes, False)
#     return jsonify({"TS":TS})

@application.route("/get_TS_initial", methods=["PUT"])
def TS_initial():
    with open("default_user.json") as f:
        default_attributes = json.load(f)
    api_request = request.get_json()
    
    if 'Algorithm' in api_request:
        if api_request['Algorithm'] == 'ITSA_A2':
            sys.path.append(os.path.abspath('../../ts/src'))
            from algs import Calculate_TS
            TS = Calculate_TS(api_request, api_request['Algorithm'])
            return jsonify({"TS":TS})

    # override with incoming values
    # default_attributes = {**default_attributes, **api_request}
    for k,v in api_request.items():
        default_attributes[k] = v 
    TS = ts4.get_ts(default_attributes, True)
    return jsonify({"TS":TS})


@application.route("/get_TS_update", methods=["GET"])
def TS_update():
    return jsonify({})


# TODO This should query the history nodes to verify update
@application.route("/post_TS_update", methods=["POST"])
def TS_update_post():
    transaction = request.get_json()
    TS = api_calls.TS_update(transaction)
    return jsonify({"new_TS":TS})


@application.route("/get_TS_token", methods=["PUT"])
def TS_token():
    uid = request.get_json()
    result = api_calls.TS_token(uid)
    return jsonify(result)


@application.route("/get_TS_from_token", methods=["PUT"])
def TS_from_token():
    token = request.get_json()
    result = api_calls.TS_from_token(token)
    return jsonify(result)


@application.route("/get_TS_history", methods=["PUT"])
def TS_history():
    # uid = request.get_json()
    return jsonify({})



# we set default parameters to that of a worst possible user
@application.route("/get_TS", methods=["PUT"])
def TS():
    return jsonify({})


@application.route("/get_TS_calculation_history", methods=["PUT"])
def TS_calculation_history():
    return jsonify({})


@application.route("/insert_update_user", methods=["POST"])
def insert_user_data():
    with open("default_user_TSUA.json") as f:
        user_info = json.load(f)
    api_request = request.get_json()
    # override default values with incoming values

    for i in api_request:
        user_info[i] = api_request[i]
    success = DB_opts.insert_new_user_in_db(user_info)
    return jsonify(success)

#

@application.route("/new_txn_update_all_DBs", methods = ["POST"])
def insert_txn_data():
    with open("default_txn.json") as f:
        txn = json.load(f)
    api_request = request.get_json()
    # override default values with incoming values
    for i in api_request:
        txn[i] = api_request[i]
    new_TS = str(DB_opts.new_txn_update_all(txn))
    print(new_TS)
    return jsonify({"senders_new_TS":new_TS})


#

@application.route("/check_spending_history", methods = ["POST"])
def check_spending_history():
    user_ID = request.get_json()["user_ID"]
    spending_history = DB_opts.send_db.get_usr_txn_history(user_ID)
    return jsonify(spending_history)

#

@application.route("/check_receiving_history", methods = ["POST"])
def check_receiving_history():
    user_ID = request.get_json()["user_ID"]
    receiving_history = DB_opts.rec_db.get_usr_txn_history(user_ID)
    return jsonify(receiving_history)

#

@application.route("/check_user_params", methods = ["POST"])
def check_user_params():
    user_ID = request.get_json()["user_ID"]
    print(user_ID)
    user_parms = DB_opts.user_db.read_usr_parms_from_db(user_ID)
    return jsonify(user_parms)



if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=False, port=1020)
    application.run(port=8020)
