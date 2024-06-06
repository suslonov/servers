# encoding: utf-8

import sys
#TODO delete for github
if (sys.version.find('conda') != -1) or (sys.version.find('Continuum') != -1):
    anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                     '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                     '/home/anton/anaconda3/lib/python3.6/site-packages']
    sys.path = anaconda_path + sys.path
import json
import datetime
import dateutil.parser
from flask import Flask, request, jsonify

#####################################
# Loading general defaults
#####################################
with open("defaults.json") as f:
    defaults = json.load(f)
with open("feature_weights.json") as f:
    j = json.load(f)
    KYC_Q1_weights = j["regressed_feature_weights"]
    Q2_weights = j["Q2_feature_weights"]
    Q3_weights = j["Q3_feature_weights"]
with open("countries.json") as f:
    country_CGIs = json.load(f)["country_CGI"]
with open("industries.json") as f:
    industry_risk = json.load(f)["industry"]
#no need to check files

fields_KYC = ["Identification", "Date_of_birth", "Proof_of_residence", "Country", "Citizenship"]
fields_Q1 = ["Marital_status", "Children", "Education", "Employment_status", "Occupation", "Income_source_declared", 
             "Stable_income", "Income", "Has_license", "Insurance", "Social_network_account", "Site", "Bank_account", 
             "Bank_reference", "Credit_card_holder"]
#Not used "Credit_history", "Investor",  "Phone",  "Stake",  "ZIP_code"
fields_Q2 = ["Industry", "Online_trade_history", "Credit_history", "Tax_return"]
fields_Q3 = ["Constitution", "Industry", "Tax_return", "Auditing", "Online_trade_history", "Credit_history", "Rating",
             "Listing", "DB_report"]

bool_T_strings = ["TRUE", "True", "T", "true", "t", "1"]
bool_F_strings = ["", "NA", "FALSE", "False", "false", "F", "f", "None", "none", "No", "no", "n", "0"]

######################################
income_str_to_val = {"None": 0.0, "$0-$1000": 0, "$1000-$2000": 1000.0, "$2000-$4000": 2000.0,
                     "$4000-$8000": 4000.0, "$8000-$16000": 8000, "$16000-$32000": 16000, "$32000+": 32000.0}

regular_boolean_parms = ["Bank_account", "Credit_card_holder", "Has_license", "Credit_history",
                         "Income_source_declared", "Insurance", "Proof_of_residence", "Investor", "Phone",
                         "Stable_income"] + ["Constitution", "Tax_return", "Auditing", "Online_trade_history", 
                         "Credit_history", "Rating", "Listing", "DB_report"] #for testnet

unregular_boolean_parms = ["Bank_reference", "ZIP_code", "Site", "Social_network_account", "Occupation"]
#####################################
# Calculation
#####################################

def reformulate_user_attribute(k: str, v):
    
# Considering numerical features
    if k == "Date_of_birth":
        age = (datetime.datetime.now() - dateutil.parser.parse(v)).days/365.25
        return "Age", min(max(age, 0), 100)

    if k == "Citizenship" or k == "Country":
        return k, float(country_CGIs[v])

    if k == "Industry":
        return k, float(industry_risk[v])

    if k == "Income":
        if type(v) in [int, float]:
            attr = float(v)
        elif type(v) == str:
            if v in income_str_to_val:
                attr = income_str_to_val[v]
            else:
                attr = float(v.replace("$", ""))
        return k, attr
    
    if k == "Stake":
        return k, float(v)

# Considering features  where multiple possible choices are possible ("Nones" are ommitted as they add no points)
    if k == "Identification": return k, 1

    if k == "Children":
        if v == "Raising_children":
            return v, 1.0
        elif v == "Have_grandchildren":
            return ["Raising_children", "Have_grandchildren"], 1
        else:
            return k, 0

    if k == "Education":
        if v == "Elementary":
            return v, 1.0
        elif v == "Secondary":
            return ["Elementary", "Secondary"], 1.0
        elif v == "Bachelor":
            return ["Elementary", "Secondary", "Bachelor"], 1.0
        elif v in ["PhD_Doctorate", "Master"]:
            return ["Elementary", "Secondary", "Bachelor", "Post_graduate"], 1.0
        else:
            return k, 0

    if k == "Marital_status":
        if v in ["Married", "Permament_relationship"]:
            return "Relationship", 1.0
        else:
            return k, 0

    if k == "Employment_status":
        if v == "Employed":
            return "Employed", 1.0
        elif v in ["Retired", "Self_employed", "Student"]:
            return "Employment_other", 1.0
        else:
            return k, 0

