import pandas as pd
import traceback
from datetime import datetime


class ActivityService:
    """
    Service class responsible for loading and processing activity-related data.

    This service provides methods for reading activity records and daily step
    summaries from external files, filtering them by date or time range,
    and returning cleaned pandas DataFrames for visualization or analysis.
    """

    def __init__(self):
        """
        Initialize the ActivityService.

        Attributes:
            cache (dict):
                Optional in-memory cache for loaded activity data.
        """
        self.cache = {}

    def load_activity_table(
        self,
        file_path: str,
        start_time: pd.Timestamp,
        end_time: pd.Timestamp
    ) -> pd.DataFrame | None:
        """
        Load activity records from an CSV or Excel file and filter them by time range.

        The method reads activity data, converts the timestamp column to
        datetime format, removes invalid rows, filters records between the
        selected start and end times, sorts them chronologically, and renames
        columns for presentation.

        Args:
            file_path (str):
                Path to the file containing activity data.

            start_time (pd.Timestamp):
                Start of the selected time interval.

            end_time (pd.Timestamp):
                End of the selected time interval.

        Returns:
            pd.DataFrame | None:
                DataFrame containing filtered activity records.

                Returns None if the file cannot be loaded, contains no valid
                data, no records match the selected range, or processing fails.
        """
        try:
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path, delimiter=";", decimal=".")
            else:
                df = pd.read_excel(file_path)

        except Exception as e:
            print(f"Activities file cannot be loaded: {e}")
            return None

        try:
            # Converts the date column to datetime format
            df["Date"] = pd.to_datetime(df.iloc[:, 1], dayfirst=True, format="mixed", errors="coerce")

            # Switch date column to first place
            cols = df.columns.tolist()
            cols[0], cols[1] = cols[1], cols[0]
            df = df[cols]

            # Removes invalid  rows
            df = df.dropna(subset=["Date"])

            if df.empty:
                print("No activities for this time range")
                traceback.print_exc()
                return None

            # Filters records between the selected start and end times
            filtered_act = df[
                (df["Date"] >= start_time) &
                (df["Date"] <= end_time)
            ]

            # Sorts filtered data chronologically
            filtered_act = filtered_act.sort_values(
                by="Date",
                ascending=True
            )

            # Renames columns
            filtered_act.columns = [
                "Time",
                "Activity type",
                "Duration",
                "Zone 1",
                "Zone 2",
                "Zone 3",
                "Note"
            ]

            return filtered_act

        except Exception as e:
            print(f"Error processing activities: {e}")
            traceback.print_exc()
            return None

    def load_steps(
            self,
            file_path: str,
            start_time: datetime | pd.Timestamp
    ) -> pd.DataFrame | None:
        """
        Load daily step count for the selected date.

        The method reads a CSV file containing daily step totals, searches
        for the row matching the date derived from ``start_time``, and returns
        the result as a one-row DataFrame.

        Args:
            file_path (str):
                Path to the CSV file containing daily step data.

            start_time (datetime | pd.Timestamp):
                Selected date used for filtering.

        Returns:
            pd.DataFrame | None:
                One-row DataFrame with column:

                - Daily steps

                Returns None if the file cannot be loaded or if no data exists
                for the selected day.
        """
        # Gets date from selected time
        day = start_time.date()

        try:
            # Loads daily steps form CSV file
            df_steps = pd.read_csv(
                file_path,
                delimiter=";",
                decimal="."
            )

        except Exception as e:
            print(f"Steps file cannot be loaded: {e}")
            return None

        # Converts date column to datetime format
        df_steps["Date"] = pd.to_datetime(df_steps["Date"], dayfirst=True, format="mixed", errors="coerce")

        # Filters row matching selected day
        filtered = df_steps.loc[
            df_steps["Date"].dt.date == day,
            "Steps"
        ]

        if filtered.empty:
            print("Steps for this day are unavailable")
            return None
        else:
            day_steps = filtered.iloc[0]

        # Final one-row DataFrame
        df_result = pd.DataFrame({
            "Daily steps": [day_steps]
        })

        df_result.index = [""]

        return df_result

