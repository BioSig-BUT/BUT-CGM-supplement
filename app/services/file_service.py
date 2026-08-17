import os
from collections import defaultdict


class FileCategorizer:
    """
    Class for automatic categorization of data files and creation
    of a virtual database structure.

    The class scans user folders inside a base directory, classifies
    files according to naming patterns, and creates a normalized
    logical mapping independent of the physical folder structure.
    """

    def __init__(
            self,
            base_path: str
    ):
        """
        Initialize the FileCategorizer.

        Args:
            base_path (str):
                Root directory containing user data folders.

        Attributes:
            base_path (str):
                Root directory path.

            virtual_db (dict):
                Virtual mapping of users and categorized files.

            cgm, hr, acc, activities, meal_sum, meals,
            steps_sum, sleep, ecg, cpet_data,
            cpet_metadata, cpet_summary, other (set):
                Internal category sets used for file recognition.
        """
        self.base_path = base_path

        # File category containers
        self.cgm = set()
        self.hr = set()
        self.acc = set()
        self.activities = set()
        self.meal_sum = set()
        self.meals = set()
        self.steps_sum = set()
        self.sleep = set()
        self.ecg = set()
        self.cpet_data = set()
        self.cpet_metadata = set()
        self.cpet_summary = set()
        self.other = set()

        # Virtual file database
        self.virtual_db = {}

    def __getitem__(
            self,
            key: str
    ) -> dict:
        """
        Return virtual file mapping for a selected user.

        Args:
            key (str):
                User identifier.

        Returns:
            dict:
                Dictionary containing logical file names
                mapped to physical file paths.
        """
        return self.virtual_db[key]

    def categorize_files(self) -> None:
        """
        Scan the base directory and classify all discovered files.

        Files are assigned into predefined groups according to
        filename suffixes or extensions.

        Categories include:

        - CGM
        - ACC
        - ECG
        - HR
        - Activities
        - Meals
        - Sleep
        - Steps
        - CPET files
        - Other

        Returns:
            None
        """
        # Walk through all folders and files
        for root, dirs, files in os.walk(self.base_path):
            for f in files:

                # Accelerometer files
                if f.endswith("_ACC.h5"):
                    self.acc.add(f)

                # ECG files
                elif f.endswith("_ECG.h5"):
                    self.ecg.add(f)

                # Heart rate files
                elif f.endswith("_HR.csv"):
                    self.hr.add(f)

                # Activity files
                elif f.endswith("_activities.xlsx") or f.endswith("_activities.csv"):
                    self.activities.add(f)

                # CGM files
                elif f.endswith("_CGM.csv"):
                    self.cgm.add(f)

                # CPET files
                elif f.endswith("_CPET_data.csv"):
                    self.cpet_data.add(f)

                elif f.endswith("_CPET_metadata.csv"):
                    self.cpet_metadata.add(f)

                elif f.endswith("_CPET_summary.csv"):
                    self.cpet_summary.add(f)

                # Meal summary files
                elif f.endswith("_daily_meal_summary.csv"):
                    self.meal_sum.add(f)

                # Daily steps files
                elif f.endswith("_daily_steps_summary.csv"):
                    self.steps_sum.add(f)

                # Meals table
                elif f.endswith("_meals.csv"):
                    self.meals.add(f)

                # Sleep files
                elif f.endswith("_sleep.csv"):
                    self.sleep.add(f)

                # Uncategorized files
                else:
                    self.other.add(f)

    def rename_by_keyword(
            self,
            file_name: str
    ) -> str | None:
        """
        Return standardized logical name for a file.

        The method checks which internal category set contains
        the file name and returns a normalized display label.

        Args:
            file_name (str):
                File name to classify.

        Returns:
            str | None:
                Logical category name, or None if unknown.
        """
        # CGM files
        if file_name in self.cgm:
            return "CGM"

        # Accelerometer files
        elif file_name in self.acc:
            return "ACC"

        # Heart rate files
        elif file_name in self.hr:
            return "HR"

        # Activity files
        elif file_name in self.activities:
            return "Activities"

        # Meal files
        elif file_name in self.meals:
            return "Meals"

        # Sleep files
        elif file_name in self.sleep:
            return "Sleep"

        # Step summary files
        elif file_name in self.steps_sum:
            return "Steps"

        # CPET summary files
        elif file_name in self.cpet_summary:
            return "CPET summary"

        # CPET metadata files
        elif file_name in self.cpet_metadata:
            return "CPET metadata"

        # Unknown category
        else:
            return None

    def create_virtual_structure(self) -> dict:
        """
        Build a virtual database structure for all users.

        Output format:

            {
                user_name: {
                    logical_name: path
                    logical_name: [path1, path2]
                }
            }

        Multi-file categories are always stored as lists.

        Returns:
            dict:
                Virtual mapping of categorized user files.
        """
        # Categories that may contain multiple files
        MULTI_TYPES = {"ECG", "ACC", "HR"}

        self.virtual_db = defaultdict(dict)

        # Iterate through user folders
        for user_folder in os.listdir(self.base_path):

            user_path = os.path.join(
                self.base_path,
                user_folder
            )

            if not os.path.isdir(user_path):
                continue

            virtual_folder_name = user_folder

            # Walk through user directory
            for root, dirs, files in os.walk(user_path):
                for f in files:

                    # Get logical category name
                    logical_name = self.rename_by_keyword(f)

                    if not logical_name:
                        continue

                    full_path = os.path.join(root, f)

                    # Store multiple files as list
                    if logical_name in MULTI_TYPES:

                        if logical_name not in self.virtual_db[virtual_folder_name]:
                            self.virtual_db[virtual_folder_name][logical_name] = []

                        self.virtual_db[virtual_folder_name][logical_name].append(
                            full_path
                        )

                    # Store single file as string
                    else:
                        self.virtual_db[virtual_folder_name][logical_name] = full_path

        return self.virtual_db
