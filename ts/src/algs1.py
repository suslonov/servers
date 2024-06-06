#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import math
import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
from enum import Enum
from flask import flash
from sklearn.externals import joblib
import csv

class Participant(object):
    trustscore = 0
    tsgroup = 0
    # There will be more internal variables for counting

# The constructor calculates trust score step-by-step according to the algorithm
    def __init__(self, params, algname, alg):
        for par in params:
            setattr(self, par, params[par])
        for a in alg:
            eval("Step_" + algname + "_" + a[0] + "(self)")

# the names of functions doing algorithm steps are:  Step + AlgorithmName + AlgorithmStepName
def Step_Random_Random(p):
    p.trustscore = random.random() * 100

#Anton
def Step_ITSU_A1_Preprocessing(p):
    if p.date_of_birth:
        if type(p.date_of_birth).__name__ == 'datetime' or type(p.date_of_birth).__name__ == 'date':
            p.age = relativedelta(datetime.date.today(), p.date_of_birth).years
        else:
            p.age = relativedelta(datetime.date.today(), datetime.datetime.strptime(p.date_of_birth, '%Y-%m-%d')).years
    else:
        p.age = None

    if p.incorporation_date:
        if type(p.incorporation_date).__name__ == 'datetime' or type(p.incorporation_date).__name__ == 'date':
            d = p.incorporation_date
        else:
            d = datetime.datetime.strptime(p.incorporation_date, '%Y-%m-%d')
        p.business_age = relativedelta(datetime.date.today(), d).years
        if p.business_age < 0: p.business_age = None
    else:
        p.business_age = None

    if p.last_fraud:
        if type(p.last_fraud).__name__ == 'datetime' or type(p.last_fraud).__name__ == 'date':
            d = p.last_fraud
        else:
            d = datetime.datetime.strptime(p.last_fraud, '%Y-%m-%d')
        p.term = relativedelta(datetime.date.today(), d).years
        p.term_days = (datetime.date.today() - d).days
    else:
        p.term = 0
        p.term_days = 0

    if p.fill_date:
        if type(p.fill_date).__name__ == 'datetime' or type(p.fill_date).__name__ == 'date':
            d = p.fill_date
        else:
            d = datetime.datetime.strptime(p.fill_date, '%Y-%m-%d')
        p.decay_term = relativedelta(datetime.date.today(), d).years
        p.decay_term_days = (datetime.date.today() - d).days
    else:
        p.decay_term = 0
        p.decay_term_days = 0


    if p.investor: p.investor = float(p.investor.replace(',',''))
    if p.income: p.income = float(p.income.replace(',',''))
    if p.merch_turn: p.merch_turn = float(p.merch_turn.replace(',',''))
    #    if p.merch_bal: p.merch_bal = float(p.merch_bal.replace(',',''))

def Step_ITSU_A1_Basketing(p):
    p.tsgroup = 3
    p.bias = 0
# without KYC the Trust Score = 0, enter disabled
    if not p.id_type:
        p.tsgroup = 0
        return
    elif p.id_type == 'Not_provided':
        p.tsgroup = 0
        return
    elif p.id_type == 'False_documentation':
        p.tsgroup = 0
        return

    if p.age:
        if p.age < 16:
            p.tsgroup = 0
            return

# the limitation term for frauds is 20 years, but after 10 years the limitation are eased 
    if p.was_fraud:
        if p.term < 10:
            p.tsgroup = 1
            return
        elif p.term < 20:
            p.tsgroup = 2
            return

# controversial point, it means that pretended merchant always have TS>40 (if no fraud)
    if p.be_merchant:
        p.tsgroup = 4

    if p.investor:
        if p.investor >= 1000:
            p.tsgroup = 5
    if p.income or p.credit_history:
        p.tsgroup = 5

