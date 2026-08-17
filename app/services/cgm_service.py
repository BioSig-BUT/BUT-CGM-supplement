import pandas as pd


class CGMService:
    """
    Service class responsible for loading and processing CGM
    (Continuous Glucose Monitoring) data.

    This service reads glucose measurements from a CSV file, converts
    timestamps and numeric values, filters records within a selected
    time range, and returns standardized outputs for plotting
    and further analysis.
    """

    def __init__(self):
        """
        Initialize the CGMService.

        Attributes:
            cache (dict):
                Optional in-memory cache for loaded CGM data.
        """
        self.cache = {}

    def load_cgm(
            self,
            cgm_file_path: str,
            start_time: pd.Timestamp,
            end_time: pd.Timestamp
    ) -> tuple[pd.DataFrame | None, pd.Series | None, pd.Series | None]:
        """
        Load CGM data from a file and filter them by time range.

        The method:
        - Loads glucose data from a CSV file
        - Converts timestamps and glucose values
        - Sorts records chronologically
        - Filters rows between start_time and end_time
        - Returns both a DataFrame and individual Series objects

        Args:
            cgm_file_path (str):
                Path to the CGM CSV file.

            start_time (pd.Timestamp):
                Start of the selected time interval.

            end_time (pd.Timestamp):
                End of the selected time interval.

        Returns:
            tuple[pd.DataFrame | None, pd.Series | None, pd.Series | None]:

                filtered:
                    DataFrame with columns:

                    - time
                    - glykemie

                time:
                    Series containing timestamps.

                glykemie:
                    Series containing glucose values.

                Returns (None, None, None) if the file path is missing,
                loading fails, or no records match the selected range.
        """
        # Validate file path
        if not cgm_file_path:
            return None, None, None

        try:
            # Load CSV file
            df = pd.read_csv(
                cgm_file_path,
                delimiter=";",
                decimal=".",
                usecols=["Timestamp", "Glycemia"],
            )

        except Exception as e:
            print(f"Error loading CGM file: {e}")
            return None, None, None

        # Convert timestamp column
        df["Timestamp"] = pd.to_datetime(
            df["Timestamp"], dayfirst=True, format="mixed", errors="coerce"
        )

        # Convert glucose values
        df["Glycemia"] = pd.to_numeric(
            df["Glycemia"].astype(str),
            errors="coerce"
        )

        # Keep only selected time range
        filtered = df[
            (df["Timestamp"] >= start_time) &
            (df["Timestamp"] <= end_time)
        ]

        if filtered.empty:
            print("No CGM data available for the selected time range")
            return None, None, None

        filtered = filtered.rename(
            columns={
                "Timestamp": "time",
                "Glycemia": "glykemie",
            }
        )[["time", "glykemie"]]

        start_time = filtered["time"].min().floor("D")
        end_time = filtered["time"].max().ceil("D") - pd.Timedelta(minutes=5)

        full_range = pd.date_range(start=start_time, end=end_time, freq="5min")
        filtered["time"] = filtered["time"].dt.round("5min")

        filtered = (
            filtered
            .groupby("time", sort=False, as_index=False)
            .agg({"glykemie": "mean"})
        )

        filtered = (
            filtered.set_index("time")
            .reindex(full_range)
            .rename_axis("time")
            .reset_index()
        )

        filtered["glykemie"] = filtered["glykemie"].interpolate(
            method="linear", limit=3
        )

        return filtered, filtered["time"], filtered["glykemie"]
