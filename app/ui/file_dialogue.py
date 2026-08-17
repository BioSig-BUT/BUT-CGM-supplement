from PySide6.QtWidgets import (
    QWidget, QPushButton, QFileDialog, QVBoxLayout,
    QLabel, QCheckBox, QHBoxLayout, QScrollArea, QComboBox, QMessageBox, QGroupBox
)
from PySide6.QtCore import Signal


class FileDialogue(QWidget):
    """
    GUI class for selecting data files and time ranges.

    Provides sections for selecting a database folder, choosing files
    to display, and selecting a time range for the data.

    Signals:
        data_loaded: Emitted when data has been successfully loaded.
    """

    data_loaded = Signal()

    def __init__(self, ):
        """
        Initialize the file selection dialog with all groups, layouts, and widgets.

        Attributes:
            controller (object | None): Controller associated with this view.
            db_group_box (QGroupBox): Group box for database selection.
            file_group_box (QGroupBox): Group box for file selection.
            time_group_box (QGroupBox): Group box for time range selection.
            combo (QComboBox): Dropdown for selecting user folders.
            checkbox_layout (QVBoxLayout): Layout holding checkboxes for files.
            day_selector (QComboBox): Dropdown for selecting a specific day.
            open_data_button (QPushButton): Button to open data after selection.
        """
        super().__init__()
        self.controller = None
        self.setWindowTitle("Data file selection")

        # ---------------- Database group-----------------
        self.db_group_box = QGroupBox("Database")
        self.db_group_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid gray;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)

        self.label1 = QLabel()
        self.label1.setText("Select the folder containing the database.")

        self.select_file_button = QPushButton("Select database folder")
        self.select_file_button.setFixedWidth(200)
        self.select_file_button.clicked.connect(self.open_dialogue)

        self.selected_folder_label = QLabel()
        self.selected_folder_label.setText("No folder selected")

        # ------------------ File group------------------------------
        self.file_group_box = QGroupBox("Data")
        self.file_group_box.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid gray;
                        border-radius: 5px;
                        margin-top: 10px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 3px;
                    }
                """)

        self.label2 = QLabel()
        self.label2.setText("Select measurement to display.")

        self.combo = QComboBox()
        self.combo.setFixedWidth(400)
        self.combo.activated.connect(self.reset_combo)

        self.show_files_button = QPushButton("Display available data")
        # self.show_files_button.setFixedHeight(40)
        self.show_files_button.setFixedWidth(200)
        self.show_files_button.clicked.connect(self.show_checkboxes)

        self.label = QLabel("Select data to display.")

        self.load_data_button = QPushButton("Load data")
        self.load_data_button.setFixedWidth(200)
        self.load_data_button.clicked.connect(self.confirm_selection)

        # -------------------- Time range group--------------
        self.time_group_box = QGroupBox("Time range")
        self.time_group_box.setStyleSheet("""
                            QGroupBox {
                                border: 1px solid gray;
                                border-radius: 5px;
                                margin-top: 10px;
                            }
                            QGroupBox::title {
                                subcontrol-origin: margin;
                                left: 10px;
                                padding: 0 3px;
                            }
                        """)

        self.time_range_label = QLabel("Time range not yet determined")

        self.day_selector_label = QLabel()
        self.day_selector_label.setText("Select day:")

        self.day_selector = QComboBox()
        self.day_selector.setFixedWidth(400)
        self.day_selector.setEnabled(False)

        self.open_data_button = QPushButton("Show data")
        self.open_data_button.setFixedWidth(200)

        self.sel_all_button = QPushButton("Select all")
        self.sel_all_button.setFixedWidth(200)
        self.sel_all_button.clicked.connect(self.select_all)

        self.sel_not_button = QPushButton("Deselect all")
        self.sel_not_button.setFixedWidth(200)
        self.sel_not_button.clicked.connect(self.clear_all)

        # Scroll area for checkboxy
        self.checkbox_area = QScrollArea()
        self.checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_container)
        self.checkbox_area.setWidgetResizable(True)
        self.checkbox_area.setWidget(self.checkbox_container)

        # ------------ Layout---------------------
        layout = QVBoxLayout()

        db_group_box_layout = QVBoxLayout()
        db_group_box_layout.addWidget(self.label1)
        db_group_box_layout.addWidget(self.select_file_button)
        db_group_box_layout.addWidget(self.selected_folder_label)

        self.db_group_box.setLayout(db_group_box_layout)
        layout.addWidget(self.db_group_box)

        file_group_box_layout = QVBoxLayout()
        file_group_box_layout.addWidget(self.label2)
        file_group_box_layout.addWidget(self.combo)
        file_group_box_layout.addWidget(self.show_files_button)
        file_group_box_layout.addWidget(self.label)

        sel_but_layout = QVBoxLayout()
        sel_but_layout.addWidget(self.sel_all_button)
        sel_but_layout.addWidget(self.sel_not_button)

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.checkbox_area)
        h_layout.addLayout(sel_but_layout)

        file_group_box_layout.addLayout(h_layout)
        file_group_box_layout.addWidget(self.load_data_button)

        self.file_group_box.setLayout(file_group_box_layout)
        layout.addWidget(self.file_group_box)

        time_group_box_layout = QVBoxLayout()

        time_group_box_layout.addWidget(self.time_range_label)
        time_group_box_layout.addWidget(self.day_selector_label)
        time_group_box_layout.addWidget(self.day_selector)
        time_group_box_layout.addWidget(self.open_data_button)

        self.time_group_box.setLayout(time_group_box_layout)
        layout.addWidget(self.time_group_box)

        self.setLayout(layout)

    def set_controller(
            self,
            controller: object
    ):
        """
        Assign a controller to this view and connect signals.

        Args:
            controller: Controller instance to handle logic for this view.
        """
        self.controller = controller
        self.open_data_button.clicked.connect(self.controller.on_show_data_clicked)

    def open_dialogue(self):
        """
        Open a folder selection dialog for the database and update the UI.
        """
        self.database_folder = QFileDialog.getExistingDirectory(self, caption="Select folder", dir="")
        if self.database_folder:
            self.selected_folder_label.setText(f"Selected folder: {self.database_folder}")
            self.controller.add_folders_to_combo(self.database_folder)

    def reset_combo(self):
        """
        Clear previous checkboxes and reset time range label and day selector.
        """
        # clear checkboxes
        while self.checkbox_layout.count():
            item = self.checkbox_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Sets time label
        self.time_range_label.setText("Time range not yet determined")

        self.day_selector.clear()

    def update_combobox(
            self,
            items: list[str]
    ):
        """
        Update the user folder dropdown with new items.

        Args:
            items (list[str]): List of folder names to populate the combo box.
        """
        self.combo.clear()
        self.combo.addItems(items)

    def show_checkboxes(self):
        """
        Trigger controller to display checkboxes for available files.
        """
        self.controller.on_show_files_requested()

    def display_checkboxes(
            self,
            file_names: list[str]
    ):
        """
        Populate the checkbox layout with file names.

        Args:
            file_names (list[str]): List of file names to create checkboxes for.
        """

        # Clear previous checkboxes
        for i in reversed(range(self.checkbox_layout.count())):
            widget = self.checkbox_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Create new checkboxes
        for name in file_names:
            checkbox = QCheckBox(name, checked=True)
            self.checkbox_layout.addWidget(checkbox)

    def get_checked_files(self) -> list[str]:
        """
        Retrieve the list of files currently checked by the user.

        Returns:
            list[str]: Names of checked files.
        """
        checked_files = []
        for i in range(self.checkbox_layout.count()):
            widget = self.checkbox_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                checked_files.append(widget.text())
        return checked_files

    def confirm_selection(self):
        """
        Confirm the selected user and files, notifying the controller.
        """
        user = self.combo.currentText()
        files = self.get_checked_files()
        self.controller.on_files_confirmed(user, files, self.database_folder)

    def show_no_files_warning(self):
        """
        Display a warning message if no files are selected.
        """
        QMessageBox.information(self, "Warning", "No file selected.")

    def select_all(self):
        """
        Check all file checkboxes.
        """
        for i in range(self.checkbox_layout.count()):
            widget = self.checkbox_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox):
                widget.setChecked(True)

    def clear_all(self):
        """
        Uncheck all file checkboxes.
        """
        for i in range(self.checkbox_layout.count()):
            widget = self.checkbox_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)

    def update_time_range(
            self,
            days: list,
            start,
            end
    ):
        """
        Update the day selector combo box and display the selected time range.

        Args:
            days (list[datetime]): List of available days.
            start (datetime): Start of the overall time range.
            end (datetime): End of the overall time range.
        """
        self.day_selector.clear()

        for d in sorted(days):
            self.day_selector.addItem(d.strftime("%Y-%m-%d"), d)

        self.day_selector.setEnabled(True)

        self.time_range_label.setText(
            f"Time range: {start.date()} – {end.date()}" # date only
            # f"Time range: {start} – {end}"             # date + time
        )


