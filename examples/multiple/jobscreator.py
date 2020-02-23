import shutil
import os.path
import sys
sys.path.insert(0, '../../')
import sdpdatafile

def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step


def clone(sdpdata, newfilename, updatedict):
    shutil.copyfile(sdpdata.filename, newfilename)
    newsdpdata = sdpdatafile.SdpDataFileWriter(newfilename)
    newsdpdata.updatefile(updatedict)

sdpdata = sdpdatafile.SdpDataFile('multiple.xmlt')
h1list = frange(0.1, 1.1, 0.3)

for it, h1 in enumerate(h1list):
    f, e = os.path.splitext(sdpdata.filename)
    newfilename = f + '_' + str(it) + '.xml'
    sf, se = os.path.splitext(sdpdata.dict['sdpFileData']['filename'])
    newsdpbfilename = sf + '_' + str(it) + '.xml'
    clone(sdpdata,
          newfilename,
          {'sdpFileData': {'h1': str(h1), 'filename': newsdpbfilename}})
