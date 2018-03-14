import subprocess as sp
import manyworlds


class LocalWorld(manyworlds.World):
    sdpfilecreator = '/Users/vanrees/.local/bin/qftinads-exe'
    sdpb = '/Users/vanrees/sdpb/sdpb-master/sdpb'

    def submit(self, sdpdata, options=None):
        sp.check_call(['/Users/vanrees/python_games/cluster/gradstudent.py',
                       '-w', 'local', sdpdata.filename])
        return -1