def Step_ITSU_A1_Counting(p):
    if p.tsgroup == 0:
        p.trustscore = 0
        return

    p.trustscore = (p.tsgroup - 1) * 10 + p.bias

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
    merch_turn_w = 1
    #    merch_bal_w = 1
    income_w = 3
    occupation_w = 1
    bank_reference_w = 2
    business_age_w = 1

    if p.id_type == 'Passport': p.trustscore = p.trustscore + id_type_w * 2/3
    elif p.id_type == 'National_ID': p.trustscore = p.trustscore + id_type_w

    p.trustscore = p.trustscore + countries(p.location_country) * location_country_w
    if p.zip_code:
        if p.zip_code != 'None' and p.zip_code != 'none':
            p.trustscore = p.trustscore + zip_code_w    # no analytics, just fact

    p_ed = 0
    if p.education == "Not_educated": p_ed = -1
    if p.education == "Elementary": p_ed = -0.5
    if p.education == "Secondary": p_ed = 0   # just for clearness
    if p.education == "Bachelor" or p.education == "Master": p_ed = 0.5
    if p.education == "PhD_Doctorate": p_ed = 1
    p.trustscore = p.trustscore + p_ed * education_w

    if p.age:
        p.trustscore = p.trustscore + ((0.2 if p.age> 18 else 0) + (0.5 if p.age> 22 else 0) + (1 if p.age> 26 else 0))*age_w

    p_fs = 0
    if p.family_status == "Single": p_fs = -0.5
    if p.family_status == "Married or in permanent relation": p_fs = 0    # just for clearness
    if p.children == "Raising children": p_fs += 0.5
    if p.children == "Have grandchildren": p_fs += 1
    p.trustscore = p.trustscore + p_fs * family_status_w

    if p.occupation: 
        if p.occupation != 'None' and p.occupation != 'none':
            p.trustscore = p.trustscore + occupation_w    # no analytics, just fact
    if p.bank_reference:
        if p.bank_reference != 'None' and p.bank_reference != 'none':
            p.trustscore = p.trustscore + bank_reference_w    # no analytics, just fact
    if p.confirm_phone: p.trustscore = p.trustscore + confirm_phone_w
    if p.por_available: p.trustscore = p.trustscore + por_available_w
    if p.driver_lic: p.trustscore = p.trustscore + driver_lic_w
    if p.social_network: p.trustscore = p.trustscore + social_network_w
    if p.site_owner: p.trustscore = p.trustscore + site_owner_w
    if p.bank_account: p.trustscore = p.trustscore + bank_account_w
    if p.insurance_available: p.trustscore = p.trustscore + insurance_available_w
    if p.cards_available: p.trustscore = p.trustscore + cards_available_w

    if p.business_age: p.trustscore = p.trustscore + smooth_sigm(p.business_age/10)*business_age_w
    if p.investor: p.trustscore = p.trustscore + smooth_sigm(p.investor/10000)*investor_w
    if p.income: p.trustscore = p.trustscore + smooth_sigm(p.income/100000)*income_w
    if p.merch_turn: p.trustscore = p.trustscore + smooth_sigm(p.merch_turn/100000)*merch_turn_w
    #    if p.merch_bal: p.trustscore = p.trustscore + smooth_sigm(p.merch_bal/1000)*merch_bal_w

    if p.trustscore < 0.001: p.trustscore = 0.001


def Step_ITSU_A2_Preprocessing(p):
    Step_ITSU_A1_Preprocessing(p)

    if p.was_fraud:
        if p.term < 10:
            p.was_fraud = 2
        elif p.term < 20:
            p.was_fraud = 1
        else:
            p.was_fraud = 0


def f_id_type(id_type, l, param):
#id_type	1hot(4)
    result = np.zeros((l, param))
    col = 0
    if id_type == 'Passport': col = 1
    elif id_type == 'National_ID': col = 2
    elif id_type == 'False_documentation': col = 3
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

def f_family_status(status, l, param):
    result = np.zeros((l, param))
    if status == "Married or in permanent relation": result[0, 0] = 1
    return result

def f_children(children, l, param):
#children up-to-1hot(3)
    result = np.zeros((l, param))
    if not children: return result
    if children == 'None': result[0, 0] =  1
    if children == 'Raising children':  result[0, 1] = 1
    if children == 'Have grandchildren': result[0, 1:3] = 1
    return result
    
def f_education(education, l, param):
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

