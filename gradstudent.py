#!/usr/bin/env python3
import time
import sys
import subprocess
import os
import sdpdatafile
import simplelogger
import argparse
import manyworlds

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
if not xmlfiles:
    # successfully created nothing
    xmlsuccess = True
else:
    if all(map(os.path.isfile, xmlfiles)):
        log.write('xmlfilecreation', 'xml file(s) already exist(s)')
        xmlsuccess = True
    else:
        try:
            log.write('xmlfilecreation', 'running xml file creator')
            start = time.time()
            world.createSdpFiles(sdpdata)
            log.write('xmlfilecreation', 'xml file creator finished')
            finish = time.time()
            log.write('xmlfilecreation', 'duration: ' + str(finish - start))
            # check if all files were created
            if all(map(os.path.isfile, xmlfiles)):
                log.write('xmlfilecreation', 'file(s) created')
                xmlsuccess = True
            else:
                log.write('xmlfilecreation', 'file(s) were not created')
                xmlsuccess = False
        except subprocess.CalledProcessError as e:
            log.write('xmlfilecreation', e.returncode)
            xmlsuccess = False
        except FileNotFoundError:
            log.write('xmlfilecreation', 'file creator not found')
            xmlsuccess = False

tr = None
if sdpdata.sdpbargs is not None and xmlsuccess:
    try:
        log.write('starting sdpb')
        world.runSdpb(sdpdata)
        log.write('sdpb finished')
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
                var = arr[0].strip(' ')
                val = arr[1].strip('"; \n')
                log.write(var, val)
                if var == 'terminateReason':
                    tr = val
    except subprocess.CalledProcessError as e:
        log.write('sdpb failed with error', e.stderr)
        tr = 'sdpb error'
        log.write('terminateReason', 'sdpb error')
    except IOError:
        tr = 'no out file'
        log.write('terminateReason', 'no out file')

world.cooldown(sdpdata, tr, log)
log.write('status', 'done')
sdpdata.unlock()
