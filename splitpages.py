#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
from dntfile import *

filename = sys.argv[1] # takes one argument which is a file name

fl = open(filename, 'r')
dnt = DNTfile.read(fl)
fl.close()
dnt.toVertical()

dntlist = split_pages(dnt, -0.15, 0.15)
for i, d in enumerate(dntlist):
    fl = open(filename[:-4]+str(i)+'.svg', 'w')
    fl.write( simple_dnt2svg(d, '../mystyle.css').getvalue() )
    fl.close()
