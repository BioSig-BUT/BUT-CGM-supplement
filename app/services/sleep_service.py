import pandas as pd
from datetime import datetime


class SleepService:
    """
    Service class responsible for loading and processing sleep data.

    This service reads sleep records from CSV files, parses date and time
    values, handles overnight sleep intervals, creates summary tables,
    and prepares daily sleep ranges for visualization.
    """

    def __init__(self):
        """
        Initialize the SleepService.

        Attributes:
            cache (dict):
                Optional in-memory cache for loaded sleep data.
        """
        self.cache = {}

    def detect_date_format(
            self,
            date_str: str
    ) -> str | None:
        """
        Detect supported date format from a string value.

        Supported formats:

        - DD.MM.YYYY
        - YYYY-MM-DD

        Args:
            date_str (str):
                Date string to validate.

        Returns:
            str | None:
                Matching datetime format string,
                or None if unsupported.
        """
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                datetime.strptime(date_str, fmt)
                return fmt
            except ValueError:
                continue

        return None

    def load_sleep(
            self,
            filepath: str
    ) -> pd.DataFrame | None:
        """
        Load sleep records from CSV file.

        The method:
        - Loads sleep data from CSV
        - Detects date format
        - Converts date and time columns
        - Builds datetime intervals
        - Corrects overnight sleep sessions

        Args:
            filepath (str):
                Path to sleep CSV file.

        Returns:
            pd.DataFrame | None:
                Parsed sleep DataFrame or None if unavailable.
        """
        if not filepath:
            print("Sleep data are unavailable")
            return None

        # Load CSV file
        df = pd.read_csv(
            filepath,
            delimiter=";",
            decimal="."
        )

        df.columns = [
            "Date",
            "Sleep_Start",
            "Sleep_End",
            "Duration_Minutes"
        ]

        # Detect file date format
        file_date_format = self.detect_date_format(
            df.loc[0, "Date"]
        )

        if file_date_format is None:
            raise ValueError(
                f"Failed to recognize the data format in the file {filepath}"
            )

        # Convert dates
        df["Date_parsed"] = pd.to_datetime(
            df["Date"],
            format=file_date_format,
            errors="coerce"
        )

        # Create sleep start datetime
        df["Sleep_Start_dt"] = pd.to_datetime(
            df["Date_parsed"].astype(str) +
            " " +
            df["Sleep_Start"],
            errors="coerce"
        )

        # Create sleep end datetime
        df["Sleep_End_dt"] = pd.to_datetime(
            df["Date_parsed"].astype(str) +
            " " +
            df["Sleep_End"],
            errors="coerce"
        )

        # Fix overnight sleep crossing midnight
        mask = df["Sleep_Start_dt"] > df["Sleep_End_dt"]

        df.loc[mask, "Sleep_Start_dt"] -= pd.Timedelta(
            days=1
        )

        return df

    def sleep_table(
            self,
            df: pd.DataFrame,
            start_day: pd.Timestamp
    ) -> pd.DataFrame | None:
        """
        Create morning and evening sleep summary table.

        Args:
            df (pd.DataFrame):
                Parsed sleep DataFrame.

            start_day (pd.Timestamp):
                Selected day.

        Returns:
            pd.DataFrame | None:
                Summary table with morning and evening sleep.
        """
        if df is None or df.empty:
            print("Sleep data are unavailable.")
            return None

        next_day = start_day + pd.Timedelta(days=1)

        # Morning sleep
        morning_df = df[
            df["Date_parsed"].dt.date == start_day.date()
        ]

        # Evening sleep
        evening_df = df[
            df["Date_parsed"].dt.date == next_day.date()
        ]

        if not morning_df.empty:
            morning = morning_df.iloc[0]
            minutes_morning = pd.to_numeric(morning["Duration_Minutes"], errors="coerce")

            if pd.isna(minutes_morning):
                hh_mm_morning = "--:--"
            else:
                hh_mm_morning = (
                    f"{int(minutes_morning // 60):02d}:"
                    f"{int(minutes_morning % 60):02d}"
                )
        else:
            print("Morning sleep is not available in this time range")
            return None

        if not evening_df.empty:
            evening = evening_df.iloc[0]
            minutes_evening = pd.to_numeric(evening["Duration_Minutes"], errors="coerce")

            if pd.isna(minutes_evening):
                hh_mm_evening = "--:--"
            else:
                hh_mm_evening = (
                    f"{int(minutes_evening // 60):02d}:"
                    f"{int(minutes_evening % 60):02d}"
                )
        else:
            evening = None
            hh_mm_evening = "--:--"

        # Create result table
        df_sleep_table = pd.DataFrame({
            "Sleep": {
                "Sleep start":
                    "--:--" if morning is None or pd.isna(morning["Sleep_Start_dt"])
                    else morning["Sleep_Start_dt"],
                "Sleep end":
                    "--:--" if morning is None or pd.isna(morning["Sleep_End_dt"])
                    else morning["Sleep_End_dt"],
                "Sleep duration": hh_mm_morning
            }
        }).T

        df_sleep_table.index = [""]

        return df_sleep_table

    def get_daily_sleep_ranges(
            self,
            df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Split sleep intervals into morning and evening
        segments for each calendar day.

        Args:
            df (pd.DataFrame):
                Parsed sleep DataFrame.

        Returns:
            pd.DataFrame:
                Daily sleep ranges with time-only columns.
        """
        df = df.dropna(
            subset=["Sleep_Start_dt", "Sleep_End_dt"]
        ).copy()

        results = {}

        for _, row in df.iterrows():

            start = row["Sleep_Start_dt"]
            end = row["Sleep_End_dt"]

            current_day = start.floor("D")
            last_day = end.floor("D")

            while current_day <= last_day:

                day_start = current_day
                day_mid = day_start + pd.Timedelta(hours=12)
                day_end = (
                    day_start +
                    pd.Timedelta(days=1) -
                    pd.Timedelta(seconds=1)
                )

                # Overlap with selected day
                sleep_from = max(start, day_start)
                sleep_to = min(end, day_end)

                # Morning segment
                m_from = max(sleep_from, day_start)
                m_to = min(sleep_to, day_mid)

                # Evening segment
                e_from = max(sleep_from, day_mid)
                e_to = min(sleep_to, day_end)

                if (
                    pd.notna(e_to) and
                    e_to.time() == pd.Timestamp.min.time()
                ):
                    e_to = e_to - pd.Timedelta(seconds=1)

                key = day_start.date()

                if key not in results:
                    results[key] = {
                        "morning_from": pd.NaT,
                        "morning_to": pd.NaT,
                        "evening_from": pd.NaT,
                        "evening_to": pd.NaT
                    }

                if m_from < m_to:
                    results[key]["morning_from"] = m_from
                    results[key]["morning_to"] = m_to

                if e_from < e_to:
                    results[key]["evening_from"] = e_from
                    results[key]["evening_to"] = e_to

                current_day += pd.Timedelta(days=1)

        # Convert to DataFrame
        result_df = pd.DataFrame.from_dict(
            results,
            orient="index"
        ).reset_index()

        result_df = result_df.rename(
            columns={"index": "date"}
        )

        result_df = result_df.sort_values(
            "date"
        ).reset_index(drop=True)

        # Convert datetime to time only
        time_cols = [
            "morning_from",
            "morning_to",
            "evening_from",
            "evening_to"
        ]

        for col in time_cols:
            result_df[col] = result_df[col].dt.time

        return result_df

    def sleep_in_range(
            self,
            sleep_file_path: str,
            selected_day: datetime | str
    ) -> pd.DataFrame:
        """
        Return sleep ranges for selected day.

        Args:
            sleep_file_path (str):
                Path to sleep CSV file.

            selected_day (datetime | str):
                Selected day.

        Returns:
            pd.DataFrame:
                One-row DataFrame containing sleep ranges
                for the selected date.
        """
        # Load raw sleep data
        df_sleep = self.load_sleep(
            sleep_file_path
        )

        # Build daily ranges
        df_ranges = self.get_daily_sleep_ranges(
            df_sleep
        )

        day = pd.to_datetime(
            selected_day, dayfirst=True, format="mixed", errors="coerce"
        ).date()

        # Filter selected day
        day_df = df_ranges[
            df_ranges["date"] == day
        ].copy()

        return day_df


