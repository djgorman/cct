from common.abstractdevices.script_scanner.scan_methods import experiment
from common.okfpgaservers.pulser.pulse_sequences.pulse_sequence import pulse_sequence
from cct.scripts.PulseSequences.subsequences.StateReadout import state_readout
from cct.scripts.PulseSequences.subsequences.TurnOffAll import turn_off_all
import numpy as np
from ion_state_detector_1d import ion_state_detector
#from ion_state_detector_1d import ion_state_detector
from labrad.units import WithUnit
import labrad
import IPython as ip
import pylab

class detect_ion_spacing(experiment):
    
    name = 'Detect Ion Spacing'

    required_parameters = [
        #('IonsOnCamera','ion_number'),
        #('IonsOnCamera','ion_positions'), #TODO ?? FIXME
        ('IonsOnCamera','reference_exposure_factor'),
        
        ('IonsOnCamera','vertical_min'),
        ('IonsOnCamera','vertical_max'),
        ('IonsOnCamera','vertical_bin'),
        
        ('IonsOnCamera','horizontal_min'),
        ('IonsOnCamera','horizontal_max'),
        ('IonsOnCamera','horizontal_bin'),
        
        ('StateReadout','state_readout_duration'),
        ('StateReadout','repeat_each_measurement'),
        ('StateReadout','state_readout_amplitude_397'),
        ('StateReadout','state_readout_frequency_397'),
        ('StateReadout','state_readout_frequency_397_2'),
        ('StateReadout','state_readout_amplitude_397_2'),
        ('StateReadout','state_readout_amplitude_866'),
        ('StateReadout','state_readout_frequency_866'),
        ('StateReadout','camera_trigger_width'),
        ('StateReadout','camera_transfer_additional'),
        
        ('DopplerCooling','doppler_cooling_repump_additional'),
        ]

    @classmethod
    def all_required_parameters(cls):
        parameters = set(cls.required_parameters)
        parameters = list(parameters)
        return parameters
    
    def initialize(self, cxn, context, ident):
        p = self.parameters.IonsOnCamera
        #print int(p.ion_number)
        self.cxncam = labrad.connect('192.168.169.30')
        #self.fitter = ion_state_detector([])
        self.ident = ident
        self.camera = self.cxncam.andor_server
        self.pulser = cxn.pulser
        self.pv = cxn.parametervault

        self.image_region = image_region = [
                             int(p.horizontal_bin),
                             int(p.vertical_bin),
                             int(p.horizontal_min),
                             int(p.horizontal_max),
                             int(p.vertical_min),
                             int(p.vertical_max),
                             ]
        self.camera.abort_acquisition()
        self.initial_exposure = self.camera.get_exposure_time()
        self.camera.set_exposure_time(self.parameters.StateReadout.state_readout_duration)
        self.initial_region = self.camera.get_image_region()
        self.initial_mode = self.camera.get_acquisition_mode()
        self.initial_trigger_mode = self.camera.get_trigger_mode()
        
        self.camera.set_acquisition_mode('Kinetics')
        self.camera.set_image_region(*image_region)
        self.camera.set_trigger_mode('External')
        #self.camera.set_trigger_mode
        self.exposures = int(p.reference_exposure_factor) * int(self.parameters.StateReadout.repeat_each_measurement)
        self.camera.set_number_kinetics(self.exposures)
        #generate the pulse sequence
        self.parameters.StateReadout.use_camera_for_readout = True
        start_time = WithUnit(20, 'ms') #do nothing in the beginning to let the camera transfer each image
        self.sequence = pulse_sequence(self.parameters, start = start_time)
        self.sequence.required_subsequences = [state_readout, turn_off_all]
        self.sequence.addSequence(turn_off_all)
        self.sequence.addSequence(state_readout)
        
    def run(self, cxn, context):
        self.camera.start_acquisition()
        self.sequence.programSequence(self.pulser)
        self.pulser.start_number(self.exposures)
        self.pulser.wait_sequence_done()
        self.pulser.stop_sequence()
        proceed = self.camera.wait_for_kinetic()
        if not proceed:
            self.camera.abort_acquisition()
            self.finalize(cxn, context)
            raise Exception ("Did not get all kinetic images from camera")
        images = self.camera.get_acquired_data(self.exposures).asarray
        print images.shape
        x_pixels = int( (self.image_region[3] - self.image_region[2] + 1.) / (self.image_region[0]) )
        y_pixels = int(self.image_region[5] - self.image_region[4] + 1.) / (self.image_region[1])
        images = np.reshape(images, (self.exposures, y_pixels, x_pixels))
        image  = np.average(images, axis = 0)
       
        ########## Remove the high intensity line:
        for i in range(image.shape[0]): image[i][-1] = image[i][-2]
        #########################################

        #ip.embed()
        np.save('37ions_global', image)
        self.fit_and_plot(image)

    def fit_and_plot(self, image):
        print "fit and plot"
        p = self.parameters.IonsOnCamera
        x_axis = np.arange(p.horizontal_min, p.horizontal_max + 1, self.image_region[0])
        y_axis = np.arange(p.vertical_min, p.vertical_max + 1, self.image_region[1])
        xx, yy = np.meshgrid(x_axis, y_axis)
        #import IPython
        #IPython.embed()

        #self.fitter.report(params)
        #ideally graphing should be done by saving to data vault and using the grapher
        #p = Process(target = self.fitter.graph, args = (x_axis, y_axis, image, params, result))
        #p.start()
        pylab.figure()
        pylab.imshow(image)
        pylab.show()
        pylab.figure()
        img_1d = np.sum(image, axis=0)
        pylab.plot(img_1d)
        threshold = pylab.ginput(0)
        threshold = threshold[0][1]
        print threshold

        ion_edges = self.isolate_ions(img_1d, threshold)
        centers = self.fit_individual_ions(img_1d, ion_edges)

        deltax = []
        for i, x in enumerate(ion_edges):
            try: deltax.append( centers[i+1] - centers[i] )
            except: pass
        pylab.figure()
        pylab.plot(deltax, 'o')
        pylab.show()

    def isolate_ions(self, img_1d, threshold):
        current_state = 'off_ion'
        ion_edges = []
        for psn, x in enumerate(img_1d):
            if current_state == 'off_ion' and x > threshold: # rising edge
                rising_edge = psn -2
                current_state = 'on_ion'
            elif current_state == 'on_ion' and x < threshold: # falling edge
                falling_edge = psn + 2
                current_state = 'off_ion'
                ion_edges.append((rising_edge, falling_edge))
            else:
                pass
        return ion_edges

    def fit_individual_ions(self, img_1d, ion_edges):
        from lmfit.models1d import  GaussianModel
        centers = []
        for i, (xmin, xmax) in enumerate(ion_edges):
            model = GaussianModel()
            x = np.arange(xmin, xmax, 1)
            y = img_1d[xmin:xmax]
            model.guess_starting_values(y, x=x)
            init_fit = model.model(x=x)
            model.fit(y, x=x)
            final_fit = model.model(x=x)
            centers.append(model.params['center'].value)
        return centers
    def finalize(self, cxn, context):
        self.camera.set_trigger_mode(self.initial_trigger_mode)
        self.camera.set_acquisition_mode(self.initial_mode)
        self.camera.set_exposure_time(self.initial_exposure)
        self.camera.set_image_region(self.initial_region)
        self.camera.start_live_display()
        self.cxncam.disconnect()

if __name__ == '__main__':
    import labrad
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = detect_ion_spacing(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)
