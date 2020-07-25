#!/usr/bin/env python3

import argparse
import datetime
import sdpdatafile
import simplelogger
import analyzer
import os.path
import sys
import manyworlds
import subprocess as sp
# from multiprocessing.dummy import Pool as ThreadPool

parser = argparse.ArgumentParser()
parser.add_argument('filenames', metavar='fn', nargs='+',
                    help="""A number of sdp data files to potentially clean up.""")
parser.add_argument('-w', '--world', choices=['local', 'cern', 'fake'],
                    help="""Select the local environment.""")

args = parser.parse_args()
sdpDataFilenames = args.filenames
if not all(map(os.path.isfile, sdpDataFilenames)):
    print('Could not find sdp data file(s)', file=sys.stderr)
    exit(1)
sdpDataFilenames = list(map(os.path.abspath, sdpDataFilenames))
world = manyworlds.getworld(args.world)

def inlineprint(expr):
    print(expr, end=' ', flush=True)

def cleanup(filename):
    sdpdata = sdpdatafile.SdpDataFile(filename)

    log = simplelogger.SimpleLogReader(sdpdata.logfilename)

    if log.getstatus() == 'concluded':
        newfilename = log.lastbonusexprwith(expr='replaced with')
        if newfilename is not None:
            world.removefile(filename)
            world.removefile(sdpdata.logfilename)

# Parallel version:
# pool = ThreadPool(len(sdpDataFilenames))
# results = pool.map(handle, sdpDataFilenames)
# pool.close()
# pool.join()

for sdpDataFilename in sdpDataFilenames:
    cleanup(sdpDataFilename)
