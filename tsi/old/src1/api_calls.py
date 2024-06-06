import random
import time
import pandas as pd

# from TSUA import calc_TSUA as tsu

time_limit = 60

users = pd.read_csv("user_init_db.csv")[["userID", "TS"]]
users_TS = dict(list(zip(users["userID"], users["TS"])))

# TODO each user can only give out one token at a time
# create blank stores for users
users_tokens = dict(zip(list(users["userID"]), [""]*len(users)))


def TS_token(uid):
    if uid in users_TS:
        token = {"uid":uid, "code":random.randint(0, 1000000000), "time_issued":time.time()}
        users_tokens[uid] = token
        return token
    else:
        return "User does not exist"

def TS_from_token(token):
    if token["uid"] in users_TS:
        if users_tokens[token["uid"]] != "":
            if token["code"] == users_tokens[token["uid"]]["code"]:
                # time limit should come from our internal storage
                if time.time() - users_tokens[token["uid"]]["time_issued"] < time_limit:
                    return users_TS[token["uid"]]
                else:
                    return "Token has expired"
            else:
                return "Token code invalid"
        else:
            return "Token does not exist"
    else:
        return "User does not exist"

# def TS_update(transaction):
#     tsu.compute_user_TS_txn()