def f_investor(investor, l, param):
#investor up-to-1hot(4)
    result = np.zeros((l, param))
    if investor:
        if investor <= 0: result[0, 0] = 1
        if investor > 0: result[0, 1] = 1
        if investor >= 100: result[0, 2] = 1
        if investor >= 1000: result[0, 3] = 1
    else: result[0, 0] = 1
    return result

def f_income(income, l, param):
#income up-to-1hot(5)
    result = np.zeros((l, param))
    if income:
        if income < 1000: result[0, 0] = 1
        if income >= 1000: result[0, 1] = 1
        if income >= 3000: result[0, 2] = 1
        if income >= 7000: result[0, 3] = 1
        if income >= 20000: result[0, 4] = 1
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

spec_fields = ['id_type', 'age', 'family_status', 'children', 'education', 'investor', 'income', 'was_fraud',
               'location_country', 'zip_code', 'occupation', 'bank_reference', 'bank_account']
spec_fields_functions = [f_id_type, f_age, f_family_status, f_children, f_education, f_investor, f_income, f_was_fraud,
                         f_simple_exists, f_simple_exists, f_simple_exists, f_simple_exists, f_simple_exists]
spec_fields_params = [4, 4, 1, 3, 6, 4, 5, 3, 1, 1, 1, 1, 1]
ML_name = 'rf'

def Step_ITSU_A2_Basketing(p):
    p.bias = 0

    if not p.id_type:
        p.tsgroup = 0
        return
    elif p.id_type == 'Not_provided':
        p.tsgroup = 0
        return
    elif p.id_type == 'False_documentation':
        p.tsgroup = 0
        return

    if p.age:
        if p.age < 16:
            p.tsgroup = 0
            return

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
        attr = getattr(p, header, '')
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

# load the model and predict the group
    rf2 = joblib.load(ML_name + '.clf')
    grp = rf2.predict(features)
    p.tsgroup = grp[0] + 1  # correction because the basket number is diminished by 1 on the counting step

# the correction according to the group mean value
    p.bias = - (15.76206 - p.tsgroup ** 1.32602)

#    print(grp)
#    print(p.bias)

#    flash(features.shape)
#    flash(features)
#    flash(grp)
#    flash(p.bias)

def Step_ITSU_A2_Counting(p):
    Step_ITSU_A1_Counting(p)

def countries(c):
    if not c:
        return -3
    if not c in Bad_and_Good_Locations.__members__ : return -3
