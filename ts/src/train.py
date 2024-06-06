#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#import pandas as pd
#f = pd.read_csv("idealtypes.csv")

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.externals import joblib
from utils import Proto_Load_TS_Data
import csv

#from sklearn.svm import SVR
#from sklearn.naive_bayes import BernoulliNB
#from sklearn.naive_bayes import GaussianNB

datapath = "../ml/"

def f1hot(col, l, param):
    result = np.zeros((l, param))
    result[np.arange(l), col.T.astype(int)] = 1
    return result

def upto1hot(col, l, param):
# here and below up-to-1hot N means the array filled with ones up to N
# (it is the sum of 1hot arrays for categorues from 0 to N )
    r = np.arange(param)
    result = (col>=r).astype(float)  # broadcasting operation
    return result

def upto1hot0(col, l, param):
    r = np.arange(param)
    result = (((col>=r)&(r > 0))|((col==0)&(r==0))).astype(float)
# broadcasting operation excluding 0 if col>0
    return result

def upto1hot_investor0(col, l, param):
    r = np.arange(param)
    col[col<0] = 0
    col[(col>0) & (col<100)] = 1
    col[(col>=100) & (col<1000)] = 2
    col[(col>=1000)] = 3
    result = (((col>=r)&(r > 0))|((col==0)&(r==0))).astype(float)
# broadcasting operation excluding 0 if col>0
    return result

def upto1hot_income0(col, l, param):
    r = np.arange(param)
    col[col<1000] = 0
    col[(col>=1000) & (col<3000)] = 1
    col[(col>=3000) & (col<7000)] = 2
    col[(col>=7000) & (col<20000)] = 3
    col[(col>=20000)] = 4
    result = (((col>=r)&(r > 0))|((col==0)&(r==0))).astype(float)
# broadcasting operation excluding 0 if col>0
    return result

spec_fields = ['id_type', 'age', 'children', 'education', 'investor', 'income', 'was_fraud']
spec_fields_random_lims = [4, 4, 3, 6, 4, 5, 3]
spec_fields_functions = [f1hot, f1hot, upto1hot0, upto1hot0, upto1hot_investor0, upto1hot_income0, f1hot]
spec_fields_params = [4, 4, 3, 6, 4, 5, 3]

def load_csv_data(fname, shuffle=1, fill='0'):
#    fname = 'idealtypes-1.csv'
    
# read the first line as headers separately
    with open(datapath + fname) as csvfile:
        s = csvfile.readline().rstrip()
        headers = s.split(',')

# and read data without the first line
    data = np.genfromtxt(datapath + fname, delimiter=',', skip_header=1)
    l = data.shape[0]

# load fields from the DB
    rowslist, _, _, _ = Proto_Load_TS_Data()
    fields = list(map(lambda x: x[1], rowslist))

# find special columns: sid, frequency, TargetBasket
#    sid_id = next((i for i, li in enumerate(headers) if li == 'sid'), None)
    frequency_id = next((i for i, li in enumerate(headers) if li == 'Frequency'), None)
    TargetBasket_id = next((i for i, li in enumerate(headers) if li == 'TargetBasket'), None)

#    sid_col =  = data[:, sid_id]
    if frequency_id: frequencies = data[:, frequency_id]
    if TargetBasket_id:
        labels = data[:, TargetBasket_id]
    else:
        return None, None, None

# collect features columns
    col_id = 0
    start = True
    out_headers = []
    for header in headers:
        # check if field is special
        field_id = next((i for i, li in enumerate(spec_fields) if li == header), None)

# = if header in spec_fields
        if field_id or field_id == 0:
            random_lim = spec_fields_random_lims[field_id]
        else:
            if header in fields:
                fi = fields.index(header)
                # if type = select, take the leangth as random_lim
                if rowslist[fi][2] == 2:
                    random_lim = len(rowslist[fi][6])
                else:
                    random_lim = 2    
            else:
                random_lim = 2    

# if column header is in DB rows or in spec_fields add to output list and process the column
        if header in fields or header in spec_fields:
            out_headers.append(header)

            # take a column
            col = data[:, col_id].reshape(l, 1)

            # fill empties
            if fill == '0':
                col[np.isnan(col)] = 0
            else:
                # generate random array with given limits by column
                col[np.isnan(col)] = np.random.randint(random_lim, size=col[np.isnan(col)].shape[0])

            # convert special columns
            if field_id or field_id == 0:
                res = spec_fields_functions[field_id](col, l, spec_fields_params[field_id])
            else:
                res = col

            # begin or not, if not - add to the end
            if start:
                features = res
                start = False
            else:
                features = np.concatenate((features, res), 1)
        col_id += 1

#repeat strings according to frequency and shuffle together with labels
    result = np.concatenate((features, labels.reshape(l,1)), 1)
    if frequency_id: result = np.repeat(result, frequencies.astype(int), 0)
    if shuffle: np.random.shuffle(result)

#split on return     features = result[:,:-1]     labels = result[:,-1]
    return result[:,:-1], result[:,-1], out_headers

def trainidealtypes():
    f,l,h = load_csv_data('idealtypes-1.csv')
    print(f.shape, l.shape)
    
    ft,lt,_ = load_csv_data('testset.csv', shuffle=0)
    print(ft.shape, lt.shape)

#    f,l = load_csv_data('simple3.csv')
#    ft,lt = load_csv_data('simple_test3.csv', shuffle=0)
    
#    svr_poly = SVR(kernel='poly', C=1e3, degree=2)
#    c_poly = svr_poly.fit(f, l)
#    p = c_poly.predict(ft)

#    clf = BernoulliNB()
#    clf = GaussianNB()
#    clf.fit(f, l)
#    p=clf.predict(ft)
    
    rf = RandomForestRegressor(n_estimators = 100)
    rf.fit(f, l)
    p = rf.predict(ft)
    q = list(zip(p,lt))
    for qi in q: print(qi)
    
    for i in rf.feature_importances_: print(i)

    joblib.dump(rf, 'rf.clf')
    with open('rf.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(h)

# h to csv

if __name__ == "__main__":
    trainidealtypes()
