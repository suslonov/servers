import math
import datetime
import dateutil.parser
from . import parameters as parms
#import parameters as parms

####################################################################################################
###                                       Quick methods                                          ###
####################################################################################################


def date_to_age(date: str):
    dob_datetime = dateutil.parser.parse(str(date))
    current_t = datetime.datetime.now()
    diff = current_t-dob_datetime
    return diff.days/365.25


def age_points(age: float):
    # risk = -0.279*age + 3.047  based on pg 53  of Stability and Change in Risk ....
    # from http://www.diw.de/documents/publikationen/73/diw_01.c.525809.de/diw_sp0816.pdf
    # Zero points if 20 or younger, max points if 75 or older
    if age <= 20:
        return 0
    elif age >= 75:
        return 1.0
    else:
        return 1.0*(age - 20.0)/(75.0 - 20.0)


def smooth(x: float, centre: float, sharpness: float):
    """Smooth the function with a Fermi-Dirac like distribution - the \"Temperature\" parameter is sharpness.
    μ is the central point (=0.5 here)"""
    return 1.0/(1.0 + math.pow(math.e, (centre-x)/sharpness))


####################################################################################################
###                                      Actual operation                                        ###
####################################################################################################
bool_T_strings = ["TRUE", "True", "T", "true", "t"]
bool_F_strings = ["", "NA", "FALSE", "False", "false",
                  "F", "f", "None", "none", "No", "no", "n"]


def compute_ITSA(in_dic: dict):
    #############################
    ##  Converting and formatting
    #############################
    calc_dic = dict()

   # Converting booleans to their mathematical equivalent for simple boolean params
    reg_bool_parms = ["Bank_account", "Credit_card_holder", "Has_license", "Credit_history",
                      "Income_source_declared", "Insurance", "Proof_of_residence", "Investor", "Phone", "Stable_income"]
    unreg_bool_parms = ["Bank_reference",
                        "ZIP_code", "Site", "Social_network_account"]

    for bool_parm in reg_bool_parms + unreg_bool_parms:
        parm_in = in_dic[bool_parm]
        if type(parm_in) == bool:
            calc_dic[bool_parm] = float(parm_in)
        elif type(parm_in) == int or type(parm_in) == float:
            if float(parm_in) == 1.0 or float(parm_in) == 0.0:
                calc_dic[bool_parm] = float(parm_in)
            else:
                message = "FAILED: Value " + str(parm_in) + \
                    " for parameter " + bool_parm + " not recognized."
                return {"TS": message}
        elif type(parm_in) == str:
            # Handling non-regular entries
            if bool_parm in unreg_bool_parms:
                calc_dic[bool_parm] = 0.0 if parm_in in bool_F_strings else 1.0
            else:
                calc_dic[bool_parm] = 1.0 if parm_in in bool_T_strings else 0.0

        else:
            message = "FAILED: Value " + str(parm_in) + \
                " for parameter " + bool_parm + " not recognized."
            return {"TS": message}

    # Converting the choice params to their point equivalents
    choices_parms = ["Identification", "Children", "Marital_status", "Education", "Citizenship", "Country",
                     "Employment_status", "Income"]
    for choice_parm in choices_parms:
        calc_dic[choice_parm] = parms.choices_dict[choice_parm][in_dic[choice_parm]]

    # Converting to special parameters to their point equivalents
    calc_dic["Expected_income"] = calc_dic["Employment_status"] * \
        calc_dic["Income"]
    calc_dic["Expected_income"] *= 1.0 if calc_dic["Stable_income"] else 0.5
    # parms.employment_status[in_dic["Employment_status"]
    #                                                       ] * parms.income[in_dic["Income"]]

    calc_dic["No_digital_footprint"] = \
        (1.0 - calc_dic["Site"]) * (1.0 - calc_dic["Social_network_account"])
    calc_dic["Date_of_birth"] = age_points(
        date_to_age(in_dic["Date_of_birth"]))
    calc_dic["Has_license"] = calc_dic["Has_license"] * calc_dic["Insurance"]
    calc_dic["Stake"] = calc_dic["Investor"] * \
        smooth(float(in_dic["Stake"]), 5000, 2500)
    # Proof of residence has double importance if using a passport
    calc_dic["Proof_of_residence"] *= 2.0 if in_dic["Identification"] == "Passport" else 1.0

    # Note that no fraud penalties are applied for COTI-ZERO
    # Actual computation of TS
    TS = 0.0
    scores = parms.score_weights
    # For testing purposes only
    for key in scores:
        contribution = calc_dic[key] * scores[key]
        print("Adding contribution: " + str(contribution) + " for " + str(key))
        TS += contribution

    # TS += sum([calc_dic[contribution]*scores[contribution] for contribution in scores])

    offset = 10
    if in_dic["Identification"] == "National_ID" or in_dic["Identification"] == "Passport":
        TS = offset + TS/4
    else:
        TS = 0
    return {"TS": TS}

