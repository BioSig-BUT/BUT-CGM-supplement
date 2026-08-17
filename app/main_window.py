import traceback
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QDialog, QLabel, QVBoxLayout, QApplication
)
from PySide6.QtCore import Qt

from app.models.app_model import AppModel
from app.ui.file_dialogue import FileDialogue
from app.ui.data_window import DataWindow
from app.controllers.file_dialogue_controller import FileDialogueController
from app.controllers.data_window_controller import DataWindowController

from app.services.temp_file_service import TempFileService
from app.services.cgm_service import CGMService
from app.services.hr_service import HRService
from app.services.calory_service import CaloryService
from app.services.activity_service import ActivityService
from app.services.acc_service import ACCService
from app.services.sleep_service import SleepService
from app.services.cpet_service import CPETService


class MainWindow(QMainWindow):
    """
    Main application window with tabs for data handling.

    This window includes:
        - Import data tab (FileDialogue)
        - Data display and plotting tab (DataWindow)
        - Temporary file and data services
    """

    def __init__(self):
        """
        Initialize the main application window and its services.

        This constructor sets up the UI, controllers, temporary file service,
        and various data services for CGM, HR, ACC, calories, activity, CPET and sleep data.
        """
        super().__init__()
        self.init_ui()
        self.init_controllers()
        self.init_temp_dir()

        self.temp_service = TempFileService()
        self.cgm_service = CGMService()
        self.hr_service = HRService()
        self.acc_service = ACCService()
        self.calory_service = CaloryService()
        self.activity_service = ActivityService()
        self.sleep_service = SleepService()
        self.cpet_service = CPETService()

    # ----------------------- INIT ------------------------
    def init_ui(self):
        """
        Initialize the user interface of the main window.

        This method sets the window title, resizes the main window,
        and creates the QTabWidget to hold different tabs of the application.
        """
        self.setWindowTitle("DistriMuSe Database Visualization")
        self.resize(1000, 700)
        self.setMinimumSize(920, 630)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

    def init_controllers(self):
        """
        Initialize all controllers and views used in the application.

        This method:
        - Creates the shared application model
        - Initializes the file dialogue view and controller
        - Initializes the data window view and controller
        - Connects signals between components
        - Adds views as tabs to the main window

        Returns:
            None
        """
        # Shared model
        self.model = AppModel()

        # FileDialogue
        self.file_dialogue_view = FileDialogue()
        self.file_dialogue_controller = FileDialogueController(
            view=self.file_dialogue_view, model=self.model
        )

        # DataWindow
        self.data_window_view = DataWindow()
        self.data_window_controller = DataWindowController(
            view=self.data_window_view, model=self.model
        )

        self.file_dialogue_controller.data_ready.connect(self.update_data_tab)

        self.data_window_view.next_day_clicked.connect(
            lambda: self.file_dialogue_controller.shift_day(1)
        )

        self.data_window_view.prev_day_clicked.connect(
            lambda: self.file_dialogue_controller.shift_day(-1)
        )

        self.data_window_view.day_selected.connect(
            self.on_day_selected
        )

        # Add tabs
        self.tabs.addTab(self.file_dialogue_view, "Import data")
        self.tabs.addTab(self.data_window_view, "Data view")

    def init_temp_dir(self):
        """
        Initialize the temporary file directory service.

        Creates a TempFileService instance with a specific folder for temporary data.
        """
        self.temp_service = TempFileService("data/temp")

    # ----------------------- UPDATE DATA TAB ------------------------
    def update_data_tab(self):
        """
        Update all data tabs based on the selected day/time range.

        Retrieves data from the model, loads CGM, HR, ACC, calorie, activitiy, CPET and
        sleep data, then updates the corresponding tables and plots.
        """

        app = QApplication.instance() or QApplication(sys.argv)

        # Loading window
        loading = QDialog()
        loading.setWindowTitle("Please wait")
        loading.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        loading.setModal(True)

        layout = QVBoxLayout()

        label = QLabel("Loading data...")
        label.setAlignment(Qt.AlignCenter)

        layout.addWidget(label)
        loading.setLayout(layout)

        loading.resize(200, 100)
        loading.show()

        QApplication.processEvents()

        # UI LOADING
        # Get data from model
        selected_user_file = self.model.selected_user_file
        selected_day = self.model.selected_day
        start_time, end_time = self.model.start_time, self.model.end_time
        available_days = self.model.available_days
        cgm_files = self.model.cgm_file_paths
        hr_files = self.model.hr_file_paths
        acc_files = self.model.acc_file_paths
        cal_file = self.model.cal_table_file_path
        act_file = self.model.act_table_file_path
        sleep_file = self.model.sleep_file_path
        steps_file = self.model.steps_sum_file_path
        cpet_sum_file = self.model.cpet_sum_file_path
        cpet_meta_file = self.model.cpet_meta_file_path

        # Load data
        cgm_data, cgm_stats = self.load_cgm(cgm_files, start_time, end_time)
        hr_series, hr_res_series, hr_stats = self.load_hr(hr_files, start_time, end_time)
        df_cal = self.load_calories(cal_file, start_time, end_time)
        df_act = self.load_activity(act_file, start_time, end_time)
        df_sleep = self.load_sleep(sleep_file, start_time)
        df_steps = self.load_steps(steps_file, start_time)
        df_sleep_table = self.sleep_service.sleep_table(self.sleep_service.load_sleep(sleep_file), start_time)
        df_cpet_sum = self.load_cpet_sum(cpet_sum_file, cpet_meta_file, start_time)
        df_cpet_meta = self.load_cpet_meta(cpet_meta_file, start_time)
        self.load_acc(acc_files, start_time, end_time, self.data_window_controller.plot_activity(df_act), df_sleep, df_cpet_meta)

        # Update tables
        self.update_table(self.data_window_view.cal_tableWidget, df_cal, "No meals data available", datetime_format="%H:%M")
        self.update_table(self.data_window_view.act_table, df_act, "No activities data available", datetime_format="%H:%M")
        self.update_table(self.data_window_view.step_table, df_steps, "No steps data available", datetime_format="%H:%M")
        self.update_table(self.data_window_view.sleep_table, df_sleep_table, "No sleep data available", datetime_format="%d.%m.%Y %H:%M")
        self.update_table(self.data_window_view.cpet_sum_table, df_cpet_sum, "No CPET summary data available", datetime_format="%d.%m.%Y %H:%M")
        self.update_table(self.data_window_view.cpet_meta_table, df_cpet_meta, "No CPET metadata available", datetime_format="%d.%m.%Y %H:%M")

        # Display graphs
        self.display_graphs(cgm_data, cgm_stats, hr_series, hr_res_series, hr_stats, df_act, df_cal, df_sleep, df_cpet_meta)

        # Data view bar
        self.data_window_view.update_timeline(selected_day, available_days)
        self.data_window_view.display_date_bar(selected_day)
        self.data_window_view.display_user_file(selected_user_file)
        self.buttons_enable(selected_day, available_days)

        self.tabs.setCurrentWidget(self.data_window_view)

        # Loading window close
        loading.close()

        app.exec()

    # ---------------------- DATE BUTTONS -------------------------
    def buttons_enable(self, date, available_days):
        """
        Enable or disable navigation buttons based on selected date.

        This method:
        - Compares the selected date with the first and last available day
        - Disables the "previous day" button if the selected day is the first day
        - Disables the "next day" button if the selected day is the last day
        - Otherwise enables both buttons

        Args:
            date (datetime | str):
                Currently selected date.

            available_days (iterable):
                Collection of available datetime values representing valid days.

        Returns:
            None
        """

        date = pd.to_datetime(date).date()

        start_day = min(d.date() for d in available_days)
        end_day = max(d.date() for d in available_days)

        # Previous day button
        if date == start_day:
            self.data_window_view.prev_day_button_enable(enable=False)
        else:
            self.data_window_view.prev_day_button_enable(enable=True)

        # Next day button
        if date == end_day:
            self.data_window_view.next_day_button_enable(enable=False)
        else:
            self.data_window_view.next_day_button_enable(enable=True)

    def on_day_selected(self, day):
        """
        Handle day selection from the timeline widget.

        Args:
            day:
                Selected date received from the timeline widget.
        """
        self.file_dialogue_controller.on_timeline_clicked(day)

    # ----------------------- LOAD METHODS ------------------------
    def load_cgm(
            self,
            cgm_files: list,
            start_time: datetime,
            end_time: datetime
    ) -> tuple[pd.DataFrame | None, dict | None]:
        """
        Load CGM (continuous glucose monitoring) data from selected files.

        Args:
            cgm_files: List of file paths to CGM CSV files.
            start_time (datetime): Start time of the observation window.
            end_time (datetime): End time of the observation window.

        Returns:
            tuple:
                - pd.DataFrame or None: DataFrame containing CGM data with columns ['time', 'glykemie'].
                - dict or None: Dictionary of statistics {'Min': float, 'Max': float, 'Average': float}.
        """

        cgm_files = cgm_files[0]

        if not cgm_files:
            return None, None
        try:
            cgm_data, _, _ = self.cgm_service.load_cgm(cgm_files, start_time, end_time)
            if cgm_data is None or cgm_data.empty:
                return None, None
            stats = {
                "Min": round(cgm_data["glykemie"].min(), 2),
                "Max": round(cgm_data["glykemie"].max(), 2),
                "Average": round(cgm_data["glykemie"].mean(), 2)
            }
            return cgm_data, stats

        except Exception as e:
            print("Error loading CGM data main_window:", e)
            traceback.print_exc()
            return None, None

    def load_acc(
            self,
            acc_files: list,
            start_time,
            end_time,
            activities: pd.DataFrame | None,
            sleep: pd.DataFrame | None,
            cpet: pd.DataFrame | None
    ) -> list:
        """
        Load accelerometer data for the selected time range and update the UI.

        This method:
        - Checks whether ACC files are available
        - Finds the file matching the selected time range
        - Loads accelerometer data using ACCService
        - Updates the data availability state of the UI
        - Creates and displays the accelerometer plot
        - Returns the loaded file information or an empty list on failure

        Args:
            acc_files (list):
                List of available accelerometer file paths.

            start_time (datetime):
                Start of the selected time window.

            end_time (datetime):
                End of the selected time window.

            activities (pd.DataFrame | None):
                Activity data used for plot annotations.

            sleep (pd.DataFrame | None):
                Sleep data used for plot annotations.

            cpet (pd.DataFrame | None):
                CPET data used for plot annotations.

        Returns:
            list:
                Loaded accelerometer file information. Returns an empty list if
                no data are available or if an error occurs.
        """

        if not acc_files:
            self.data_window_controller.update_display(
                self.data_window_view.web_view3,
                [],
                "No ACC data available"
            )
            return []

        try:
            acc_file_path = self.acc_service.acc_in_range(start_time, acc_files)

            files = self.acc_service.load_acc(start_time, acc_file_path)

            self.data_window_controller.update_display(
                self.data_window_view.web_view3,
                files,
                "No ACC data available"
            )

            self.data_window_controller.plot_acc_window(
                acc_file_path,
                start_time,
                end_time,
                self.data_window_view.web_view3,
                self.data_window_view.acc_stack,
                activities,
                sleep,
                cpet
            )

            return files

        except Exception as e:
            print("Error loading ACC data:", e)
            traceback.print_exc()
            return []

    def load_hr(
            self,
            hr_files: list,
            start_time,
            end_time
    ) -> tuple[pd.Series | None, pd.Series | None, dict | None]:
        """
        Load heart rate (HR) data and compute statistics.

        This method:
        - Selects the HR file corresponding to the given time range
        - Loads and resamples HR data using HRService
        - Creates raw and filtered HR series
        - Computes basic statistics (min, max, mean)
        - Handles missing data safely

        Args:
            hr_files (list):
                List of HR file paths.

            start_time (datetime):
                Start of the selected time window.

            end_time (datetime):
                End of the selected time window.

        Returns:
            tuple[pd.Series | None, pd.Series | None, dict | None]:
                - pd.Series | None: Raw heart rate series indexed by datetime.
                - pd.Series | None: Resampled/smoothed heart rate series.
                - dict | None: Statistics dictionary containing:
                    - "Min"
                    - "Max"
                    - "Průměr"
        """

        if not hr_files:
            return None, None, None

        try:
            file_path = self.hr_service.hr_in_range(start_time, hr_files)

            if file_path is None:
                return None, None, None

            _, hr_s = self.hr_service.resample_hr(
                start_time,
                file_path,
                10,
                step=1
            )

            _, hr_s_res = self.hr_service.resample_hr(
                start_time,
                file_path,
                200,
                step=1
            )

            hr_series = pd.Series(hr_s.values, index=hr_s.index).sort_index()
            hr_res_series = pd.Series(hr_s_res.values, index=hr_s_res.index).sort_index()

            stats = {
                "Min": round(float(np.nanmin(hr_s.values)), 2),
                "Max": round(float(np.nanmax(hr_s.values)), 2),
                "Average": round(float(np.nanmean(hr_s.values)), 2)
            }

            return hr_series, hr_res_series, stats

        except Exception as e:
            print("Error processing HR data (main_window):", e)
            traceback.print_exc()
            return None, None, None

    def load_calories(
            self,
            cal_file: str,
            start_time,
            end_time
    ) -> pd.DataFrame | None:
        """
        Load calorie intake data for the selected time range.

        This method:
        - Checks if a calorie file is available
        - Delegates loading and processing to CaloryService
        - Returns a cleaned DataFrame ready for display
        - Handles errors safely

        Args:
            cal_file (str):
                Path to the calorie table file.

            start_time (datetime):
                Start of the selected time window.

            end_time (datetime):
                End of the selected time window.

        Returns:
            pd.DataFrame | None:
                Processed calorie data as a DataFrame, or None if unavailable or error occurs.
        """

        if not cal_file:
            return None

        try:
            return self.calory_service.load_calory_table(
                cal_file,
                start_time,
                end_time
            )

        except Exception as e:
            print("Error processing Meal data:", e)
            traceback.print_exc()
            return None

    def load_activity(
            self,
            act_file: str,
            start_time,
            end_time
    ) -> pd.DataFrame | None:
        """
        Load activity data from a file for the specified time range.

        Args:
            act_file: Path to the activity table file.
            start_time (datetime): Start of the observation window.
            end_time (datetime): End of the observation window.

        Returns:
            pd.DataFrame | None: Loaded activity data as a DataFrame. Returns None if
            the file is missing or an error occurs.
        """

        if not act_file:
            return None
        try:
            return self.activity_service.load_activity_table(act_file, start_time, end_time)
        except Exception as e:
            print("Error processing Activities data:", e)
            traceback.print_exc()
            return None

    def load_steps(
            self,
            steps_file: str,
            start_time,
    ) -> pd.DataFrame | None:
        """
        Load daily step count data for the selected day.

        This method:
        - Checks if a steps file is available
        - Delegates loading to ActivityService
        - Returns a DataFrame with step counts
        - Handles missing data and errors safely

        Args:
            steps_file (str):
                Path to the steps summary file.

            start_time (datetime):
                Reference date used to select the correct day.

        Returns:
            pd.DataFrame | None:
                DataFrame containing step count for the selected day,
                or None if data is unavailable or an error occurs.
        """

        if not steps_file:
            return None

        try:
            return self.activity_service.load_steps(
                steps_file,
                start_time
            )

        except Exception as e:
            print("Error processing Steps data:", e)
            traceback.print_exc()
            return None

    def load_sleep(self, sleep_file, start_time):
        """
        Load sleep data for the selected day and return processed sleep ranges.

        Args:
            sleep_file: Path to the sleep data file.
            start_time: Reference start time used to extract the relevant day.

        Returns:
            pd.DataFrame | None:
                Processed sleep table for the selected day. Returns None if
                the file is missing or an error occurs.
        """

        if not sleep_file:
            return None
        try:
            return self.sleep_service.sleep_in_range(sleep_file, start_time)
        except Exception as e:
            print("Error processing Sleep data:", e)
            traceback.print_exc()
            return None

    def load_cpet_sum(
            self,
            cpet_sum_file: str,
            cpet_meta_file,
            start_time
    ) -> pd.DataFrame | None:
        """
        Load calorie intake data for the selected time range.

        This method:
        - Checks if a calorie file is available
        - Delegates loading and processing to CaloryService
        - Returns a cleaned DataFrame ready for display
        - Handles errors safely

        Args:
            cal_file (str):
                Path to the calorie table file.

            start_time (datetime):
                Start of the selected time window.

            end_time (datetime):
                End of the selected time window.

        Returns:
            pd.DataFrame | None:
                Processed calorie data as a DataFrame, or None if unavailable or error occurs.
        """

        if not cpet_sum_file:
            return None

        try:
            return self.cpet_service.load_cpet_sum_table(
                cpet_sum_file, cpet_meta_file, start_time
            )

        except Exception as e:
            print("Error processing CPET sum data:", e)
            traceback.print_exc()
            return None

    def load_cpet_meta(
            self,
            cpet_meta_file: str,
            start_time
    ) -> pd.DataFrame | None:
        """
        Load calorie intake data for the selected time range.

        This method:
        - Checks if a calorie file is available
        - Delegates loading and processing to CaloryService
        - Returns a cleaned DataFrame ready for display
        - Handles errors safely

        Args:
            cal_file (str):
                Path to the calorie table file.

            start_time (datetime):
                Start of the selected time window.

            end_time (datetime):
                End of the selected time window.

        Returns:
            pd.DataFrame | None:
                Processed calorie data as a DataFrame, or None if unavailable or error occurs.
        """

        if not cpet_meta_file:
            return None

        try:
            return self.cpet_service.load_cpet_meta_table(
                cpet_meta_file, start_time
            )

        except Exception as e:
            print("Error processing CPET meta data:", e)
            traceback.print_exc()
            return None

    # ----------------------- TABLE & GRAPH ------------------------
    def update_table(
            self,
            table_widget,
            df: pd.DataFrame,
            empty_message: str,
            datetime_format
    ):
        """
        Update a QTableWidget with data from a DataFrame, or show a message if no data is available.

        Args:
            table_widget (QTableWidget): Target table widget.
            df (pd.DataFrame | None): Source data for the table.
            empty_message (str): Message shown when the DataFrame is empty or None.
            datetime_format (str): Format used for datetime values in the table.

        Returns:
            None
        """

        self.data_window_controller.update_display(table_widget, df, empty_message)

        if df is not None and not df.empty:
            self.data_window_controller.fill_table(
                table_widget,
                df,
                datetime_format=datetime_format
            )

    def display_graphs(
            self,
            cgm_data: pd.DataFrame | None,
            cgm_stats: dict | None,
            hr_series: pd.Series | None,
            hr_res_series: pd.Series | None,
            hr_stats: dict | None,
            df_act: pd.DataFrame | None,
            df_cal: pd.DataFrame | None,
            df_sleep: pd.DataFrame | None,
            df_cpet
    ):
        """
        Display CGM + HR graphs together with activity, meal, and sleep overlays.

        Args:
            cgm_data (pd.DataFrame | None): CGM time series data.
            cgm_stats (dict | None): Statistics for CGM (Min, Max, Average).
            hr_series (pd.Series | None): Raw heart rate series.
            hr_res_series (pd.Series | None): Filtered/resampled heart rate series.
            hr_stats (dict | None): Statistics for heart rate (Min, Max, Average).
            df_act (pd.DataFrame | None): Activity data.
            df_cal (pd.DataFrame | None): Calorie/meal data.
            df_sleep (pd.DataFrame | None): Sleep data.
            df_cpet (pd.DataFrame | None): CPET data.

        Returns:
            None
        """

        self.data_window_controller.show_cgm_hr_combined(
            cgm_data=cgm_data,
            hr_series=hr_series,
            hr_res_series=hr_res_series,
            cgm_stats=cgm_stats,
            hr_stats=hr_stats,
            web_view=self.data_window_view.web_view1,
            activities=self.data_window_controller.plot_activity(df_act),
            meals=df_cal,
            sleep=df_sleep,
            cpet=df_cpet
        )

    # ----------------------- CLOSE EVENT ------------------------
    def closeEvent(
            self,
            event
    ):
        """
        Handle the window close event.

        This method cleans up temporary files before the application closes.

        Args:
            event (QCloseEvent): The close event triggered when the window is closing.
        """
        self.temp_service.cleanup()
        super().closeEvent(event)
