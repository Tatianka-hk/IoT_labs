from csv import reader
from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.aggregated_data import AggregatedData
from domain.parking import Parking
import config
import pandas as pd

class FileDatasource:
    def __init__(
        self,
        accelerometer_filename: str,
        gps_filename: str,
        parking_filename:str,
    ) -> None:
        pass

    def read(self) -> AggregatedData:
        """Метод повертає дані отримані з датчиків"""
        accelerometer_data = Accelerometer(1, 2, 3)
        gps_data = Gps(4, 5)
        parking_instance = Parking(6, gps_data)
        return AggregatedData(
            accelerometer_data,
            gps_data,
            parking_instance,
            datetime.now(),
            config.USER_ID,
        )

    def startReading(self, *args, **kwargs):
        """Метод повинен викликатись перед початком читання даних"""

    def stopReading(self, *args, **kwargs):
        """Метод повинен викликатись для закінчення читання даних"""