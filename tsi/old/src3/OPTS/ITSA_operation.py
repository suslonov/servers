import os
import math
import random
import string
import datetime
import dateutil.parser
from . import parameters as parms
from . import RDB_types
# import parameters as parms
# import RDB_types

####################################################################################################
###                                       Quick methods                                          ###
####################################################################################################
def date_to_age(date:str):
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
use_itsa_db = parms.use_db_for_itsa
if use_itsa_db:
    if not os.path.isdir(parms.db_dir):
        os.makedirs(parms.db_dir)
    itsa_value_db = RDB_types.CotiRocksUsrDB(
        parms.itsa_db_name, ordered_string_parms=parms.ordered_itsa_ts_fields, allow_updating=False)
#

def __calc_score(input_dict: dict):
    if use_itsa_db:
        if "user_ID" not in input_dict:
            message = "FAILED: user_ID not found in input. Please choose a user_ID " + str(parms.uid_length) + " characters long. Consisting of ascii characters (lowercase and uppercase) and digits. Nothing added to DB."
            return {"TS":message}
    #############################
    ##  Converting and formatting
    #############################
    format_dict = dict()

    # Converting booleans to their mathematical equivalent
    bool_params = ["Bank_account", "Bank_reference", "Credit_card_holder", "Has_license", "Income_source_declared", "Insurance","Investor", "No_digital_footprint","No_frauds", "Phone", "Proof_of_residence", "ZIP_code" ]
    
    for bool_parm in bool_params:
        if type(input_dict[bool_parm]) == bool:
            format_dict[bool_parm] = int(input_dict[bool_parm])
        elif type(input_dict[bool_parm]) == str:
            format_dict[bool_parm] = 1.0 if input_dict[bool_parm] in bool_T_strings else 0.0
        else:
            message = "FAILED: Value of " + str(input_dict[bool_parm]) + " not recognized. Nothing added to DB."
            return {"TS":message}
    
    # Converting the choice params to their point equivalents
    format_dict["Identification"] = parms.identification[input_dict["Identification"]]
    format_dict["Marital_status"] = parms.family_status[input_dict["Marital_status"]]
    format_dict["Education"] = parms.education[input_dict["Education"]]
    format_dict["Country"] = parms.countries[input_dict["Country"]]

    # Converting to special parameters to their point equivalents
    format_dict["Expected_income"] = parms.employment_status[input_dict["Employment_status"]] * parms.income[input_dict["Income"]]
    format_dict["Date_of_birth"] = age_points(date_to_age(input_dict["Date_of_birth"]))
    format_dict["Has_license"] = format_dict["Has_license"] * format_dict["Insurance"]
    format_dict["Stake"] = format_dict["Investor"] * smooth(float(input_dict["Stake"]), centre=5000, sharpness=2500)
    
    # Proof of residence has double importance if using a passport
    if input_dict["Identification"] == "Passport":
        format_dict["Proof_of_residence"] = 2.0 * format_dict["Proof_of_residence"]

    # Check if fraud penalties must be applied
    apply_fraud_penalty = False
    if type(input_dict["No_frauds"]) == bool:
        apply_fraud_penalty = not input_dict["No_frauds"]
    elif type(input_dict["No_frauds"]) == str:
        apply_fraud_penalty = False if input_dict["No_frauds"] in bool_T_strings else True
    else:
        message = "FAILED: Value of " + str(input_dict[input_dict["No_frauds"]]) + " not recognized. Nothing added to DB."
        return {"TS":message}  

    # Actual computation of TS
    TS = 0.0
    scores = parms.score_weights
    TS += sum([format_dict[contribution]*scores[contribution] for contribution in scores])

    offset = 10
    if apply_fraud_penalty:
        fraud_age = date_to_age(input_dict["Last_fraud_date"])
        if fraud_age < 20:
            penalty_factor = smooth(fraud_age, centre = 10, sharpness = 5) 
            offset *= penalty_factor 
            TS *= penalty_factor

    TS = max(0, min(100, TS))

    if input_dict["Identification"] == "National_ID" or input_dict["Identification"] == "Passport":
        TS = offset + TS/4
    else:
        TS = 0
    return {"TS":TS}
#

