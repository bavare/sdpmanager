#!/usr/bin/env python3
import os.path
import mpmath
import argparse
import sdpdatafile
import simplelogger

validtrlist = ['maxComplementarity exceeded',
               'primal feasible jump detected',
               'dual feasible jump detected',
               'found primal feasible solution',
               'found dual feasible solution',
               'found primal-dual optimal solution']


def addcounter(filename):
    filenameroot, filenamext = os.path.splitext(filename)
    filenamebare, maybecounter = os.path.splitext(filenameroot)
    if maybecounter[:6] == '.count':
        counter = '.count' + str(int(maybecounter[6:]) + 1).zfill(3)
        return filenamebare + counter + filenamext
    else:
        return filenamebare + maybecounter + '.count001' + filenamext


def nextinbinarysearch(sdpdata, tr):
    sdpdict = sdpdata.dict
    analyzerdict = sdpdict.get('analyzer')
    oldprimal = mpmath.mpf(analyzerdict.get('primalpt'))
    olddual = mpmath.mpf(analyzerdict.get('dualpt'))
    varname = analyzerdict.get('varname')
    threshold = mpmath.mpf(analyzerdict.get('threshold'))
    varval = mpmath.mpf(sdpdict.get('sdpFileData').get(varname))

    if tr == 'found primal feasible solution' or \
            tr == 'primal feasible jump detected':
        newprimal = varval
        newdual = olddual
    elif tr == 'found dual feasible solution' or \
            tr == 'dual feasible jump detected':
        newprimal = oldprimal
        newdual = varval
    else:
        raise ValueError('not sure what to do with terminateReason: ' + tr)

    newvarval = (newdual + newprimal)/2

    newfilename = addcounter(sdpdata.filename)
    newsdpdataw = sdpdatafile.SdpDataFileWriter(newfilename)
    newsdpdataw.updatefile(sdpdict)
    newsdpdataw.updatefile({'analyzer': {'primalpt': newprimal,
                                         'dualpt': newdual}})
    newsdpdataw.updatefile({'sdpFileData': {varname: newvarval}})

    if abs(newdual - newprimal) <= threshold:
        newsdpdata = sdpdatafile.SdpDataFile(newfilename)
        newlogw = simplelogger.SimpleLogWriter('ana', newsdpdata.logfilename)
        newlogw.write('binary search ended')
        newlogw.setstatus('concluded')
        return None
    else:
        return newfilename


def analyze(sdpdata, tr, primopt):
    """
    Analyzes an xml file and returns a filename with a new sdpb run, or none.
    """
    newfilename = None
    if tr is None:
        raise ValueError('no terminateReason found')
    elif tr not in validtrlist:
        raise ValueError('invalid terminateReason: ' + tr)

    analyzerdict = sdpdata.dict.get('analyzer')

    if analyzerdict is not None:
        if 'binarysearch' in analyzerdict.keys():
                newfilename = nextinbinarysearch(sdpdata, tr)
        elif 'maximumsearch' in analyzerdict.keys():
                raise NotImplementedError("Maximum search not implemented")
        else:
                raise ValueError("Not sure what to analyze here")

    return newfilename


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', metavar='fn', nargs='+',
                        help='a number of sdp data files to analyze')
    args = parser.parse_args()
    sdpDataFilenames = args.filenames
    for filename in sdpDataFilenames:
        sdpdata = sdpdatafile.SdpDataFile(filename)
        log = simplelogger.SimpleLogReader(sdpdata.logfilename)
        tr = log.lastbonusexprwith(expr='terminateReason')
        primopt = log.lastbonusexprwith(expr='primalObjective')
        an = analyze(sdpdata, tr, primopt)
        if an is not None:
            print(an)
