from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QTableWidget, QHBoxLayout, QPushButton, QSizePolicy, QStackedLayout
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, Signal

from app.ui.widgets.day_timeline_widget import DayTimelineWidget


class DataWindow(QWidget):
    """
    GUI class for the data display tab in the application.

    This class manages multiple sub-tabs for displaying CGM/HR graphs,
    calorie intake tables, activity tables, sleep tables, and accelerometer data visualizations.
    """

    next_day_clicked = Signal()
    prev_day_clicked = Signal()
    day_selected = Signal(object)

    def __init__(self):
        """
        Initialize the data display window with navigation controls,
        sub-tabs, and widgets for visualizing user data.

        Attributes:
            controller (object | None):
                Controller associated with this view.

            canvas (object | None):
                Placeholder for optional plot canvas.

            layout (QVBoxLayout):
                Main vertical layout of the window.

            bar_layout (QHBoxLayout):
                Top navigation bar containing buttons and labels.

            btn_prev (QPushButton):
                Button for switching to the previous day.

            btn_next (QPushButton):
                Button for switching to the next day.

            center_layout (QVBoxLayout):
                Center layout containing ID and date labels.

            label_id (QLabel):
                Label displaying selected user ID.

            label_day (QLabel):
                Label displaying selected date.

            sub_tabs (QTabWidget):
                Main tab widget containing all data sub-tabs.
        """

        super().__init__()
        self.controller = None
        self.canvas = None
        self.setWindowTitle("Data view")

        # Main layout
        self.layout = QVBoxLayout(self)

        # ---------------------------------------------------
        # Header: Navigation + Day timeline
        # ---------------------------------------------------
        self.header_layout = QVBoxLayout()

        # ---------------------------------------------------
        # Row 1: Previous / ID + Date / Next
        # ---------------------------------------------------
        self.bar_layout = QHBoxLayout()

        # Previous day button
        self.btn_prev = QPushButton("← Previous day")
        self.bar_layout.addWidget(self.btn_prev)
        self.btn_prev.clicked.connect(self.on_prev_day_clicked)

        # ID + Date
        self.center_layout = QVBoxLayout()
        self.center_layout.setAlignment(Qt.AlignCenter)

        self.label_id = QLabel("ID")
        self.label_day = QLabel("Date")

        self.label_id.setAlignment(Qt.AlignCenter)
        self.label_day.setAlignment(Qt.AlignCenter)

        self.label_id.setStyleSheet(
            "font-weight: bold; font-size: 14px;"
        )
        self.label_day.setStyleSheet(
            "font-size: 13px;"
        )

        self.center_layout.addWidget(self.label_id)
        self.center_layout.addWidget(self.label_day)

        self.bar_layout.addLayout(self.center_layout, stretch=1)

        # Next day button
        self.btn_next = QPushButton("Next day →")
        self.bar_layout.addWidget(self.btn_next)
        self.btn_next.clicked.connect(self.on_next_day_clicked)

        self.header_layout.addLayout(self.bar_layout)

        # ---------------------------------------------------
        # Row 2: Day timeline
        # ---------------------------------------------------

        self.day_timeline = DayTimelineWidget()
        self.day_timeline.daySelected.connect(
            self.on_day_selected
        )

        self.header_layout.addWidget(self.day_timeline)

        # ---------------------------------------------------
        # Add complete header
        # ---------------------------------------------------
        self.layout.addLayout(self.header_layout)

        # ---------------------------------------------------
        # Subtabs
        # ---------------------------------------------------
        self.sub_tabs = QTabWidget()
        self.layout.addWidget(self.sub_tabs)

        # ---------------------------------------------------
        # Subtab 1: CGM a HR
        # ---------------------------------------------------
        self.cgm_tab = QWidget()
        self.cgm_layout = QVBoxLayout(self.cgm_tab)
        self.sub_tabs.addTab(self.cgm_tab, "CGM && HR")

        self.web_view1 = QWebEngineView()
        self.cgm_layout.addWidget(self.web_view1)

        # ----------------------------------------------------
        # Subtab 2: Calory table
        # ----------------------------------------------------
        self.cal_tab = QWidget()
        self.cal_layout = QVBoxLayout(self.cal_tab)
        self.sub_tabs.addTab(self.cal_tab, "Meals")
        self.cal_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.cal_label = QLabel("Meals")
        self.cal_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.cal_layout.addWidget(self.cal_label)

        self.cal_tableWidget = QTableWidget()
        self.cal_layout.addWidget(self.cal_tableWidget)

        # ----------------------------------------------------
        # Subtab 3: Activities + Sleep
        # ----------------------------------------------------

        self.act_tab = QWidget()
        self.act_layout = QVBoxLayout(self.act_tab)
        self.sub_tabs.addTab(self.act_tab, "Activities")
        self.act_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # --- ACTIVITIES ---
        self.act_label = QLabel("Activities")
        self.act_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.act_layout.addWidget(self.act_label)

        self.act_table = QTableWidget()
        self.act_layout.addWidget(self.act_table, stretch=3)
        self.act_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- STEPS ---
        self.step_label = QLabel("Steps")
        self.step_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.act_layout.addWidget(self.step_label)

        self.step_table = QTableWidget()
        self.act_layout.addWidget(self.step_table, stretch=1)
        self.step_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.step_table.setMaximumHeight(120)

        # --- SLEEP ---
        self.sleep_label = QLabel("Sleep")
        self.sleep_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.act_layout.addWidget(self.sleep_label)

        self.sleep_table = QTableWidget()
        self.act_layout.addWidget(self.sleep_table, stretch=1)
        self.sleep_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        # --------------------------------------------------------------------------
        # Subtab 4: CPET summary
        # ------------------------------------------------------------------------
        self.cpet_tab = QWidget()
        self.cpet_layout = QHBoxLayout(self.cpet_tab)
        self.sub_tabs.addTab(self.cpet_tab, "CPET")

        self.cpet_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # --- SUMMARY ---
        self.cpet_sum_layout = QVBoxLayout()
        self.cpet_sum_label = QLabel("CPET summary")
        self.cpet_sum_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.cpet_sum_table = QTableWidget()

        self.cpet_sum_layout.addWidget(self.cpet_sum_label)
        self.cpet_sum_layout.addWidget(self.cpet_sum_table)

        # --- METADATA ---
        self.cpet_meta_layout = QVBoxLayout()
        self.cpet_meta_label = QLabel("CPET metadata")
        self.cpet_meta_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.cpet_meta_table = QTableWidget()

        self.cpet_meta_layout.addWidget(self.cpet_meta_label)
        self.cpet_meta_layout.addWidget(self.cpet_meta_table)

        # ------
        self.cpet_layout.addLayout(self.cpet_sum_layout)
        self.cpet_layout.addLayout(self.cpet_meta_layout)

        # --------------------------------------------------------------------------
        # Subtab 5: Accelerometer
        # ------------------------------------------------------------------------
        self.acc_tab = QWidget()
        self.acc_layout = QVBoxLayout(self.acc_tab)
        self.sub_tabs.addTab(self.acc_tab, "Accelerometer data")


        self.web_view3 = QWebEngineView()
        self.acc_stack = QStackedLayout()
        self.acc_stack.addWidget(self.web_view3)

        self.acc_loading = QLabel("Loading chart...")
        self.acc_loading.setAlignment(Qt.AlignCenter)

        self.acc_stack.addWidget(self.acc_loading)
        self.acc_layout.addLayout(self.acc_stack)

        self.acc_stack.setCurrentWidget(self.web_view3)

        # -------------------------------------------------------------------------
        # Main layout set
        # -------------------------------------------------------------------
        self.setLayout(self.layout)

    def set_controller(
            self,
            controller: object
    ):
        """
        Assign a controller to this view.

        Args:
            controller (object): Controller instance to handle logic for this view.
        """
        self.controller = controller

    def on_next_day_clicked(self):
        """
        Emit signal when the next day button is clicked.

        Returns:
            None
        """
        self.next_day_clicked.emit()

    def on_prev_day_clicked(self):
        """
        Emit signal when the previous day button is clicked.

        Returns:
            None
        """
        self.prev_day_clicked.emit()

    def display_date_bar(
            self,
            selected_date: str
    ):
        """
        Update the displayed date in the top navigation bar.

        Args:
            selected_date (str):
                Date string to display.

        Returns:
            None
        """
        self.label_day.setText(f"Current day: {selected_date}")

    def update_timeline(self, selected_day, available_days):
        """
        Update the day timeline with available and selected dates.

        Args:
            selected_day:
                Currently selected date to highlight.

            available_days:
                Collection of available dates to display.
        """

        self.day_timeline.set_days(
            available_days,
            selected_day
        )

    def on_day_selected(self, day):
        """
        Handle day selection from the timeline widget.

        Args:
            day:
                Selected date received from the timeline widget.
        """

        print(day)
        self.day_selected.emit(day)

    def display_user_file(
            self,
            selected_user_file: str
    ):
        """
        Update the displayed user ID in the top navigation bar.

        Args:
            selected_user_file (str):
                User identifier to display.

        Returns:
            None
        """
        self.label_id.setText(f"ID: {selected_user_file}")

    def prev_day_button_enable(
            self,
            enable: bool
    ):
        """
        Enable or disable the previous day button.

        Args:
            enable (bool):
                True to enable the button, False to disable it.

        Returns:
            None
        """
        self.btn_prev.setEnabled(enable)

    def next_day_button_enable(
            self,
            enable: bool
    ):
        """
        Enable or disable the next day button.

        Args:
            enable (bool):
                True to enable the button, False to disable it.

        Returns:
            None
        """
        self.btn_next.setEnabled(enable)

    def show_no_data_message(
            self,
            layout_or_widget,
            message="No data available"
    ):
        """
        Display a no-data message inside the specified widget or layout.

        The method removes any previously displayed no-data message, hides
        existing content, stores the original layout settings, and inserts
        a centered label informing the user that no data are available.

        Args:
            layout_or_widget:
                Target widget or layout where the no-data message will be shown.

            message:
                Text displayed when no data are available.
        """

        self.clear_no_data_message(layout_or_widget)

        if isinstance(layout_or_widget, QWidget):
            widget = layout_or_widget
            layout = widget.layout() or QVBoxLayout(widget)
        else:
            layout = layout_or_widget
            widget = layout.parentWidget()

        self._set_layout_visible(layout, False)

        widget.setProperty("orig_margins", layout.getContentsMargins())
        widget.setProperty("orig_spacing", layout.spacing())

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        label = QLabel(message, widget)
        label.setProperty("is_no_data_msg", True)
        label.setAlignment(Qt.AlignCenter)

        label.setStyleSheet("""
            QLabel {
                color: gray;
                font-size: 14px;
                font-style: italic;
                background-color: white;
                border-radius: 4px;
            }
        """)

        layout.addWidget(label)

    def clear_no_data_message(
            self,
            layout_or_widget,
            *args
    ):
        """
        Remove the no-data message and restore the original layout state.

        The method removes previously displayed no-data message widgets,
        restores stored layout margins and spacing, and makes hidden widgets
        visible again.

        Args:
            layout_or_widget:
                Target widget or layout containing the no-data message.

            *args:
                Additional unused arguments for compatibility with callers.
        """

        if isinstance(layout_or_widget, QWidget):
            widget = layout_or_widget
            layout = widget.layout()
        else:
            layout = layout_or_widget
            widget = layout.parentWidget() if layout else None

        if not layout:
            return

        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            w = item.widget()

            if w and w.property("is_no_data_msg"):
                layout.removeWidget(w)
                w.deleteLater()

        if widget:
            margins = widget.property("orig_margins")
            spacing = widget.property("orig_spacing")

            if margins:
                layout.setContentsMargins(*margins)

            if spacing is not None:
                layout.setSpacing(spacing)

        self._set_layout_visible(layout, True)

    def _set_layout_visible(self, layout, visible):
        """
        Set visibility recursively for all widgets in a layout.

        Args:
            layout:
                Layout whose child widgets should be updated.

            visible:
                Visibility state to apply to contained widgets.
        """

        for i in range(layout.count()):
            item = layout.itemAt(i)

            if item.widget():
                item.widget().setVisible(visible)

            elif item.layout():
                self._set_layout_visible(item.layout(), visible)



