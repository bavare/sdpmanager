#!/usr/bin/env python3
import time
import sys
import subprocess
import os
import os.path
import sdpdatafile
import argparse
import manyworlds

print(os.getcwd())

parser = argparse.ArgumentParser()
parser.add_argument('filename', metavar='file', help='an sdp data file')
parser.add_argument('-w', '--world', choices=['local', 'cern'],
                    help='select the local environment', required=True)
args = parser.parse_args()
if not os.path.isfile(args.filename):
    print('Could not find sdp data file(s)', file=sys.stderr)
    exit(1)
world = manyworlds.getworld(args.world)

sdpdata = sdpdatafile.SdpDataFile(args.filename)
print('Running with ' + args.filename + '.')

world.warmup(sdpdata)

xmlfiles = sdpdata.xmlfilenames
if xmlfiles:
    print('Found instructions to create xmlfile(s).')
    if all(map(os.path.isfile, xmlfiles)):
        sdpdata.writelog('result', 'xml file(s) already exist(s)')
        success = True
    else:
        try:
            start = time.time()
            world.createSdpFiles(sdpdata)
            print('xml file creation duration: ' + str(time.time() - start))
            # check if all files were created
            if all(map(os.path.isfile, xmlfiles)):
                sdpdata.writelog('result', 'file(s) created')
                success = True
            else:
                sdpdata.writelog('error', 'file(s) not created')
                success = False
        except subprocess.CalledProcessError as e:
            sdpdata.writelog('error', e.returncode)
            success = False
        except FileNotFoundError:
            sdpdata.writelog('error', 'sdpFilecreator not found')
            success = False
    if not success:
        print('Could not create xml files. Exiting.')
        exit(1)

if sdpdata.sdpbargs is None:
    exit()
print('Found instructions to run sdpb...')
try:
    world.runSdpb(sdpdata)
    print('...sdpb finished.')
    with open(sdpdata.outfile, 'r') as of:
        # terminateReason
        # primalObjective
        # dualObjective
        # dualityGap
        # primalError
        # dualError
        # runtime
        for _ in range(7):
            arr = of.readline().split('=')
            sdpdata.writelog(arr[0].strip(' '), arr[1].strip('"; \n'))
except subprocess.CalledProcessError as e:
    print('...sdpb failed.')
    sdpdata.writelog('stderr', e.stderr)
    sdpdata.writelog('terminateReason', 'sdpb error')
except IOError:
    sdpdata.writelog('terminateReason', 'Out file not found')

world.cooldown(sdpdata)

sdpdata.writelog('submissionresult', 'completed')
