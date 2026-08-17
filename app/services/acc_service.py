import pandas as pd
import numpy as np
import h5py

from datetime import datetime


class ACCService:
    """
    Service class for loading and filtering accelerometer (ACC) data.

    The class provides methods for:

    - locating accelerometer files for a selected date,
    - loading raw accelerometer signals from HDF5 files,
    - converting signals into a time-indexed pandas DataFrame.

    Loaded signals contain the three acceleration axes:

    - ACC_X
    - ACC_Y
    - ACC_Z

    The resulting DataFrame uses a datetime index named ``Time``.
    """

    def __init__(self):
        """
        Initialize the accelerometer service.

        Attributes:
            cache (dict):
                Dictionary reserved for future caching of loaded data.
        """
        self.cache = {}

    def load_acc(
            self,
            start_time: datetime | str,
            file_path: str,
    ) -> pd.DataFrame | None:
        """
        Load accelerometer data from an HDF5 file.

        The method reads raw accelerometer signals stored in the datasets:

        - ``ACC_X``
        - ``ACC_Y``
        - ``ACC_Z``

        together with the sampling frequency stored in
        ``sampling_freq``.

        A time index is generated using the provided ``start_time``
        and the sampling frequency. The output is returned as a
        pandas DataFrame indexed by timestamps.

        Args:
            start_time (datetime | str):
                Start timestamp of the recording.

                The value is converted using ``pandas.to_datetime()``.

            file_path (str):
                Path to the HDF5 accelerometer file.

        Returns:
            pd.DataFrame | None:
                DataFrame containing accelerometer signals with columns:

                - ``ACC_X``
                - ``ACC_Y``
                - ``ACC_Z``

                The DataFrame index is a datetime index named ``Time``.

                Returns ``None`` if the file path is invalid.
        """
        if file_path is None or not file_path:
            print(
                f"ACC does not exist or is unavailable: {file_path}"
            )
            return None

        with h5py.File(file_path, "r") as f:
            acc_x = f["ACC_X"][:].squeeze().astype(np.float32)
            acc_y = f["ACC_Y"][:].squeeze().astype(np.float32)
            acc_z = f["ACC_Z"][:].squeeze().astype(np.float32)

            fs = int(f["sampling_freq"][()])

            # TIME INDEX
            start_time = pd.to_datetime(
                start_time,
                dayfirst=True,
                format="mixed",
                errors="coerce"
            )

            time_index = start_time + pd.to_timedelta(
                np.arange(len(acc_x)) / fs,
                unit="s"
            )

            # DATAFRAME
            df = pd.DataFrame({
                "ACC_X": acc_x,
                "ACC_Y": acc_y,
                "ACC_Z": acc_z
            }, index=time_index)

            df.index.name = "Time"

        return df

    def acc_in_range(
            self,
            start_time: datetime,
            acc_file_paths: list[list[str]]
    ) -> str | None:
        """
        Find the accelerometer file matching the selected date.

        The method searches through available accelerometer file paths
        and returns the file whose name contains the date derived
        from ``start_time``.

        Args:
            start_time (datetime):
                Selected datetime used for file matching.

            acc_file_paths (list[list[str]]):
                Nested list containing available accelerometer
                file paths.

        Returns:
            str | None:
                Matching accelerometer file path if found,
                otherwise ``None``.
        """
        date_str = start_time.strftime("%Y-%m-%d")

        if not acc_file_paths or not acc_file_paths[0]:
            print("ACC are not available")
            return None

        acc_file = None

        for file in acc_file_paths[0]:
            if date_str in file:
                acc_file = file

        return acc_file
