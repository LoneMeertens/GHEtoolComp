from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import warnings

from typing import Tuple, TYPE_CHECKING

from GHEtool.VariableClasses.LoadData._LoadData import _LoadData
from GHEtool.logger import ghe_logger

if TYPE_CHECKING:
    from numpy.typing import ArrayLike


class HourlyGeothermalLoad(_LoadData):
    """
    This class contains all the information for geothermal load data with a monthly resolution and absolute input.
    This means that the inputs are both in kWh/month and kW/month.
    """

    __slots__ = tuple(_LoadData.__slots__) + ("_heating_load", "_cooling_load")

    def __init__(self, heating_load: ArrayLike = None,
                 cooling_load: ArrayLike = None,
                 simulation_period: int = 20,
                 dhw: float = 0.):
        """

        Parameters
        ----------
        heating_load : np.ndarray, list, tuple
            Heating load [kWh/h]
        cooling_load : np.ndarray, list, tuple
            Cooling load [kWh/h]
        simulation_period : int
            Length of the simulation period in years
        dhw : float
            Yearly consumption of domestic hot water [kWh/year]
        """

        super().__init__(hourly_resolution=True, simulation_period=simulation_period)

        # initiate variables
        self._hourly_heating_load: np.ndarray = np.zeros(8760)
        self._hourly_cooling_load: np.ndarray = np.zeros(8760)

        # set variables
        self.hourly_heating_load: np.ndarray = np.zeros(8760) if heating_load is None else np.array(heating_load)
        self.hourly_cooling_load: np.ndarray = np.zeros(8760) if cooling_load is None else np.array(cooling_load)
        self.dhw = dhw

    def _check_input(self, load_array: ArrayLike) -> bool:
        """
        This function checks whether the input is valid or not.
        The input is correct if and only if:
        1) the input is a np.ndarray, list or tuple
        2) the length of the input is 8760
        3) the input does not contain any negative values.

        Parameters
        ----------
        load_array : np.ndarray, list or tuple

        Returns
        -------
        bool
            True if the inputs are valid
        """
        if not isinstance(load_array, (np.ndarray, list, tuple)):
            ghe_logger.error("The load should be of type np.ndarray, list or tuple.")
            return False
        if not len(load_array) == 8760:
            ghe_logger.error("The length of the load should be 8760.")
            return False
        if np.min(load_array) < 0:
            ghe_logger.error("No value in the load can be smaller than zero.")
            return False
        return True

    @property
    def hourly_heating_load(self) -> np.ndarray:
        """
        This function returns the hourly heating load in kWh/h including DHW.

        Returns
        -------
        hourly heating : np.ndarray
            Hourly heating values (incl. DHW) [kWh/h] for one year, so the length of the array is 8760
        """
        return self.correct_for_start_month(self._hourly_heating_load + self.dhw / 8760)

    @hourly_heating_load.setter
    def hourly_heating_load(self, load: ArrayLike) -> None:
        """
        This function sets the hourly heating load [kWh/h] after it has been checked.

        Parameters
        ----------
        load : np.ndarray, list or tuple
            Hourly heating [kWh/h]

        Returns
        -------
        None

        Raises
        ------
        ValueError
            When either the length is not 8760, the input is not of the correct type, or it contains negative
            values
        """
        if self._check_input(load):
            self._hourly_heating_load = load
            return
        raise ValueError

    def set_hourly_heating(self, load: ArrayLike) -> None:
        """
        This function sets the hourly heating load [kWh/h] after it has been checked.

        Parameters
        ----------
        load : np.ndarray, list or tuple
            Hourly heating [kWh/h]

        Returns
        -------
        None

        Raises
        ------
        ValueError
            When either the length is not 8760, the input is not of the correct type, or it contains negative
            values
        """
        self.hourly_heating_load = load

    @property
    def hourly_cooling_load(self) -> np.ndarray:
        """
        This function returns the hourly cooling load in kWh/h.

        Returns
        -------
        hourly cooling : np.ndarray
            Hourly cooling values [kWh/h] for one year, so the length of the array is 8760
        """
        return self.correct_for_start_month(self._hourly_cooling_load)

    @hourly_cooling_load.setter
    def hourly_cooling_load(self, load: ArrayLike) -> None:
        """
        This function sets the hourly cooling load [kWh/h] after it has been checked.

        Parameters
        ----------
        load : np.ndarray, list or tuple
            Hourly cooling [kWh/h]

        Returns
        -------
        None

        Raises
        ------
        ValueError
            When either the length is not 8760, the input is not of the correct type, or it contains negative
            values
        """
        if self._check_input(load):
            self._hourly_cooling_load = load
            return
        raise ValueError

    def set_hourly_cooling(self, load: ArrayLike) -> None:
        """
        This function sets the hourly cooling load [kWh/h] after it has been checked.

        Parameters
        ----------
        load : np.ndarray, list or tuple
            Hourly cooling [kWh/h]

        Returns
        -------
        None

        Raises
        ------
        ValueError
            When either the length is not 8760, the input is not of the correct type, or it contains negative
            values
        """
        self.hourly_cooling_load = load

    @property
    def imbalance(self) -> float:
        """
        This function calculates the ground imbalance.
        A positive imbalance means that the field is injection dominated, i.e. it heats up every year.

        Returns
        -------
        imbalance : float
        """
        return np.sum(self.hourly_cooling_load - self.hourly_heating_load)

    def resample_to_monthly(self, hourly_load: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        This function resamples an hourly_load to monthly peaks (kW/month) and baseloads (kWh/month).

        Parameters
        ----------
        hourly_load : np.ndarray
            Hourly loads in kWh/h

        Returns
        -------
        peak loads [kW], monthly average loads [kWh/month] : np.ndarray, np.ndarray
        """
        data = np.array_split(hourly_load, np.cumsum(self.UPM)[:-1])

        if self.all_months_equal:
            return np.max(data, axis=1), np.sum(data, axis=1)

        return np.array([np.max(i) for i in data]), np.array([np.sum(i) for i in data])

    @property
    def baseload_cooling(self) -> np.ndarray:
        """
        This function returns the baseload cooling in kWh/month.

        Returns
        -------
        baseload cooling : np.ndarray
            Baseload cooling values [kWh/month] for one year, so the length of the array is 12
        """
        return self.resample_to_monthly(self.hourly_cooling_load)[1]

    @property
    def baseload_heating(self) -> np.ndarray:
        """
        This function returns the baseload heating in kWh/month.

        Returns
        -------
        baseload heating : np.ndarray
            Baseload heating values [kWh/month] for one year, so the length of the array is 12
        """
        return self.resample_to_monthly(self.hourly_heating_load)[1]

    @property
    def peak_cooling(self) -> np.ndarray:
        """
        This function returns the peak cooling load in kW/month.

        Returns
        -------
        peak cooling : np.ndarray
            Peak cooling values for one year, so the length of the array is 12
        """
        return self.resample_to_monthly(self.hourly_cooling_load)[0]

    @property
    def peak_heating(self) -> np.ndarray:
        """
        This function returns the peak heating load in kW/month.

        Returns
        -------
        peak heating : np.ndarray
            Peak heating values for one year, so the length of the array is 12
        """
        return self.resample_to_monthly(self.hourly_heating_load)[0]

    @property
    def hourly_cooling_load_simulation_period(self) -> np.ndarray:
        """
        This function returns the hourly cooling in kWh/h for a whole simulation period.

        Returns
        -------
        hourly cooling : np.ndarray
            hourly cooling for the whole simulation period
        """
        return np.tile(self.hourly_cooling_load, self.simulation_period)

    @property
    def hourly_load_simulation_period(self) -> np.ndarray:
        """
        This function calculates the resulting hourly load in kW for the whole simulation period.

        Returns
        -------
        resulting hourly load : np.ndarray
        """
        return self.hourly_cooling_load_simulation_period - self.hourly_heating_load_simulation_period

    @property
    def hourly_heating_load_simulation_period(self) -> np.ndarray:
        """
        This function returns the hourly heating in kWh/h for a whole simulation period.

        Returns
        -------
        hourly heating : np.ndarray
            hourly heating for the whole simulation period
        """
        return np.tile(self.hourly_heating_load, self.simulation_period)

    def load_hourly_profile(
        self, file_path: str, header: bool = True, separator: str = ";", decimal_seperator: str = ".", col_heating: int = 0, col_cooling: int = 1
    ) -> None:
        """
        This function loads in an hourly load profile [kW].

        Parameters
        ----------
        file_path : str
            Path to the hourly load file
        header : bool
            True if this file contains a header row
        separator : str
            Symbol used in the file to separate the columns
        decimal_seperator : str
            Symbol used for the decimal number separation
        col_heating : int
            Column index for heating
        col_cooling : int
            Column index for cooling

        Returns
        -------
        None
        """
        if header:
            header: int = 0
        else:
            header = None

        # TODO implement single column
        # if col_heating == col_cooling:
        #     ghe_logger.info('Only one column with data selected. Load will be splitted into heating and cooling load.')

        # import data
        df = pd.read_csv(file_path, sep=separator, header=header, decimal=decimal_seperator)

        # set data
        self.hourly_heating_load = np.array(df.iloc[:, col_heating])
        self.hourly_cooling_load = np.array(df.iloc[:, col_cooling])

        ghe_logger.info("Hourly profile loaded!")

    def __eq__(self, other) -> bool:
        if not isinstance(other, HourlyGeothermalLoad):
            return False
        if not np.array_equal(self.hourly_cooling_load, other.hourly_cooling_load):
            return False
        if not np.array_equal(self.hourly_heating_load, other.hourly_heating_load):
            return False
        if not self.simulation_period == other.simulation_period:
            return False
        return True

    def __add__(self, other):
        if isinstance(other, HourlyGeothermalLoad):
            if self.simulation_period != other.simulation_period:
                warnings.warn(
                    f"The simulation period for both load classes are different. "
                    f"The maximum simulation period of "
                    f"{max(self.simulation_period, other.simulation_period)} years will be taken."
                )
            return HourlyGeothermalLoad(
                self._hourly_heating_load + other._hourly_heating_load,
                self._hourly_cooling_load + other._hourly_cooling_load,
                max(self.simulation_period, other.simulation_period),
                self.dhw + other.dhw,
            )

        try:
            return other.__add__(self)
        except TypeError:  # pragma: no cover
            raise TypeError("Cannot perform addition. Please check if you use correct classes.")  # pragma: no cover

    @property
    def _start_hour(self) -> int:
        """
        This function returns the hour at which the year starts based on the start month.

        Returns
        -------
        int
            Start hour of the year
        """
        return int(np.sum([self.UPM[i] for i in range(self.start_month - 1)]))

    def correct_for_start_month(self, array: np.ndarray) -> np.ndarray:
        """
        This function corrects the load for the correct start month.
        If the simulation starts in september, the start month is 9 and hence the array should start
        at index 9.

        Parameters
        ----------
        array : np.ndarray
            Load array

        Returns
        -------
        load : np.ndarray
        """
        if self.start_month == 1:
            return array
        return np.concatenate((array[self._start_hour :], array[: self._start_hour]))

    def plot_load_duration(self, legend: bool = False) -> Tuple[plt.Figure, plt.Axes]:
        """
        This function makes a load-duration curve from the hourly values.

        Parameters
        ----------
        legend : bool
            True if the figure should have a legend

        Returns
        ----------
        Tuple
            plt.Figure, plt.Axes
        """
        # sort heating and cooling load
        heating = self.hourly_heating_load.copy()
        heating[::-1].sort()

        cooling = self.hourly_cooling_load.copy()
        cooling[::-1].sort()
        cooling = cooling * (-1)
        # create new figure and axes if it not already exits otherwise clear it.
        fig = plt.figure()
        ax = fig.add_subplot(111)
        # add sorted loads to plot
        ax.step(np.arange(0, 8760, 1), heating, "r-", label="Heating")
        ax.step(np.arange(0, 8760, 1), cooling, "b-", label="Cooling")
        # create 0 line
        ax.hlines(0, 0, 8759, color="black")
        # add labels
        ax.set_xlabel("Time [hours]")
        ax.set_ylabel("Power [kW]")
        # set x limits to 8760
        ax.set_xlim(0, 8760)
        # plot legend if wanted
        if legend:
            ax.legend()  #
        plt.show()
        return fig, ax
