import os
import math
import rocksdb
import datetime
from . import parameters as parms
from . import coti_rdb_types
# import parameters as parms
# import coti_rdb_types

############################################################
######              Quick methods                        ###
############################################################


def iso_to_datetime(isostring: str):
    return datetime.datetime.strptime(isostring, parms.py_datetime_isoformat)


def __sigmoid_points(coti_spent,
                     sharpness=1,
                     turnover_devoted_points=parms.ts_node["turnover_devoted_points"],
                     expected_ave_turnover=parms.ts_node["expected_turnover_over_timespan"]):
    denominator = 1 + math.exp(-sharpness*(coti_spent - expected_ave_turnover))
    value = turnover_devoted_points * (-1 + 2 / denominator)
    return value


################################################################
##                      Actual operation                      ##
################################################################
if not os.path.isdir(parms.db_dir):
    os.makedirs(parms.db_dir)
user_db = coti_rdb_types.CotiRocksUsrDB(parms.user_db_name)
send_db = coti_rdb_types.CotiRocksTxnDB(
    parms.send_db_name, db_id_by="sender_ID")
rec_db = coti_rdb_types.CotiRocksTxnDB(
    parms.rec_db_name, db_id_by="receiver_ID")


def insert_new_user_in_db(user_info: dict):
    try:
        if "user_ID" not in user_info:
            raise Exception("Incorrect user info submitted -"
                            "at the very minimum a ", parms.uid_length,
                            " character uid,  is needed, but ",
                            user_info, " was entered")
        elif len(user_info["user_ID"]) != parms.uid_length:
            raise Exception("Incorrect user info submitted -"
                            "at the very minimum a ", parms.uid_length,
                            " character uid,  is needed, but ",
                            user_info["user_ID"], " was entered")
        else:
            for key in user_info:
                if key not in parms.default_user:
                    raise Exception("Unrecognized key", key)
        user_db.update_write_user_parms_to_db(user_info)
        message = "User " + \
            str(user_info["user_ID"]) + " successfully added to db."
        return (message)
    except Exception as e:
        print(e, file=os.sys.stderr)
        return ("Failed to add user ", user_info["user_ID"], " to db.")


def new_txn_update_all(transaction: dict, peek=False, mark_overspending_as="major"):
    #
    try:
        sender_parms = user_db.read_usr_parms_from_db(transaction["sender_ID"])
        transaction["sender_trust"] = sender_parms["TS"]
    except Exception as e:
        print("Sender ", e, " not in DB. Aborting.")
        return ("Sender ", e, " not in DB. Aborting.")
    try:
        user_db.read_usr_parms_from_db(transaction["receiver_ID"])
    except Exception as e:
        print("Receiver ", e, " not in DB. Aborting.")
        return ("Receiver ", e, " not in DB. Aborting.")

    new_TS = __compute_update_sender_by_txn(
        transaction, peek=peek, mark_overspending_as=mark_overspending_as)
    #
    __update_receiver_txn_db(transaction)
    print("Apparrent success - sender ",
          transaction["sender_ID"], " TS updated to ", new_TS)
    return new_TS


def __update_receiver_txn_db(transaction: dict):
    if transaction["wrong_doing"] != "major":
        receiver_parms = user_db.read_usr_parms_from_db(
            str(transaction["receiver_ID"]))
        balance = float(receiver_parms["balance"])
        balance += float(transaction["amount"])
        receiver_parms["balance"] = str(balance)
        receiver_parms["user_ID"] = str(transaction["receiver_ID"])
        user_db.update_write_user_parms_to_db(receiver_parms)
    else:
        transaction["amount"] = 0

    send_db.add_txn_to_db(transaction)
    rec_db.add_txn_to_db(transaction)