def compute_ITSA_pass_TSUA_info(input_dict: dict, peek=False):
    calculated_TS = __calc_score(input_dict)
    TS = None
    try:
        TS = float(calculated_TS["TS"])
    except Exception as e:
        print(e, file = os.sys.stderr)
        return calculated_TS

    time = datetime.datetime.now().isoformat()
    itsa_values = dict()
    TSUA_user_info = {
        "TS":TS,
        "time_joined": time,
        "time_prev_txn": time,
        "time_last_turn_adj": time
    }
    #   Adding optional values
    for key in ["balance", "user_ID"]:
        if key in input_dict:
            TSUA_user_info[key] = input_dict[key]
            itsa_values[key] = input_dict[key]
    #

    for field in parms.ordered_itsa_ts_fields:
        itsa_values[field] = input_dict[field]
    if not peek and use_itsa_db:
        itsa_value_db.update_write_user_parms_to_db(itsa_values)
   
    return TSUA_user_info


####################################################################################################
###                            Deprecated not for COTI ZERO                                      ###
####################################################################################################


# def generate_uid():
#     potential_uid = ""
#     while len(potential_uid) < parms.uid_length:
#         potential_uid += random.choice(string.ascii_letters + string.digits)
#     return potential_uid



# def generate_unused_uid(database):
#     potential_id = generate_uid()
#     tried_uids = set()
#     while True:
#         if potential_id in tried_uids:
#             potential_id = generate_uid()
#             continue
#         elif itsa_value_db.check_if_usr_in_db(potential_id):
#             tried_uids.add(potential_id.copy())
#             potential_id = generate_uid()
#             continue
#         else:
#             break
#     return potential_id



# # Credit score not included in COTI zero
# def credit_score_points(credit_score):
#     #  General credit scoring ranges are all the same, and
#     #  generally 550  or less is very bad and 750 or more is excellent
#     #  generall the range of scores is 300 - 850
#     #  Again y = mx + c so (y0 - y1) / (x0 - x1) = m
#     #  m = (5 - (-5))/(750 - 550)
#     #  c = y - mx = -5 - m*550
#     grad = (5.0 + 5.0) / (750.0 - 550.0)
#     intercept = -5.0 - grad * 550.0
#     points = grad * credit_score + intercept
#     return min(5.0, max(-5.0, points))



# def __calc_score(input_dict: dict):
    
#     scores = parms.score_weights
#     TS = 1.0

#     # Converting booleans to their mathematical equivalent
#     bool_params = ["Bank_account", "Bank_reference", "Income_source_declared", "Proof_of_residence", "Insurance",
#                              "Phone", "No_frauds", "ZIP_code", "Proof_of_residence", "No_digital_footprint"]
    
#     TS += sum([input_dict[x]*scores[x] for x in bool_params])

#     # Multiple choice params
#     multi_parm_dict = parms.identification.copy()
#     multi_parm_dict.update(parms.family_status)
#     multi_parm_dict.update(parms.education)
#     multi_parm_dict.update(parms.countries)
#     choice_params = ["Identification", "Family_status", "Education", "Country"]
#     TS += sum([multi_parm_dict[input_dict[x]]*scores[x] for x in choice_params])

#     # Special parameters
#     expected_income = parms.employment_status[
#         input_dict["Employment_status"]] * parms.income[input_dict["Income"]]
#     TS += expected_income * scores["Expected_income"]
#     TS += age_points(input_dict["Age"]) * scores["Age"]
#     TS += input_dict["Has_license"] * input_dict["Insurance"]*scores["Has_license"]
#     TS += smooth(input_dict["Stake"], centre=5000, sharpness=2500) * input_dict["Investor"] * \
#         scores["Stake"]
#     # Note that credit score has been removed from 0. The points for credit score will have to be redistributed.
#     TS += input_dict["Credit_card_holder"] * scores["Credit_card_holder"]
#     # Proof of residence has double importance if you are using a passport - so add it again
#     TS += input_dict["Proof_of_residence"] * scores["Proof_of_residence"] \
#         if input_dict["Identification"] == "Passport" else 0

#     # Penalties for previous fraudulent behavior
#     if not input_dict["No_frauds"]:
#         if input_dict["Last_fraud_time"] < 20:
#             TS *= smooth(input_dict["Last_fraud_time"], centre=10, sharpness=5)
#     TS = max(0, min(100, TS))

#     # TS can't be less than 1 or more than 100
#     if input_dict["Identification"] == "National_ID" or input_dict["Identification"] == "Passport":   
#         return  10 + TS/4
#     else:
#         return 0
