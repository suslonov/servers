import time
import random
import options
import requests
import matplotlib.pyplot as plt


########################################
## Methods and defaults
########################################
num_rand_users = 1000
server_url = "http://0.0.0.0:8022/calculate_initial_TS"


def create_random_input():
    count = random.choice(options.countries)
    out_dict = {
        "Bank_account": random.choice([True, False]),
        "Bank_reference": random.choice(["Yes", "No"]),
        "Children": random.choice(options.children),
        "Citizenship": count,
        "Country": count,
        "Credit_card_holder": random.choice([True, False]),
        "Credit_history": random.choice([True, False]),
        "Date_of_birth": str(random.randint(1900, 2015)),
        "Education": random.choice(options.education),
        "Employment_status": random.choice(options.employment_status),
        "Has_license": random.choice([True, False]),
        # random.choice(list(parms.identification.keys())),
        "Identification": random.choice(["National_ID", "Passport"]),
        "Income": random.choice(options.income),
        "Income_source_declared": random.choice([True, False]),
        "Insurance": random.choice([True, False]),
        "Investor": random.choice([True, False]),
        "Marital_status": random.choice(options.marital_status),
        "Occupation": "",
        "Phone": random.choice([True, False]),
        "Proof_of_residence": random.choice([True, False]),
        "Site": random.choice(["Yes", "No"]),
        "Social_network_account": random.choice(["Yes", "No"]),
        "Stable_income": random.choice([True, False]),
        "Stake": 10000*random.random(),
        "ZIP_code": random.choice(["Yes", "No"])
    }
    return out_dict


default_best = {
    "Bank_account": True,  # boolean
    "Bank_reference": "Mr. Smith",  # string
    "Children": "Have_grandchildren",  # string
    "Citizenship": "SGP",  # string
    "Country": "SGP",  # string
    "Credit_card_holder": True,  # boolean
    "Credit_history": True,  # boolean (new)
    "Date_of_birth": '1910-06-29T12:02:30.168326',  # date
    "Education": "PhD_Doctorate",  # string
    "Employment_status": "Employed",  # string
    "Has_license": True,  # boolean
    "Identification": "National_ID",  # string
    "Income": "$32000+",  # string
    "Income_source_declared": True,  # boolean
    "Insurance": True,  # boolean
    "Investor": True,  # boolean
    "Marital_status": "Married",  # string
    "Occupation": "Clown",  # string (new)
    "Phone": True,  # boolean
    "Proof_of_residence": True,  # boolean
    "Site": "coolbeans.com",  # string   (new)
    "Social_network_account": "theres.something.about.Mary",  # string
    "Stable_income": True,  # boolean (new)
    "Stake": 10000000000,  # decimal
    "ZIP_code": "1458"  # string
}


default_worst = {
    "Bank_account": False,  # boolean
    "Bank_reference": "None",  # string
    "Children": "None",  # string
    "Citizenship": "NA",  # string
    "Country": "NA",  # string
    "Credit_card_holder": False,  # boolean
    "Credit_history": False,  # boolean (new)
    "Date_of_birth": '2018-06-29T12:02:30.168326',  # date
    "Education": "Not_educated",  # string
    "Employment_status": "None",  # string
    "Has_license": False,  # boolean
    "Identification": "Not_provided",  # string
    "Income": "None",  # string
    "Income_source_declared": False,  # boolean
    "Insurance": False,  # boolean
    "Investor": False,  # boolean
    "Marital_status": "Single",  # string
    "Occupation": "Clown",  # string (new)
    "Phone": False,  # boolean
    "Proof_of_residence": False,  # boolean
    "Site": "NA",  # string   (new)
    "Social_network_account": "NA",  # string
    "Stable_income": False,  # boolean (new)
    "Stake": 0,  # decimal
    "ZIP_code": "None"  # string
}


########################################
# Calls to the server
########################################


print("Testing ITSA server.")
t0 = time.clock()
ts_array = list()
for i in range(num_rand_users):
    ts = requests.put(url=server_url, json=create_random_input()).json()

    ts_array.append(ts["TS"])


plt.hist(ts_array, bins=int(100))
plt.show()

t1 = time.clock()
print(str(t1-t0) + " seconds for test.")