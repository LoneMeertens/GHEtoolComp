"""
This file contains the base class for the load classes.
"""
import abc
from abc import ABC

import numpy as np

from GHEtool.VariableClasses.BaseClass import BaseClass


class _LoadData(BaseClass, ABC):
    """
    This class contains information w.r.t. load data for the borefield sizing.
    """
    __slots__ = "hourly_resolution"

    def __init__(self, hourly_resolution: bool):
        """

        Parameters
        ----------
        hourly_resolution : bool
            True if the load class uses an hourly resolution
        """
        self.hourly_resolution: bool = hourly_resolution

    @abc.abstractmethod
    def _check_input(self, input: np.array | list | tuple) -> bool:
        """
        This function checks whether the input is valid or not.

        Parameters
        ----------
        input : np.array, list, tuple
            Thermal load input

        Returns
        -------
        bool
            True if the input is correct for the load class
        """

    @abc.abstractmethod
    def peak_heating(self) -> np.array:
        """
        This function returns the peak heating load in kW/month.

        Returns
        -------
        peak heating : np.array
        """

    @abc.abstractmethod
    def peak_cooling(self) -> np.array:
        """
        This function returns the peak cooling load in kW/month.

        Returns
        -------
        peak cooling : np.array
        """

    @abc.abstractmethod
    def baseload_heating(self) -> np.array:
        """
        This function returns the baseload heating in kWh/month.

        Returns
        -------
        baseload heating : np.array
        """

    @abc.abstractmethod
    def baseload_cooling(self) -> np.array:
        """
        This function returns the baseload cooling in kWh/month.

        Returns
        -------
        baseload cooling : np.array
        """

    @property
    def imbalance(self) -> float:
        """
        This function calculates the ground imbalance.
        A positive imbalance means that the field is injection dominated, i.e. it heats up every year.

        Returns
        -------
        imbalance : float
        """
        return np.sum(self.baseload_cooling() - self.baseload_heating())