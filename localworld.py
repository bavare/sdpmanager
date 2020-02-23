import subprocess as sp
import manyworlds
import psutil
import time


class LocalWorld(manyworlds.World):
    # sdpfilecreator = '/Applications/Mathematica.app/Contents/MacOS/' \
    #                  'MathematicaScript -file ../mathematica/nbevaluator.m'
    sdpfilecreator = '/Users/vanrees/.local/bin/qftinads-exe'
    sdpb = '/Users/vanrees/.local/bin/sdpb'

    def submit(self, sdpdata, options=None):
        # execute in background
        process = sp.Popen(['/Users/vanrees/.local/bin/worker.py',
                            '-w', 'local', sdpdata.filename])
        pid = str(process.pid)
        return pid

    def isreallyrunning(self, submissionid):
        return psutil.pid_exists(int(submissionid))

    def waitforcompletion(self, submissionid):
        while psutil.pid_exists(int(submissionid)):
            # necessary to avoid zombie status
            sp._cleanup()
            time.sleep(1)
