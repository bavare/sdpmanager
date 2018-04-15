#!/usr/bin/env python3

import argparse
import datetime
import sdpdatafile
import postdoc
import os.path
import sys
import manyworlds
import subprocess as sp
# from multiprocessing.dummy import Pool as ThreadPool

parser = argparse.ArgumentParser()
parser.add_argument('filenames', metavar='fn', nargs='+',
                    help="""A number of sdp data files to handle.""")
parser.add_argument('-w', '--world', choices=['local', 'cern'],
                    help="""Select the local environment.""", required=True)
parser.add_argument('-m', '--maxsubmissions', type=int, default=10,
                    help="""Maximum number of submissions of a job.""")
parser.add_argument('-p', '--pause', action='store_true',
                    help="""Wait for completion of jobs.""")
parser.add_argument('-r', '--reallyrunning', action='store_true',
                    help="""Query the cluster to see if job is really running.
                            Resubmit if this is not the case.""")
# parser.add_argument('-f', '--force', action='store_true',
#                     help='force resubmission after mysterious failures')
args = parser.parse_args()
sdpDataFilenames = args.filenames
if not all(map(os.path.isfile, sdpDataFilenames)):
    print('Could not find sdp data file(s)', file=sys.stderr)
    exit(1)
sdpDataFilenames = list(map(os.path.abspath, sdpDataFilenames))
world = manyworlds.getworld(args.world)


def submit(sdpdata):
    print('Submitting ' + sdpdata.filename + '.')
    # log submission time
    sdpdata.adddict('log', {}, append=False)
    now = str(datetime.datetime.now())
    sdpdata.writelog('submissiontime', now)
    # submit
    try:
        submissionid = world.submit(sdpdata)
    except sp.CalledProcessError as e:
        sdpdata.writelog('submissionerror', e.returncode)
        raise
    # log processid
    sdpdata.writelog('submissionid', submissionid)
    return submissionid


def handle(oldfilename):
    filename = postdoc.analyze(sdpdatafile.SdpDataFile(oldfilename))
    if filename is None:
        print('Will not submit with ' + oldfilename + '.')
        return None
    if filename != oldfilename:
        print('File ' + oldfilename + ' replaced with ' + filename + '.')
    sdpdata = sdpdatafile.SdpDataFile(filename)

    # maxsubmissions exceeded?
    if args.maxsubmissions and sdpdata.numlogs() > args.maxsubmissions:
        print('Too many submissions for ' + filename)
        return None

    # submit if necessary
    submissionid = sdpdata.getlogitem('submissionid')
    submissionresult = sdpdata.getlogitem('submissionresult')
    if submissionid is None or submissionresult == 'completed':
        submissionid = submit(sdpdata)
    else:
        print('Found existing submission for ' + filename + '.')
        if args.reallyrunning:
            if not world.isreallyrunning(submissionid):
                print('Submission of ' + filename + ' seems to have failed.',
                      file=sys.stderr)
                sdpdata.writelog('submissionresult', 'failed')

    # wait for completion
    if args.pause:
        print('Waiting for completion of ' + filename + '...')
        world.waitforcompletion(submissionid)
        print('...' + filename + ' completed.')
        if sdpdata.getlogitem('terminateReason') is not None:
            handle(sdpdata.filename)
        else:
            print('Submission of ' + filename + ' seems to have failed.',
                  file=sys.stderr)


# pool = ThreadPool(len(sdpDataFilenames))
# results = pool.map(handle, sdpDataFilenames)
results = list(map(handle, sdpDataFilenames))
# pool.close()
# pool.join()