#    if c in ('Singapore', 'United_States_of_America', 'Estonia', 'Australia', 'France', 'Canada', 
#             'Japan', 'Norway', 'United_Kingdom', 'Republic_of_Korea', 'Netherlands', 'Finland', 'Sweden', 
#             'Switzerland', 'New_Zealand', 'Israel', 'Latvia', 'Germany', 'Ireland', 'Belgium', 'Austria', 
#             'Italy', 'Poland', 'Denmark', 'Czech_Republic', 'Luxembourg', 'Croatia', 'Romania', 'Bulgaria', 
#             'Hungary', 'Spain', 'The_Former_Yugoslav_Republic_of_Macedonia', 'Portugal', 'Lithuania', 'Cyprus', 
#             'Greece', 'Montenegro', 'Malta', 'Iceland', 'Slovakia', 'Slovenia', 'Monaco', 'Liechtenstein', 
#             'Andorra', 'Vatican'):
#        return 3
#    if c in ('Russian_Federation', 'India', 'Uruguay', 'China', 'Philippines', 'Brazil', 'Belarus', 'Turkey', 
#             'Argentina', 'Ecuador', 'Sri_Lanka', 'Peru', 'Chile', 'Kazakhstan', 'Jamaica', 'Costa_Rica', 'Paraguay', 
#             'Serbia', 'Nepal', 'Barbados', 'Armenia', 'Guatemala', 'Kuwait', 'Trinidad_and_Tobago', 'Mauritius',
#             'Georgia', 'South_Africa', 'Hong_Kong', 'Taiwan'):
#        return 1
#    if c in ('Malaysia', 'Oman', 'Egypt', 'Thailand', 'Qatar', 'Mexico', 'Tunisia', 'Kenya', 'Colombia',
#             'Saudi_Arabia', 'United_Arab_Emirates', 'Azerbaijan', 'Morocco', 'Brunei_Darussalam', 'Bangladesh',
#             'Ukraine', 'Panama', 'Bahrain', 'Pakistan', 'Algeria', 'Botswana', 'Indonesia', 'Moldova', 'Cote_dIvoire',
#             'Cameroon', 'Venezuela', 'Ghana', 'Tanzania', 'Senegal'):
#        return 0
#    if c in ('Nigeria', 'Cuba', 'Albania', 'Zambia', 'Tajikistan', 'Tonga', 'Cambodia', 'Uzbekistan', 'Jordan',
#             'Kyrgyzstan', 'Ethiopia', 'Myanmar', 'Viet_Nam', 'Mongolia', 'Fiji', 'Togo', 'Burkina_Faso',
#             'El_Salvador', 'Mozambique', 'Bhutan', 'Saint_Vincent_and_the_Grenadines', 'Seychelles', 'Belize',
#             'Antigua_and_Barbuda', 'San_Marino', 'Lebanon', 'Madagascar', 'Dominican_Republic', 'Suriname', 'Liberia',
#             'Mauritania', 'Nicaragua', 'Sierra_Leone', 'Nauru', 'Gabon', 'Bahamas', 'Gambia', 'Turkmenistan',
#             'Kiribati', 'Bolivia', 'Burundi', 'Grenada', 'Djibouti', 'Solomon_Islands', 'Lesotho', 'Guinea', 'Malawi',
#             'Angola', 'Chad', 'Benin', 'Papua_New_Guinea', 'Saint_Kitts_and_Nevis', 'Namibia', 'Mali', 'Cape_Verde',
#             'Maldives', 'Saint_Lucia', 'Palau', 'Honduras', 'Samoa', 'Marshall_Islands', 'Micronesia', 'Swaziland',
#             'Sao_Tome_and_Principe', 'Comoros', 'Guinea_Bissau', 'Timor_Leste', 'Tuvalu', 'Dominica',
#             'Central_African_Republic', 'Equatorial_Guinea'):
#        return -1
#    if c in ('Rwanda', 'Sudan', 'Afghanistan', 
#             'Syrian_Arab_Republic', 'Libya', 'Zimbabwe', 'Niger', 'Eritrea', 'South_Sudan', 
#             'Congo', 'Democratic_Republic_of_the_Congo', 'Haiti', 'Somalia', 'Yemen'):
#        return -3
# EU Directive 2016/1675 of 14 July 2016
    if c in ('Democratic_Peoples_Republic_of_Korea', 'Iran', 'Uganda', 'Afghanistan', 'Syrian_Arab_Republic', 'State_of_Palestine', 'Iraq', 'Yemen', 
             'Bosnia_and_Herzegovina', 'Guyana', 'Lao', 'Vanuatu'):
        return -5
    if c == 'None': c = 'NA'
    return Bad_and_Good_Locations[c].value / 3

def smooth_sigm(x):
    return 1 / (1 + math.exp(-x))


# ISAZI
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

