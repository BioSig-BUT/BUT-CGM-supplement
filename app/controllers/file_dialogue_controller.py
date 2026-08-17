import pandas as pd
from PySide6.QtCore import Signal, QObject

from app.services.file_service import FileCategorizer
from app.services.time_range_service import TimeRangeService


class FileDialogueController(QObject):
    """
    Controller responsible for handling file selection and data preparation in the GUI.

    This class acts as a bridge between the View (UI) and the Model, managing
    file categorization, user selection, and time-range analysis.

    Attributes:
        data_ready (Signal): Qt Signal emitted when the data model is fully prepared
            and ready for display.
        model: The data model object where processed information is stored.
        view: The UI view object representing the file selection dialog.
        time_range_service (TimeRangeService): Service for analyzing date ranges
            and file availability.
        virtual_db (dict): A mapping of categorized folders and their file paths.
    """

    data_ready = Signal()

    def __init__(self, view, model):
        """
        Initializes the controller with a view and a model.

        Args:
            view: The UI component this controller will manage.
            model: The data structure where the final selection will be saved.
        """
        super().__init__()
        self.model = model
        self.view = view
        self.view.set_controller(self)

        self.time_range_service = TimeRangeService()
        self.virtual_db = {}

        if self.view:
            self._connect_signals()

    def set_view(
            self,
            view,
    ):
        """
        Links the controller to a specific view and initializes signal connections.

        Args:
            view: The UI view instance to be connected.
        """
        self.view = view
        self._connect_signals()

    def _connect_signals(self):
        """
        Connect UI signals to controller slots.
        """
        self.view.open_data_button.clicked.connect(self.on_show_data_clicked)

    def add_folders_to_combo(
            self,
            base_path: str,
    ):
        """
        Load, categorize files from the base path and populate the user selector.

        Args:
            base_path: Root directory containing user data folders.
        """
        self.virtual_db = FileCategorizer(base_path)
        self.virtual_db.categorize_files()
        virtual_db = self.virtual_db.create_virtual_structure()

        foldernames = virtual_db.keys()

        # Pass folder names back to the UI
        self.view.update_combobox(foldernames)

    def on_show_files_requested(self):
        """
        Handles the request to display available files for the currently selected user.
        """
        user = self.view.combo.currentText()
        files = self.get_files_for_user(user)
        self.view.display_checkboxes(sorted(files))

    def get_files_for_user(
            self,
            user_folder: str,
    ) -> list[str]:
        """
        Retrieve all virtual file names available for a given user.

        Args:
            user_folder: Selected user folder name.

        Returns:
            A list of virtual file names.
        """
        user_files = []
        files = self.virtual_db[user_folder]
        for vname, real_path in files.items():
             user_files.append(vname)

        return user_files

    def on_files_confirmed(
            self,
            user: str,
            files: list[str],
            base_dir_path
    ):
        """
        Handle confirmation of selected files and update application data.

        If no files are selected, files for the selected user are loaded
        automatically. The method analyzes the selected files, updates the
        available time range, and stores the resulting file context and
        available days in the model.

        Args:
            user: Selected user folder name.
            files: Selected virtual file names.
            base_dir_path: Base directory path used for file analysis.
        """
        if not files:
            self.view.show_no_files_warning()
            files = self.get_files_for_user(user)

        result = self.time_range_service.analyze(
            self.virtual_db,
            files,
            user
        )

        self.model.available_days = result.available_days
        self.model.file_context = result.file_context

        self.view.update_time_range(
            result.available_days,
            result.start_time,
            result.end_time
        )

    def on_show_data_clicked(self):
        """
        Process final selection, update the model, and emit signal that data is ready.

        The method:
        - Reads selected user, files, and day from the UI
        - Validates selection
        - Uses TimeRangeService to resolve file paths and metadata
        - Computes start and end time for the selected day
        - Stores all resolved values into the shared model
        - Emits `data_ready` signal

        Returns:
            None
        """
        selected_user_file = self.view.combo.currentText()
        selected_files = self.view.get_checked_files()
        selected_day = self.view.day_selector.currentText()

        if not selected_files:
            self.view.show_no_files_warning()
            return

        result = self.time_range_service.analyze(
            self.virtual_db,
            selected_files,
            selected_user_file
        )

        # Start/end time for the selected day
        start_time = self.view.day_selector.currentData()

        # End of the same day
        end_time = (
                start_time.normalize()
                + pd.Timedelta(days=1)
                - pd.Timedelta(microseconds=1)
        )

        # Store data into model
        self.model.selected_user_file = selected_user_file
        self.model.selected_files = selected_files
        self.model.selected_day = selected_day
        self.model.start_time = start_time
        self.model.end_time = end_time

        self.model.cgm_file_paths = [result.file_context.get("CGM")]
        self.model.hr_file_paths = [v for k, v in result.file_context.items() if "HR" in k]
        self.model.acc_file_paths = [v for k, v in result.file_context.items() if "ACC" in k]
        self.model.cal_table_file_path = result.file_context.get("Meals")
        self.model.act_table_file_path = result.file_context.get("Activities")
        self.model.sleep_file_path = result.file_context.get("Sleep")
        self.model.steps_sum_file_path = result.file_context.get("Steps")
        self.model.meal_sum_file_path = result.file_context.get("Meal summary")
        self.model.cpet_sum_file_path = result.file_context.get("CPET summary")
        self.model.cpet_meta_file_path = result.file_context.get("CPET metadata")

        # Signal UI that data is ready
        self.data_ready.emit()

    def shift_day(self, offset: int):
        """
        Shift the currently selected day forward or backward and reload related data.

        The method:
        - Checks if a valid start time exists in the model
        - Finds the current index in available days
        - Applies the given offset to move to a new day
        - Re-analyzes file context via TimeRangeService
        - Updates the model with new time range and file paths
        - Emits `data_ready` signal

        Args:
            offset (int):
                Day shift offset (e.g. -1 for previous day, +1 for next day).

        Returns:
            None
        """

        if self.model.start_time is None:
            return

        available = sorted(self.model.available_days)

        if self.model.start_time not in available:
            return

        idx = available.index(self.model.start_time)
        new_idx = idx + offset

        if new_idx < 0 or new_idx >= len(available):
            return

        new_start_time = available[new_idx]

        selected_user_file = self.model.selected_user_file
        selected_files = self.model.selected_files

        result = self.time_range_service.analyze(
            self.virtual_db,
            selected_files,
            selected_user_file
        )

        end_time = (
                new_start_time
                + pd.Timedelta(days=1)
                - pd.Timedelta(microseconds=1)
        )

        self.model.start_time = new_start_time
        self.model.end_time = end_time
        self.model.selected_day = new_start_time.strftime("%Y-%m-%d")

        self.model.cgm_file_paths = [result.file_context.get("CGM")]
        self.model.hr_file_paths = [v for k, v in result.file_context.items() if "HR" in k]
        self.model.acc_file_paths = [v for k, v in result.file_context.items() if "ACC" in k]
        self.model.cal_table_file_path = result.file_context.get("Meals")
        self.model.act_table_file_path = result.file_context.get("Activities")
        self.model.sleep_file_path = result.file_context.get("Sleep")
        self.model.steps_sum_file_path = result.file_context.get("Steps")
        self.model.meal_sum_file_path = result.file_context.get("Meal summary")

        self.data_ready.emit()

    def on_timeline_clicked(self, timeline_clicked_day):
        """
        Process final selection, update the model, and emit signal that data is ready.

        The method:
        - Reads selected user, files, and day from the UI
        - Validates selection
        - Uses TimeRangeService to resolve file paths and metadata
        - Computes start and end time for the selected day
        - Stores all resolved values into the shared model
        - Emits `data_ready` signal

        Returns:
            None
        """
        new_start_time = timeline_clicked_day

        selected_user_file = self.model.selected_user_file
        selected_files = self.model.selected_files

        result = self.time_range_service.analyze(
            self.virtual_db,
            selected_files,
            selected_user_file
        )

        end_time = (
                new_start_time
                + pd.Timedelta(days=1)
                - pd.Timedelta(microseconds=1)
        )

        self.model.start_time = new_start_time
        self.model.end_time = end_time
        self.model.selected_day = new_start_time.strftime("%Y-%m-%d")

        self.model.cgm_file_paths = [result.file_context.get("CGM")]
        self.model.hr_file_paths = [v for k, v in result.file_context.items() if "HR" in k]
        self.model.acc_file_paths = [v for k, v in result.file_context.items() if "ACC" in k]
        self.model.cal_table_file_path = result.file_context.get("Meals")
        self.model.act_table_file_path = result.file_context.get("Activities")
        self.model.sleep_file_path = result.file_context.get("Sleep")
        self.model.steps_sum_file_path = result.file_context.get("Steps")
        self.model.meal_sum_file_path = result.file_context.get("Meal summary")

        self.data_ready.emit()