# Converting booleans to their mathematical equivalent for regular and unregular boolean params
    if k in regular_boolean_parms + unregular_boolean_parms:
        fail_message = "FAILED: " + str(v)+" for parameter "+ k +" not recognized."

        if type(v) == bool:
            attr = float(v)
        elif type(v) in [int, float] and float(v) in [0.0, 1.0]:
            attr = float(v)
        elif type(v) == str:
            if k in unregular_boolean_parms:
                attr = 0.0 if v in bool_F_strings else 1.0
            else:
                attr = 1.0 if v in bool_T_strings else 0.0
        else:
            return "Error", fail_message
        return k, attr

#####################################
# Server operation
#####################################

application = Flask(__name__)

@application.route("/calculate_initial_TS", methods=["PUT"])
def report_ITSA():
# for backward compatibility
    api_request = request.get_json()

    TS = 10
    eo_semaphore = 0
    fields = fields_KYC + fields_Q1
    for k, v in api_request.items():
        if  k in fields:
            if k == "Identification" and (v not in ["National_ID", "Passport"]):
                return jsonify({"TS": 0})
            attr_key, attr_v = reformulate_user_attribute(k, v)
            if attr_key == "Error":
                return jsonify({"Error": attr_v})
            if eo_semaphore == 1: attr_v = 0
            if attr_key in ["Employment_status", "Occupation"] and attr_v == 0: eo_semaphore = 1
            if type(attr_key) == list:
                for a in attr_key:
                    TS += attr_v * KYC_Q1_weights.get(a, 0)
            else:
                TS += attr_v * KYC_Q1_weights.get(attr_key, 0)
        
    return jsonify({"TS": TS})

@application.route("/calculate_initial_TS_KYC", methods=["PUT"])
def report_ITSA_KYC():
    api_request = request.get_json()

    TS = 0
    for k, v in api_request.items():
        if  k in fields_KYC:
            if k == "Identification" and (v not in ["National_ID", "Passport"]):
                return jsonify({"TS": 0})
            attr_key, attr_v = reformulate_user_attribute(k, v)
            if attr_key == "Error":
                return jsonify({"Error": attr_v})
            if type(attr_key) == list:
                for a in attr_key:
                    TS += attr_v * KYC_Q1_weights.get(a, 0)
            else:
                TS += attr_v * KYC_Q1_weights.get(attr_key, 0)

    return jsonify({"TS": TS})

@application.route("/calculate_initial_TS_Q1", methods=["PUT"])
def report_ITSA_Q1():
    api_request = request.get_json()

    TS = 0
    eo_semaphore = 0
    for k, v in api_request.items():
        if  k in fields_Q1:
            attr_key, attr_v = reformulate_user_attribute(k, v)
            if attr_key == "Error":
                return jsonify({"Error": attr_v})
            if eo_semaphore == 1: attr_v = 0
            if attr_key in ["Employment_status", "Occupation"] and attr_v == 0: eo_semaphore = 1
            if type(attr_key) == list:
                for a in attr_key:
                    TS += attr_v * KYC_Q1_weights.get(a, 0)
            else:
                TS += attr_v * KYC_Q1_weights.get(attr_key, 0)
        
    return jsonify({"TS": TS})

@application.route("/calculate_initial_TS_Q2", methods=["PUT"])
def report_ITSA_Q2():
    api_request = request.get_json()

    TS = 0
    for k, v in api_request.items():
        if  k in fields_Q2:
            attr_key, attr_v = reformulate_user_attribute(k, v)
            if attr_key == "Error":
                return jsonify({"Error": attr_v})
            if type(attr_key) == list:
                for a in attr_key:
                    TS += attr_v * Q2_weights.get(a, 0)
            else:
                TS += attr_v * Q2_weights.get(attr_key, 0)
        
    return jsonify({"TS": TS})

@application.route("/calculate_initial_TS_Q3", methods=["PUT"])
def report_ITSA_Q3():
    api_request = request.get_json()

    TS = 0
    for k, v in api_request.items():
        if  k in fields_Q3:
            attr_key, attr_v = reformulate_user_attribute(k, v)
            if attr_key == "Error":
                return jsonify({"Error": attr_v})
            if type(attr_key) == list:
                for a in attr_key:
                    TS += attr_v * Q3_weights.get(a, 0)
            else:
                TS += attr_v * Q3_weights.get(attr_key, 0)
        
    return jsonify({"TS": TS})

if __name__ == '__main__':
    application.run(host=defaults["ip_address"]["host"],
                    debug=False, port=defaults["ip_address"]["port"])
