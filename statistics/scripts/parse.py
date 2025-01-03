"""
Script to parse the input data and generate the CSV files in the data/ folder.
"""

import os
import pandas as pd
from pathlib import Path

from typing import Tuple

from ratfr_statistics import questions


YEAR = 2024
REMOVE_SOURCE_FILES = False


def preprocess_attendance(
    attendance_source_path: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    This function reads the attendance data from CSV and preprocesses it for further analysis.

    Format of the raw data:

    ;How did you find RatFr?;19.01.2024;02.02.2024;16.02.2024;01.03.2024;15.03.2024;29.03.2024;12.04.2024;13.04.2024;26.04.2024;10.05.2024;24.05.2024;07.06.2024;21.06.2024;05.07.2024;19.07.2024;27.09.2024;11.10.2024;25.10.2024;08.11.2024;22.11.2024;06.12.2024;20.12.2024;Abs. Attendance;Rel. Attendance
    Omar;;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;1;0;1;1;1;21;95.4545454545455%
    Matthias;;1;1;1;1;1;1;0;0;1;1;1;1;1;1;0;0;1;1;1;1;1;1;18;81.8181818181818%
    Ben Mor;;1;1;1;1;0;1;0;1;0;1;1;0;1;1;1;0;1;1;1;1;1;1;17;77.2727272727273%
    Anjali;meetup.com;0;2;1;1;1;1;1;1;1;1;1;1;1;0;0;1;1;0;1;0;1;0;16;72.7272727272727%
    """

    if not attendance_source_path.is_file():
        return

    df = pd.read_csv(attendance_source_path, sep=";")
    df.drop(
        [
            "Abs. Attendance",
            "Rel. Attendance",
        ],
        axis=1,
        inplace=True,
    )

    # Ensure that names are unique
    names = df.iloc[:, 0]
    duplicate_names = names[names.duplicated(keep=False)]
    if not duplicate_names.empty:
        duplicates_count = duplicate_names.value_counts()
        duplicates_message = "\n".join(
            [
                f"The name {name} appears {count} times."
                for name, count in duplicates_count.items()
            ]
        )
        raise ValueError(f"Duplicate names found:\n{duplicates_message}")

    new_people_data = []
    for person_index in range(len(df)):
        for date_index in range(1, len(df.columns)):
            if df.iloc[person_index, date_index] == 2:
                first_event_date = pd.to_datetime(df.columns[date_index], dayfirst=True)
                new_people_data.append(
                    {
                        "Name": df.iloc[person_index, 0],
                        "Referral": df.iloc[person_index, 1],
                        "First event": first_event_date,
                    }
                )
                break

    new_people = pd.DataFrame(
        new_people_data, columns=["Name", "Referral", "First event"]
    )

    attendance_data = []
    for person_index in range(len(df)):
        for date_index in range(1, len(df.columns)):
            if df.iloc[person_index, date_index] in (1, 2):
                attendance_data.append(
                    {
                        "Name": df.iloc[person_index, 0],
                        "Date": pd.to_datetime(df.columns[date_index], dayfirst=True),
                    }
                )

    attendance = pd.DataFrame(attendance_data, columns=["Name", "Date"])

    return new_people, attendance


def generate_attendance_files(
    source_path: Path,
    attendance_path: Path,
    events_per_person_path: Path,
    newcomer_path: Path,
):
    if not source_path.is_file:
        return

    new_people_preprocessed, attendance_preprocessed = preprocess_attendance(
        source_path
    )

    # Note we count twice, once the number of events attended per person and
    # then the number of people who attended that many events.
    attendance_per_person = (
        attendance_preprocessed["Name"].value_counts().value_counts()
    )
    attendance_per_person.sort_index(ascending=True, inplace=True)
    # Group the 10+ together
    attendance_per_person.index = attendance_per_person.index.astype(str)
    attendance_per_person.rename(index={"10": "10+"}, inplace=True)
    attendance_per_person.loc["10+"] += attendance_per_person.iloc[10:].sum()
    attendance_per_person.drop(attendance_per_person.index[10:], inplace=True)

    # Rename for clarity
    attendance_per_person.index.name = "Events attended"
    attendance_per_person = attendance_per_person.rename("People")
    attendance_per_person.to_csv(events_per_person_path, index=True)

    attendance = attendance_preprocessed.copy(deep=True)
    attendance["Retained3"] = 0
    attendance["RetainedAll"] = 0

    all_dates = sorted(set(attendance_preprocessed["Date"]))

    for date_index, date in enumerate(all_dates):
        for idx, row in attendance.iterrows():
            if row["Date"] != date:
                continue
            person = row["Name"]
            for next_date_index in range(date_index + 1, len(all_dates)):
                next_date = all_dates[next_date_index]
                if (
                    person
                    in attendance_preprocessed[
                        attendance_preprocessed["Date"] == next_date
                    ]["Name"].unique()
                ):
                    if next_date_index - date_index <= 3:
                        attendance.loc[idx, "Retained3"] += 1
                    attendance.loc[idx, "RetainedAll"] += 1
                    break

    attendance = (
        attendance.groupby("Date")
        .agg(
            {
                "Name": "count",
                "Retained3": "sum",
                "RetainedAll": "sum",
            }
        )
        .reset_index()
        .rename(columns={"Name": "Total"})
    )

    attendance["New"] = 0
    attendance["Recurring"] = 0
    for idx, row in attendance.iterrows():
        date = row["Date"]
        new = new_people_preprocessed[new_people_preprocessed["First event"] == date]
        attendance.loc[idx, "New"] = len(new)
        attendance.loc[idx, "Recurring"] = row["Total"] - len(new)

    # Reorder columns
    attendance = attendance[
        ["Date", "Recurring", "New", "Total", "Retained3", "RetainedAll"]
    ]

    attendance.to_csv(attendance_path, index=False)

    referrals_summary = new_people_preprocessed.copy(deep=True)
    # add retained column
    referrals_summary["Retained3"] = 0
    referrals_summary["RetainedAll"] = 0

    for date_index, date in enumerate(all_dates):
        # iterate over all people (i.e. rows) of referrals_summary
        for idx, row in referrals_summary.iterrows():
            if row["First event"] != date:
                continue
            person = row["Name"]
            for next_date_index in range(date_index + 1, len(all_dates)):
                next_date = all_dates[next_date_index]
                if (
                    person
                    in attendance_preprocessed[
                        attendance_preprocessed["Date"] == next_date
                    ]["Name"].unique()
                ):
                    if next_date_index - date_index <= 3:
                        referrals_summary.loc[idx, "Retained3"] += 1
                    referrals_summary.loc[idx, "RetainedAll"] += 1
                    break

    # Calculate retention per referral type
    referrals_summary = (
        referrals_summary.groupby(["First event", "Referral"])
        .agg(
            {
                "Name": "count",  # Count the number of people
                "Retained3": "sum",  # Sum the Retained3 column
                "RetainedAll": "sum",  # Sum the RetainedAll column
            }
        )
        .reset_index()
        .rename(columns={"Name": "People", "First event": "Date"})
    )

    referrals_summary.to_csv(newcomer_path, index=False)

    if REMOVE_SOURCE_FILES:
        os.remove(source_path)


def generate_feedback_file(
    de_source_path: Path, en_source_path: Path, cleaned_path: Path
):
    """
    This function reads the feedback data from the source files, cleans it up
    and writes it out into a new file.
    The source files are then removed.
    """
    if not de_source_path.is_file or not en_source_path.is_file:
        return
    # First we clean up the data after download it from Google forms
    df_de = pd.read_csv(de_source_path)
    df_en = pd.read_csv(en_source_path)

    # Rename the columns of the German dataframe to the English column names
    df_de.columns = df_en.columns

    df = pd.concat([df_de, df_en], axis=0, ignore_index=True)

    # Remove the timestamp and name columns
    df.drop(["Timestamp", "13. (optional) Name"], axis=1, inplace=True)

    df["Date of the event"] = pd.to_datetime(df["Date of the event"], format="%d/%m/%Y")
    q09_mapping = {v: k for k, v in questions.Q09_RESPONSES_DE.items()}
    q09_mapping.update({v: v for v in questions.Q09_RESPONSES})
    df[questions.QUESTIONS[9]] = df[questions.QUESTIONS[9]].map(q09_mapping)
    df[questions.QUESTIONS[10]] = df[questions.QUESTIONS[10]].map(
        questions.map_q10_responses
    )

    df.sort_values(by=["Date of the event"] + list(df.columns[1:]), inplace=True)

    df.to_csv(cleaned_path, index=False)
    if REMOVE_SOURCE_FILES:
        # Remove the original files
        os.remove(de_source_path)
        os.remove(en_source_path)


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
    )
    generate_feedback_file(
        source_feedback_de_path, source_feedback_en_path, feedback_path
    )


if __name__ == "__main__":
    main()
