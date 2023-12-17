import numpy as np
from typing import Union

from src.digital_twin.battery_models.ecm_components.generic_component import ECMComponent
from src.digital_twin.parameters.variables import Scalar, ParametricFunction, LookupTableFunction


class OCVGenerator(ECMComponent):
    """
    Open Circuit Voltage (OCV) element for Thevenin equivalent circuits.

    Parameters
    ----------

    """
    def __init__(self,
                 name,
                 ocv_potential: Union[Scalar, ParametricFunction, LookupTableFunction],
                 ):
        super().__init__(name, )
        self._ocv_potential = ocv_potential

    @property
    def ocv_potential(self):
        input_vars = {}

        if not isinstance(self._ocv_potential, Scalar):
            try:
                input_vars = {name: getattr(self, name) for name in self._ocv_potential.x_names}
            except:
                raise Exception(
                    "Cannot retrieve required input variables to compute resistance for {}!".format(self.name))

        return self._ocv_potential.get_value(input_vars=input_vars)

    @ocv_potential.setter
    def ocv_potential(self, value: float):
        self._ocv_potential = value

    def compute_v(self):
        """

        """
        v_ocv = 3.43 + 0.68 * self._soc - 0.68 * (self._soc ** 2) + 0.81 * (self._soc ** 3) - 0.31 * np.exp(-46 * self._soc)
        return v_ocv

