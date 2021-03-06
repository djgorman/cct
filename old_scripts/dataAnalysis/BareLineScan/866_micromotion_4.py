from __future__ import division
import numpy as np
from matplotlib import pyplot
from scipy import linalg
from scipy import special as bessel
import labrad
import lmfit


def micro_model(params, x):
    beta = params['beta'].value
    Omega= params['Omega'].value
    B = params['B'].value
    gamma=params['gamma'].value
    amplitude=params['amplitude'].value
    offset=params['offset'].value
    center=params['center'].value
    x = x-center
    flour = np.zeros_like(x)
    
    for n in np.arange(-50,51,1):
        flour_temp1 = bessel.jv(n,beta)**2/((x+n*Omega-14.0*B/10.0)**2+(gamma/2.0)**2)
        flour_temp2 = bessel.jv(n,beta)**2/((x+n*Omega-6.0*B/10.0)**2+(gamma/2.0)**2)
        flour_temp3 = bessel.jv(n,beta)**2/((x+n*Omega-2.0*B/10.0)**2+(gamma/2.0)**2)
        flour_temp4 = bessel.jv(n,beta)**2/((x+n*Omega+2.0*B/10.0)**2+(gamma/2.0)**2)
        flour_temp5 = bessel.jv(n,beta)**2/((x+n*Omega+6.0*B/10.0)**2+(gamma/2.0)**2)
        flour_temp6 = bessel.jv(n,beta)**2/((x+n*Omega+14.0*B/10.0)**2+(gamma/2.0)**2)
        flour = flour+amplitude*(flour_temp1+flour_temp2+flour_temp3+flour_temp4+flour_temp5+flour_temp6)/6.0+offset
    return flour
'''
define how to compare data to the function
'''
def micro_fit(params , x, data, err):
    model = micro_model(params, x)
    return (model - data)/err

cxn = labrad.connect('192.168.169.197')
dv = cxn.data_vault
dv.cd('','Experiments','BareLineScanRed','2013Nov16','1812_09')
dv.open(3)
data1=dv.get().asarray

data1_x = data1[:,0]
data1_yerr = np.sqrt(data1[:,1])/35.0
data1_y = data1[:,1]/35.0

data1_y = data1_y[:-3]
data1_yerr = data1_yerr[:-3]
data1_x = data1_x[:-3]



data_x = data1_x*2.0
data_y = data1_y
data_yerr = data1_yerr



#pyplot.plot(data1_x,data1_y)
#pyplot.plot(data2_x,data2_y)
#pyplot.plot(data_x,data_y)


params = lmfit.Parameters()
params.add('amplitude', value = 6700)
params.add('gamma', value = 22.4, vary = True)
params.add('offset', value = 0.104)
params.add('beta', value = 0.02, min=0.01)
params.add('Omega', value = 30.704, vary = False)
params.add('B', value = 0.8*1.4, vary= False)
params.add('center', value = 160)


result = lmfit.minimize(micro_fit, params, args = (data_x, data_y, data1_yerr))

fit_values  = data_y + result.residual

lmfit.report_errors(params)

lmfit.report_fit(params)

normalization = 1.15*params['amplitude']/(params['gamma']/2.0)**2


pyplot.plot(np.arange(110,250,0.1)-params['center'],micro_model(params,np.arange(110,250,0.1))/normalization,linewidth=1.5)
pyplot.errorbar(data_x-params['center'],data_y/normalization,data_yerr/normalization,linestyle='None',markersize = 4.0,fmt='o',color='black')
pyplot.axis([-60,60,0.1,1.0])
pyplot.show()