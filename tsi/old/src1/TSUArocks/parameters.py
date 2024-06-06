############################################################################
######                  Some DB parameters                               ###
############################################################################
db_dir = "./DBs"
user_db_name = db_dir + "/" + "coti_user_db.db"
send_db_name = db_dir + "/" + "send_txns_db.db"                    
rec_db_name = db_dir + "/" + "rec_txns_db.dbb"
py_datetime_isoformat = "%Y-%m-%dT%H:%M:%S.%f"
encoding = "utf-8"
seperator = ","
uid_length = 5
consider_behavior_over_time = True
penalize_for_not_spending = False
#
#
default_user = {
    "user_ID": None,
    "alpha": 0.01,
    "beta": 1,
    "TS": 1,
    "balance":100,
    "centrality": 0.01,
    "txns_last_maj_wrong": 10000,
    "txns_last_min_wrong": 10000,
    "time_joined":"2018-06-19T07:14:22.708370",
    "time_prev_txn": "2018-06-19T07:14:22.708370",
    "time_last_turn_adj": "2018-06-19T07:14:22.708370"
}
ordered_user_parms = sorted(default_user)
#
#
ts_node = {
    "gamma": 0.5,
    "delta": 0.95,
    "reset_minor":30,
    "reset_major":1000,
    "major_wrong_TS":1,
    "use_gamma_TS_penalty":True,
    "turnover_devoted_points":2.0,
    "time_span_considered_days": 7,
    "expected_turnover_over_timespan": 100
}
ordered_ts_node_parms = sorted(ts_node)
#
#
default_txn = {
    # hours since beginning of network
    "transaction_time": "2018-06-19T07:14:22.708370",
    "sender_ID": 1,
    "sender_trust": None,
    # sender trust used as a parameter, but no default is set, as the value is taken from the db
    "receiver_ID": 2,
    "amount": 1,
    # major / minor / none
    "wrong_doing": "major"
}
ordered_txn_parms = sorted(default_txn)