# Based on GCI index : https://www.itu.int/dms_pub/itu-d/opb/str/D-STR-GCI.01-2017-PDF-E.pdf
class Bad_and_Good_Locations(Enum):
    NA = (0 - 0.925/2)*12
    Singapore = (0.925 - 0.925/2)*12
    United_States_of_America = (0.919 - 0.925/2)*12
    Malaysia = (0.893 - 0.925/2)*12
    Oman = (0.871 - 0.925/2)*12
    Estonia = (0.846 - 0.925/2)*12
    Mauritius = (0.830 - 0.925/2)*12
    Australia = (0.824 - 0.925/2)*12
    Georgia = (0.819 - 0.925/2)*12
    France = (0.819 - 0.925/2)*12
    Canada = (0.818 - 0.925/2)*12
    Russian_Federation = (0.788 - 0.925/2)*12
    Japan = (0.786 - 0.925/2)*12
    Norway = (0.786 - 0.925/2)*12
    United_Kingdom = (0.783 - 0.925/2)*12
    Republic_of_Korea = (0.782 - 0.925/2)*12
    Egypt = (0.772 - 0.925/2)*12
    Netherlands = (0.760 - 0.925/2)*12
    Finland = (0.741 - 0.925/2)*12
    Sweden = (0.733 - 0.925/2)*12
    Switzerland = (0.727 - 0.925/2)*12
    New_Zealand = (0.718 - 0.925/2)*12
    Israel = (0.691 - 0.925/2)*12
    Latvia = (0.688 - 0.925/2)*12
    Thailand = (0.684 - 0.925/2)*12
    India = (0.683 - 0.925/2)*12
    Germany = (0.679 - 0.925/2)*12
    Qatar = (0.676 - 0.925/2)*12
    Ireland = (0.675 - 0.925/2)*12
    Belgium = (0.671 - 0.925/2)*12
    Mexico = (0.660 - 0.925/2)*12
    Uruguay = (0.647 - 0.925/2)*12
    Austria = (0.639 - 0.925/2)*12
    Italy = (0.626 - 0.925/2)*12
    China = (0.624 - 0.925/2)*12
    Hong_Kong = (0.624 - 0.925/2)*12    #added
    Taiwan = (0.624 - 0.925/2)*12       #added
    Poland = (0.622 - 0.925/2)*12
    Denmark = (0.617 - 0.925/2)*12
    Czech_Republic = (0.609 - 0.925/2)*12
    Rwanda = (0.602 - 0.925/2)*12
    Luxembourg = (0.602 - 0.925/2)*12
    Philippines = (0.594 - 0.925/2)*12
    Brazil = (0.593 - 0.925/2)*12
    Belarus = (0.592 - 0.925/2)*12
    Tunisia = (0.591 - 0.925/2)*12
    Croatia = (0.590 - 0.925/2)*12
    Romania = (0.585 - 0.925/2)*12
    Turkey = (0.581 - 0.925/2)*12
    Bulgaria = (0.579 - 0.925/2)*12
    Kenya = (0.574 - 0.925/2)*12
    Colombia = (0.569 - 0.925/2)*12
    Saudi_Arabia = (0.569 - 0.925/2)*12
    Nigeria = (0.569 - 0.925/2)*12
    United_Arab_Emirates = (0.566 - 0.925/2)*12
    Azerbaijan = (0.559 - 0.925/2)*12
    Morocco = (0.541 - 0.925/2)*12
    Uganda = (0.536 - 0.925/2)*12
    Hungary = (0.534 - 0.925/2)*12
    Democratic_Peoples_Republic_of_Korea = (0.532 - 0.925/2)*12
    Brunei_Darussalam = (0.524 - 0.925/2)*12
    Bangladesh = (0.524 - 0.925/2)*12
    Spain = (0.519 - 0.925/2)*12
    The_Former_Yugoslav_Republic_of_Macedonia = (0.517 - 0.925/2)*12
    Portugal = (0.508 - 0.925/2)*12
    Lithuania = (0.504 - 0.925/2)*12
    South_Africa = (0.502 - 0.925/2)*12
    Ukraine = (0.501 - 0.925/2)*12
    Iran = (0.494 - 0.925/2)*12
    Cyprus = (0.487 - 0.925/2)*12
    Panama = (0.485 - 0.925/2)*12
    Argentina = (0.482 - 0.925/2)*12
    Greece = (0.475 - 0.925/2)*12
    Bahrain = (0.467 - 0.925/2)*12
    Ecuador = (0.466 - 0.925/2)*12
    Pakistan = (0.447 - 0.925/2)*12
    Algeria = (0.432 - 0.925/2)*12
    Botswana = (0.430 - 0.925/2)*12
    Indonesia = (0.424 - 0.925/2)*12
    Montenegro = (0.422 - 0.925/2)*12
    Sri_Lanka = (0.419 - 0.925/2)*12
    Moldova = (0.418 - 0.925/2)*12
    Cote_dIvoire = (0.416 - 0.925/2)*12
    Cameroon = (0.413 - 0.925/2)*12
    Malta = (0.399 - 0.925/2)*12
    Lao = (0.392 - 0.925/2)*12
    Iceland = (0.384 - 0.925/2)*12
    Peru = (0.374 - 0.925/2)*12
    Venezuela = (0.372 - 0.925/2)*12
    Chile = (0.367 - 0.925/2)*12
    Slovakia = (0.362 - 0.925/2)*12
    Kazakhstan = (0.352 - 0.925/2)*12
    Slovenia = (0.343 - 0.925/2)*12
    Jamaica = (0.339 - 0.925/2)*12
    Costa_Rica = (0.336 - 0.925/2)*12
    Ghana = (0.326 - 0.925/2)*12
    Paraguay = (0.326 - 0.925/2)*12
    Tanzania = (0.317 - 0.925/2)*12
    Senegal = (0.314 - 0.925/2)*12
    Albania = (0.314 - 0.925/2)*12
    Serbia = (0.311 - 0.925/2)*12
    Zambia = (0.292 - 0.925/2)*12
    Tajikistan = (0.292 - 0.925/2)*12
    Tonga = (0.292 - 0.925/2)*12
    Cambodia = (0.283 - 0.925/2)*12
    Uzbekistan = (0.277 - 0.925/2)*12
    Jordan = (0.277 - 0.925/2)*12
    Nepal = (0.275 - 0.925/2)*12
    Barbados = (0.273 - 0.925/2)*12
    Sudan = (0.271 - 0.925/2)*12
    Kyrgyzstan = (0.270 - 0.925/2)*12
    Guyana = (0.269 - 0.925/2)*12
    Ethiopia = (0.267 - 0.925/2)*12
    Myanmar = (0.263 - 0.925/2)*12
    Viet_Nam = (0.245 - 0.925/2)*12
    Afghanistan = (0.245 - 0.925/2)*12
    Syrian_Arab_Republic = (0.237 - 0.925/2)*12
    Monaco = (0.236 - 0.925/2)*12
    Mongolia = (0.228 - 0.925/2)*12
    State_of_Palestine = (0.228 - 0.925/2)*12
    Libya = (0.224 - 0.925/2)*12
    Fiji = (0.222 - 0.925/2)*12
    Togo = (0.218 - 0.925/2)*12
    Burkina_Faso = (0.208 - 0.925/2)*12
    El_Salvador = (0.208 - 0.925/2)*12
    Mozambique = (0.206 - 0.925/2)*12
    Bhutan = (0.199 - 0.925/2)*12
    Armenia = (0.196 - 0.925/2)*12
    Liechtenstein = (0.194 - 0.925/2)*12
    Zimbabwe = (0.192 - 0.925/2)*12
    Saint_Vincent_and_the_Grenadines = (0.189 - 0.925/2)*12
    Seychelles = (0.184 - 0.925/2)*12
    Belize = (0.182 - 0.925/2)*12
    Antigua_and_Barbuda = (0.179 - 0.925/2)*12
    San_Marino = (0.174 - 0.925/2)*12
    Lebanon = (0.172 - 0.925/2)*12
    Niger = (0.170 - 0.925/2)*12
    Madagascar = (0.168 - 0.925/2)*12
    Dominican_Republic = (0.162 - 0.925/2)*12
    Suriname = (0.155 - 0.925/2)*12
    Liberia = (0.149 - 0.925/2)*12
    Mauritania = (0.146 - 0.925/2)*12
    Nicaragua = (0.146 - 0.925/2)*12
    Sierra_Leone = (0.145 - 0.925/2)*12
    Nauru = (0.140 - 0.925/2)*12
    Gabon = (0.139 - 0.925/2)*12
    Bahamas = (0.137 - 0.925/2)*12
    Gambia = (0.136 - 0.925/2)*12
    Vanuatu = (0.134 - 0.925/2)*12
    Turkmenistan = (0.133 - 0.925/2)*12
    Kiribati = (0.123 - 0.925/2)*12
    Bolivia = (0.122 - 0.925/2)*12
    Burundi = (0.120 - 0.925/2)*12
    Bosnia_and_Herzegovina = (0.116 - 0.925/2)*12
    Grenada = (0.115 - 0.925/2)*12
    Guatemala = (0.114 - 0.925/2)*12
    Kuwait = (0.104 - 0.925/2)*12
    Djibouti = (0.099 - 0.925/2)*12
    Trinidad_and_Tobago = (0.098 - 0.925/2)*12
    Solomon_Islands = (0.095 - 0.925/2)*12
    Lesotho = (0.094 - 0.925/2)*12
    Guinea = (0.090 - 0.925/2)*12
    Malawi = (0.084 - 0.925/2)*12
    Angola = (0.078 - 0.925/2)*12
    Eritrea = (0.076 - 0.925/2)*12
    Chad = (0.072 - 0.925/2)*12
    Benin = (0.069 - 0.925/2)*12
    South_Sudan = (0.067 - 0.925/2)*12
    Papua_New_Guinea = (0.067 - 0.925/2)*12
    Saint_Kitts_and_Nevis = (0.066 - 0.925/2)*12
    Namibia = (0.066 - 0.925/2)*12
    Mali = (0.060 - 0.925/2)*12
    Cape_Verde = (0.058 - 0.925/2)*12
    Cuba = (0.058 - 0.925/2)*12
    Andorra = (0.057 - 0.925/2)*12
    Maldives = (0.056 - 0.925/2)*12
    Saint_Lucia = (0.053 - 0.925/2)*12
    Palau = (0.053 - 0.925/2)*12
    Honduras = (0.048 - 0.925/2)*12
    Samoa = (0.048 - 0.925/2)*12
    Marshall_Islands = (0.048 - 0.925/2)*12
    Micronesia = (0.044 - 0.925/2)*12
    Iraq = (0.043 - 0.925/2)*12
    Swaziland = (0.041 - 0.925/2)*12
    Congo = (0.040 - 0.925/2)*12
    Democratic_Republic_of_the_Congo = (0.040 - 0.925/2)*12
    Haiti = (0.040 - 0.925/2)*12
    Sao_Tome_and_Principe = (0.040 - 0.925/2)*12
    Vatican = (0.040 - 0.925/2)*12
    Comoros = (0.040 - 0.925/2)*12
    Guinea_Bissau = (0.034 - 0.925/2)*12
    Somalia = (0.034 - 0.925/2)*12
    Timor_Leste = (0.034 - 0.925/2)*12
    Tuvalu = (0.034 - 0.925/2)*12
    Dominica = (0.010 - 0.925/2)*12
    Central_African_Republic = (0.007 - 0.925/2)*12
    Yemen = (0.007 - 0.925/2)*12
    Equatorial_Guinea = (0.000 - 0.925/2)*12
    Other = (0 - 0.925/2)*12