def __compute_update_sender_by_txn(transaction: dict, peek=False, mark_overspending_as="major"):
    """ Computes the TS of the user now, using the α, β, TS, last_maj_wrong (# txns since last),
    last_maj_wrong (# txns since last), values for each user stored in user_parameters."""

    sender_parms = user_db.read_usr_parms_from_db(
        str(transaction["sender_ID"]))
    #
    alpha = float(sender_parms["alpha"])
    beta = float(sender_parms["beta"])
    TS = float(sender_parms["TS"])
    balance = float(sender_parms["balance"])
    lst_maj_bad = int(sender_parms["txns_last_maj_wrong"])
    lst_min_bad = int(sender_parms["txns_last_min_wrong"])
    #
    # Checking for overspending, and marking accordingly
    if float(transaction["amount"] > balance):
        message = "ERROR - an attempt at ovespending was detected, marking accordingly as " + \
            mark_overspending_as
        print(message, file=os.sys.stderr)
        transaction["wrong_doing"] = mark_overspending_as
    #
    if transaction["wrong_doing"] == "major":
        lst_maj_bad = 0
        alpha *= float(parms.ts_node["gamma"])
        TS = TS * \
            float(parms.ts_node["gamma"]) if parms.ts_node["use_gamma_TS_penalty"] \
            else float(parms.ts_node["major_wrong_TS"])
        # no money transferred therefore no change in balance
        balance -= 0

    #   More possibilities to be added to minor wrong-doings
    elif transaction["wrong_doing"] == "minor":
        lst_min_bad = 0
        beta = parms.ts_node["delta"]*beta
        TS = beta*TS
        balance -= transaction["amount"]

    elif transaction["wrong_doing"] == "none":
        lst_maj_bad += 1
        lst_min_bad += 1
        TS += alpha*(70 - TS)
        balance -= transaction["amount"]

        if lst_maj_bad > parms.ts_node["reset_major"]:
            alpha = parms.default_user["alpha"]
        if lst_min_bad > parms.ts_node["reset_minor"]:
            beta = parms.default_user["beta"]

    #######################
    ## Behavioural terms ##
    #######################
    turnover_adjusted = False
    if parms.consider_behavior_over_time:
        transaction, bonus_points, turnover_adjusted = __behavior_contribution(
            sender_parms, transaction, penalize=parms.penalize_for_not_spending)
        TS += bonus_points
        if transaction["wrong_doing"] == "minor":
            lst_min_bad = 0

    TS = min(max(0, TS), 100)

    if not peek:
        t_prev_trans = transaction["transaction_time"] if transaction[
            "wrong_doing"] != "major" else sender_parms["time_prev_txn"]
        t_last_turn_adj = transaction["transaction_time"] if turnover_adjusted else sender_parms["time_last_turn_adj"]

        updated_usr_params = {
            "user_ID": str(transaction["sender_ID"]),
            "alpha": alpha,
            "beta": beta,
            "TS": TS,
            "balance": balance,
            "centrality": 0.01,
            "txns_last_maj_wrong": lst_maj_bad,
            "txns_last_min_wrong": lst_min_bad,
            "time_joined": sender_parms["time_joined"],
            "time_prev_txn": t_prev_trans,
            "time_last_turn_adj": t_last_turn_adj
        }

        user_db.update_write_user_parms_to_db(updated_usr_params)
    return TS


def __behavior_contribution(user_params: dict, transaction: dict,
                            penalize=parms.penalize_for_not_spending,
                            expected_ave_turnover=parms.ts_node["expected_turnover_over_timespan"]):
    #
    this_txn_time = iso_to_datetime(transaction["transaction_time"])
    time_prev_txn = iso_to_datetime(user_params["time_prev_txn"])
    time_last_adj = iso_to_datetime(user_params["time_last_turn_adj"])
    time_span = \
        datetime.timedelta(days=parms.ts_node["time_span_considered_days"])
    #
    time_in_network = this_txn_time - time_prev_txn
    time_since_last_update = this_txn_time - time_last_adj
    turnover_adjustment = False
    #
    if time_in_network < time_span:
        return transaction, 0, turnover_adjustment
    elif time_since_last_update < time_span:
        return transaction, 0, turnover_adjustment
    else:
        if transaction["wrong_doing"] == "major":
            # major wrong doing is not punished here.
            return transaction, 0, turnover_adjustment
        else:
            turnover_adjustment = True
            #
            send_history = send_db.get_usr_txn_history(
                str(transaction["sender_ID"]))
            coti_spent = get_spending_over_timespan(
                send_history, transaction, time_span)
            spending_points = __sigmoid_points(coti_spent)
            if not penalize:
                spending_points = max(0, spending_points)

            if coti_spent < parms.ts_node["expected_turnover_over_timespan"] and penalize:
                transaction["wrong_doing"] = "minor"
            print("Adjusted for turnover. \"Bonus points\" = ", spending_points)

            return transaction, spending_points, turnover_adjustment


def get_spending_over_timespan(send_history: dict, transaction: dict, timespan: datetime.timedelta):
    # Note that this doesn't consider the coti's received - only those spent
    # - this will probably be a problem for merchants
    this_transaction_time = iso_to_datetime(transaction["transaction_time"])
    coti_spent = 0
    counter = 0
    for isotime in send_history["transaction_time"]:
        if this_transaction_time - timespan <= iso_to_datetime(isotime) < this_transaction_time:
            coti_spent += float(send_history["amount"][counter])
        counter += 1
    coti_spent += transaction["amount"] if transaction["wrong_doing"] != "major" else 0
    return coti_spent


def get_received_txns_over_timespan(rec_history: dict, transaction: dict, timespan: datetime.timedelta):
    # Note that this doesn't consider the coti's received - only those spent
    # - this will probably be a problem for merchants
    this_transaction_time = iso_to_datetime(transaction["transaction_time"])
    coti_spent = 0
    counter = 0
    for isotime in rec_history["transaction_time"]:
        if this_transaction_time - timespan <= iso_to_datetime(isotime) < this_transaction_time:
            coti_spent += float(rec_history["amount"][counter])
        counter += 1
    coti_spent += transaction["amount"] if transaction["wrong_doing"] != "major" else 0
    return coti_spent
