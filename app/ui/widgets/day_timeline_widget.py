from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF, QRectF
import pandas as pd

from PySide6.QtCore import Signal


class DayTimelineWidget(QWidget):
    """
    Custom Qt widget displaying a selectable timeline of available days.

    The widget visualizes available dates as points connected by lines.
    Missing days are indicated using dotted connections, while the currently
    selected day and hovered day are highlighted.

    The widget emits the `daySelected` signal when the user selects a day
    by clicking on its corresponding point.
    """

    daySelected = Signal(object)

    def __init__(self, parent=None):
        """
        Initialize the day timeline widget.

        Args:
            parent:
                Optional parent widget.
        """
        super().__init__(parent)

        self.setMinimumHeight(70)

        self.days = []
        self.current_day = None

        self.point_positions = []

        self.hover_day = None
        self.setMouseTracking(True)

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        if not self.days:
            return

        y = 20

        left = 30
        right = self.width() - 30

        sorted_days = sorted(self.days)

        count = len(sorted_days)

        if count > 1:
            step = (right - left) / (count - 1)
        else:
            step = 0

        self.point_positions.clear()

        # -------------------------
        # Lines between days
        # -------------------------

        for i in range(count - 1):

            day = sorted_days[i]
            next_day = sorted_days[i + 1]

            x1 = left + i * step
            x2 = left + (i + 1) * step

            if (next_day - day).days > 1:

                # missing days
                pen = QPen(
                    QColor("#666666")
                )

                pen.setStyle(
                    Qt.PenStyle.DotLine
                )

            else:

                # days around
                pen = QPen(
                    QColor("#333333")
                )

                pen.setStyle(
                    Qt.PenStyle.SolidLine
                )

            pen.setWidth(1)

            painter.setPen(pen)

            painter.drawLine(
                x1,
                y,
                x2,
                y
            )

        # -------------------------
        # Points + Dates
        # -------------------------

        for i, day in enumerate(sorted_days):

            x = left + i * step

            self.point_positions.append((x, y, day))

            # -------------------------
            # Hover halo
            # -------------------------

            if day == self.hover_day:
                painter.setPen(Qt.NoPen)

                painter.setBrush(
                    QColor(100, 180, 255, 80)
                )

                painter.drawEllipse(
                    QPointF(x, y),
                    12,
                    12
                )

            # -------------------------
            # Point
            # -------------------------

            painter.setPen(Qt.NoPen)

            if day == self.current_day:

                painter.setBrush(
                    QColor("#9fcbff")
                )

                pen = QPen(QColor("#666666"))
                pen.setWidth(2)
                painter.setPen(pen)

                radius = 7

            else:

                painter.setBrush(
                    QColor("#666666")
                )

                radius = 4

            painter.drawEllipse(
                QPointF(x, y),
                radius,
                radius
            )

            # -------------------------
            # Date
            # -------------------------

            painter.setPen(
                QColor("#333333")
            )

            font = painter.font()
            font.setBold(
                day == self.current_day
            )
            painter.setFont(font)

            painter.drawText(
                QRectF(
                    x - 25,
                    y + 12,
                    50,
                    20
                ),
                Qt.AlignmentFlag.AlignCenter,
                day.strftime("%m-%d")
            )

        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

    def set_days(self, days, current_day):
        """
        Set available days and update the selected day.

        The provided dates are normalized to remove time information,
        sorted chronologically, and displayed on the timeline.

        Args:
            days:
                Collection of available dates to display.

            current_day:
                Currently selected date to highlight.
        """

        self.days = sorted(
            [
                pd.Timestamp(day).normalize()
                for day in days
            ]
        )

        self.current_day = (
            pd.Timestamp(current_day)
            .normalize()
        )

        self.update()

    def mousePressEvent(self, event):

        for x, y, day in self.point_positions:

            dx = event.position().x() - x
            dy = event.position().y() - y

            if dx * dx + dy * dy <= 10 * 10:
                self.daySelected.emit(day)

                break

    def mouseMoveEvent(self, event):

        self.hover_day = None

        for x, y, day in self.point_positions:

            dx = event.position().x() - x
            dy = event.position().y() - y

            if dx * dx + dy * dy <= 10 * 10:
                self.hover_day = day
                break

        self.update()

    def leaveEvent(self, event):

        self.hover_day = None
        self.update()

        super().leaveEvent(event)