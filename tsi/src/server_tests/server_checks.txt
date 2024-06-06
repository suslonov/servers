#! /bin/bash

############################### 
## Checks - adding users     ##
###############################

############# Get a good user ITSA	##
curl -X PUT -H "Content-Type:application/json" $1/calculate_initial_TS -d '{"Bank_account": true,"Bank_reference": "None","Children": "None","Citizenship": "USA","Country": "SGP","Credit_card_holder": true,"Credit_history": true,"Date_of_birth": "1950-06-29","Education": "Master","Employment_status": "Self_employed","Has_license": true,"Identification": "Passport","Income": "$16000-$32000","Income_source_declared": true,"Insurance": true,"Investor": true,"Marital_status": "Single","Occupation": "Scientist","Phone": true,"Proof_of_residence": false,"Site": "NA","Social_network_account": false,"Stable_income": true,"Stake": 10000}'
echo '{"TS":23.767967188986972}'
echo 
########## Adding to working (TSUA) DB 	##
curl -X PUT -H "Content-Type:application/json" $1/calculate_initial_TS -d '{"Identification": "Not_available"}'
echo '{"TS":0}'
echo

