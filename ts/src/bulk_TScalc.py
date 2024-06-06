#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utils import Proto_Load_TS_Data, Proto_Save_TS_Only
from algs import Calculate_TS
import csv

datapath = "../ml/"
def calc_TS_from_db(sid, algname):
   
    rowslist, userid, algs, re = Proto_Load_TS_Data(0, sid)
    
#    print(re)

    trustscore = Calculate_TS(re, algname)
#    print (trustscore)

    Proto_Save_TS_Only(sid, userid, algname, trustscore)
   

def TScalc():
    
#    fname='presale1.csv'
#    with open(datapath + fname) as csvfile:
#        csvreader = csv.reader(csvfile)
#        titles = True
#        data = [] #list sids
#        for row in csvreader:
#            if titles:
#                # read the first line as headers
#                sid_r = row.index('sid')
#                titles = False
#            else:
#                # and read the data
#                data.append(row[sid_r])
    
    data=['015859b2cf191ea7b17377eb22723f0f',
#        '2015a1116ebf8f84d6f5c66334a019bd',
#        '40bbfa4400a72d14a09c8a7dbd6a43a1',
#        '789805b96122d6a1113d2ce0c64ea0e8',
        '8cb1b288209f14d9a9b0bd64e4b15160',]
#        'b5d51b6bc2ed38f0f7110eba5874a344',
#        'c123deaad6a35014621bd44d93bdca8f',
#        'd1ea6e554cf674fd1cf5700b136fa2a1',
#        'd2439cc297327dccefa8d1042d5871fd',
#        'ecf791b065d6ba1e9cd3d33b19dde251',]

    for s in data:
        calc_TS_from_db(s, 'ITSU_A2')
        calc_TS_from_db(s, 'ITSU_I1')
    
#    calc_TS_from_db('teenagers626549', 'ITSU_A2')
#    calc_TS_from_db('students865644', 'ITSU_A2')
#    calc_TS_from_db('youths397670', 'ITSU_A2')
#    calc_TS_from_db('youngfamilies265212', 'ITSU_A2')
#    calc_TS_from_db('laborers497470', 'ITSU_A2')
#    calc_TS_from_db('professionals115357', 'ITSU_A2')
#    calc_TS_from_db('geeks308740', 'ITSU_A2')
#    calc_TS_from_db('eliteprofessionals533731', 'ITSU_A2')
#    calc_TS_from_db('tradesmans595221', 'ITSU_A2')
#    calc_TS_from_db('topmanagers367526', 'ITSU_A2')
#    calc_TS_from_db('proffessors11827', 'ITSU_A2')
#    calc_TS_from_db('tycoons286555', 'ITSU_A2')
#    calc_TS_from_db('splurgers736130', 'ITSU_A2')
#    calc_TS_from_db('vacuouspersons324041', 'ITSU_A2')
#    calc_TS_from_db('paupers695558', 'ITSU_A2')
#    calc_TS_from_db('jerks712863', 'ITSU_A2')
#    calc_TS_from_db('cheaters792192', 'ITSU_A2')
#
#    calc_TS_from_db('teenagers626549', 'ITSU_A1')
#    calc_TS_from_db('students865644', 'ITSU_A1')
#    calc_TS_from_db('youths397670', 'ITSU_A1')
#    calc_TS_from_db('youngfamilies265212', 'ITSU_A1')
#    calc_TS_from_db('laborers497470', 'ITSU_A1')
#    calc_TS_from_db('professionals115357', 'ITSU_A1')
#    calc_TS_from_db('geeks308740', 'ITSU_A1')
#    calc_TS_from_db('eliteprofessionals533731', 'ITSU_A1')
#    calc_TS_from_db('tradesmans595221', 'ITSU_A1')
#    calc_TS_from_db('topmanagers367526', 'ITSU_A1')
#    calc_TS_from_db('proffessors11827', 'ITSU_A1')
#    calc_TS_from_db('tycoons286555', 'ITSU_A1')
#    calc_TS_from_db('splurgers736130', 'ITSU_A1')
#    calc_TS_from_db('vacuouspersons324041', 'ITSU_A1')
#    calc_TS_from_db('paupers695558', 'ITSU_A1')
#    calc_TS_from_db('jerks712863', 'ITSU_A1')
#    calc_TS_from_db('cheaters792192', 'ITSU_A1')
#
#    calc_TS_from_db('teenagers626549', 'ITSU_I1')
#    calc_TS_from_db('students865644', 'ITSU_I1')
#    calc_TS_from_db('youths397670', 'ITSU_I1')
#    calc_TS_from_db('youngfamilies265212', 'ITSU_I1')
#    calc_TS_from_db('laborers497470', 'ITSU_I1')
#    calc_TS_from_db('professionals115357', 'ITSU_I1')
#    calc_TS_from_db('geeks308740', 'ITSU_I1')
#    calc_TS_from_db('eliteprofessionals533731', 'ITSU_I1')
#    calc_TS_from_db('tradesmans595221', 'ITSU_I1')
#    calc_TS_from_db('topmanagers367526', 'ITSU_I1')
#    calc_TS_from_db('proffessors11827', 'ITSU_I1')
#    calc_TS_from_db('tycoons286555', 'ITSU_I1')
#    calc_TS_from_db('splurgers736130', 'ITSU_I1')
#    calc_TS_from_db('vacuouspersons324041', 'ITSU_I1')
#    calc_TS_from_db('paupers695558', 'ITSU_I1')
#    calc_TS_from_db('jerks712863', 'ITSU_I1')
#    calc_TS_from_db('cheaters792192', 'ITSU_I1')


if __name__ == "__main__":
    TScalc()
