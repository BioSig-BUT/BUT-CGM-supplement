from PySide6.QtCore import (QUrl, QTimer)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidgetItem
)

import time
from datetime import datetime
import pandas as pd

import plotly.graph_objects as go
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from app.services.temp_file_service import TempFileService
from app.services.cgm_service import CGMService
from app.services.hr_service import HRService
from app.services.activity_service import ActivityService
from app.services.calory_service import CaloryService
from app.services.acc_service import ACCService
from app.services.sleep_service import SleepService
from app.services.cpet_service import CPETService

from app.ui.themes.plot_theme import PlotTheme


class DataWindowController(QWidget):
    """
    Controller for processing and visualizing physiological and activity data.

    This controller manages various data services (CGM, EDF, HR, etc.) and transforms
    raw data into interactive Plotly visualizations or PySide6 table widgets.
    It handles the logic for data resampling, filtering by time range, and
    displaying fallback messages when data is missing.

    Attributes:
        view: The UI window instance this controller manages.
        model: Data container holding shared application state.
        temp_service (TempFileService): Service for managing temporary HTML files for plots.
        cgm_service (CGMService): Service for processing glucose monitoring data.
        hr_service (HRService): Service for heart rate data processing.
        calory_service (CaloryService): Service for nutritional/calory data.
        activity_service (ActivityService): Service for physical activity logs.
    """

    def __init__(self, view, model):
        """
        Initialize the data window controller.

        Args:
            view: UI view responsible for displaying plots and tables.
            model: Application model containing selected files and time range.
        """
        super().__init__()
        self.view = view
        self.model = model
        self.view.set_controller(self)

        self.temp_service = TempFileService()
        self.cgm_service = CGMService()
        self.hr_service = HRService()
        self.acc_service = ACCService()
        self.calory_service = CaloryService()
        self.activity_service = ActivityService()
        self.sleep_service = SleepService()
        self.cpet_service = CPETService()

    def cleanup(self):
        """
        Clean up temporary files created during plotting.
        """
        self.temp_service.cleanup()

    # ------------------------------------------------------------------
    # Generic UI helpers
    # ------------------------------------------------------------------

    def update_display(
            self,
            layout_or_widget,
            data,
            no_data_message: str = "No data available",
    ) -> bool:
        """
        Show or hide UI elements depending on data availability.

        Args:
            layout_or_widget: Target widget or layout.
            data: Data to be checked for availability.
            no_data_message: Message shown when no data are available.

        Returns:
            True if data are available, otherwise False.
        """
        if data is None or (hasattr(data, "empty") and data.empty) or (
                isinstance(data, (list, tuple)) and not data):
            self.view.show_no_data_message(layout_or_widget, no_data_message)
            return False

        self.view.clear_no_data_message(layout_or_widget, no_data_message)

        if isinstance(layout_or_widget, QVBoxLayout):
            for i in range(layout_or_widget.count()):
                widget = layout_or_widget.itemAt(i).widget()
                if widget:
                    widget.show()
        else:
            layout_or_widget.show()

        return True

    def display_plot(
            self,
            fig,
            web_view,
            stack=None
    ) -> None:
        """
        Renders a Plotly figure as HTML and loads it into a QWebEngineView.

        If no figure is provided, the web view is replaced with a no-data message.
        During plot loading, the web view content is temporarily cleared to prevent
        displaying an outdated chart. Optionally, a QStackedWidget can be used to
        switch between loading and chart display states.

        Args:
            fig: Plotly figure to display.
            web_view: The PySide6 web view widget where the plot will be shown.
            stack: Optional QStackedWidget used to switch between loading and
                   chart display pages.

        Returns:
            None: The function renders the figure in the provided web view.
                  If `fig` is None, a "no data" message is displayed instead.
        """

        if fig is None:
            self.view.show_no_data_message(
                web_view,
                "No chart data available"
            )
            return

        self.view.clear_no_data_message(
            web_view,
            "No chart data available"
        )

        web_view.setUpdatesEnabled(False)

        web_view.page().runJavaScript(
            """
            document.body.innerHTML = "";
            """
        )

        plot_name = f"plot_{time.time_ns()}.html"
        path = self.temp_service.save_plot_html(fig, plot_name)

        if path:

            def on_loaded(ok):

                if ok:
                    web_view.page().runJavaScript(
                        """
                        window.dispatchEvent(new Event('resize'));
                        """
                    )

                if stack:
                    stack.setCurrentIndex(0)

                web_view.loadFinished.disconnect(on_loaded)

            web_view.loadFinished.connect(on_loaded)

            web_view.setUpdatesEnabled(False)

            web_view.setHtml(
                "<html><body></body></html>"
            )

            def load_new_plot(ok):

                web_view.loadFinished.disconnect(load_new_plot)

                web_view.setUpdatesEnabled(True)

                web_view.page().runJavaScript(
                    """
                    window.dispatchEvent(new Event('resize'));
                    """
                )

            web_view.loadFinished.connect(load_new_plot)
            if stack:
                stack.setCurrentIndex(1)

            QTimer.singleShot(
                50,
                lambda: web_view.setUrl(QUrl.fromLocalFile(path))
            )

    def fill_table(
            self,
            table_widget,
            df: pd.DataFrame,
            datetime_format: str = "%H:%M",
    ):
        """
        Populate a QTableWidget with data from a pandas DataFrame.

        This method transfers tabular data from a pandas DataFrame into a Qt
        table widget. It handles empty datasets, formats datetime values, and
        configures both row and column headers.

        Args:
            table_widget:
                Target QTableWidget instance that will be filled with data.

            df (pd.DataFrame):
                Source DataFrame containing tabular data.

            datetime_format (str):
                Format string used for displaying datetime values
                (default: "%H:%M").

        Returns:
            None:
                The function modifies the UI component in-place.
                If the DataFrame is empty or None, the table is hidden
                and a "no data" message is displayed.
        """

        if df is None or df.empty:
            table_widget.hide()
            self.view.show_no_data_message(
                table_widget,
                "No table data available"
            )
            return

        table_widget.setRowCount(len(df))
        table_widget.setColumnCount(len(df.columns))
        table_widget.setHorizontalHeaderLabels(
            [str(col) for col in df.columns]
        )

        index_values = list(df.index)

        if all(isinstance(i, str) for i in index_values):
            row_labels = [str(i) for i in index_values]
        else:
            row_labels = [str(i + 1) for i in range(len(df))]

        table_widget.setVerticalHeaderLabels(row_labels)
        table_widget.verticalHeader().setVisible(True)

        for row_idx, (_, row) in enumerate(df.iterrows()):
            for col_idx, value in enumerate(row):

                if isinstance(value, pd.Timestamp):
                    value_str = value.strftime(datetime_format)

                else:
                    value_str = "" if pd.isna(value) else str(value)

                table_widget.setItem(
                    row_idx,
                    col_idx,
                    QTableWidgetItem(value_str)
                )

        table_widget.resizeColumnsToContents()
        table_widget.show()

    # ------------------------------------------------------------------
    # Accelerometer
    # ------------------------------------------------------------------

    def plot_acc_window(
            self,
            files: list,
            start_time: datetime,
            end_time: datetime,
            web_view,
            acc_stack,
            activities: pd.DataFrame | None,
            sleep: pd.DataFrame | None,
            cpet: pd.DataFrame | None
    ) -> None:
        """
        Plot accelerometer data for the selected time window.

        The method validates the availability of accelerometer data,
        creates the accelerometer figure, and displays it in the
        provided web view.

        Args:
            files (list):
                Accelerometer file path or collection of file paths.

            start_time (datetime):
                Start timestamp of the selected interval.

            end_time (datetime):
                End timestamp of the selected interval.

            web_view:
                Web view widget used for displaying the Plotly figure.

        Returns:
            None:
                The figure is displayed directly in the provided web view.
        """

        fig, data_added = self.create_accelerometer_figure(
            files=files,
            start_time=start_time,
            end_time=end_time,
            activities=activities,
            sleep=sleep,
            cpet=cpet
        )

        if data_added:
            self.view.clear_no_data_message(web_view)
            self.display_plot(fig, web_view, acc_stack)

    def create_accelerometer_figure(
            self,
            files: list,
            start_time: datetime,
            end_time: datetime,
            activities: pd.DataFrame | None,
            sleep: pd.DataFrame | None,
            cpet: pd.DataFrame | None
    ) -> [go.Figure, bool]:
        """
        Create a Plotly figure containing accelerometer signals.

        The figure contains three synchronized subplots representing
        accelerometer axes:

        - ACC_X
        - ACC_Y
        - ACC_Z

        The displayed data are filtered to the selected time interval
        and dynamically downsampled for efficient visualization.
        Additional annotations for activities, sleep periods, and CPET events
        are added when the corresponding data are available.

        Args:
            files (list):
                Accelerometer file path or collection of file paths.

            start_time (datetime):
                Start timestamp of the selected interval.

            end_time (datetime):
                End timestamp of the selected interval.

            activities (pd.DataFrame | None):
                Activity data used for adding annotations to the figure.

            sleep (pd.DataFrame | None):
                Sleep data used for adding annotations to the figure.

            cpet (pd.DataFrame | None):
                CPET data used for adding annotations to the figure.

        Returns:
            tuple[go.Figure, bool]:
                Tuple containing:

                - Plotly Figure object containing accelerometer traces.
                - Boolean indicating whether accelerometer data were added.
        """

        colors = PlotTheme.colors()

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
        )

        graph_colors = ["#1f77b4", "#2ca02c", "#ff7f0e"]

        axis_names = ["ACC_X", "ACC_Y", "ACC_Z"]

        trace_names = {
            "ACC_X": "X-axis",
            "ACC_Y": "Y-axis",
            "ACC_Z": "Z-axis",
        }

        data_added = False

        df = self.acc_service.load_acc(
            start_time=start_time,
            file_path=files,
        )

        if df is None or df.empty:
            return fig, False

        df = df[
            (df.index >= start_time) &
            (df.index <= end_time)
            ]

        if df.empty:
            return fig, False

        # Downsampling for display
        max_points = 250_000
        step = max(1, len(df) // max_points)


        # Add traces
        for axis_index, axis in enumerate(axis_names):
            fig.add_trace(
                go.Scattergl(
                    x=df.index[::step],
                    y=df[axis].values[::step],
                    mode="lines",
                    name=trace_names[axis],
                    line=dict(
                        color=graph_colors[axis_index],
                        width=1
                    ),
                ),
                row=axis_index + 1,
                col=1,
            )

            data_added = True

        fig.update_layout(
            title=dict(
                text="<b>Accelerometer data</b>",
                font=dict(
                    family="Segoe UI",
                    color=colors["text"]
                )
            ),
            hovermode="x unified",
            template="plotly_white",
            uirevision="constant",
            showlegend=True,

            legend=dict(
                x=1.05,
                y=0.5,
                xanchor="left",
                yanchor="middle",
                bgcolor="rgba(255,255,255,0)"
            ),

            margin=dict(
                l=80,
                r=60,
                t=60,
                b=40
            ),

            annotations=[

                dict(
                    text="<b>Acceleration [mg]</b>",
                    x=0,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    xshift=-70,
                    textangle=-90,
                    showarrow=False,
                    font=dict(
                        size=14,
                        family="Segoe UI",
                        color=colors["text"]
                    )
                ),

                dict(
                    text="<b>X-axis</b>",
                    x=1,
                    y=0.87,
                    xref="paper",
                    yref="paper",
                    xshift=25,
                    textangle=-90,
                    showarrow=False,
                    font=dict(
                        size=14,
                        family="Segoe UI",
                        color=colors["text"]
                    )
                ),

                dict(
                    text="<b>Y-axis</b>",
                    x=1,
                    y=0.50,
                    xref="paper",
                    yref="paper",
                    xshift=25,
                    textangle=-90,
                    showarrow=False,
                    font=dict(
                        size=14,
                        family="Segoe UI",
                        color=colors["text"]
                    )
                ),

                dict(
                    text="<b>Z-axis</b>",
                    x=1,
                    y=0.13,
                    xref="paper",
                    yref="paper",
                    xshift=25,
                    textangle=-90,
                    showarrow=False,
                    font=dict(
                        size=14,
                        family="Segoe UI",
                        color=colors["text"]
                    )
                )
            ]
        )

        self.add_acc_annotations(fig, activities, sleep, cpet)

        fig.update_yaxes(side="left", row=1, col=1)
        fig.update_yaxes(side="left", row=2, col=1)
        fig.update_yaxes(side="left", row=3, col=1)

        fig.update_xaxes(
            title=dict(
                text="<b>Time</b>",
                font=dict(
                    family="Segoe UI",
                    color=colors["text"]
                )
            ),
            row=3,
            col=1,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor"
        )

        self.add_acc_legend(fig)

        return fig, data_added

    def add_acc_annotations(
            self,
            fig: go.Figure,
            activities: pd.DataFrame | None,
            sleep: pd.DataFrame | None,
            cpet: pd.DataFrame | None
    ) -> None:
        """
        Add CGM-specific annotations to a single CGM figure.

        Args:
            fig (go.Figure):
                Plotly figure to which annotations will be added.

            cgm_data (pd.DataFrame):
                DataFrame containing CGM data with a "time" column.

            activities (pd.DataFrame | None):
                DataFrame with activity start times and durations.

            meals (pd.DataFrame | None):
                DataFrame with meal timestamps.

            sleep (pd.DataFrame | None):
                DataFrame with sleep intervals.

            cpet (pd.DataFrame | None):
                DataFrame with CPET activity start and duration.

        Returns:
            None
        """

        # Activities
        if activities is not None and not activities.empty:
            for _, row in activities.iterrows():
                fig.add_shape(
                    type="rect",
                    x0=row["start_time"],
                    x1=row["start_time"] + row["duration"],
                    y0=0, y1=1,
                    xref="x",
                    yref="paper",
                    fillcolor="orange",
                    opacity=0.3,
                    layer="below",
                    line_width=0
                )

        # CPET
        if cpet is not None and not cpet.empty:
            start_cpet = pd.to_datetime(
                cpet.loc[cpet["Field"].eq("Start Time"), "Value"].iloc[0], dayfirst=True, format="mixed",
                errors="coerce"
            )
            duration = pd.to_timedelta(cpet.loc[cpet["Field"].eq("Duration"), "Value"].iloc[0])
            end_cpet = start_cpet + duration

            fig.add_shape(
                type="rect",
                x0=start_cpet,
                x1=end_cpet,
                y0=0, y1=1,
                xref="x",
                yref="paper",
                fillcolor="rgba(180, 83, 9, 0.3)",
                layer="below",
                line_width=0
            )

        # Sleep
        if sleep is not None and not sleep.empty:
            for _, sleep_time in sleep.iterrows():
                # Morning
                if pd.notna(sleep_time["morning_from"]) and pd.notna(sleep_time["morning_to"]):
                    morning_from = datetime.combine(sleep_time["date"], sleep_time["morning_from"])
                    morning_to = datetime.combine(sleep_time["date"], sleep_time["morning_to"])

                    # CGM
                    fig.add_shape(
                        type="rect",
                        x0=morning_from,
                        x1=morning_to,
                        y0=0, y1=1,
                        xref="x",
                        yref="paper",
                        fillcolor="rgba(60, 30, 90, 0.35)",
                        layer="below",
                        line_width=0,
                    )

                # Evening
                if pd.notna(sleep_time["evening_from"]) and pd.notna(sleep_time["evening_to"]):
                    evening_from = datetime.combine(sleep_time["date"], sleep_time["evening_from"])
                    evening_to = datetime.combine(sleep_time["date"], sleep_time["evening_to"])

                    # CGM
                    fig.add_shape(
                        type="rect",
                        x0=evening_from,
                        x1=evening_to,
                        y0=0, y1=1,
                        xref="x",
                        yref="paper",
                        fillcolor="rgba(60, 30, 90, 0.3)",
                        layer="below",
                        line_width=0,
                    )

    def add_acc_legend(
            self,
            fig: go.Figure,
    ) -> None:
        """
        Add legend items for accelerometer-related annotations.

        The added legend entries represent additional annotated regions or
        events displayed in the accelerometer figure, including activities,
        CPET events, and sleep periods.

        Args:
            fig (go.Figure):
                Plotly figure to which the legend items will be added.

        Returns:
            None
        """
        # Activities
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="orange", opacity=0.3),
                name="Activities"
            ),
            row=1, col=1
        )

        # CPET
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="rgba(180, 83, 9, 0.5)"),
                name="CPET"
            )
        )

        # Sleep
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="rgba(60, 30, 90, 0.35)"),
                name="Sleep"
            ),
            row=1, col=1
        )

    # ------------------------------------------------------------------
    # Activity
    # ------------------------------------------------------------------
    def plot_activity(
            self,
            act_data: pd.DataFrame
    ) -> pd.DataFrame | None:
        """
        Create a DataFrame representing user activities with start time and duration.

        Args:
            act_data: Raw activity DataFrame

        Returns:
            DataFrame with columns:
                - start_time (datetime): Start of activity.
                - duration (timedelta): Duration of activity.
            Returns None if input data is None or empty.
        """

        if act_data is not None and not act_data.empty:
            start_time_series = pd.to_datetime(act_data["Time"], dayfirst=True, format="mixed", errors="coerce")
        else:
            print("act_data is None or empty DataFrame")
            return

        df_activity = pd.DataFrame({
            'start_time': pd.to_datetime(act_data["Time"], dayfirst=True, format="mixed", errors="coerce"),
            'duration': pd.to_timedelta(act_data["Duration"])
        })

        return df_activity

    # ------------------------------------------------------------------
    # CGM + HR
    # ------------------------------------------------------------------

    def show_cgm_hr_combined(
            self,
            cgm_data: pd.DataFrame | None,
            hr_series: pd.Series | None,
            hr_res_series: pd.Series | None,
            cgm_stats: dict,
            hr_stats: dict,
            web_view,
            activities: pd.DataFrame | None = None,
            meals: pd.DataFrame | None = None,
            sleep: pd.DataFrame | None = None,
            cpet: pd.DataFrame | None = None
    ) -> None:
        """
        Display a combined CGM + Heart Rate figure with a shared X-axis.

        Args:
            cgm_data (pd.DataFrame | None):
                CGM time series DataFrame with "time" and "glykemie" columns.

            hr_series (pd.Series | None):
                Raw heart rate time series.

            hr_res_series (pd.Series | None):
                Resampled/smoothed heart rate series.

            cgm_stats (dict):
                Dictionary with CGM statistics ("Min", "Max", "Average").

            hr_stats (dict):
                Dictionary with HR statistics ("Min", "Max", "Average").

            web_view:
                WebView object where the figure will be displayed.

            activities (pd.DataFrame | None, optional):
                Optional DataFrame with user activities.

            meals (pd.DataFrame | None, optional):
                Optional DataFrame with meal timestamps.

            sleep (pd.DataFrame | None, optional):
                Optional DataFrame with sleep intervals.

            cpet (pd.DataFrame | None, optional):
                Optional DataFrame with CPET measurement.

        Returns:
            None. The figure is displayed in the provided web_view.
        """

        cgm_available = cgm_data is not None and not cgm_data.empty
        hr_available = hr_series is not None and not hr_series.empty

        if not cgm_available and not hr_available:
            self.display_plot(None, web_view)
            return

        if cgm_available and not hr_available:
            fig = self.create_cgm_only_figure(
                cgm_data, cgm_stats, activities, meals, sleep, cpet
            )
            self.display_plot(fig, web_view)
            return

        if hr_available and not cgm_available:
            fig = self.create_hr_only_figure(
                hr_series, hr_res_series, hr_stats, activities, sleep, cpet
            )
            self.display_plot(fig, web_view)
            return

        fig = self.create_cgm_hr_combined_figure(
            cgm_data, hr_series, hr_res_series,
            cgm_stats, hr_stats,
            activities, meals, sleep, cpet
        )

        self.display_plot(fig, web_view)

    def create_cgm_only_figure(
            self,
            cgm_data: pd.DataFrame,
            cgm_stats: dict,
            activities: pd.DataFrame | None = None,
            meals: pd.DataFrame | None = None,
            sleep: pd.DataFrame | None = None,
            cpet: pd.DataFrame | None = None
    ) -> go.Figure:
        """
        Create a CGM-only figure with time series and statistics.

        Args:
            cgm_data (pd.DataFrame):
                CGM DataFrame with columns "time" and "glykemie".

            cgm_stats (dict):
                Dictionary with CGM statistics ("Min", "Max", "Průměr").

            activities (pd.DataFrame | None, optional):
                Optional DataFrame with activity start and duration.

            meals (pd.DataFrame | None, optional):
                Optional DataFrame with meal timestamps.

            sleep (pd.DataFrame | None, optional):
                Optional DataFrame with sleep intervals.

            cpet (pd.DataFrame | None, optional):
                Optional DataFrame with CPET measurement.

        Returns:
            go.Figure:
                Plotly Figure object containing CGM line plot,
                annotations, and statistics table.
        """

        colors = PlotTheme.colors()

        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.7, 0.3],
            specs=[[{"type": "xy"}, {"type": "domain"}]],
            subplot_titles=(
                "<b>Glucose level over time</b>",
                "<b>Statistics</b>"
            ),
            horizontal_spacing=0.05
        )

        fig.add_trace(
            go.Scatter(
                x=cgm_data["time"],
                y=cgm_data["glykemie"],
                mode="lines",
                line=dict(color="#5C7CFA"),
                name="Glucose level"
            ),
            row=1, col=1
        )

        self.add_cgm_annotations_single(fig, cgm_data, activities, meals, sleep, cpet)

        fig.add_trace(
            go.Table(
                columnwidth=[100, 150],
                header=dict(
                    values=["<b>Metric</b>", "<b>Glucose level</b><br>[mmol/l]"],
                    fill_color='#B8C1EC',
                    align='center',
                    font=dict(family="Segoe UI", size=12, color=colors["text"]),
                    height=40
                ),
                cells=dict(
                    values=[
                        ["Min", "Max", "Average"],
                        [cgm_stats["Min"], cgm_stats["Max"], cgm_stats["Average"]]
                    ],
                    fill_color=['#DCE3F7'] * 3,
                    align='center',
                    font=dict(family="Segoe UI", size=12, color=colors["text"]),
                    line_color='white',
                    height=30
                )
            ),
            row=1, col=2
        )

        fig.update_xaxes(title_text="<b>Time</b>", rangeslider=dict(visible=True, thickness=0.1), row=1, col=1)
        fig.update_yaxes(title_text="<b>Glucose level [mmol/l]</b>", row=1, col=1)

        self.add_cgm_legend_single(fig)

        fig.update_layout(
            template="plotly_white",
            font=dict(family="Segoe UI", size=13, color=colors["text"]),
            legend=dict(font=dict(family="Segoe UI", size=12))
        )

        fig.update_xaxes(
            title_font=dict(family="Segoe UI", size=13, color=colors["text"]),
            tickfont=dict(family="Segoe UI", size=12, color=colors["text"]),
            row=1, col=1
        )

        fig.update_yaxes(
            title_font=dict(family="Segoe UI", size=13, color=colors["text"]),
            tickfont=dict(family="Segoe UI", size=12, color=colors["text"]),
            row=1, col=1
        )

        return fig

    def create_hr_only_figure(
            self,
            hr_series: pd.Series,
            hr_res_series: pd.Series,
            hr_stats: dict,
            activities,
            sleep,
            cpet
    ) -> go.Figure:
        """
        Create a heart rate-only figure with raw and filtered HR series
        and statistics.

        Args:
            hr_series (pd.Series):
                Raw heart rate time series.

            hr_res_series (pd.Series):
                Filtered/resampled heart rate series.

            hr_stats (dict):
                Dictionary with HR statistics
                ("Min", "Max", "Průměr").

            activities:
                Activity annotation data used for adding
                activity markers into the figure.

            sleep:
                Sleep annotation data used for adding
                sleep intervals into the figure.

            cpet:
                CPET annotation data used for adding
                CPET markers into the figure.

        Returns:
            go.Figure:
                Plotly Figure object with HR line plots
                and statistics table.
        """

        colors = PlotTheme.colors()

        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.7, 0.3],
            specs=[[{"type": "xy"}, {"type": "domain"}]],
            subplot_titles=("<b>Heart rate</b>", "<b>Statistics</b>"),
            horizontal_spacing=0.05
        )

        fig.add_trace(
            go.Scatter(
                x=hr_series.index,
                y=hr_series.values,
                mode="lines",
                line=dict(color="#ff6f61"),
                name="Heart rate"
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=hr_res_series.index,
                y=hr_res_series.values,
                mode="lines",
                line=dict(color="#b22222"),
                name="Heart rate – filtered"
            ),
            row=1, col=1
        )

        self.add_hr_annotations_single(fig, activities, sleep, cpet)

        fig.add_trace(
            go.Table(
                columnwidth=[100, 150],
                header=dict(
                    values=["<b>Metric</b>", "<b>HR</b><br>[bpm]"],
                    fill_color='#FFB3A7',
                    align='center',
                    font=dict(family="Segoe UI", size=12, color=colors["text"]),
                    height=40
                ),
                cells=dict(
                    values=[
                        ["Min", "Max", "Average"],
                        [hr_stats["Min"], hr_stats["Max"], hr_stats["Average"]]
                    ],
                    fill_color=['#FFE1DB'] * 3,
                    align='center',
                    font=dict(family="Segoe UI", size=12, color=colors["text"]),
                    line_color='white',
                    height=30
                )
            ),
            row=1, col=2
        )

        fig.update_xaxes(title_text="<b>Time</b>", rangeslider=dict(visible=True, thickness=0.1), row=1, col=1)
        fig.update_yaxes(title_text="<b>HR [bpm]</b>", row=1, col=1)

        self.add_hr_legend_single(fig)

        fig.update_layout(
            template="plotly_white",
            font=dict(family="Segoe UI", size=13, color=colors["text"]),
            legend=dict(font=dict(family="Segoe UI", size=12))
        )

        fig.update_xaxes(
            title_font=dict(family="Segoe UI", size=13, color=colors["text"]),
            tickfont=dict(family="Segoe UI", size=12, color=colors["text"]),
            row=1, col=1
        )

        fig.update_yaxes(
            title_font=dict(family="Segoe UI", size=13),
            tickfont=dict(family="Segoe UI", size=12, color=colors["text"]),
            row=1, col=1
        )

        return fig

    def create_cgm_hr_combined_figure(
            self,
            cgm_data: pd.DataFrame,
            hr_series: pd.Series,
            hr_res_series: pd.Series,
            cgm_stats: dict,
            hr_stats: dict,
            activities: pd.DataFrame | None = None,
            meals: pd.DataFrame | None = None,
            sleep: pd.DataFrame | None = None,
            cpet: pd.DataFrame | None = None
    ) -> go.Figure:
        """
        Create a combined CGM + heart rate figure with statistics tables.

        Args:
            cgm_data (pd.DataFrame):
                CGM DataFrame with columns "time" and "glykemie".

            hr_series (pd.Series):
                Raw heart rate series.

            hr_res_series (pd.Series):
                Filtered/resampled HR series.

            cgm_stats (dict):
                Dictionary with CGM statistics ("Min", "Max", "Average").

            hr_stats (dict):
                Dictionary with HR statistics ("Min", "Max", "Average").

            activities (pd.DataFrame | None, optional):
                Optional DataFrame of user activities.

            meals (pd.DataFrame | None, optional):
                Optional DataFrame of meal timestamps.

            sleep (pd.DataFrame | None, optional):
                Optional DataFrame with sleep intervals.

            cpet (pd.DataFrame | None, optional):
                Optional DataFrame with CPET measurement.

        Returns:
            go.Figure:
                Plotly Figure object containing CGM and HR line plots,
                annotations, and statistics tables.
        """

        colors = PlotTheme.colors()

        fig = make_subplots(
            rows=2, cols=2,
            column_widths=[0.7, 0.3],
            row_heights=[0.5, 0.5],
            specs=[
                [{"type": "xy"}, {"type": "domain", "rowspan": 2}],
                [{"type": "xy"}, None]
            ],
            subplot_titles=(
                "<b>Glucose level over time</b>", "<b>Statistics</b>",
                "<b>Heart rate</b>", None
            )
        )

        # Glucose
        fig.add_trace(
            go.Scatter(
                x=cgm_data["time"],
                y=cgm_data["glykemie"],
                mode="lines",
                line=dict(color=colors["glucose_graph"]),
                name="Glucose level"
            ),
            row=1, col=1
        )

        fig.update_yaxes(
            title_text="<b>Glucose level [mmol/l]</b>",
            row=1, col=1
        )

        self.add_cgm_annotations_combined(fig, cgm_data, activities, meals, sleep, cpet)

        # Heart rate
        fig.add_trace(
            go.Scatter(
                x=hr_series.index,
                y=hr_series.values,
                mode="lines",
                line=dict(color=colors["hr_graph"]),
                name="Heart rate"
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=hr_res_series.index,
                y=hr_res_series.values,
                mode="lines",
                line=dict(color=colors["hr_filtered_graph"]),
                name="Heart rate – filtered"
            ),
            row=2, col=1
        )

        fig.update_xaxes(
            title_text="<b>Time</b>",
            rangeslider=dict(visible=True, thickness=0.08),
            row=2, col=1
        )
        fig.update_yaxes(
            title_text="<b>HR [bpm]</b>",
            row=2, col=1
        )

        # United table
        fig.add_trace(
            go.Table(
                columnwidth=[90, 110, 110],

                header=dict(
                    values=["<b>Metrics</b>", "<b>Glucose level</b><br>[mmol/l]", "<b>HR</b><br>[bpm]"],
                    fill_color=['#D1D5DB', '#B8C1EC', '#FFB3A7'],
                    align='center',
                    font=dict(family="Segoe UI", size=12, color=colors["text"]),
                    height=40
                ),
                cells=dict(
                    values=[
                        ["Min", "Max", "Average"],
                        [cgm_stats["Min"], cgm_stats["Max"], cgm_stats["Average"]],
                        [hr_stats["Min"], hr_stats["Max"], hr_stats["Average"]]
                    ],
                    fill_color=[
                        ['#ECEFF3'] * 3,
                        ['#DCE3F7'] * 3,
                        ['#FFE1DB'] * 3
                    ],
                    align='center',
                    font=dict(family="Segoe UI", size=12, color=colors["text"]),
                    line_color='white',
                    height=30
                )
            ),
            row=1, col=2
        )

        self.add_cgm_legend_combined(fig)

        fig.update_xaxes(matches="x")

        fig.update_layout(
            template="plotly_white",
            font=dict(family="Segoe UI", size=13, color=colors["text"]),
            legend=dict(font=dict(family="Segoe UI", size=12))
        )

        fig.update_annotations(
            font=dict(family="Segoe UI", size=16, color=colors["text"])
        )

        fig.update_xaxes(
            title_font=dict(family="Segoe UI", size=13, color=colors["text"]),
            tickfont=dict(family="Segoe UI", size=12, color=colors["text"]),
            row=1, col=1
        )

        fig.update_xaxes(
            title_font=dict(family="Segoe UI", size=13, color=colors["text"]),
            tickfont=dict(family="Segoe UI", size=12, color=colors["text"]),
            row=2, col=1
        )

        fig.update_yaxes(
            title_font=dict(family="Segoe UI", size=13, color=colors["text"]),
            tickfont=dict(family="Segoe UI", size=12, color=colors["text"]),
            row=1, col=1
        )

        fig.update_yaxes(
            title_font=dict(family="Segoe UI", size=13, color=colors["text"]),
            tickfont=dict(family="Segoe UI", size=12, color=colors["text"]),
            row=2, col=1
        )

        return fig

    def add_cgm_annotations_single(
            self,
            fig: go.Figure,
            cgm_data: pd.DataFrame,
            activities: pd.DataFrame | None,
            meals: pd.DataFrame | None,
            sleep: pd.DataFrame | None,
            cpet: pd.DataFrame | None
    ) -> None:
        """
        Add CGM-specific annotations to a single CGM figure.

        Args:
            fig (go.Figure):
                Plotly figure to which annotations will be added.

            cgm_data (pd.DataFrame):
                DataFrame containing CGM data with a "time" column.

            activities (pd.DataFrame | None):
                DataFrame with activity start times and durations.

            meals (pd.DataFrame | None):
                DataFrame with meal timestamps.

            sleep (pd.DataFrame | None):
                DataFrame with sleep intervals.

            cpet (pd.DataFrame | None, optional):
                DataFrame with CPET measurement.

        Returns:
            None
        """
        # Hypoglycemia
        fig.add_shape(
            type="rect",
            x0=cgm_data["time"].min(),
            x1=cgm_data["time"].max(),
            y0=0, y1=3.9,
            xref="x", yref="y",
            fillcolor="red",
            opacity=0.2,
            line_width=0
        )

        # Hyperglycemia
        fig.add_shape(
            type="rect",
            x0=cgm_data["time"].min(),
            x1=cgm_data["time"].max(),
            y0=13.9, y1=15,
            xref="x", yref="y",
            fillcolor="red",
            opacity=0.2,
            line_width=0
        )

        # Activities
        if activities is not None and not activities.empty:
            for _, row in activities.iterrows():
                fig.add_shape(
                    type="rect",
                    x0=row["start_time"],
                    x1=row["start_time"] + row["duration"],
                    y0=0, y1=1,
                    xref="x",
                    yref="paper",
                    fillcolor="orange",
                    opacity=0.3,
                    layer="below",
                    line_width=0
                )

        # CPET
        if cpet is not None and not cpet.empty:
            start_cpet = pd.to_datetime(
                cpet.loc[cpet["Field"].eq("Start Time"), "Value"].iloc[0], dayfirst=True, format="mixed",
                errors="coerce"
            )
            duration = pd.to_timedelta(cpet.loc[cpet["Field"].eq("Duration"), "Value"].iloc[0])
            end_cpet = start_cpet + duration

            fig.add_shape(
                type="rect",
                x0=start_cpet,
                x1=end_cpet,
                y0=0, y1=1,
                xref="x",
                yref="y domain",
                fillcolor="rgba(180, 83, 9, 0.3)",
                # opacity=0.3,
                layer="below",
                line_width=0
            )

        # Sleep
        if sleep is not None and not sleep.empty:
            for _, sleep_time in sleep.iterrows():
                # Morning
                if pd.notna(sleep_time["morning_from"]) and pd.notna(sleep_time["morning_to"]):
                    morning_from = datetime.combine(sleep_time["date"], sleep_time["morning_from"])
                    morning_to = datetime.combine(sleep_time["date"], sleep_time["morning_to"])

                    # CGM
                    fig.add_shape(
                        type="rect",
                        x0=morning_from,
                        x1=morning_to,
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="y domain",
                        fillcolor="rgba(60, 30, 90, 0.35)",
                        layer="below",
                        line_width=0,
                    )

                # Evening
                if pd.notna(sleep_time["evening_from"]) and pd.notna(sleep_time["evening_to"]):
                    evening_from = datetime.combine(sleep_time["date"], sleep_time["evening_from"])
                    evening_to = datetime.combine(sleep_time["date"], sleep_time["evening_to"])

                    # CGM
                    fig.add_shape(
                        type="rect",
                        x0=evening_from,
                        x1=evening_to,
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="y domain",
                        fillcolor="rgba(60, 30, 90, 0.3)",
                        layer="below",
                        line_width=0,
                    )

        # Meals
        if meals is not None and not meals.empty:
            for _, row in meals.iterrows():
                meal_time = pd.to_datetime(row["Time"], dayfirst=True, format="mixed", errors="coerce")

                if pd.isna(meal_time):
                    continue

                fig.add_shape(
                    type="line",
                    x0=meal_time,
                    x1=meal_time,
                    y0=0, y1=1,
                    xref="x",
                    yref="paper",
                    line=dict(color="green", width=2, dash="dot")
                )

    def add_hr_annotations_single(
            self,
            fig: go.Figure,
            activities: pd.DataFrame | None,
            sleep: pd.DataFrame | None,
            cpet: pd.DataFrame | None
    ) -> None:
        """
        Add CGM-specific annotations to a single CGM figure.

        Args:
            fig (go.Figure):
                Plotly figure to which annotations will be added.

            activities (pd.DataFrame | None):
                DataFrame with activity start times and durations.

            sleep (pd.DataFrame | None):
                DataFrame with sleep intervals.

            cpet (pd.DataFrame | None, optional):
                DataFrame with CPET measurement.

        Returns:
            None
        """

        # Activities
        if activities is not None and not activities.empty:
            for _, row in activities.iterrows():
                fig.add_shape(
                    type="rect",
                    x0=row["start_time"],
                    x1=row["start_time"] + row["duration"],
                    y0=0, y1=1,
                    xref="x",
                    yref="paper",
                    fillcolor="orange",
                    opacity=0.3,
                    layer="below",
                    line_width=0
                )

        # CPET
        if cpet is not None and not cpet.empty:
            start_cpet = pd.to_datetime(
                cpet.loc[cpet["Field"].eq("Start Time"), "Value"].iloc[0], dayfirst=True, format="mixed",
                errors="coerce"
            )
            duration = pd.to_timedelta(cpet.loc[cpet["Field"].eq("Duration"), "Value"].iloc[0])
            end_cpet = start_cpet + duration

            fig.add_shape(
                type="rect",
                x0=start_cpet,
                x1=end_cpet,
                y0=0, y1=1,
                xref="x",
                yref="y domain",
                fillcolor="rgba(180, 83, 9, 0.3)",
                layer="below",
                line_width=0,
            )

        # Sleep
        if sleep is not None and not sleep.empty:
            for _, sleep_time in sleep.iterrows():
                # Morning
                if pd.notna(sleep_time["morning_from"]) and pd.notna(sleep_time["morning_to"]):
                    morning_from = datetime.combine(sleep_time["date"], sleep_time["morning_from"])
                    morning_to = datetime.combine(sleep_time["date"], sleep_time["morning_to"])

                    # CGM
                    fig.add_shape(
                        type="rect",
                        x0=morning_from,
                        x1=morning_to,
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="y domain",
                        fillcolor="rgba(60, 30, 90, 0.35)",
                        layer="below",
                        line_width=0,
                    )

                # Evening
                if pd.notna(sleep_time["evening_from"]) and pd.notna(sleep_time["evening_to"]):
                    evening_from = datetime.combine(sleep_time["date"], sleep_time["evening_from"])
                    evening_to = datetime.combine(sleep_time["date"], sleep_time["evening_to"])

                    # CGM
                    fig.add_shape(
                        type="rect",
                        x0=evening_from,
                        x1=evening_to,
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="y domain",
                        fillcolor="rgba(60, 30, 90, 0.3)",
                        layer="below",
                        line_width=0,
                    )

    def add_cgm_annotations_combined(
            self,
            fig: go.Figure,
            cgm_data: pd.DataFrame,
            activities: pd.DataFrame | None,
            meals: pd.DataFrame | None,
            sleep: pd.DataFrame | None,
            cpet
    ) -> None:
        """
        Add CGM-specific annotations to a combined CGM + HR figure.

        Args:
            fig (go.Figure):
                Plotly figure to which annotations will be added.

            cgm_data (pd.DataFrame):
                DataFrame containing CGM data with a "time" column.

            activities (pd.DataFrame | None):
                DataFrame with activity start times and durations.

            meals (pd.DataFrame | None):
                DataFrame with meal timestamps.

            sleep (pd.DataFrame | None):
                DataFrame with sleep intervals.

            cpet (pd.DataFrame | None, optional):
                DataFrame with CPET measurement.

        Returns:
            None
        """
        # Hypoglycemia
        fig.add_shape(
            type="rect",
            x0=cgm_data["time"].min(),
            x1=cgm_data["time"].max(),
            y0=0, y1=3.9,
            xref="x1",
            yref="y1",
            fillcolor="red",
            opacity=0.2,
            line_width=0,
            row=1,
            col=1
        )

        # Hyperglycemia
        fig.add_shape(
            type="rect",
            x0=cgm_data["time"].min(),
            x1=cgm_data["time"].max(),
            y0=13.9, y1=15,
            xref="x1",
            yref="y1",
            fillcolor="red",
            opacity=0.2,
            line_width=0,
            row=1,
            col=1
        )

        # Activities
        if activities is not None and not activities.empty:
            for _, row in activities.iterrows():
                fig.add_shape(
                    type="rect",
                    x0=row["start_time"],
                    x1=row["start_time"] + row["duration"],
                    y0=0, y1=1,
                    xref="x",
                    yref="y domain",
                    fillcolor="orange",
                    opacity=0.3,
                    layer="below",
                    line_width=0,
                    row=1,
                    col=1
                )

                fig.add_shape(
                    type="rect",
                    x0=row["start_time"],
                    x1=row["start_time"] + row["duration"],
                    y0=0, y1=1,
                    xref="x",
                    yref="y2 domain",
                    fillcolor="orange",
                    opacity=0.3,
                    layer="below",
                    line_width=0,
                    row=2,
                    col=1
                )

        # CPET
        if cpet is not None and not cpet.empty:
            start_cpet = pd.to_datetime(
                cpet.loc[cpet["Field"].eq("Start Time"), "Value"].iloc[0], dayfirst=True, format="mixed",
                errors="coerce"
            )
            duration = pd.to_timedelta(cpet.loc[cpet["Field"].eq("Duration"), "Value"].iloc[0])
            end_cpet = start_cpet + duration

            fig.add_shape(
                type="rect",
                x0=start_cpet,
                x1=end_cpet,
                y0=0, y1=1,
                xref="x",
                yref="y domain",
                fillcolor="rgba(180, 83, 9, 0.3)",
                layer="below",
                line_width=0,
                row=1,
                col=1
            )

            fig.add_shape(
                type="rect",
                x0=start_cpet,
                x1=end_cpet,
                y0=0, y1=1,
                xref="x",
                yref="y2 domain",
                fillcolor="rgba(180, 83, 9, 0.3)",
                layer="below",
                line_width=0,
                row=2,
                col=1
            )

        # Sleep
        if sleep is not None and not sleep.empty:
            for _, sleep_time in sleep.iterrows():
                # Morning
                if pd.notna(sleep_time["morning_from"]) and pd.notna(sleep_time["morning_to"]):
                    morning_from = datetime.combine(sleep_time["date"], sleep_time["morning_from"])
                    morning_to = datetime.combine(sleep_time["date"], sleep_time["morning_to"])

                    # CGM
                    fig.add_shape(
                        type="rect",
                        x0=morning_from,
                        x1=morning_to,
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="y domain",
                        fillcolor="rgba(60, 30, 90, 0.35)",
                        layer="below",
                        line_width=0,
                        row=1,
                        col=1
                    )

                    # HR
                    fig.add_shape(
                        type="rect",
                        x0=morning_from,
                        x1=morning_to,
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="y2 domain",
                        fillcolor="rgba(60, 30, 90, 0.3)",
                        layer="below",
                        line_width=0,
                        row=2,
                        col=1
                    )

                # Evening
                if pd.notna(sleep_time["evening_from"]) and pd.notna(sleep_time["evening_to"]):
                    evening_from = datetime.combine(sleep_time["date"], sleep_time["evening_from"])
                    evening_to = datetime.combine(sleep_time["date"], sleep_time["evening_to"])

                    # CGM
                    fig.add_shape(
                        type="rect",
                        x0=evening_from,
                        x1=evening_to,
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="y domain",
                        fillcolor="rgba(60, 30, 90, 0.3)",
                        layer="below",
                        line_width=0,
                        row=1,
                        col=1
                    )

                    # HR
                    fig.add_shape(
                        type="rect",
                        x0=evening_from,
                        x1=evening_to,
                        y0=0,
                        y1=1,
                        xref="x",
                        yref="y2 domain",
                        fillcolor="rgba(60, 30, 90, 0.3)",
                        layer="below",
                        line_width=0,
                        row=2,
                        col=1
                    )

        # Meals
        if meals is not None and not meals.empty:
            for _, row in meals.iterrows():
                meal_time = pd.to_datetime(row["Time"], dayfirst=True, format="mixed", errors="coerce")

                if pd.isna(meal_time):
                    continue

                # CGM
                fig.add_shape(
                    type="line",
                    x0=meal_time,
                    x1=meal_time,
                    y0=0, y1=1,
                    xref="x",
                    yref="y domain",
                    line=dict(color="green", width=2, dash="dot"),
                    row=1,
                    col=1
                )

    def add_cgm_legend_single(
            self,
            fig: go.Figure,
    ) -> None:
        """
        Add legend items to a single CGM figure.

        The added legend entries represent additional CGM-related annotations
        and reference elements displayed in the figure, including activities,
        CPET events, sleep periods, meals, and glucose thresholds.

        Args:
            fig (go.Figure):
                Plotly figure to which the legend items will be added.

        Returns:
            None
        """

        # Activities
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="orange", opacity=0.3),
                name="Activities"
            )
        )

        # CPET
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="rgba(180, 83, 9, 0.5)"),
                name="CPET"
            )
        )

        # Sleep
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="rgba(60, 30, 90, 0.35)"),
                name="Sleep"
            )
        )

        # Meals
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="lines",
                line=dict(color="green", width=2, dash="dot"),
                name="Meals"
            )
        )

        # Thresholds
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="red", opacity=0.2),
                name="Glucose thresholds"
            )
        )

        fig.update_layout(
            template="plotly_white",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.35,
                xanchor="left",
                x=0.72,
                bgcolor="rgba(255,255,255,0.8)"
            ),
            margin=dict(l=50, r=20, t=50, b=50)
        )

    def add_hr_legend_single(
            self,
            fig: go.Figure,
    ) -> None:
        """
        Add legend items to a heart rate figure.

        Args:
            fig (go.Figure):
                Plotly figure to which the legend will be added.

        Returns:
            None
        """
        # Activities
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="orange", opacity=0.3),
                name="Activities"
            )
        )

        # CPET
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="rgba(180, 83, 9, 0.5)"),
                name="CPET"
            )
        )

        # Sleep
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="rgba(60, 30, 90, 0.35)"),
                name="Sleep"
            )
        )

        fig.update_layout(
            template="plotly_white",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.35,
                xanchor="left",
                x=0.72,
                bgcolor="rgba(255,255,255,0.8)"
            ),
            margin=dict(l=50, r=20, t=50, b=50)
        )

    def add_cgm_legend_combined(
            self,
            fig: go.Figure,
    ) -> None:
        """
        Add legend items to a combined CGM + HR figure.

        Args:
            fig (go.Figure):
                Plotly figure to which the legend will be added.

        Returns:
            None
        """
        # Activities
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="orange", opacity=0.3),
                name="Activities"
            ),
            row=1, col=1
        )

        # CPET
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="rgba(180, 83, 9, 0.5)"),
                name="CPET"
            )
        )

        # Sleep
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="rgba(60, 30, 90, 0.35)"),
                name="Sleep"
            ),
            row=1, col=1
        )

        # Meals
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="lines",
                line=dict(color="green", width=2, dash="dot"),
                name="Meals"
            ),
            row=1, col=1
        )

        # Thresholds
        fig.add_trace(
            go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(size=20, color="red", opacity=0.2),
                name="Glucose thresholds"
            ),
            row=1, col=1
        )

        # Layout set
        fig.update_layout(
            template="plotly_white",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.35,
                xanchor="left",
                x=0.73,
                bgcolor="rgba(255,255,255,0)",
                font=dict(size=12)
            ),
            margin=dict(l=20, r=20, t=50, b=20)
        )

