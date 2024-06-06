import string
import random
import datetime
from . import parameters as parms
from . import TSUA_operations as DBs
# import parameters as parms
# import coti_rdbs_TSUA_operations as DBs

############################################################
######              Quick methods                        ###
############################################################


def iso_to_datetime(isostring: str):
    return datetime.datetime.strptime(isostring, parms.py_datetime_isoformat)

def rndnt_rnge(rnge: list):
    if len(rnge) != 2:
        raise Exception
    else:
        return random.randint(rnge[0], rnge[1])


def gen_random_iso_extended_time(yearrange=[2018, 2018], monthrange=[3, 6], dayrange=[1, 28], hourrange=[0, 23], minrange=[0, 59], second_range=[0, 59]):
    year = "{:04d}".format(rndnt_rnge(yearrange))
    mon = "{:02d}".format(rndnt_rnge(monthrange))
    day = "{:02d}".format(rndnt_rnge(dayrange))
    hour = "{:02d}".format(rndnt_rnge(hourrange))
    minute = "{:02d}".format(rndnt_rnge(minrange))
    sec_val = second_range[0] + \
        random.random()*(second_range[1]-second_range[0])
    second = "{:09.6f}".format(sec_val)
    iso_t_string = year + "-" + mon + "-" + day + \
        "T" + hour + ":" + minute + ":" + second
    return iso_t_string


def weighed_random_choice(choices: list, probabilities: list):
    if len(choices) != len(probabilities):
        raise IndexError("Length of choices and probabilities are different")

    sorters = [x*random.random() for x in probabilities]
    srt_prb_chc = sorted(zip(sorters, choices),
                         key=lambda x: x[0], reverse=True)
    srt_probs, srt_choices = map(list, zip(*srt_prb_chc))
    return srt_choices



################################################################
##                      Initiation                      ##
################################################################
num_users = 100
num_to_transact = 2
transaction_checks = 40
transaction_amounts = [50, 200]
bal_min, bal_max = 1000, 10000


user_dict = dict()
for i in range(num_users):
    uid = ""
    for j in range(parms.uid_length):
        uid += random.choice(string.ascii_lowercase + string.digits)

    user_to_add = {"user_ID": uid, "TS": random.randint(1, 99),  "balance": float(random.randint(bal_min, bal_max)),
                   "time_joined": gen_random_iso_extended_time(monthrange=[1, 2]),
                   "time_prev_txn": gen_random_iso_extended_time(monthrange=[3, 4]),
                   "time_last_turn_adj": gen_random_iso_extended_time(monthrange=[4, 4], dayrange=[30, 30])}

    for p in parms.ordered_TSUA_parms:
        if p not in user_to_add:
            user_to_add[p] = parms.default_TSUA_params[p]
    user_dict[uid] = user_to_add
    DBs.insert_new_user_in_db(user_to_add)

##############################################################
###                    Some checks                         ###
##############################################################


def check_db_vs_dict(user_dict: dict):
    for u in user_dict:
        db_dict = DBs.user_db.read_usr_parms_from_db(u)

        print("\t\t\t\t\t From dictionary      \t\t\t From db")
        for p in parms.default_TSUA_params:
            if p == "user_ID":
                continue

            print("{:>20s}".format(p), "\t\t\t", "{:25s}".format(
                str(user_dict[u][p])), "\t", db_dict[p])
        print("_________________________________________________________________________")


def diff_check_db_vs_dict(user_dict: dict):
    print("Checking differences between dictionary in memory and DB.")
    for u in user_dict:
        db_dict = DBs.user_db.read_usr_parms_from_db(u)

        for p in parms.default_TSUA_params:
            if p == "user_ID":
                continue
            if str(user_dict[u][p]) != str(db_dict[p]):
                print("Critical difference detected for user ",
                      u, " parameter ", p)
                print("\t\t\t\t\t From dictionary      \t\t\t From db")
                print("{:>20s}".format(p), "\t\t\t", "{:25s}".format(
                    str(user_dict[u][p])), "\t", db_dict[p])
                print(
                    "_________________________________________________________________________")


diff_check_db_vs_dict(user_dict)


##############################################################
###            Further initiation and checks               ###
##############################################################


transacting_users = list()

while len(transacting_users) < num_to_transact:
    user = random.choice(list(user_dict.keys()))
    if user not in transacting_users:
        transacting_users.append(user)


counter = 0
while counter < transaction_checks:
    sender = random.choice(transacting_users)
    receiver = random.choice(list(user_dict.keys()))
    if sender == receiver:
        continue

    transaction = {"sender_ID": sender, "receiver_ID": receiver}
    transaction["sender_trust"] = user_dict[sender]["TS"]

    min_t = round(23*(counter-1)/transaction_checks)
    max_t = round(23 * counter / transaction_checks)

    transaction["transaction_time"] = gen_random_iso_extended_time(
        monthrange=[6, 6], dayrange=[19, 19], hourrange=[max(0, min_t), max_t])
    transaction["amount"] = random.randint(transaction_amounts[0], transaction_amounts[1])
    txn_wrongness = weighed_random_choice(
        ["none", "minor", "major"], [96, 3, 1])[0]
    transaction["wrong_doing"] = txn_wrongness

    #"none" #random.choice(["major", "minor", "none"])

    if transaction["wrong_doing"] != "major":
        counter += 1
        user_dict[sender]["balance"] -= transaction["amount"]
        user_dict[receiver]["balance"] += transaction["amount"]

    new_TS = DBs.new_txn_update_all(transaction)
    user_dict[sender]["TS"] = new_TS

diff_check_db_vs_dict(user_dict)
