#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
import os.path
import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from sklearn.externals import joblib
from utils import countries # Based on GCI index : https://www.itu.int/dms_pub/itu-d/opb/str/D-STR-GCI.01-2017-PDF-E.pdf
from utils import Proto_Load_TS_Data

def Calculate_TS(TSparameters, algname):

    if algname == "ITSA_A2":
        rowslist, _, _, _ = Proto_Load_TS_Data()
        for r in rowslist:
            if not r[1] in TSparameters:
                TSparameters[r[1]] = None
        return Calculate_ITSA_A2(TSparameters)
    else:
        return 0

ML_name = os.path.dirname(__file__) + '/rf'

# weights for the Trust Score calculation
id_type_w = 3
location_country_w = 1
citizenship_country_w = 1
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
    if status == "Married": result[0, 0] = 1
    return result

def f_Children(children, l, param):
#children up-to-1hot(3)
    result = np.zeros((l, param))
    if not children: return result
    if children == 'None': result[0, 0] =  1
    if children == 'Raising_children':  result[0, 1] = 1
    if children == 'Have_grandchildren': result[0, 1:3] = 1
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


def f_f_Employment(es, l, param):   #TODO correct after training
#Employment_status 1hot(6)
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
        if income == "$0-$1000": result[0, 0] = 1
        elif income == "$1000-$2000": result[0, 1] = 1
        elif income == "$2000-$4000": result[0, 1] = 1   # TODO correct after training
        elif income == "$4000-$8000": result[0, 2] = 1
        elif income == "$8000-$16000": result[0, 3] = 1
        elif income == "$16000-$32000": result[0, 3] = 1
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

spec_fields = ['Identification', 'age', 'Marital_status', 'Children', 'Education', 'Stake', 'Income', 'was_fraud',
               'Citizenship', 'Country', 'ZIP_code', 'Occupation', 'Bank_reference', 'Bank_account']
spec_fields_functions = [f_Identification, f_age, f_Family_status, f_Children, f_Education, f_Stake, f_Income, f_was_fraud,
                         f_simple_exists, f_simple_exists, f_simple_exists, f_simple_exists, f_simple_exists, f_simple_exists]
spec_fields_params = [4, 4, 1, 3, 6, 4, 5, 3, 1, 1, 1, 1, 1, 1]

def Calculate_ITSA_A2(p):
    trustscore = 0
    tsgroup = 0
    bias = 0

# TODO add checks

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

    if p["Income"] == "$0-$1000": p["income"] = 0
    elif p["Income"] == "$1000-$2000": p["income"] = 1000
    elif p["Income"] == "$2000-$4000": p["income"] = 2000
    elif p["Income"] == "$4000-$8000": p["income"] = 4000
    elif p["Income"] == "$8000-$16000": p["income"] = 8000
    elif p["Income"] == "$16000-$32000": p["income"] = 16000
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
    trustscore = trustscore + countries(p["Citizenship"], 'a') * citizenship_country_w
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
    if p["Marital_status"] == "Single": p_fs = -0.5
    if p["Marital_status"] == "Married": p_fs = 0    # just for clearness
    if p["Children"] == "Raising_children": p_fs += 0.5
    if p["Children"] == "Have_grandchildren": p_fs += 1
    trustscore = trustscore + p_fs * family_status_w

    p_es = 0
    if p["Employment_status"] == "None" or p["Employment_status"] == "Unemployed": p_es = -1
    if p["Employment_status"] == "Retired" or p["Employment_status"] == "Student": p_es = 0
    if p["Employment_status"] == "Employed" or p["Employment_status"] == "Self_employed": p_es = 1
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

