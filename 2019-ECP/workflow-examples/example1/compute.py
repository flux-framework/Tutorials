#!/bin/env python

import argparse
import time

parser = argparse.ArgumentParser (description='compute for seconds')
parser.add_argument ('integer', metavar='S', type=int,
                     help='an integer for the number of seconds to compute')

args = parser.parse_args ()

print "Will compute for " + str (args.integer) + " seconds."
time.sleep (args.integer)

