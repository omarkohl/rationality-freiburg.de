#!/usr/bin/env python3

"""
Script to parse the input data and generate the CSV files in the data/ folder.
"""

from pathlib import Path

from ratfr_statistics.parse import generate_attendance_files, generate_feedback_file


YEAR = 2025
REMOVE_SOURCE_FILES = False


def main():
    source_attendance_path = Path("attendance-statistics.csv")
    source_feedback_en_path = Path("Event Feedback (Responses) - EN.csv")
    source_feedback_de_path = Path("Event Feedback (Responses) - DE.csv")

    attendance_path = Path("data", "attendance.csv")
    events_per_person_path = Path("data", f"events_per_person_{YEAR}.csv")
    newcomer_path = Path("data", "newcomer.csv")
    feedback_path = Path("data", f"feedback{YEAR}.csv")
    generate_attendance_files(
        source_attendance_path,
        attendance_path,
        events_per_person_path,
        newcomer_path,
        REMOVE_SOURCE_FILES,
    )
    generate_feedback_file(
        source_feedback_de_path,
        source_feedback_en_path,
        feedback_path,
        REMOVE_SOURCE_FILES,
    )


if __name__ == "__main__":
    main()
