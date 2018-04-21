#!/usr/bin/env python3
import time
import sys
import subprocess
import os
import sdpdatafile
import simplelogger
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
log = simplelogger.SimpleLogWriter('run', sdpdata.logfilename)
log.write('status', 'running')

world.warmup(sdpdata, log)

xmlfiles = sdpdata.xmlfilenames
if xmlfiles:
    if all(map(os.path.isfile, xmlfiles)):
        log.write('xmlfilecreation', 'xml file(s) already exist(s)')
        success = True
    else:
        try:
            log.write('xmlfilecreation', 'running xml file creator')
            start = time.time()
            world.createSdpFiles(sdpdata)
            log.write('xmlfilecreation', 'duration: ' + str(time.time() - start))
            # check if all files were created
            if all(map(os.path.isfile, xmlfiles)):
                log.write('xmlfilecreation', 'file(s) created')
                success = True
            else:
                log.write('xmlfilecreation', 'file(s) were not created')
                success = False
        except subprocess.CalledProcessError as e:
            log.write('xmlfilecreation', e.returncode)
            success = False
        except FileNotFoundError:
            log.write('xmlfilecreation', 'file creator not found')
            success = False
    if not success:
        log.write('status', 'done')
        exit(1)

if sdpdata.sdpbargs is None:
    log.write('status', 'done')
    exit()
try:
    log.write('sdpb', 'starting sdpb')
    world.runSdpb(sdpdata)
    log.write('sdpb', 'sdpb finished')
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
            log.write(arr[0].strip(' '), arr[1].strip('"; \n'))
except subprocess.CalledProcessError as e:
    log.write('sdpb', 'sdpb failed with error:' + e.stderr)
    log.write('terminateReason', 'sdpb error')
except IOError:
    log.write('terminateReason', 'no out file')

log.write('status', 'done')
sdpdata.unlock()