#####################################################
# Checks
#####################################################

# import random
# import matplotlib.pyplot as plt

# def create_random_input():
#     count = random.choice(list(parms.countries.keys()))
#     out_dict = {
#         "Bank_account": random.choice([True, False]),
#         "Bank_reference": random.choice(["Yes", "No"]),
#         "Children": random.choice(list(parms.children.keys())),
#         "Citizenship": count,
#         "Country": count,
#         "Credit_card_holder": random.choice([True, False]),
#         "Credit_history": random.choice([True, False]),
#         "Date_of_birth": str(random.randint(1900, 2015)),
#         "Education": random.choice(list(parms.education.keys())),
#         "Employment_status": random.choice(list(parms.employment_status.keys())),
#         "Has_license": random.choice([True, False]),
#         "Identification": random.choice(["National_ID", "Passport"]), #random.choice(list(parms.identification.keys())),
#         "Income": random.choice(list(parms.income.keys())),
#         "Income_source_declared": random.choice([True, False]),
#         "Insurance": random.choice([True, False]),
#         "Investor": random.choice([True, False]),
#         "Marital_status": random.choice(list(parms.marital_status.keys())),
#         "Occupation": "",
#         "Phone": random.choice([True, False]),
#         "Proof_of_residence": random.choice([True, False]),
#         "Site": random.choice(["Yes", "No"]),
#         "Social_network_account": random.choice(["Yes", "No"]),
#         "Stable_income": random.choice([True, False]),
#         "Stake": 10000*random.random(),
#         "ZIP_code": random.choice(["Yes", "No"])
#     }
#     return out_dict

# ts_array = list()
# for i in range(1000):
#     ts_array.append(compute_ITSA(create_random_input())["TS"])

# plt.hist(ts_array, bins = 100)
# plt.show()

# default_best = {
#     "Bank_account": True,  # boolean
#     "Bank_reference": "Mr. Smith",  # string
#     "Children": "Have_grandchildren",  # string
#     "Citizenship": "SGP",  # string
#     "Country": "SGP",  # string
#     "Credit_card_holder": True,  # boolean
#     "Credit_history": True,  # boolean (new)
#     "Date_of_birth": '1910-06-29T12:02:30.168326',  # date
#     "Education": "PhD_Doctorate",  # string
#     "Employment_status": "Employed",  # string
#     "Has_license": True,  # boolean
#     "Identification": "National_ID",  # string
#     "Income": "$32000+",  # string
#     "Income_source_declared": True,  # boolean
#     "Insurance": True,  # boolean
#     "Investor": True,  # boolean
#     "Marital_status": "Married",  # string
#     "Occupation": "Clown",  # string (new)
#     "Phone": True,  # boolean
#     "Proof_of_residence": True,  # boolean
#     "Site": "coolbeans.com",  # string   (new)
#     "Social_network_account": "theres.something.about.Mary",  # string
#     "Stable_income": True,  # boolean (new)
#     "Stake": 10000000000,  # decimal
#     "ZIP_code": "1458"  # string
# }


# default_worst = {
#     "Bank_account": False,  # boolean
#     "Bank_reference": "None",  # string
#     "Children": "None",  # string
#     "Citizenship": "NA",  # string
#     "Country": "NA",  # string
#     "Credit_card_holder": False,  # boolean
#     "Credit_history": False,  # boolean (new)
#     "Date_of_birth": '2018-06-29T12:02:30.168326',  # date
#     "Education": "Not_educated",  # string
#     "Employment_status": "None",  # string
#     "Has_license": False,  # boolean
#     "Identification": "Not_provided",  # string
#     "Income": "None",  # string
#     "Income_source_declared": False,  # boolean
#     "Insurance": False,  # boolean
#     "Investor": False,  # boolean
#     "Marital_status": "Single",  # string
#     "Occupation": "Clown",  # string (new)
#     "Phone": False,  # boolean
#     "Proof_of_residence": False,  # boolean
#     "Site": "NA",  # string   (new)
#     "Social_network_account": "NA",  # string
#     "Stable_income": False,  # boolean (new)
#     "Stake": 0,  # decimal
#     "ZIP_code": "None"  # string
# }
