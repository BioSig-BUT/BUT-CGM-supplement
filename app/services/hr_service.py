import pandas as pd
import numpy as np
from datetime import datetime


class HRService:
    """
    Service class for loading and processing heart rate (HR) data.

    The service reads HR and RR interval data from CSV files, generates
    a time axis based on RR intervals, applies physiological filtering,
    and provides smoothed heart rate series for visualization.
    """

    def __init__(self):
        """
        Initialize the HRService.

        Attributes:
            cache (dict):
                Optional cache for precomputed HR results.
        """
        self.cache = {}

    def calculate_hr(
            self,
            start_time: datetime | str,
            file_path: str
    ) -> tuple[pd.Series, pd.Series, pd.DatetimeIndex]:
        """
        Load heart rate data and reconstruct a timestamped HR time series.

        The method:
        - Loads heart rate (HR) and RR interval data from a CSV file
        - Converts HR and RR values to numeric format
        - Detects RR unit scaling (seconds vs milliseconds)
        - Cleans invalid physiological values
        - Reconstructs time axis using cumulative RR intervals
        - Aligns timestamps to the provided start_time
        - Applies optional end-of-day alignment shift when needed
        - Returns structured HR signal with timestamps

        Args:
            start_time (datetime | str):
                Start timestamp of the recording. Used as the anchor
                for reconstructing the time axis.

            file_path (str):
                Path to the HR CSV file.

        Returns:
            tuple[pd.Series, pd.Series, pd.DatetimeIndex]:

                heart_rate:
                    Cleaned heart rate signal (HR values, with invalid values set to NaN).

                rr_intervals:
                    RR intervals reconstructed for timing (in milliseconds).

                hr_time:
                    DatetimeIndex representing timestamps for each HR measurement.
        """
        df = pd.read_csv(file_path, sep=None, engine="python")

        df.columns = df.columns.str.strip().str.lower()

        rename_map = {}

        for col in df.columns:
            if "hr" in col:
                rename_map[col] = "HR"
            elif "rr" in col:
                rename_map[col] = "RR"
            else:
                rename_map[col] = "QRS"

        df = df.rename(columns=rename_map)

        df = df[["HR", "RR", "QRS"]]

        # Convert columns to numeric
        df["RR"] = pd.to_numeric(
            df["RR"],
            errors="coerce"
        )

        df["HR"] = pd.to_numeric(
            df["HR"],
            errors="coerce"
        )

        df["QRS"] = pd.to_numeric(
            df["QRS"],
            errors="coerce"
        )

        # Detect RR units (seconds vs milliseconds)
        median_rr = df["RR"].median()

        if pd.notna(median_rr) and median_rr < 10:
            df["RR"] = df["RR"] * 1000

        # Remove invalid RR values
        df.loc[df["RR"] <= 0, "RR"] = np.nan

        start_day = start_time.date()
        first_qrs = df["QRS"].iloc[1]

        start_time = (
                pd.to_datetime(start_day)
                + pd.to_timedelta(first_qrs, unit="ms")
        )

        df["datetime"] = start_time + pd.to_timedelta(
            df["QRS"] - first_qrs,
            unit="ms"
        )

        # Physiological RR filter
        mask = (
            (df["RR"] >= 300) &
            (df["RR"] <= 2000)
        )

        df.loc[~mask, ["HR", "RR"]] = np.nan

        # Outputs
        heart_rate = df["HR"]
        rr_intervals = df["RR"]
        hr_time = pd.DatetimeIndex(df["datetime"])

        return heart_rate, rr_intervals, hr_time

    def resample_hr(
            self,
            start_time: datetime | str,
            file_path: str,
            window_s: float,
            step: float = 1
    ) -> tuple[None, pd.Series]:
        """
        Resample and smooth heart rate values to uniform time intervals.

        The method:
        - Loads HR data using calculate_hr()
        - Creates regular time axis
        - Interpolates missing values
        - Applies rolling mean smoothing

        Args:
            start_time (datetime | str):
                Start timestamp of the recording.

            file_path (str):
                Path to the HR CSV file.

            window_s (float):
                Smoothing window size in seconds.

            step (float, optional):
                Resampling step in seconds.
                Default is 1.

        Returns:
            tuple[None, pd.Series]:

                None:
                    Reserved placeholder.

                hr_smooth:
                    Smoothed HR time series indexed by datetime.
        """
        # Load HR data
        heart_rate, rr, hr_time = self.calculate_hr(
            start_time,
            file_path
        )

        if len(heart_rate) == 0:
            raise ValueError("HR series is empty")

        # Create HR series
        hr_series = pd.Series(
            heart_rate.values,
            index=hr_time
        )

        # Create uniform timeline
        uniform_time = pd.date_range(
            start=pd.to_datetime(start_time, dayfirst=True, format="mixed", errors="coerce"),
            end=hr_series.index.max(),
            freq=f"{step}s"
        )

        # Interpolate values to uniform timeline
        hr_uniform = (
            hr_series
            .reindex(hr_series.index.union(uniform_time))
            .interpolate("time")
            .reindex(uniform_time)
        )

        # Apply rolling mean smoothing
        window_samples = max(
            int(window_s / step),
            1
        )

        hr_smooth = hr_uniform.rolling(
            window_samples,
            min_periods=1,
            center=True
        ).mean()

        return None, hr_smooth

    def hr_in_range(
            self,
            start_time: datetime | str,
            hr_file_paths: list[list[str]]
    ) -> str | None:
        """
        Find HR file matching the selected date.

        Args:
            start_time (datetime | str):
                Selected date.

            hr_file_paths (list[list[str]]):
                Nested list of available HR file paths.

        Returns:
            str | None:
                Matching file path or None if not found.
        """
        date_str = pd.to_datetime(start_time, dayfirst=True, format="mixed", errors="coerce").strftime(
            "%Y-%m-%d"
        )

        for file in hr_file_paths[0]:
            if date_str in file:
                return file

        return None


