from fmpy import *

fmu = 'DTMockup.fmu'

dump(fmu)  # get information

result = simulate_fmu(fmu)
from fmpy.util import plot_result  # import the plot function
plot_result(result)                # plot two variables
