class PlotTheme:
    """
    Provides centralized color themes for Plotly visualizations.

    The class stores color definitions for light and dark modes and provides
    access to the currently selected theme. Colors are used across plots,
    tables, annotations, and UI-related visualization elements.

    The active theme is controlled by the `MODE` class attribute.
    """

    # ==========================
    # Actual theme
    # ==========================

    MODE = "light"


    # ==========================
    # LIGHT
    # ==========================

    LIGHT = {

        "background": "#FFFFFF",
        "plot_background": "#FFFFFF",

        "text": "#455364",
        "grid": "#D9DEE7",
        "border": "#AAB2BD",

        "glucose_graph": "#5C7CFA",
        "hr_graph": "#FF6F61",
        "hr_filtered_graph": "#B22222",

        "table_header": "#D1D5DB",
        "table_cell": "#ECEFF3",

        "table_glucose": "#DCE3F7",
        "table_hr": "#FFE1DB",

    }


    # ==========================
    # DARK
    # ==========================

    DARK = {

        "background": "#1E1E1E",
        "plot_background": "#252526",

        "text": "#FFFFFF",
        "grid": "#444444",
        "border": "#666666",

        "glucose_graph": "#8AA4FF",
        "hr_graph": "#FF8A80",
        "hr_filtered_graph": "#FF5252",

        "table_header": "#333333",
        "table_cell": "#2D2D2D",

        "table_glucose": "#303B55",
        "table_hr": "#553333",

    }


    @classmethod
    def colors(cls):
        """
        Return colors for the currently selected theme.

        The returned color dictionary is determined by the current value of
        the `MODE` class attribute.

        Returns:
            dict:
                Dictionary containing color definitions for the active theme.
        """

        if cls.MODE == "dark":
            return cls.DARK

        return cls.LIGHT