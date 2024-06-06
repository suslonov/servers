#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
import os.path
import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from enum import Enum
from flask import flash
from sklearn.externals import joblib
import csv
from utils import countries # Based on GCI index : https://www.itu.int/dms_pub/itu-d/opb/str/D-STR-GCI.01-2017-PDF-E.pdf
from utils import Proto_Load_TS_Data

def Calculate_TS(TSparameters, algname):

    if algname == "ITSA_A2":
        rowslist, _, _, _ = Proto_Load_TS_Data()
        for r in rowslist:
            if not r[1] in TSparameters:
                TSparameters[r[1]] = None
        return Calculate_ITSA_A2(TSparameters)
    if algname == "ITSA_I1":
        return Calculate_ITSA_I1(TSparameters)

#Anton
ML_name = os.path.dirname(__file__) + '/rf'
# weights for the Trust Score calculation
id_type_w = 3
location_country_w = 2
zip_code_w = 1
age_w = 2
family_status_w = 1
confirm_phone_w = 1
education_w = 3
por_available_w = 3
driver_lic_w = 1
social_network_w = 1
site_owner_w = 1
investor_w = 3
bank_account_w = 2
insurance_available_w = 1
cards_available_w = 1
income_w = 3
occupation_w = 1
bank_reference_w = 2
employment_status_w = 1

def f_Identification(Identification, l, param):
#Identification	1hot(4)
    result = np.zeros((l, param))
    col = 0
    if Identification == 'Passport': col = 1
    elif Identification == 'National_ID': col = 2
    elif Identification == 'False_documentation': col = 3
    result[0, col] = 1
    return result

def f_age(age, l, param):
#age 1hot(4)
    result = np.zeros((l, param))
    if not age: return result
    col = 0
    if age > 16 : col = 1
    elif age > 22 : col = 2
    elif age > 26 : col = 3
    result[0, col] = 1
    return result

def f_Family_status(status, l, param):
    result = np.zeros((l, param))
    if status == "Married or in permanent relation": result[0, 0] = 1
    return result

def f_Children(children, l, param):
#children up-to-1hot(3)
    result = np.zeros((l, param))
    if not children: return result
    if children == 'None': result[0, 0] =  1
    if children == 'Raising children':  result[0, 1] = 1
    if children == 'Have grandchildren': result[0, 1:3] = 1
    return result
    
def f_Education(education, l, param):
#education up-to-1hot(6)
    result = np.zeros((l, param))
    if not education: return result
    if education == "Not_educated": result[0, 0] = 1
    if education == "Elementary": result[0, 1] = 1
    if education == "Secondary": result[0, 1:3] = 1
    if education == "Bachelor":  result[0, 1:4] = 1
    if education == "Master":  result[0, 1:5] = 1
    if education == "PhD_Doctorate":  result[0, 1:6] = 1
    return result


def f_f_Education(es, l, param):   #TODO correct after training
#f_Education 1hot(6)
    result = np.zeros((l, param))
    if not es: return result
    if es == "None": result[0, 0] = 1
    if es == "Employed": result[0, 1] = 1
    if es == "Self-Employed": result[0, 2] = 1
    if es == "Retired":  result[0, 3] = 1
    if es == "Student":  result[0, 5] = 1
    if es == "Unemployed":  result[0, 5] = 1
    return result

def f_Stake(stake, l, param):
#investor up-to-1hot(4)
    result = np.zeros((l, param))
    if stake:
        if stake <= 0: result[0, 0] = 1
        if stake > 0: result[0, 1] = 1
        if stake >= 100: result[0, 2] = 1
        if stake >= 1000: result[0, 3] = 1
    else: result[0, 0] = 1
    return result

