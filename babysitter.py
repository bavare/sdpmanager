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
from multiprocessing.dummy import Pool as ThreadPool

parser = argparse.ArgumentParser()
parser.add_argument('filenames', metavar='fn', nargs='+',
                    help="""A number of sdp data files to handle.""")
parser.add_argument('-w', '--world', choices=['local', 'cern', 'fake'],
                    help="""Select the local environment.""", required=True)
parser.add_argument('-m', '--maxsubmissions', type=int, default=10,
                    help="""Maximum number of submissions of a job.""")
parser.add_argument('-p', '--pause', action='store_true',
                    help="""Wait for completion of jobs.""")
parser.add_argument('-r', '--reallyrunning', action='store_true',
                    help="""Query the cluster to see if job is really running.
                            Resubmit if this is not the case.""")
parser.add_argument('-f', '--force', action='store_true',
                    help="""force resubmission of a 'failed' job'""")

args = parser.parse_args()
sdpDataFilenames = args.filenames
if not all(map(os.path.isfile, sdpDataFilenames)):
    print('Could not find sdp data file(s)', file=sys.stderr)
    exit(1)
sdpDataFilenames = list(map(os.path.abspath, sdpDataFilenames))
world = manyworlds.getworld(args.world)


def submit(sdpdata):
    logw = simplelogger.SimpleLogWriter('sub', sdpdata.logfilename)
    # log submission time
    now = str(datetime.datetime.now())
    # submit
    try:
        submissionid = world.submit(sdpdata)
    except sp.CalledProcessError as e:
        logw.write('submissionerror', e.returncode)
        logw.setstatus('failed')
        raise
    # logw processid
    logw.setstatus('submitted')
    logw.write('submissionid', submissionid)
    logw.write('submissiontime', now)
    return submissionid


def handle(filename):
    sdpdata = sdpdatafile.SdpDataFile(filename)

    log = simplelogger.SimpleLogReader(sdpdata.logfilename)
    logw = simplelogger.SimpleLogWriter('sub', sdpdata.logfilename)

    status = log.getstatus()

    if status == 'concluded':
        print('All done with ' + filename + '.')
    elif status is None or status == 'tosubmit':
        print('Submitting ' + filename + '...')
        submit(sdpdata)
        handle(filename)
    elif status == 'failed':
        if args.force:
            print('Force resubmitting of failed ' + filename + '...')
            submit(sdpdata)
            handle(filename)
        else:
            print('Failed submission of ' + filename + '.')
    elif status == 'submitted' or status == 'running':
        print('Successful but uncompleted submission for ' + filename + '.')
        if args.reallyrunning:
            submissionid = log.lastbonusexprwith(expr='submissionid')
            if world.isreallyrunning(submissionid):
                print('Checked that ' + filename + ' is running.')
            else:
                print('Checked that ' + filename + ' is NOT running.')
                logw.setstatus('failed')
                handle(filename)
        if args.pause:
            print('Waiting for completion of ' + filename + '...')
            submissionid = log.lastbonusexprwith(expr='submissionid')
            world.waitforcompletion(submissionid)
            print('...' + filename + ' completed.')
            handle(filename)
    elif status == 'finished':
        tr = log.lastbonusexprwith(expr='terminateReason')
        primopt = log.lastbonusexprwith(expr='primalObjective')
        if tr == 'maxRuntime exceeded' or \
                tr == 'maxIterations exceeded':
            if args.maxsubmissions and \
                    log.numlineswith(expr='status', bonusexpr='submitted') >= \
                    args.maxsubmissions:
                print('Too many submissions for ' + filename + '.')
                logw.write('too many submissions')
                logw.setstatus('failed')
                handle(sdpdata)
            else:
                print('Resubmitting ' + sdpdata.filename + '.')
                submit(sdpdata)
                handle(sdpdata)
        else:  # i.e. terminateReason is not timed out
            try:
                newfilename = analyzer.analyze(sdpdata, tr, primopt)
            except ValueError:
                logw.write('analyzer failed with ValueError')
                logw.setstatus('failed')
                handle(filename)
            else:
                logw.setstatus('concluded')
                if newfilename is None:
                    print('All done with ' + filename + '.')
                elif newfilename == filename:
                    print('File ' + filename + ' needs to be resubmitted.')
                    logw.setstatus('tosubmit')
                    handle(filename)
                else:
                    print('File ' + filename + ' replaced with ' +
                          newfilename + '.')
                    handle(newfilename)
    else:
        # How did you get here?
        print('Unknown status for ' + filename + '!')


# Parallel version:
pool = ThreadPool(len(sdpDataFilenames))
results = pool.map(handle, sdpDataFilenames)
pool.close()
pool.join()
# results = list(map(handle, sdpDataFilenames))
