import pandas as pd


class CPETService:
    """
    Service class responsible for loading and processing CPET measurement data.

    This service loads CPET measurement results and metadata from CSV files,
    validates the selected measurement date, and returns formatted pandas
    DataFrames containing CPET parameters and measurement information.
    """

    def __init__(self):
        """
        Initialize the CPETService.
        """
        self.cache = {}

    def load_cpet_sum_table(
            self,
            file_path: str,
            meta_file_path,
            start_time
    ) -> pd.DataFrame | None:
        """
        Load and process CPET summary measurement data from a CSV file.

        The method loads CPET results, renames columns for internal
        compatibility, converts numeric values, and validates that the
        corresponding CPET metadata belongs to the selected time range.

        Args:
            file_path (str):
                Path to the CPET summary CSV file.

            meta_file_path:
                Path to the CPET metadata CSV file used for validation.

            start_time:
                Start timestamp of the selected time range.

        Returns:
            pd.DataFrame | None:
                Processed CPET summary data if available and valid,
                otherwise None.
        """

        try:
            df = pd.read_csv(
                file_path,
                delimiter=";",
                decimal="."
            )

        except Exception as e:
            print(f"CPET file cannot be loaded: {e}")
            return None

        if df.empty:
            print("CPET file is empty.")
            return None

        # Rename columns (for compatibility)
        df.columns = [
            "Data",
            "Unit",
            "VT1",
            "VT2",
            "VO2peak"
        ]

        numeric_cols = [
            "VT1",
            "VT2",
            "VO2peak"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        if self.load_cpet_meta_table(meta_file_path, start_time) is None:
            return None

        return df

    def load_cpet_meta_table(
            self,
            file_path: str,
            start_time
    ) -> pd.DataFrame | None:
        """
        Load and validate CPET metadata from a CSV file.

        The method extracts CPET start time and duration from the metadata,
        calculates the measurement end time, and returns the metadata only
        if the CPET measurement matches the selected date.

        Args:
            file_path (str):
                Path to the CPET metadata CSV file.

            start_time:
                Start timestamp of the selected time range.

        Returns:
            pd.DataFrame | None:
                CPET metadata table if the measurement belongs to the
                selected date, otherwise None.
        """

        try:
            df = pd.read_csv(
                file_path,
                delimiter=";",
                decimal="."
            )

        except Exception as e:
            print(f"CPET meta file cannot be loaded: {e}")
            return None

        if df.empty:
            print("CPET meta file is empty.")
            return None

        # Rename columns (for compatibility)
        df.columns = [
            "Field",
            "Value"
        ]

        start_cpet = pd.to_datetime(
            df.loc[df["Field"].eq("Start Time"), "Value"].iloc[0], dayfirst=True, format="mixed", errors="coerce"
        )
        duration = pd.to_timedelta(df.loc[df["Field"].eq("Duration"), "Value"].iloc[0])
        end_cpet = start_cpet + duration

        if start_cpet.day == start_time.day:
            return df
        else:
            return None