def f_Income(income, l, param):
#income up-to-1hot(5)
    result = np.zeros((l, param))
    if income:
        if income == "$0 - $1000": result[0, 0] = 1
        elif income == "$1000 - $2000": result[0, 1] = 1
        elif income == "$2000 - $4000": result[0, 1] = 1   # TODO correct after training
        elif income == "$4000 - $8000": result[0, 2] = 1
        elif income == "$8000 - $16000": result[0, 3] = 1
        elif income == "$16000 - $32000": result[0, 3] = 1
        elif income == "$32000+": result[0, 4] = 1
        else: result[0, 0] = 1
    else: result[0, 0] = 1
    return result

def f_was_fraud(fraud, l, param):
#was_fraud 1hot(3)
    result = np.zeros((l, param))
    if fraud:
        if fraud == 2:
            result[0, 2] = 1
        elif fraud == 1:
            result[0, 1] = 1
        else:
            result[0, 0] = 1
    else:
        result[0, 0] = 1
    return result

def f_simple_exists(c, l, param):
#just stub, this field is not used for ML
    result = np.zeros((l, param))
    if c:
        if c != 'None' and c != 'none':
            result[0, 0] = 1
    return result

spec_fields = ['Identification', 'age', 'Family_status', 'Children', 'Education', 'Stake', 'Income', 'was_fraud',
               'Country', 'ZIP_code', 'Occupation', 'Bank_reference', 'Bank_account']
spec_fields_functions = [f_Identification, f_age, f_Family_status, f_Children, f_Education, f_Stake, f_Income, f_was_fraud,
                         f_simple_exists, f_simple_exists, f_simple_exists, f_simple_exists, f_simple_exists]
spec_fields_params = [4, 4, 1, 3, 6, 4, 5, 3, 1, 1, 1, 1, 1]

def Calculate_ITSA_A2(p):
    trustscore = 0
    tsgroup = 0
    bias = 0

# TODO add checking

# preprocessing step
    if p["Date_of_birth"]:
        if type(p["Date_of_birth"]).__name__ == 'datetime' or type(p["Date_of_birth"]).__name__ == 'date':
            p["age"] = relativedelta(datetime.date.today(), p["Date_of_birth"]).years
        else:
            p["age"] = relativedelta(datetime.date.today(), datetime.datetime.strptime(p["Date_of_birth"], '%Y-%m-%d')).years
    else:
        p["age"] = None

    if p["Fill_date"]:
        if type(p["Fill_date"]).__name__ == 'datetime' or type(p["Fill_date"]).__name__ == 'date':
            d = p["Fill_date"]
        else:
            d = datetime.datetime.strptime(p["Fill_date"], '%Y-%m-%d')
        p["decay_term"] = relativedelta(datetime.date.today(), d).years
        p["decay_term_days"] = (datetime.datetime.today() - d).days
    else:
        p["decay_term"] = 0
        p["decay_term_days"] = 0


    if p["Stake"]: p["Stake"] = float(p["Stake"].replace(',',''))   # TODO clear it
    if p["Income"] == "$0 - $1000": p["income"] = 0
    elif p["Income"] == "$1000 - $2000": p["income"] = 1000
    elif p["Income"] == "$2000 - $4000": p["income"] = 2000   # TODO correct after training
    elif p["Income"] == "$4000 - $8000": p["income"] = 4000
    elif p["Income"] == "$8000 - $16000": p["income"] = 8000
    elif p["Income"] == "$16000 - $32000": p["income"] = 16000
    elif p["Income"] == "$32000+": p["income"] = 32000
    else: p["income"] = 0

# basketing  step

# without KYC the Trust Score = 0, enter disabled
    if not p["Identification"]:
        return 0
    elif p["Identification"] == 'Not_provided':
        return 0
    elif p["Identification"] == 'False_documentation':
        return 0

    if p["age"]:
        if p["age"] < 16:
            return 0

# read the headers from file
    with open(ML_name + '.csv') as csvfile:
        s = csvfile.readline().rstrip()
        headers = s.split(',')

