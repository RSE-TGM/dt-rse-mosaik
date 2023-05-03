import abc
import pint
from typing import Union
from abc import ABCMeta

from src.digital_twin.parameters.data_checker import check_data_unit
from src.digital_twin.parameters.units import Unit


class GenericModel(metaclass=ABCMeta):
    """

    """
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'reset_model') and
                callable(subclass.reset_model) and
                hasattr(subclass, 'init_model') and
                callable(subclass.init_model) and
                hasattr(subclass, 'load_battery_state') and
                callable(subclass.load_battery_state) and
                hasattr(subclass, 'get_final_results') and
                callable(subclass.get_final_results) or
                NotImplemented)

    @abc.abstractmethod
    def reset_model(self):
        raise NotImplementedError

    @abc.abstractmethod
    def init_model(self, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def load_battery_state(self, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def get_final_results(self, **kwargs):
        raise NotImplementedError


class ElectricalModel(GenericModel):
    """

    """
    def __init__(self, units_checker):
        self.units_checker = units_checker

        self._v_load_series = []
        self._i_load_series = []
        self._power_series = []
        # self._times = []

    def reset_model(self):
        pass

    def init_model(self, **kwargs):
        pass

    def load_battery_state(self, temp:float, soc:float, soh:float):
        pass

    def build_components(self, components:dict):
        pass

    def compute_generated_heat(self, k:int):
        pass

    def get_final_results(self, **kwargs):
        pass

    def get_v_load_series(self, k=None):
        """
        Getter of the specific value at step K, if specified, otherwise of the entire collection
        """
        if k is not None:
            assert type(k) == int, \
                "Cannot retrieve load voltage of the electrical model at step K, since it has to be an integer"

            if len(self._v_load_series) > k:
                if not self.units_checker:
                    return self._v_load_series[k]
                else:
                    return self._v_load_series[k].magnitude
            else:
                raise IndexError("Load Voltage V of the electrical model at step K not computed yet")
        return self._v_load_series

    def get_i_load_series(self, k=None):
        """
        Getter of the specific value at step K, if specified, otherwise of the entire collection
        """
        if k is not None:
            assert type(k) == int, \
                "Cannot retrieve load current of the electrical model at step K, since it has to be an integer"

            if len(self._i_load_series) > k:
                if not self.units_checker:
                    return self._i_load_series[k]
                else:
                    return self._i_load_series[k].magnitude
            else:
                raise IndexError("Load Current I of the electrical model at step K not computed yet")
        return self._i_load_series

    def get_power_series(self, k=None):
        """
        Getter of the specific value at step K, if specified, otherwise of the entire collection
        """
        if k is not None:
            assert type(k) == int, \
                "Cannot retrieve power of the electrical model at step K, since it has to be an integer"

            if len(self._power_series) > k:
                if not self.units_checker:
                    return self._power_series[k]
                else:
                    return self._power_series[k].magnitude
            else:
                raise IndexError("Power P of the electrical model at step K not computed yet")
        return self._power_series

    def update_v_load(self, value: Union[float, pint.Quantity]):
        if self.units_checker:
            self._v_load_series.append(check_data_unit(value, Unit.VOLT))
        else:
            self._v_load_series.append(value)

    def update_i_load(self, value: Union[float, pint.Quantity]):
        if self.units_checker:
            self._i_load_series.append(check_data_unit(value, Unit.AMPERE))
        else:
            self._i_load_series.append(value)

    def update_power(self, value: Union[float, pint.Quantity]):
        if self.units_checker:
            self._power_series.append(check_data_unit(value, Unit.WATT))
        else:
            self._power_series.append(value)

    # def update_times(self, value:int):
    #     if self.units_checker:
    #         self._times.append(check_data_unit(value, Unit.SECOND))
    #     else:
    #         self._times.append(value)


class ThermalModel(GenericModel):
    """

    """
    def __init__(self, units_checker):
        self.units_checker = units_checker

        self._temp_series = []
        self._heat_series = []
        # self._times = []

    def reset_model(self):
        pass

    def init_model(self, **kwargs):
        pass

    def load_battery_state(self, **kwargs):
        pass

    def compute_temp(self, **kwargs):
        pass

    def get_final_results(self, **kwargs):
        """
        Returns a dictionary with all final results
        """
        return {'Temperature [C]': self._temp_series,
                'Dissipated Heat [W]': self._heat_series}

    def get_temp_series(self, k=None):
        """
        Getter of the specific value at step K, if specified, otherwise of the entire collection
        """
        if k is not None:
            assert type(k) == int, \
                "Cannot retrieve temperature of thermal model at step K, since it has to be an integer"

            if len(self._temp_series) > k:
                if not self.units_checker:
                    return self._temp_series[k]
                else:
                    return self._temp_series[k].magnitude
            else:
                raise IndexError("Temperature of thermal model at step K not computed yet")
        return self._temp_series

    def get_heat_series(self, k=None):
        """
        Getter of the specific value at step K, if specified, otherwise of the entire collection
        """
        if k is not None:
            assert type(k) == int, \
                "Cannot retrieve dissipated heat of thermal model at step K, since it has to be an integer"

            if len(self._heat_series) > k:
                if not self.units_checker:
                    return self._heat_series[k]
                else:
                    return self._heat_series[k].magnitude
            else:
                raise IndexError("Dissipated heat of thermal model at step K not computed yet")
        return self._heat_series

    def update_temp(self, value: Union[float, pint.Quantity]):
        if self.units_checker:
            self._temp_series.append(check_data_unit(value, Unit.CELSIUS))
        else:
            self._temp_series.append(value)

    def update_heat(self, value: Union[float, pint.Quantity]):
        if self.units_checker:
            self._heat_series.append(check_data_unit(value, Unit.WATT))
        else:
            self._heat_series.append(value)


class DegradationModel(GenericModel):
    """

    """
    def reset_model(self):
        pass

    def init_model(self, **kwargs):
        pass

    def load_battery_state(self, **kwargs):
        pass

    def get_final_results(self, **kwargs):
        pass
