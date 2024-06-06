#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import datetime
from utils import Proto_Load_TS_Data, Proto_Save_TS_Data

def f_age(age):
    if age:
        a = int(age)
        if a == 0: age_years = 15
        elif a == 1: age_years = 22
        elif a == 2: age_years = 26
        elif a == 3: age_years = 27
        else: age_years = 70
        return str(datetime.date(datetime.date.today().year - age_years, datetime.date.today().month, datetime.date.today().day))
    else:
        return ''

def f_business_age(age):
    if age:
        a = float(age)
        age_years = int(a)
        age_months = int((a - age_years)*12)
        if datetime.date.today().month - age_months <= 0:
            age_years = age_years + 1
            age_months = - age_months
        return str(datetime.date(datetime.date.today().year - age_years, datetime.date.today().month - age_months, datetime.date.today().day))
    else:
        return ''

def f_was_fraud(wf):
    if not wf: return ''
    if wf == '0': return ''
    elif wf: return '1'

spec_fields = ['age', 'business_age', 'was_fraud']
spec_fields_functions = [f_age, f_business_age, f_was_fraud]
spec_fields_names = ['date_of_birth', 'incorporation_date', 'was_fraud']


datapath = "../ml/"
def load_csv_data_to_db(fname, userid='upload'):
    rowslist, _, _, _ = Proto_Load_TS_Data()
    fields = list(map(lambda x: x[1], rowslist))
    
    with open(datapath + fname) as csvfile:
        csvreader = csv.reader(csvfile)
        titles = True
        data = [] #list of rows
        for row in csvreader:
            if titles:
                # read the first line as headers
                headers = row
                titles = False
            else:
                # and read the data
                r = [ri if ri != "None" else "" for ri in row]
                rr = dict(zip(headers, r))
                data.append((rr['sid'], rr))  #sid by name

# convert derivative fields, for example age to date of birth
    for t in headers:
        if t in spec_fields:
            ti = spec_fields.index(t)
            for b in data:
                b[1][spec_fields_names[ti]] = spec_fields_functions[ti](b[1][t])
#    print (data)

# change select-type data from numbers to options and add ommited fields as empty
    for t in rowslist:
        if not t[1] in headers:
            for b in data:
                b[1][t[1]] = ''
        # '0' in checkbox or string data to be deleted
        if t[2] == 1 or t[2] == 0:
            for b in data:
                if b[1][t[1]] == '0':
                    b[1][t[1]] = ''
        if t[2] == 2:
            for b in data:
                if b[1][t[1]]:
                    rs = next((s for s in t[6] if s[0] == int(b[1][t[1]])), None)
                else:
                    rs = next((s for s in t[6] if s[0] == 0), None)
                b[1][t[1]] = rs[1]
            

# save all the data to DB
    for b in data:
        res = {}
        # create a (shallow) copy or a row to exclude nonneeded fields
        for ti in b[1]:
            if ti in fields:
                res[ti] = b[1][ti]
        print(b[0], res)
        Proto_Save_TS_Data(b[0], userid, rowslist, res, '', 0)
        
def loaddata():
#    load_csv_data_to_db('idealtypes.csv', 'upload')
    load_csv_data_to_db('presale1.csv', 'upload')

    
    
if __name__ == "__main__":
    loaddata()
