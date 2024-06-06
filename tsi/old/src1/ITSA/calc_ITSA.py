import os
import math
import random
import json
import pandas as pd

from . import available_parameters as params

#  General credit scoring ranges are all the same, and
#  generally 550  or less is very bad and 750 or more is excellent
#  generall the range of scores is 300 - 850
#  Again y = mx + c so (y0 - y1) / (x0 - x1) = m
#  m = (5 - (-5))/(750 - 550)
#  c = y - mx = -5 - m*550


def credit_score_points(credit_score):
    grad = (5.0 + 5.0) / (750.0 - 550.0)
    intercept = -5.0 - grad * 550.0
    points = grad * credit_score + intercept
    return min(5.0, max(-5.0, points))

# risk = -0.279*age + 3.047  based on pg 53  of Stability and Change in Risk ....
# i.e. it seems (from what the psychologists are saying) that -risk ~ age. Thus Trust Points ~ age
# from http://www.diw.de/documents/publikationen/73/diw_01.c.525809.de/diw_sp0816.pdf
# Zero points if 20 or younger, max points if 75 or older


def age_points(age: float):
    points = 5.0*(age - 20.0)/(75.0-20.0) if 20.0 <= age <= 75.0 else 5.0 if 75.0 < age else 0.0
    return points


def smooth(x: float, mu: float, a: float):
    """Smooth the function with a Fermi-Dirac like distribution - the \"Temperature\" parameter is a.
    μ is the central point (=0.5 here)"""
    return 1.0/(1.0 + math.pow(math.e, (mu-x)/a))


def rescale(ts):
    return 4*ts + 10


def calc_score(input_dict: dict):
    TS = 1.0

    TS += params.identification[input_dict["Identification"]]
    if input_dict["Identification"] == "Passport":
        TS += 2*input_dict["Proof_of_residence"] * \
            params.score_weights["Proof_of_residence"]
    else:
        TS += input_dict["Proof_of_residence"] * \
            params.score_weights["Proof_of_residence"]

    TS += input_dict["Investor"] * \
        smooth(input_dict["Stake"], 0, 10000)*params.score_weights["Stake"]

    TS += params.employment_status[input_dict["Employment_status"]] * \
        params.income[input_dict["Income"]]*params.score_weights["Employment_status"]

    proportional_parameters = ["Bank_account", "Bank_reference", "Income_source_declared",
                               "Insurance", "Phone", "No_frauds", "ZIP_code", "Proof_of_residence", "No_digital_footprint"]
    if input_dict["ZIP_code"]: input_dict["ZIP_code"] = 1
    if input_dict["Bank_account"]: input_dict["Bank_account"] = 1
    if input_dict["Bank_reference"]: input_dict["Bank_reference"] = 1
    
    TS += sum([input_dict[x]*params.score_weights[x]
               for x in proportional_parameters])

    # No merchant for COTI Zero
    # if input_dict["Merchant"]:
    #     if 1 <= input_dict["Business_age"] < 20:
    #         TS += params.score_weights["Business_age"] * \
    #             smooth(input_dict["Business_age"], 10, 10)
    #     elif input_dict["Business_age"] >= 20:
    #         TS += params.score_weights["Business_age"]
    #     else:
    #         TS += 0
    #     # Rescaling fields for a merhant so that they are more highly weighted
    #     TS *= 100.0/78.0
    # else:
    TS += age_points(input_dict["Age"])
    TS += params.family_status[input_dict["Family_status"]]
    TS += params.education[input_dict["Education"]]
    TS += input_dict["Credit_card_holder"] * \
        params.score_weights["Credit_card_holder"]
    TS += input_dict["Credit_card_holder"] * \
        credit_score_points(input_dict["Credit_score"])
    TS += input_dict["Has_license"] * \
        input_dict["Insurance"]*params.score_weights["Has_license"]

    if not input_dict["No_frauds"]:
        if input_dict["Last_fraud_time"] < 20:
            TS *= smooth(input_dict["Last_fraud_time"], 10, 10)

    # TS can't be less than 1 or more than 100
    TS = max(1, min(100, TS))
    return rescale(TS)


def get_line(newID, query, TS):
    # append new line
    new_line = [newID] + [query[x] for x in params.ts_fields] + [TS]
    return pd.DataFrame([new_line], columns=["userID"]+params.ts_fields+["TS"])


def get_ts(query: dict, save_result: bool):
    TS = calc_score(query)
    if save_result:
        # Creating a db of users if one doesn't already exist
        if os.path.exists("./user_init_db.csv"):
            users = pd.read_csv("user_init_db.csv")
            newID = len(users)
        else:
            users = pd.DataFrame(columns=["userID"]+params.ts_fields+["TS"])
            newID = 1
        line = get_line(newID, query, TS)
        user = users.append(line)
        user.to_csv("user_init_db.csv", sep=",", index=False)
    return TS

