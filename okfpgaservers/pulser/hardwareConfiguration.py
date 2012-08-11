class channelConfiguration(object):
    """
    Stores complete configuration for each of the channels
    """
    def __init__(self, channelNumber, ismanual, manualstate,  manualinversion, autoinversion):
        self.channelnumber = channelNumber
        self.ismanual = ismanual
        self.manualstate = manualstate
        self.manualinv = manualinversion
        self.autoinv = autoinversion
        
class ddsConfiguration(object):
    """
    Stores complete configuration of each DDS board
    """
    def __init__(self, address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
        self.channelnumber = address
        self.allowedfreqrange = allowedfreqrange
        self.allowedamplrange = allowedamplrange
        self.frequency = frequency
        self.amplitude = amplitude
        self.state = True
        self.boardfreqrange = args.get('boardfreqrange', (0.0, 800.0))
        self.boardamplrange = args.get('boardamplrange', (-63.0, -3.0))
        self.boardphaserange = args.get('boardphaserange', (0.0, 360.0))
        self.off_parameters = args.get('off_parameters', (0.0, -63.0))
        self.remote = args.get('remote', False)        

class remoteChannel(object):
    def __init__(self, ip, server, reset, program):
        self.ip = ip
        self.server = server
        self.reset = reset
        self.program = program
        
class hardwareConfiguration(object):
    channelTotal = 32
    timeResolution = 40.0e-9 #seconds
    timeResolvedResolution = timeResolution/4.0
    maxSwitches = 1022
    isProgrammed = False
    sequenceType = None #none for not programmed, can be 'one' or 'infinite'
    collectionMode = 'Normal' #default PMT mode
    collectionTime = {'Normal':0.100,'Differential':0.100} #default counting rates
    okDeviceID = 'Pulser'
    okDeviceFile = 'photon.bit'
    
    #name: (channelNumber, ismanual, manualstate,  manualinversion, autoinversion)
    channelDict = {
		    '866':channelConfiguration(0, True, True, False, False),
		   'bluePI':channelConfiguration(1, True, True, False, False),
                   #'rst':channelConfiguration(2, False, False, False, False),
                   #'dat':channelConfiguration(3, False, False, False, True),
                   #'clk':channelConfiguration(4, False, False, False, True),
                   #'RST':channelConfiguration(5, False, False, False, False),
                   #'DAT':channelConfiguration(6, False, False, False, True),
                   #'CLK':channelConfiguration(7, False, False, False, True),
                   #------------INTERNAL CHANNELS----------------------------------------#
                   'DiffCountTrigger':channelConfiguration(16, False, False, False, False),
                   'TimeResolvedCount':channelConfiguration(17, False, False, False, False),
                   'AdvanceDDS':channelConfiguration(18, False, False, False, False),
                   'ResetDDS':channelConfiguration(19, False, False, False, False)
                   }
    
    ddsDict = {
               '866DP':ddsConfiguration(3, (30.0,130.0),  (-63.0,-3.0), 80.0, -33.0),
#               '397':ddsConfiguration(2, (170.0,270.0), (190.0,250.0), (-63.0,-3.0), (-63.0,-3.0), 220.0, -33.0),               
               #'729DP':ddsConfiguration(0, (190.0,250.0), (-63.0,-3.0), 220.0, -33.0, remote = 'pulser_729')
               }

    remoteChannels = {}#{ 'pulser_729': remoteChannel('192.168.169.49', 'pulser_729', 'reset_dds','program_dds')}