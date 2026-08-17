import pandas as pd
from pathlib import Path
from datetime import datetime
import traceback


class TimeRangeResult:
    """
    Container object holding results of time range analysis.

    This object stores computed metadata about a user's measurement
    period, including global start/end timestamps, available days,
    file mappings, and the total number of recorded days.

    It acts as a structured return type for TimeRangeService.
    """

    def __init__(self):
        """
        Initialize an empty TimeRangeResult.

        Attributes:
            start_time (pd.Timestamp | None):
                Earliest timestamp in the dataset.

            end_time (pd.Timestamp | None):
                Latest timestamp in the dataset.

            available_days (set[pd.Timestamp]):
                Set of timestamps representing available measurement days.

            file_context (dict[str, str]):
                Mapping of logical file names to physical file paths
                for the selected user.

            number_of_days (int | None):
                Total number of recorded days in the dataset.
        """
        self.start_time = None
        self.end_time = None
        self.available_days = set()
        self.file_context = {}
        self.number_of_days = None


class TimeRangeService:
    """
    Service responsible for analyzing time coverage of user data files.

    This service processes a virtual database of user files,
    extracts metadata about measurement time ranges, and determines
    which calendar days are covered by the dataset.
    """

    def analyze(
            self,
            virtual_db: dict,
            selected_files: set[str],
            user_file: str,
    ) -> TimeRangeResult:
        """
        Analyze selected user files and compute time coverage information.

        The method performs the following steps:

        - Filters user files based on selected logical categories
        - Loads metadata file with measurement start/end information
        - Extracts global time range for the selected user
        - Computes number of measurement days
        - Builds a set of available calendar days
        - Returns a structured result object

        Args:
            virtual_db (dict):
                Virtual database mapping users to their categorized files.

            selected_files (set[str]):
                Set of logical file types to include in the analysis.

            user_file (str):
                Identifier of the user whose data should be processed.

        Returns:
            TimeRangeResult:
                Object containing:

                - start_time (pd.Timestamp | None):
                    Earliest measurement timestamp.

                - end_time (pd.Timestamp | None):
                    Latest measurement timestamp.

                - available_days (set[pd.Timestamp]):
                    Set of timestamps representing available days.

                - file_context (dict[str, str]):
                    Mapping of selected file types to file paths.

                - number_of_days (int | None):
                    Total number of recorded days.
        """

        result = TimeRangeResult()
        files = virtual_db[user_file]

        cgm_path = None
        hr_paths = []
        acc_paths = []
        sleep_path = None
        steps_path = None
        cal_path = None
        act_path = None
        cpet_sum_path = None
        cpet_meta_path = None

        # Split files by logical type
        for vname, path in files.items():
            if vname not in selected_files:
                continue
            if vname == "CGM":
                cgm_path = path
            elif "HR" in vname:
                hr_paths.append(path)
            elif "ACC" in vname:
                acc_paths.append(path)
            elif vname == "Sleep":
                sleep_path = path
            elif vname == "Steps":
                steps_path = path
            elif vname == "Meals":
                cal_path = path
            elif vname == "Activities":
                act_path = path
            elif vname == "CPET summary":
                cpet_sum_path = path
            elif vname == "CPET metadata":
                cpet_meta_path = path

            result.file_context[vname] = path

        # Process individual file types
        if hr_paths:
            for hr_file in hr_paths[0]:
                self.process_hr(hr_file, result)

        if acc_paths:
            for acc_file in acc_paths[0]:
                self.process_acc(acc_file, result)

        if cgm_path:
            self.process_cgm(cgm_path, result)

        if sleep_path:
            self.process_sleep(sleep_path, result)

        if steps_path:
            self.process_steps(steps_path, result)

        if cal_path:
            self.process_calories(cal_path, result)

        if act_path:
            self.process_activities(act_path, result)

        # if cpet_sum_path:
        #     self.process_cpet_sum(cpet_sum_path, result)

        if cpet_meta_path:
            self.process_cpet_meta(cpet_meta_path, result)

        return result

    def process_acc(self, path, result: TimeRangeResult):

        try:
            file_name = Path(path).stem
            date_str = file_name.split("_")[1]

            start = pd.Timestamp(datetime.strptime(date_str, "%Y-%m-%d"))
            end = start + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

            self.update_range(start, end, result)

            day = start.normalize()

            while day <= end.normalize():
                result.available_days.add(day)
                day += pd.Timedelta(days=1)
        except Exception as e:
            print(f"Error loading ACC file {path}: {e}")

    def process_hr(self, path, result: TimeRangeResult):

        try:
            file_name = Path(path).stem
            date_str = file_name.split("_")[1]

            start = pd.Timestamp(datetime.strptime(date_str, "%Y-%m-%d"))
            end = start + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

            self.update_range(start, end, result)

            day = start.normalize()

            while day <= end.normalize():
                result.available_days.add(day)
                day += pd.Timedelta(days=1)
        except Exception as e:
            print(f"Error loadin HR file {path}: {e}")

    def process_cgm(
            self,
            path: str,
            result: TimeRangeResult
    ):
        """
        Processes a CGM (Continuous Glucose Monitoring) file and updates
        the global time range and available days.

        The method loads CGM data from a CSV or Excel file, extracts valid
        timestamps, determines the earliest and latest measurements,
        and updates the result accordingly.

        Args:
            path (str):
                Absolute path to the CGM data file (.csv or .xlsx).
            result (TimeRangeResult):
                Shared result object where time range and available days
                are accumulated.

        Returns:
            None:
                This method updates the `result` object in place.
        """
        try:
            df = pd.read_csv(path, delimiter=";", decimal=".")

            ts = pd.to_datetime(df["Timestamp"], dayfirst=True, format="mixed", errors="coerce").dropna()
            day = ts.dt.normalize()

            result.available_days.update(day)

            start, end = ts.min(), ts.max()
            self.update_range(start, end, result)
        except Exception as e:
            print(f"Error loading CGM file {path}: {e}")

    def process_sleep(
            self,
            path: str,
            result: TimeRangeResult
    ):
        """
        Processes a CGM (Continuous Glucose Monitoring) file and updates
        the global time range and available days.

        The method loads CGM data from a CSV or Excel file, extracts valid
        timestamps, determines the earliest and latest measurements,
        and updates the result accordingly.

        Args:
            path (str):
                Absolute path to the CGM data file (.csv or .xlsx).
            result (TimeRangeResult):
                Shared result object where time range and available days
                are accumulated.

        Returns:
            None:
                This method updates the `result` object in place.
        """
        try:
            df = pd.read_csv(path, delimiter=";", decimal=".")

            ts = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce").dropna()
            day = ts.dt.normalize()

            result.available_days.update(day)

            start, end = ts.min(), ts.max()
            self.update_range(start, end, result)
        except Exception as e:
            print(f"Error loading Sleep file {path}: {e}")

    def process_steps(
            self,
            path: str,
            result: TimeRangeResult
    ):
        """
        Processes a CGM (Continuous Glucose Monitoring) file and updates
        the global time range and available days.

        The method loads CGM data from a CSV or Excel file, extracts valid
        timestamps, determines the earliest and latest measurements,
        and updates the result accordingly.

        Args:
            path (str):
                Absolute path to the CGM data file (.csv or .xlsx).
            result (TimeRangeResult):
                Shared result object where time range and available days
                are accumulated.

        Returns:
            None:
                This method updates the `result` object in place.
        """
        try:
            df = pd.read_csv(path, delimiter=";", decimal=".")

            ts = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce").dropna()
            day = ts.dt.normalize()

            result.available_days.update(day)

            start, end = ts.min(), ts.max()
            self.update_range(start, end, result)
        except Exception as e:
            print(f"Error loading Steps file {path}: {e}")

    def process_calories(
            self,
            path: str,
            result: TimeRangeResult
    ):
        """
        Processes a calorie table file and updates available days and time range.

        The method reads all sheets from an Excel file, extracts dates encoded
        in sheet names, updates available days, and updates the global time range
        based on the detected dates.

        Args:
            path (str):
                Absolute path to the calorie table Excel file.
            result (TimeRangeResult):
                Shared result object where time range and available days
                are accumulated.

        Returns:
            None:
                This method updates the `result` object in place.
        """
        try:
            df = pd.read_csv(path, delimiter=";", decimal=".")

            ts = pd.to_datetime(df["Time"], dayfirst=True, format="mixed", errors="coerce").dropna()
            day = ts.dt.normalize()

            result.available_days.update(day)

            start, end = ts.min(), ts.max()
            self.update_range(start, end, result)
        except Exception as e:
            print(f"Error loading Meals file {path}: {e}")

    def process_activities(
            self,
            path: str,
            result: TimeRangeResult
    ):
        """
        Processes an activities file and updates available days and time range.

        The method loads activity data from a CSV file, parses timestamps
        from the second column, determines the covered date range,
        and updates the result.

        Args:
            path (str):
                Absolute path to the activities CSV file.
            result (TimeRangeResult):
                Shared result object where time range and available days
                are accumulated.

        Returns:
            None:
                This method updates the `result` object in place.
        """
        try:
            if path.endswith("csv"):
                df = pd.read_csv(path, delimiter=";", decimal=".")
            else:
                df = pd.read_excel(path)

            ts = pd.to_datetime(df["Date"], dayfirst=True, format="mixed", errors="coerce").dropna()
            day = ts.dt.normalize()

            result.available_days.update(day)

            start, end = ts.min(), ts.max()
            self.update_range(start, end, result)
        except Exception as e:
            print(f"Error loading Activities file {path}: {e}")

    def process_cpet_meta(
            self,
            path: str,
            result: TimeRangeResult
    ):
        """
        Processes CPET metadata file and updates available days and time range.
        """
        try:
            df = pd.read_csv(path, delimiter=";", decimal=".")

            start_time = pd.to_datetime(
                df.loc[df["Field"].eq("Start Time"), "Value"].iloc[0], dayfirst=True, format="mixed", errors="coerce"
            )

            duration = pd.to_timedelta(
                df.loc[df["Field"].eq("Duration"), "Value"].iloc[0]
            )

            end_time = start_time + duration

            day = start_time.normalize()
            result.available_days.add(day)

            self.update_range(start_time, end_time, result)
        except Exception as e:
            print(f"Error loading CPET meta file {path}: {e}")
            traceback.print_exc()

    def update_range(
            self,
            start: datetime,
            end: datetime,
            result: TimeRangeResult
    ):
        """
        Updates the global start and end time of the analyzed data.

        The method compares the provided time interval with the current
        values stored in the result and expands the range if necessary.

        Args:
            start (datetime):
                Start timestamp of the processed data segment.
            end (datetime):
                End timestamp of the processed data segment.
            result (TimeRangeResult):
                Shared result object holding the global time range.

        Returns:
            None:
                This method updates the `result` object in place.
        """
        if result.start_time is None or start < result.start_time:
            result.start_time = start
        if result.end_time is None or end > result.end_time:
            result.end_time = end


