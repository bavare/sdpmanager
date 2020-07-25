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

def inlineprint(expr):
    print(expr, end=' ', flush=True)

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
        inlineprint('all done.')
    elif status is None or status == 'tosubmit':
        inlineprint('submitting...')
        submit(sdpdata)
        handle(filename)
    elif status == 'failed':
        if args.force:
            inlineprint('failed; forced resubmission...')
            submit(sdpdata)
            handle(filename)
        else:
            inlineprint('failed.')
    elif status == 'submitted' or status == 'running':
        inlineprint('submitted.')
        if args.reallyrunning:
            inlineprint('checking...')
            submissionid = log.lastbonusexprwith(expr='submissionid')
            if world.isreallyrunning(submissionid):
                inlineprint('is really running.')
            else:
                inlineprint('is NOT really running:')
                logw.setstatus('failed')
                handle(filename)
        if args.pause:
            inlineprint('waiting for completion...')
            submissionid = log.lastbonusexprwith(expr='submissionid')
            world.waitforcompletion(submissionid)
            inlineprint('completed.')
            handle(filename)
    elif status == 'finished':
        tr = log.lastbonusexprwith(expr='terminateReason')
        primopt = log.lastbonusexprwith(expr='primalObjective')
        if tr == 'maxRuntime exceeded' or \
                tr == 'maxIterations exceeded':
            inlineprint('ran out of time.')
            if args.maxsubmissions and \
                    log.numlineswith(expr='status', bonusexpr='submitted') >= \
                    args.maxsubmissions:
                inlineprint('too many submissions to resubmit.')
                logw.write('too many submissions.')
                logw.setstatus('failed')
                handle(filename)
            else:
                inlineprint('resubmitting... ')
                submit(sdpdata)
                handle(filename)
        else:  # i.e. terminateReason is not timed out
            try:
                newfilename = analyzer.analyze(sdpdata, tr, primopt)
            except ValueError:
                logw.write('analyzer failed with ValueError')
                logw.setstatus('failed')
                inlineprint('could not analyze the result.')
                handle(filename)
            else:
                logw.setstatus('concluded')
                if newfilename is None:
                    inlineprint('done.')
                elif newfilename == filename:
                    inlineprint('resubmitting according to analyzer...')
                    logw.setstatus('tosubmit')
                    handle(filename)
                else:
                    print('replaced -->')
                    inlineprint(os.path.basename(newfilename) + ' :')
                    logw.write('replaced with', newfilename)
                    handle(newfilename)
    else:
        # How did you get here?
        print('Unknown status for ' + filename + '!')


# Parallel version:
# pool = ThreadPool(len(sdpDataFilenames))
# results = pool.map(handle, sdpDataFilenames)
# pool.close()
# pool.join()

for sdpDataFilename in sdpDataFilenames:
    inlineprint(os.path.basename(sdpDataFilename) + ' :')
    handle(sdpDataFilename)
    print()