# collect the features vector from the fields
    start = True
    for header in headers:
        # check if field is special
        field_id = next((i for i, li in enumerate(spec_fields) if li == header), None)

        # take a field
        if header in p:
            attr = p[header]
        else:
            attr = ''
        col = np.array(attr).reshape(1,1)

        # convert special columns
        if field_id or field_id == 0:
            res = spec_fields_functions[field_id](col, 1, spec_fields_params[field_id])
        else:
            if attr:
                if attr == 'None' or attr == 'none':
                    res = np.zeros((1, 1))
                elif attr == 'on':
                    res = np.zeros((1, 1))
                    res[0, 0] = 1
                else:
                    res = col
            else:
                res = np.zeros((1, 1))

        # begin or not, if not - add to the end
        
        if start:
            features = res
            start = False
        else:
            features = np.concatenate((features, res), 1)

# load the model and predict the basket
    rf2 = joblib.load(ML_name + '.clf')

#    flash(features)

    grp = rf2.predict(features)
    tsgroup = grp[0]

# the correction according to the group mean value
    bias = - (15.76206 - tsgroup ** 1.32602)

#    print(grp)
#    print(p.bias)

#    flash(features.shape)
#    flash(features)
#    flash(grp)
#    flash(p.bias)

# Calculation step
    if tsgroup == 0:
        return 0

    trustscore = (tsgroup) * 10 + bias

    if p["Identification"] == 'Passport': trustscore = trustscore + id_type_w * 2/3
    elif p["Identification"] == 'National_ID': trustscore = trustscore + id_type_w

    trustscore = trustscore + countries(p["Country"], 'a') * location_country_w
    if p["ZIP_code"]:
        if p["ZIP_code"] != 'None' and p["ZIP_code"] != 'none':
            trustscore = trustscore + zip_code_w    # no analytics, just fact

    p_ed = 0
    if p["Education"] == "Not_educated": p_ed = -1
    if p["Education"] == "Elementary": p_ed = -0.5
    if p["Education"] == "Secondary": p_ed = 0   # just for clearness
    if p["Education"] == "Bachelor" or p["Education"] == "Master": p_ed = 0.5
    if p["Education"] == "PhD_Doctorate": p_ed = 1
    trustscore = trustscore + p_ed * education_w

    if p["age"]:
        trustscore = trustscore + ((0.2 if p["age"]> 18 else 0) + (0.5 if p["age"]> 22 else 0) + (1 if p["age"]> 26 else 0))*age_w

    p_fs = 0
    if p["Family_status"] == "Single": p_fs = -0.5
    if p["Family_status"] == "Married or in permanent relation": p_fs = 0    # just for clearness
    if p["Children"] == "Raising children": p_fs += 0.5
    if p["Children"] == "Have grandchildren": p_fs += 1
    trustscore = trustscore + p_fs * family_status_w

    p_es = 0
    if p["Employment_status"] == "None" or p["Employment_status"] == "Unemployed": p_es = -1
    if p["Employment_status"] == "Retired" or p["Employment_status"] == "Student": p_es = 0
    if p["Employment_status"] == "Employed" or p["Employment_status"] == "Self-Employed": p_ed = 1
    trustscore = trustscore + p_es * employment_status_w

    if p["Occupation"]: 
        if p["Occupation"] != 'None' and p["Occupation"] != 'none':
            trustscore = trustscore + occupation_w    # no analytics, just fact
    if p["Bank_reference"]:
        if p["Bank_reference"] != 'None' and p["Bank_reference"] != 'none':
            trustscore = trustscore + bank_reference_w    # no analytics, just fact
    if p["Phone"]: trustscore = trustscore + confirm_phone_w
    if p["Proof_of_residence"]: trustscore = trustscore + por_available_w
    if p["Has_license"]: trustscore = trustscore + driver_lic_w
    if p["Social_network_account"]: trustscore = trustscore + social_network_w
    if p["Site"]: trustscore = trustscore + site_owner_w
    if p["Bank_account"]: trustscore = trustscore + bank_account_w
    if p["Insurance"]: trustscore = trustscore + insurance_available_w
    if p["Credit_card_holder"]: trustscore = trustscore + cards_available_w

    if p["Stake"]: trustscore = trustscore + smooth_sigm(p["Stake"]/10000)*investor_w
    if p["income"]: trustscore = trustscore + smooth_sigm(p["income"]/100000)*income_w

    if trustscore < 1: trustscore = 1
    return trustscore

