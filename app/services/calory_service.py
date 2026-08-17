import pandas as pd


class CaloryService:
    """
    Service class responsible for loading and processing calorie intake data.

    This service reads nutritional data from a CSV file, filters records within a selected time range,
    and returns a formatted pandas DataFrame including summary totals.
    """

    def __init__(self):
        """
        Initialize the CaloryService.
        """
        self.cache = {}

    def load_calory_table(
            self,
            file_path: str,
            start_time: pd.Timestamp,
            end_time: pd.Timestamp
    ) -> pd.DataFrame | None:
        """
        Load calorie intake records from CSV file and process meal table.
        """

        try:
            df = pd.read_csv(
                file_path,
                delimiter=";",
                decimal="."
            )

        except Exception as e:
            print(f"Meals cannot be loaded: {e}")
            return None

        if df.empty:
            print("Meals file is empty.")
            return None

        # Rename columns (for compatibility)
        df.columns = [
            "Time",
            "Meal",
            "Calories",
            "Protein",
            "Carbs",
            "Sugar",
            "Fats"
        ]

        # Datetime + numeric conversions
        df["Time"] = pd.to_datetime(df["Time"], dayfirst=True, format="mixed", errors="coerce")

        numeric_cols = [
            "Calories",
            "Protein",
            "Carbs",
            "Sugar",
            "Fats"
        ]

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df[
            df["Calories"] != 0
            ].reset_index(drop=True)

        # Sort + filter time range
        df = df.sort_values("Time")

        filtered = df[
            (df["Time"] >= start_time) &
            (df["Time"] <= end_time)
        ]

        if filtered.empty:
            print("No calorie data available for the selected time range")
            return None

        # Final output table
        filtered = pd.DataFrame({
            "Time": filtered["Time"],
            "Meal": filtered["Meal"],
            "Calories [kcal]": filtered["Calories"],
            "Protein [g]": filtered["Protein"],
            "Carbs [g]": filtered["Carbs"],
            "Sugar [g]": filtered["Sugar"],
            "Fats [g]": filtered["Fats"],
        })

        totals_row = {
            "Time": pd.NaT,
            "Meal": "SUMMARY",
            "Calories [kcal]": round(filtered["Calories [kcal]"].sum(), 1),
            "Protein [g]": round(filtered["Protein [g]"].sum(), 1),
            "Carbs [g]": round(filtered["Carbs [g]"].sum(), 1),
            "Sugar [g]": round(filtered["Sugar [g]"].sum(), 1),
            "Fats [g]": round(filtered["Fats [g]"].sum(), 1),
        }

        summary_df = pd.DataFrame([totals_row])

        summary_df["Time"] = pd.to_datetime(summary_df["Time"])

        filtered_and_sum = pd.concat(
            [filtered, summary_df],
            ignore_index=True
        )

        return filtered_and_sum
