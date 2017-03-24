from common.abstractdevices.script_scanner.scan_methods import experiment
from excitations import excitation_729
from cct.scripts.scriptLibrary.common_methods_729 import common_methods_729 as cm
from cct.scripts.scriptLibrary import dvParameters
import time
import labrad
from labrad.units import WithUnit
from numpy import linspace

class rabi_flopping(experiment):
    
    name = 'RabiFlopping'
    trap_frequencies         = [
                                ('TrapFrequencies','axial_frequency'),
                                ('TrapFrequencies','radial_frequency_1'),
                                ('TrapFrequencies','radial_frequency_2'),
                                ('TrapFrequencies','rf_drive_frequency'),                       
                                ]
    rabi_required_parameters = [
                               ('RabiFlopping','rabi_amplitude_729'),
                               ('RabiFlopping','manual_scan'),
                               ('RabiFlopping','manual_frequency_729'),
                               ('RabiFlopping','line_selection'),
                               ('RabiFlopping','rabi_amplitude_729'),
                               ('RabiFlopping','frequency_selection'),
                               ('RabiFlopping','sideband_selection'),
                               # Beam addressing scan parameters:
                               ('RabiFlopping','beam_to_scan'),
                               ('RabiFlopping','beam_scan_range_x'),
                               ('RabiFlopping','beam_scan_range_y'),
                               ('RabiFlopping','beam_scan_x_step_size'),
                               ('RabiFlopping','beam_scan_y_step_size'),
                               ('RabiFlopping','beam_scan_x_speed'),
                               ('RabiFlopping','beam_scan_y_speed'),
                                ]

    
    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.rabi_required_parameters)
        parameters = parameters.union(set(cls.trap_frequencies))
        parameters = parameters.union(set(excitation_729.all_required_parameters()))
        parameters = list(parameters)
        #removing parameters we'll be overwriting, and they do not need to be loaded
        parameters.remove(('Excitation_729','rabi_excitation_amplitude'))
        parameters.remove(('Excitation_729','rabi_excitation_duration'))
        parameters.remove(('Excitation_729','rabi_excitation_frequency'))
        return parameters
    
    def initialize(self, cxn, context, ident):
        self.ident = ident
        self.excite = self.make_experiment(excitation_729)
        self.excite.initialize(cxn, context, ident)
        self.scan = []
        self.scan_beam_window =  []

        self.amplitude = None
        self.duration = None
        #self.cxnlab = labrad.connect('192.168.169.49') #connection to labwide network
        self.drift_tracker = cxn.sd_tracker
        self.dv = cxn.data_vault
        self.rabi_flop_save_context = cxn.context()
    
    def setup_sequence_parameters(self):
        self.load_frequency()
        flop = self.parameters.RabiFlopping
        self.parameters['Excitation_729.rabi_excitation_amplitude'] = flop.rabi_amplitude_729
        minim,maxim,steps = flop.manual_scan
        minim = minim['us']; maxim = maxim['us']
        self.scan = linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'us') for pt in self.scan]

    def setup_sequence_parameters_edit(self):
        self.load_frequency()
        flop = self.parameters.RabiFlopping
        self.parameters['Excitation_729.rabi_excitation_amplitude'] = flop.rabi_amplitude_729
        minim,maxim,steps = flop.manual_scan
        minim = minim['us']; maxim = maxim['us']
        self.scan = linspace(minim,maxim, steps)
        self.scan = [WithUnit(pt, 'us') for pt in self.scan]


        # Setting up beam addressing scanner parameters:  HOW DO I CREATE AN INTERFACE AS A SUBSET OF A LABRAD SCRIPT? 
        scan_beam_min, scan_beam_max, scan_beam_steps = 
        self.scan_beam_window = linspace(scan_beam_min, scan_beam_max, scan_beam_steps)
        
    def setup_data_vault(self):
        localtime = time.localtime()
        datasetNameAppend = time.strftime("%Y%b%d_%H%M_%S",localtime)
        dirappend = [ time.strftime("%Y%b%d",localtime) ,time.strftime("%H%M_%S", localtime)]
        directory = ['','Experiments']
        directory.extend([self.name])
        directory.extend(dirappend)
        self.dv.cd(directory ,True, context = self.rabi_flop_save_context)
        output_size = self.excite.output_size
        dependants = [('Excitation','Ion {}'.format(ion),'Probability') for ion in range(output_size)]
        self.dv.new('Rabi Flopping {}'.format(datasetNameAppend),[('Excitation', 'us')], dependants , context = self.rabi_flop_save_context)
        self.dv.add_parameter('Window', ['Rabi Flopping'], context = self.rabi_flop_save_context)
        self.dv.add_parameter('plotLive', True, context = self.rabi_flop_save_context)
    
    def load_frequency(self):
        #reloads trap frequencyies and gets the latest information from the drift tracker
        self.reload_some_parameters(self.trap_frequencies) 
        flop = self.parameters.RabiFlopping
        frequency = cm.frequency_from_line_selection(flop.frequency_selection, flop.manual_frequency_729, flop.line_selection, self.drift_tracker)
        trap = self.parameters.TrapFrequencies
        if flop.frequency_selection == 'auto':
            frequency = cm.add_sidebands(frequency, flop.sideband_selection, trap)
        self.parameters['Excitation_729.rabi_excitation_frequency'] = frequency
        
    def run(self, cxn, context):
        self.setup_data_vault()
        self.setup_sequence_parameters()
        for i,duration in enumerate(self.scan):
            should_stop = self.pause_or_stop()
            if should_stop: break
            excitation = self.do_get_excitation(cxn, context, duration)
            if excitation is None: break 
            submission = [duration['us']]
            submission.extend(excitation)
            self.dv.add(submission, context = self.rabi_flop_save_context)
            self.update_progress(i)
    
    def run_edit(self, cxn, context):
        self.setup_data_vault()
        self.setup_sequence_parameters()
        
        for j,position in enumerate(self.scan_beam_window):
            #Move the beam to position:


            for i,duration in enumerate(self.scan):
                should_stop = self.pause_or_stop()
                if should_stop: break
                excitation = self.do_get_excitation(cxn, context, duration)
                if excitation is None: break 
                submission = [duration['us']]
                submission.extend(excitation)
                self.dv.add(submission, context = self.rabi_flop_save_context)
                self.update_progress(i)
        

    def do_get_excitation(self, cxn, context, duration):
        self.load_frequency()
        self.parameters['Excitation_729.rabi_excitation_duration'] = duration
        self.excite.set_parameters(self.parameters)
        excitation, readouts = self.excite.run(cxn, context)
        return excitation
     

    def finalize(self, cxn, context):
        #self.save_parameters(self.dv, cxn, self.cxnlab, self.rabi_flop_save_context)
        self.excite.finalize(cxn, context)

    def update_progress(self, iteration):
        progress = self.min_progress + (self.max_progress - self.min_progress) * float(iteration + 1.0) / len(self.scan)
        self.sc.script_set_progress(self.ident,  progress)

    def save_parameters(self, dv, cxn, cxnlab, context):
        measuredDict = dvParameters.measureParameters(cxn, cxnlab)
        dvParameters.saveParameters(dv, measuredDict, context)
        dvParameters.saveParameters(dv, dict(self.parameters), context)   







if __name__ == '__main__':
    cxn     = labrad.connect()
    scanner = cxn.scriptscanner

    ##### Beam Addressing Scan:
    cxn_apt  =  labrad.connect('192.168.169.30')
    apt  =  cnx_apt.apt_motor_server

    
    devicenames = apt.get_available_devices()
    if devicenames == []: raise Exception("No Devices Found.")



    #####################################

    exprt = rabi_flopping(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)