def smooth_sigm(x):
    return 1 / (1 + math.exp(-x))



# TODO delete ISAZI
class Identification(Enum):
    False_documentation = -200
    Not_provided = -100
    Passport = 10
    National_ID = 15

class Highest_education(Enum):
    Not_educated = 0
    Elementary = 1
    Secondary = 3
    Bachelor = 5
    Master = 6
    PhD_Doctorate = 7
    
class Family_Status(Enum):
    Single = -1
    Married_permament_relation = 0
    Raising_children = 1
    Have_grandchildren = 2

def Calculate_ITSA_I1(p):

    user_details = {}
    user_details["Identification"] = Identification[p["Identification"]]
    user_details["Bank account"] = 1 if p["Bank_account"] else 0
    user_details["Bank reference"] = 1 if p["Bank_reference"] else 0

    if p["Family_status"] == "Single": user_details["Family status"] = Family_Status.Single
    elif p["Family_status"] == "Married or in permanent relation": user_details["Family status"] = Family_Status.Married_permament_relation
    
    if p["Children"] == "Raising children": user_details["Family status"] = Family_Status.Raising_children
    elif p["Children"] == "Have grandchildren": user_details["Family status"] = Family_Status.Have_grandchildren

#    user_details["Merchant"] = 1 if p["be_merchant"] else 0
    user_details["Income source declared"] = 1 if p["Income_source_declared"] else 0
    user_details["Stable income"] = 1 if p["Stable_income"] else 0

    is_investing = 1 if p["Investor"] else 0
    user_details["Investor"] = is_investing
    user_details["Stake"] = 0 if not is_investing else float(p["Stake"].replace(',',''))
    user_details["Education"] = Highest_education[p["Education"]]
    if p["Country"] == 'None': p["Country"] = 'NA'
    user_details["Country"] = p["Country"]   #I've changed it
#    user_details["No frauds"] = 0 if p["was_fraud"] else 1
#    user_details["Last fraud time"] = safe_strip_time(p["last_fraud"])
#    user_details["Business age"] = safe_strip_time(p["incorporation_date"])
    user_details["Insurance"] = 1 if p["Insurance"] else 0
    user_details["Age"] = safe_strip_time(p["Date_of_birth"])
    user_details["Proof of residence"] = 1 if p["Proof_of_residence"] else 0
    user_details["Credit card holder"] = 1 if p["Credit_card_holder"] else 0
    
    user_details["Has license"] = 1 if p["Has_license"] else 0
    user_details["No digital footprint"] = 0 if p["Social_network_account"] or p["Site"] else 1
    user_details["Phone"] = 1 if p["Phone"] else 0
    user_details["ZIP code"] = 1 if p["ZIP_code"] else 0
    
    ts = 0
    i = 0
    for x, s in trans_to_pnt_scores(user_details).items():
        i += 1
        #print(i, ":\t Computing for ", x, " with value: ", s)

        if x != "Fraud multiplier":
            ts += s
        else:
            ts *= s

    ts = ts if ts > 1 else 1
    ts = max(0, min(100, ts))

    return ts

# risk = -0.279*age + 3.047  based on pg 53  of Stability and Change in Risk ....
# i.e. it seems (from what the psychologists are saying) that -risk ~ age. Thus Trust Points ~ age
# from http://www.diw.de/documents/publikationen/73/diw_01.c.525809.de/diw_sp0816.pdf
# Zero points if 20 or younger, max points if 75 or older
def age_points(age: float):
    points = 5*(age - 20)/(75-20) if 20 <= age <= 75 else 5 if 75 < age else 0
    return points

