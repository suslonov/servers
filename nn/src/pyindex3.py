#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.append('/usr/local/bin')


from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():#
    return "Hello World!"
 
if __name__ == "__main__":
    app.run()

def application(env, start_response):
    start_response('200 OK', [('Content-Type','text/html')])
    return [b"Hello World"]


#import sys

#def application(env, start_response):
#    start_response('200 OK', [('Content-Type','text/html')])

#    s = str(sys.version_info) + "<br>" +  str(sys.path)
#    return [bytes(s , 'utf-8')]
#    return s


