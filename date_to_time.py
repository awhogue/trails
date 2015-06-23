#!/usr/bin/python

import time, datetime, sys;

print int(time.mktime(datetime.datetime(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])).timetuple()))