def safe_strip_time(entered_time):
    years_past = 0
    try:
        if type(entered_time).__name__ == 'datetime'  or type(entered_time).__name__ == 'date':
            years_past = relativedelta(datetime.date.today(), entered_time).years
        else:
            years_past = relativedelta(datetime.date.today(), datetime.datetime.strptime(entered_time, '%Y-%m-%d')).years
    except Exception as e:
        years_past = 0
    return years_past

def smooth(x: float, mu: float, a: float):
    """Smooth the function with a Fermi-Dirac like distribution - the \"Temperature\" parameter is a.
    ? is the central point (=0.5 here)"""
    return 1/(1 + np.exp((mu-x)/a))

def trans_to_pnt_scores(input_dict: dict):
    score_weights = {
        #' Note that these are only applicable for True/False answers
        "Bank account": 10,
        "Bank reference": 2,
        "Business age": 7,
        "Income source declared": 6,
        "Stable income": 6,
        "Stake": 6,
        "No frauds": 6,
        "Insurance": 5,
        "Proof of residence": 5,
        "ZIP code": 2,
        "Credit card holder": 5,
        "Has license": 5,
        "No digital footprint": -3,
        "Phone": 2,
    }
    
    output_dict = dict()

    # For all users
    output_dict["Identification"] = input_dict["Identification"].value
    output_dict["Bank account"] = \
        score_weights["Bank account"] * input_dict["Bank account"]
    output_dict["Bank reference"] = \
        score_weights["Bank reference"] * input_dict["Bank reference"]
    output_dict["Income source declared"] = score_weights["Income source declared"] * \
        input_dict["Income source declared"]
    output_dict["Stable income"] = \
        score_weights["Stable income"] * input_dict["Stable income"]
    output_dict["Stake"] = input_dict["Investor"] * \
        smooth(input_dict["Stake"], 0, 10000)*score_weights["Stake"]
    output_dict["Location"] = countries(input_dict["Country"])   #I've changed it
    output_dict["Insurance"] = \
        input_dict["Insurance"] * score_weights["Insurance"]

    output_dict["Proof of residence"] = \
        input_dict["Proof of residence"] * score_weights["Proof of residence"]
    if input_dict["Identification"] == Identification.Passport:
        output_dict["Proof of residence"] = 2 * input_dict["Proof of residence"] * \
            score_weights["Proof of residence"]
    output_dict["No digital footprint"] = input_dict["No digital footprint"] * \
        score_weights["No digital footprint"]
    output_dict["Phone"] = input_dict["Phone"] * score_weights["Phone"]
#    output_dict["No frauds"] = input_dict["No frauds"] * \
#        score_weights["No frauds"]
    output_dict["ZIP code"] = input_dict["ZIP code"]*score_weights["ZIP code"]

#    if not input_dict["Merchant"]:
    output_dict["Age"] = age_points(input_dict["Age"])
    output_dict["Family status"] = input_dict["Family status"].value
    output_dict["Education"] = input_dict["Education"].value
    output_dict["Credit card holder"] = input_dict["Credit card holder"] * \
        score_weights["Credit card holder"]
    output_dict["Has license"] = input_dict["Has license"] * \
        input_dict["Insurance"]*score_weights["Has license"]
#    else:
#        ba = input_dict["Business age"]
#        if 1 <= ba < 20:
#            output_dict["Business age"] = score_weights["Business age"] * \
#                smooth(ba, 10, 10)
#        elif ba >= 20:
#            output_dict["Business age"] = score_weights["Business age"]
#        else:
#            output_dict["Business age"] = 0
        # Rescaling fields for a merhant so that they are more highly weighted
#        for key in output_dict.keys():
#            if key != "Fraud multiplier":
#                output_dict[key] *= 100/78

#    if input_dict["No frauds"]:
#        output_dict["Fraud multiplier"] = 1
#    else:
#        lst_time = input_dict["Last fraud time"]
#        if lst_time > 20:
#            output_dict["No frauds"] = score_weights["No frauds"]
#            output_dict["Fraud multiplier"] = 1
#        else:
#            output_dict["Fraud multiplier"] = smooth(lst_time, 10, 10)

    return output_dict