def Step_ITSU_I1_Preprocessing(p):

    user_details = {}
    user_details["Identification"] = Identification[p.id_type]
    user_details["Bank account"] = 1 if p.bank_account else 0
    user_details["Bank reference"] = 1 if p.bank_reference else 0

    if p.family_status == "Single": user_details["Family status"] = Family_Status.Single
    elif p.family_status == "Married or in permanent relation": user_details["Family status"] = Family_Status.Married_permament_relation
    
    if p.children == "Raising children": user_details["Family status"] = Family_Status.Raising_children
    elif p.children == "Have grandchildren": user_details["Family status"] = Family_Status.Have_grandchildren

    user_details["Merchant"] = 1 if p.be_merchant else 0
    user_details["Income source declared"] = 1 if p.income_source_declared else 0
    user_details["Stable income"] = 1 if p.stable_income else 0

    is_investing = 1 if p.investor else 0
    user_details["Investor"] = is_investing
    user_details["Stake"] = 0 if not is_investing else float(p.investor.replace(',',''))
    user_details["Education"] = Highest_education[p.education]
    if p.location_country == 'None': p.location_country = 'NA'
    user_details["Location"] = Bad_and_Good_Locations[p.location_country]
    user_details["No frauds"] = 0 if p.was_fraud else 1
    user_details["Last fraud time"] = safe_strip_time(p.last_fraud)
    user_details["Business age"] = safe_strip_time(p.incorporation_date)
    user_details["Insurance"] = 1 if p.insurance_available else 0
    user_details["Age"] = safe_strip_time(p.date_of_birth)
    user_details["Proof of residence"] = 1 if p.por_available else 0
    user_details["Credit card holder"] = 1 if p.cards_available else 0
    
    user_details["Credit score"] = int(p.credit_score.replace(',','')) if p.credit_score else 300
    user_details["Has license"] = 1 if p.driver_lic else 0
    user_details["No digital footprint"] = 0 if p.social_network or p.site_owner else 1
    user_details["Phone"] = 1 if p.confirm_phone else 0
    user_details["ZIP code"] = 1 if p.zip_code else 0
    
    p.user_details = user_details

