import numpy as np

def generate_wavefunc(coupling_strength, detuning, Npoints=1000):
    """Creates a sine multiplied by a Gaussian given the parameters

    coupling_strength: in Hz
    detuning: in Hz
    Npoints=1000
    """
    coupling_strength = float(coupling_strength)
    swap_time = 1/(2.*coupling_strength)/np.sqrt(2*np.pi)
    detuning = float(detuning)
    exp_corr = 6 #Correction to keep the area constant
    t = np.linspace(0,swap_time * exp_corr,Npoints) - swap_time/2*exp_corr
    y = np.exp(-t**2/(swap_time**2))*np.sin(detuning*2*np.pi*t)
    return t,y, 2*max(t)

def generate_wavefunc_blackman(coupling_strength, detuning, Npoints=1000):
    """Creates a sine multiplied by a Gaussian given the parameters

    coupling_strength: in Hz
    detuning: in Hz
    Npoints=1000
    """
    coupling_strength = float(coupling_strength)
    swap_time = 1/(2*coupling_strength)
    detuning = float(detuning)
    exp_corr = 1/.42 #Correction to keep the area constant
    t = np.linspace(0,swap_time * exp_corr,Npoints)# - swap_time/2*exp_corr
    t0 = swap_time * exp_corr
    alph = .16
    a = [(1-alph)/2.0, 1/2., alph/2.]
    y_blackman = a[0] - a[1] * np.cos(2*np.pi*t/t0) +  a[2] * np.cos(4*np.pi*t/t0) 
    y = y_blackman *np.sin(detuning*2*np.pi*t)
    print max(t)
    return t,y, max(t)
            
def to_str(y):
    s1 = ''
    for i in y:
        s1 += str(i) +', '
    return s1.strip(', ')

def write_to_agilent(coupling_strength,detuning,amplitude,Npoints=10000, is_black=True):
    """Writes the wavefunction directly to the generator
    coupling_strength in Hz
    detuning in Hz
    amplitude in dBm
    """
    if is_black:
        t,y,duration = generate_wavefunc_blackman(coupling_strength,detuning,Npoints)
    else:
        t,y,duration = generate_wavefunc(coupling_strength,detuning,Npoints)
    s1 = to_str(y)
    freq = 1/duration
    import labrad
    from labrad.units import WithUnit
    cxn = labrad.connect('192.168.169.30')
    a = cxn.agilent_server
    a.select_device()
    a.output(False)
    a.arbitrary_waveform2(s1)
    a.output(True)
    a.amplitude(WithUnit(amplitude,'dBm'))
    a.frequency(WithUnit(freq,'Hz'))
    print freq

def write_to_rigol(coupling_strength,detuning,amplitude1,amplitude2,Npoints=100000, is_black=True):
    """Writes the wavefunction directly to the generator
    coupling_strength in Hz
    detuning in Hz
    amplitude in dBm
    """
    if is_black:
        t,y,duration = generate_wavefunc_blackman(coupling_strength,detuning,Npoints)
    else:
        t,y,duration = generate_wavefunc(coupling_strength,detuning,Npoints)
    s1 = to_str(y)
    freq = 1/duration
    import labrad
    from labrad.units import WithUnit
    cxn = labrad.connect('192.168.169.30')
    a = cxn.rigol_dg4062_server
    a.select_device()
    #Set channel 1
    a.burst_state(True,1)
    a.arbitrary_waveform(s1,1)
    a.voltage(WithUnit(amplitude1,'V'),1)
    a.frequency(WithUnit(freq,'Hz'),1)

    #Set channel 2
    a.burst_state(True,2)
    a.arbitrary_waveform(s1,2)
    a.frequency(WithUnit(freq,'Hz'),2)
    a.voltage(WithUnit(amplitude2,'V'),2)
    a.burst_state(True,2)
    a.burst_state(True,1)
    print freq


if __name__ == "__main__":
    t,y,duration = generate_wavefunc(8e3, 133e3)
    freq= 1/duration
    coupling_strength = 5.e3
    detuning = 1.695e6
    amplitude = 13
    amplitude2 = 1.0
#    write_to_rigol(coupling_strength,detuning,amplitude,amplitude2)
    write_to_agilent(coupling_strength,detuning,amplitude,is_black=True,Npoints=50000)
