import os
import math
import random
import string
import datetime
from . import parameters as parms
from . import RDB_types
# import parameters as parms
# import RDB_types

####################################################################################################
###                                       Quick methods                                          ###
####################################################################################################


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


def generate_uid():
    potential_uid = ""
    while len(potential_uid) < parms.uid_length:
        potential_uid += random.choice(string.ascii_letters + string.digits)
    return potential_uid


def generate_unused_uid(database):
    potential_id = generate_uid()
    tried_uids = set()
    while True:
        if potential_id in tried_uids:
            potential_id = generate_uid()
            continue
        elif aml_kyc_db.check_if_usr_in_db(potential_id):
            tried_uids.add(potential_id.copy())
            potential_id = generate_uid()
            continue
        else:
            break
    return potential_id


def rescale(ts):
    return ts/4 + 10
####################################################################################################
###                                      Actual operation                                        ###
####################################################################################################


if not os.path.isdir(parms.db_dir):
    os.makedirs(parms.db_dir)
aml_kyc_db = RDB_types.CotiRocksUsrDB(
    parms.kyc_db_name, ordered_string_parms=parms.ordered_itsa_ts_fields, allow_updating=False)
#
#


def __calc_score(input_dict: dict):
    in_dict = input_dict
    scores = parms.score_weights
    TS = 1.0

    # Simple params
    simple_boolean_params = ["Bank_account", "Bank_reference", "Income_source_declared", "Proof_of_residence", "Insurance",
                             "Phone", "No_frauds", "ZIP_code", "Proof_of_residence", "No_digital_footprint"]
    if input_dict["ZIP_code"]: input_dict["ZIP_code"] = 1
    if input_dict["Bank_account"]: input_dict["Bank_account"] = 1
    if input_dict["Bank_reference"]: input_dict["Bank_reference"] = 1
    TS += sum([in_dict[x]*scores[x] for x in simple_boolean_params])

    # Multiple choice params
    multi_parm_dict = parms.identification.copy()
    multi_parm_dict.update(parms.family_status)
    multi_parm_dict.update(parms.education)
    multi_parm_dict.update(parms.countries)
    choice_params = ["Identification", "Family_status", "Education", "Country"]
    TS += sum([multi_parm_dict[in_dict[x]]*scores[x] for x in choice_params])

    # Special parameters
    expected_income = parms.employment_status[
        in_dict["Employment_status"]] * parms.income[in_dict["Income"]]
    TS += expected_income * scores["Expected_income"]
    TS += age_points(in_dict["Age"]) * scores["Age"]
    TS += in_dict["Has_license"] * in_dict["Insurance"]*scores["Has_license"]
    TS += smooth(in_dict["Stake"], centre=5000, sharpness=2500) * in_dict["Investor"] * \
        scores["Stake"]
    # Note that credit score has been removed from 0. The points for credit score will have to be redistributed.
    TS += in_dict["Credit_card_holder"] * scores["Credit_card_holder"]
    # Proof of residence has double importance if you are using a passport - so add it again
    TS += in_dict["Proof_of_residence"] * scores["Proof_of_residence"] \
        if in_dict["Identification"] == "Passport" else 0

    # Penalties for previous fraudulent behavior
    if not in_dict["No_frauds"]:
        if in_dict["Last_fraud_time"] < 20:
            TS *= smooth(in_dict["Last_fraud_time"], centre=10, sharpness=5)

    # TS can't be less than 1 or more than 100 - it is rescaled to be between 0 and 35, though, so don't worry about it now
    TS = max(0, min(100, TS))
    return rescale(TS)
#
#


def on_board(input_dict: dict, peek=False):
    TS = __calc_score(input_dict)
    user_id = generate_unused_uid(aml_kyc_db)
    time = datetime.datetime.now().isoformat()

    TSUA_user_info = {
        "user_ID": user_id,
        "TS": TS,
        "balance": input_dict["balance"],
        #"centrality": 0.01,    # No centrality for COTI-ZERO
        "time_joined": time,
        "time_prev_txn": time,
        "time_last_turn_adj": time
    }

    kyc_data = dict()
    kyc_data["user_ID"] = user_id
    for field in parms.ordered_itsa_ts_fields:
        kyc_data[field] = input_dict[field]
    message = ""
    if not peek:
        aml_kyc_db.update_write_user_parms_to_db(kyc_data)
        message = "Successfully added user " + user_id + \
            " to the cold-storage kyc DB. Initial TS calculated as " + str(TS)
    else:
        message = "Initial TS calculated as " + str(TS)
    return message, TSUA_user_info


####################################################################################################
###                            Deprecated not for COTI ZERO                                      ###
####################################################################################################

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