def Step_ITSU_I1_Counting(p):

#code from  get_ts(query: dict, remember_me: bool)
    ts = 0
    i = 0
    for x, s in trans_to_pnt_scores(p.user_details).items():
        i += 1
        #print(i, ":\t Computing for ", x, " with value: ", s)

        if x != "Fraud multiplier":
            ts += s
        else:
            ts *= s

    ts = ts if ts > 1 else 1
    ts = max(0, min(100, ts))

    p.trustscore = ts


#  General credit scoring ranges are all the same, and
#  generally 550  or less is very bad and 750 or more is excellent
#  generall the range of scores is 300 - 850
#  Again y = mx + c so (y0 - y1) / (x0 - x1) = m
#  m = (5 - (-5))/(750 - 550)
#  c = y - mx = -5 - m*550
def credit_score_points(credit_score):
    grad = (5 + 5) / (750 - 550)
    intercept = -5 - grad * 550 
    points = grad * credit_score + intercept if 550 <= credit_score <= 750 else -5.0 if credit_score < 550 else 5.0
    return points

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
    output_dict["Location"] = input_dict["Location"].value
    output_dict["Insurance"] = \
        input_dict["Insurance"] * score_weights["Insurance"]
    #
    output_dict["Proof of residence"] = \
        input_dict["Proof of residence"] * score_weights["Proof of residence"]
    if input_dict["Identification"] == Identification.Passport:
        output_dict["Proof of residence"] = 2 * input_dict["Proof of residence"] * \
            score_weights["Proof of residence"]
    output_dict["No digital footprint"] = input_dict["No digital footprint"] * \
        score_weights["No digital footprint"]
    output_dict["Phone"] = input_dict["Phone"] * score_weights["Phone"]
    output_dict["No frauds"] = input_dict["No frauds"] * \
        score_weights["No frauds"]
    output_dict["ZIP code"] = input_dict["ZIP code"]*score_weights["ZIP code"]

    if not input_dict["Merchant"]:
        output_dict["Age"] = age_points(input_dict["Age"])
        output_dict["Family status"] = input_dict["Family status"].value
        output_dict["Education"] = input_dict["Education"].value
        output_dict["Credit card holder"] = input_dict["Credit card holder"] * \
            score_weights["Credit card holder"]
        output_dict["Credit score"] = input_dict["Credit card holder"] * \
            credit_score_points(input_dict["Credit score"])
        output_dict["Has license"] = input_dict["Has license"] * \
            input_dict["Insurance"]*score_weights["Has license"]
    else:
        ba = input_dict["Business age"]
        if 1 <= ba < 20:
            output_dict["Business age"] = score_weights["Business age"] * \
                smooth(ba, 10, 10)
        elif ba >= 20:
            output_dict["Business age"] = score_weights["Business age"]
        else:
            output_dict["Business age"] = 0
        # Rescaling fields for a merhant so that they are more highly weighted
        for key in output_dict.keys():
            if key != "Fraud multiplier":
                output_dict[key] *= 100/78

    if input_dict["No frauds"]:
        output_dict["Fraud multiplier"] = 1
    else:
        lst_time = input_dict["Last fraud time"]
        if lst_time > 20:
            output_dict["No frauds"] = score_weights["No frauds"]
            output_dict["Fraud multiplier"] = 1
        else:
            output_dict["Fraud multiplier"] = smooth(lst_time, 10, 10)

    return output_dict
