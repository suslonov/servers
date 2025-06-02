#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

if (sys.version.find('anaconda') != -1) or (sys.version.find('Continuum') != -1):
  anaconda_path = ['/home/anton/anaconda3/lib/python3.6',
                   '/home/anton/anaconda3/lib/python3.6/lib-dynload',
                   '/home/anton/anaconda3/lib/python3.6/site-packages']
  sys.path = anaconda_path + sys.path

from toynn import application

if __name__ == "__main__":
    application.run()
#    application.run(debug=True)


