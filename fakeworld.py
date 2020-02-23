import manyworlds


class FakeWorld(manyworlds.World):

    def submit(self, sdpdata, options=None):
        print('FakeWorld: would have submitted with file ' + sdpdata.filename)
        return '[submissionid: ' + sdpdata.filename + ']'

    def isreallyrunning(self, submissionid):
        print('FakeWorld: would have checked that process ' +
              submissionid + ' was still running.')
        return True

    def waitforcompletion(self, submissionid):
        print('FakeWorld: would have waited for completion of process ' +
              submissionid + ' was still running.')

    def warmup(self, sdpdata, log=None):
        print('FakeWorld: warmup with file ' + sdpdata.filename)

    def cooldown(self, sdpdata, tr, log=None):
        print('FakeWorld: cooldown with file ' + sdpdata.filename)

    def createSdpFiles(self, sdpdata, options=None):
        return print('FakeWorld: would have created sdpfiles for file ' +
                     sdpdata.filename)

    def runSdpb(self, sdpdata, options=None):
        return print('FakeWorld: would have ran sdpb for file ' +
                     sdpdata.filename)
