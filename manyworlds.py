import subprocess as sp
import os


class World:
    sdpfilecreator = 'echo'
    sdpb = 'echo'
    submitter = 'echo'

    def createSdpFiles(self, sdpdata, options=None):
        return sp.run([self.sdpfilecreator, sdpdata.filename],
                      encoding='ascii', check=True)

    def runSdpb(self, sdpdata, options=None):
        return sp.run([self.sdpb] + sdpdata.sdpbargs, stderr=sp.PIPE,
                      encoding='ascii', check=True)

    def submit(self, sdpdata, options=None):
        return sp.run([self.submitter, sdpdata.filename], stderr=sp.PIPE,
                      encoding='ascii', check=True)

    def waitforcompletion(self, sdpdata):
        pass

    def warmup(self, sdpdata):
        pass

    def cooldown(self, sdpdata):
        tr = sdpdata.getlogitem('terminateReason')
        if tr == 'maxRuntime exceeded' or tr == 'maxIterations exceeded':
            pass
        else:
            try:
                list(map(os.remove, sdpdata.xmlfilenames))
                os.remove(sdpdata.checkpointfile)
                os.remove(sdpdata.outfile)
            except FileNotFoundError:
                print('Could not find sdpb files to remove. Oh well.')


def getworld(arg):
    if arg == 'cern':
        import cernworld
        return cernworld.CernWorld()
    elif arg == 'local':
        import localworld
        return localworld.LocalWorld()
    else:
        # default
        return World()
