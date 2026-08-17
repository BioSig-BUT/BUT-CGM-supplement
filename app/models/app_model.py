class AppModel:
    """
    Central shared data model for the application.

    This class is used to store and share selected files, dates, time ranges,
    and processed data paths between controllers, views, and other components.
    It serves as a common state container across the entire application.
    """

    def __init__(self):
        """
        Initialize the application model with default empty values.

        Attributes:
            selected_user_file (str | None):
                Path to the user-selected main file.

            selected_files (list[str]):
                List of currently selected files.

            selected_day (date | datetime | None):
                Currently selected day for visualization or processing.

            available_days (list):
                List of days available for selection.

            start_time (datetime | None):
                Start time of the selected interval.

            end_time (datetime | None):
                End time of the selected interval.

            cgm_file_paths (list[str] | None):
                Paths to continuous glucose monitoring (CGM) data files.

            hr_file_paths (list[str]):
                Paths to heart rate data files.

            acc_file_paths (list[str]):
                Paths to accelerometer data files.

            cal_table_file_path (list[str]):
                Paths to calorie table files.

            act_table_file_path (list[str]):
                Paths to activity table files.

            sleep_file_path (str | None):
                Path to the sleep data file.

            steps_sum_file_path (str | None):
                Path to the daily steps summary file.

            cpet_sum_file_path (str | None):
                Path to the CPET summary file.

            cpet_meta_file_path (str | None):
                Path to the CPET metadata file.
        """
        self.selected_user_file = None
        self.selected_files = []
        self.selected_day = None
        self.available_days = []
        self.start_time = None
        self.end_time = None
        self.cgm_file_paths = None
        self.hr_file_paths = []
        self.acc_file_paths = []
        self.cal_table_file_path = []
        self.act_table_file_path = []
        self.sleep_file_path = None
        self.steps_sum_file_path = None
        self.cpet_sum_file_path = None
        self.cpet_meta_file_path = None

