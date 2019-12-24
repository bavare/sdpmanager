#!/usr/bin/env python3

import os.path
import sys
import mpmath
import shutil
import argparse
import sdpdatafile
import simplelogger


def addcounter(filename):
    filenameroot, filenamext = os.path.splitext(filename)
    filenamebare, counter = os.path.splitext(filenameroot)
    if counter:
        counter = '.' + str(int(counter.strip('.')) + 1).zfill(3)
    else:
        counter = '.001'
    return filenamebare + counter + filenamext


def nextwithincreasedprecision(sdpdata):
    prec = sdpdata.getdict('sdpbParams').get('precision')
    if prec is not None:
        newprec = str(mpmath.mpf(prec * 2))
    else:
        newprec = '800'
    newfilename = addcounter(sdpdata.filename)
    shutil.copyfile(sdpdata.filename, newfilename)
    newsdpdata = sdpdatafile.SdpDataFileWriter(newfilename)
    newsdpdata.adddict('sdpbParams',
                       {'precision': newprec},
                       overwrite=True)
    return newfilename


def nextwithmitigatemaxcomp(sdpdata):
    newfilename = addcounter(sdpdata.filename)
    shutil.copyfile(sdpdata.filename, newfilename)
    newsdpdata = sdpdatafile.SdpDataFileWriter(newfilename)
    newsdpdata.update('sdpbParams',
                      {'precision': '2000',
                       'initialMatrixScalePrimal': '1e50',
                       'initialMatrixScaleDual': '1e50',
                       'maxComplementarity': '1e200'},
                       overwrite=True)
    return newfilename


def nextinbinarysearch(sdpdata, tr):
    # todo: create proper copy of tree
    tree = sdpdata._tree()
    root = tree.getroot()
    binsearchdataTree = root.find('binarysearch')
    primal_el = binsearchdataTree.find('primal')
    dual_el = binsearchdataTree.find('dual')
    # update with result
    var = binsearchdataTree.find('varname').text
    for sdpfiledata in root.findall('sdpFileData'):
        current_el = sdpfiledata.find(var)
        if current_el is not None:
            break
    # current_xml =
    current = mpmath.mpf(current_el.text)
    if tr == 'found primal feasible solution':
        primal_el.text = str(current)
    elif tr == 'found dual feasible solution':
        dual_el.text = str(current)
    else:
        return None
    # are we done?
    primal = mpmath.mpf(primal_el.text)
    dual = mpmath.mpf(dual_el.text)
    thr = mpmath.mpf(binsearchdataTree.find('threshold').text)
    if abs(primal - dual) < thr:
        return None
    # build new file
    current_el.text = str((primal + dual) / 2)
    sdpfiledata.find('filename').text = \
        addcounter(sdpfiledata.find('filename').text)
    newfilename = addcounter(sdpdata.filename)
    tree.write(newfilename)
    return newfilename


def analyze(filename):
    sdpdata = sdpdatafile.SdpDataFile(filename)

    if sdpdata.islocked():
        return filename

    if sdpdata.isfinished():
        return None

    log = simplelogger.SimpleLogReader(sdpdata.logfilename)
    tr = log.lastbonusexprwith(expr='terminateReason')

    # no restult - needs to be submitted
    if tr is None:
        return sdpdata.filename

    # analyze the terminateReason
    if tr == 'maxRuntime exceeded' or \
            tr == 'maxIterations exceeded':
        return sdpdata.filename

    newfilename = None
    if tr == 'maxComplementarity exceeded':
        pass
        # newfilename = nextwithmitigatemaxcomp(sdpdata)
    elif tr == 'primal feasible jump detected' or \
            tr == 'dual feasible jump detected':
        newfilename = nextwithincreasedprecision(sdpdata)
    elif tr == 'found primal feasible solution' or \
            tr == 'found dual feasible solution' or \
            tr == 'found primal-dual optimal solution':
        if sdpdata.getdict('binarysearch'):
            newfilename = nextinbinarysearch(sdpdata, tr)
        elif sdpdata.getdict('maximumsearch'):
            raise NotImplementedError("Maximum search not implemented")
    else:
        print('Cannot parse terminateReason in ' + sdpdata.filename + '.',
              file=sys.stderr)
        newfilename = None
    sdpdata.setfinished()
    return newfilename


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', metavar='fn', nargs='+',
                        help='a number of sdp data files to analyze')
    args = parser.parse_args()
    sdpDataFilenames = args.filenames
    for filename in sdpDataFilenames:
        an = analyze(filename)
        if an is not None:
            print(an)
