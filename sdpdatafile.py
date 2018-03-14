import os.path
import xml.etree.ElementTree as ET

# usage for logging:
# sdpDataFile.newsubmission()
# sdpDataFile.addtosubmission(tag, value)
# sdpDataFile.log(tag, value)


class SdpDataFile:

    def __init__(self, filename):
        self.filename = os.path.abspath(filename)
        self.xmlfilenames = self.__setxmlfilenames(self._root())
        self.sdpbargs = self.__setsdpbargs(self._root(), self.xmlfilenames)
        self.outfile = self.__setoutfile(self.sdpbargs)
        self.checkpointfile = self.__setcheckpointfile(self.sdpbargs)
        self.backupcheckpointfile = self.checkpointfile + '.bk'

    def _tree(self):
        return ET.parse(self.filename)

    def _root(self):
        return self._tree().getroot()

    def numlogs(self):
        return len(self._root().findall('log'))

    def getdict(self, tag):
        trees = self._root().findall(tag)
        if not trees:
            return {}
        dict = {}
        tree = trees[-1]
        for child in tree:
            dict[child.tag] = child.text
        return dict

    def adddict(self, tag, dict, append=True, overwrite=False):
        with open(self.filename, "r+b") as file:
            maintree = ET.parse(file)
            root = maintree.getroot()
            trees = root.findall(tag)
            tree = None
            if trees and (append or overwrite):
                tree = trees[-1]
            else:
                tree = ET.SubElement(root, tag)
                tree.text = '\n'
                tree.tail = '\n'
            for key, value in dict.items():
                els = tree.findall(key)
                if els and overwrite:
                    el = els[-1]
                else:
                    el = ET.SubElement(tree, key)
                if value:
                    el.text = value
                else:
                    el.text = '\n'
                el.tail = '\n'
            file.seek(0)
            maintree.write(file)
            file.truncate()

    def getlogitem(self, tag):
        lastlog = self.getdict('log')
        return lastlog.get(tag)

    # @staticmethod
    # def subTree(parent, tag, value=''):
    #     if parent:
    #         white = parent[-1].tail
    #         parent[-1].tail += '  '
    #     else:
    #         white = parent.text
    #         parent.text += '  '
    #     el = ET.SubElement(parent, str(tag))
    #     if value:
    #         el.text = str(value)
    #     else:
    #         el.text = white + '  '
    #     print(white.strip('\n') + str(tag) + ': ' + el.text.strip('\n'))
    #     el.tail = white
    #     return el

    # def newlog(self):
    #     self.adddict('log', {})

    def writelog(self, key, value):
        # with open(self.filename, "r+b") as file:
        #     tree = ET.parse(file)
        #     logtreelist = tree.getroot().findall('log')
        #     if logtreelist:
        #         logtree = logtreelist[-1]
        #     else:
        #         logtree = ET.SubElement(tree.getroot(), 'log')
        #         logtree.text = '\n'
        #         logtree.tail = '\n'
        #     el = ET.SubElement(logtree, str(tag))
        #     if value:
        #         el.text = str(value)
        #     el.tail = '\n'
        print('LOG for ' + self.filename + ': ' + key + ' = ' + str(value))
        self.adddict('log', {key: str(value)})

    # def cleanlogs(self):
    #     with open(self.filename, "r+b") as file:
    #         tree = ET.parse(file)
    #         for log in tree.getroot().findall('log'):
    #             tree.getroot().remove(log)
    #         file.seek(0)
    #         tree.write(file)
    #         file.truncate()

    @staticmethod
    def __setxmlfilenames(root):
        xmlfilenames = []
        for child in root.findall('sdpFileData'):
            xmlfilenames.append(child.find('filename').text)
        return xmlfilenames

    @staticmethod
    def __setsdpbargs(root, xmlfilenames):
        sdpbParamsTree = root.find('sdpbParams')
        if sdpbParamsTree is None:
            return None
        arglist = []
        for xmlfilename in xmlfilenames:
            arglist.extend(['--sdpFile', xmlfilename])
        sdpbSettingsWithArg = ['sdpFile',
                               'paramFile',
                               'outFile',
                               'checkpointFile',
                               'precision',
                               'maxThreads',
                               'checkpointInterval',
                               'maxIterations',
                               'maxRuntime',
                               'dualityGapThreshold',
                               'primalErrorThreshold',
                               'dualErrorThreshold',
                               'initialMatrixScalePrimal',
                               'initialMatrixScaleDual',
                               'feasibleCenteringParameter',
                               'infeasibleCenteringParameter',
                               'stepLengthReduction',
                               'choleskyStabilizeThreshold',
                               'maxComplementarity']
        for sdpbSetting in sdpbSettingsWithArg:
            setting = sdpbParamsTree.find(sdpbSetting)
            if setting is not None:
                arglist.extend(['--' + sdpbSetting, setting.text])
        sdpbSettingsWithOutArg = ['findPrimalFeasible',
                                  'findDualFeasible',
                                  'detectPrimalFeasibleJump',
                                  'detectDualFeasibleJump',
                                  'noFinalCheckpoint']
        for sdpbSetting in sdpbSettingsWithOutArg:
            setting = sdpbParamsTree.find(sdpbSetting)
            if setting is not None:
                arglist.extend(['--' + sdpbSetting])
        sdpbSettingString = sdpbParamsTree.find('argString')
        if sdpbSettingString is not None:
            arglist.extend(sdpbSettingString.text.split())
        return arglist

    @staticmethod
    def __setoutfile(args):
        if args is None:
            return None
        for i in range(len(args)):
            if args[i] == '--outFile' or args[i] == '-o':
                return args[i + 1]
        else:
            for i in range(len(args)):
                if args[i] == '--sdpFile' or args[i] == '-s':
                    return os.path.splitext(args[i + 1])[0] + '.out'

    @staticmethod
    def __setcheckpointfile(args):
        if args is None:
            return None
        for i in range(len(args)):
            if args[i] == '--checkpointFile' or args[i] == '-c':
                return args[i + 1]
        else:
            for i in range(len(args)):
                if args[i] == '--sdpFile' or args[i] == '-s':
                    return os.path.splitext(args[i + 1])[0] + '.ck'
