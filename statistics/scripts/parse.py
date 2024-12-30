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
    attendance_per_event_path: Path,
    events_per_person_path: Path,
    newcomer_referral_path: Path,
    retention_per_referral_type_path: Path,
):
    if not source_path.is_file:
        return

    new_people_preprocessed, attendance_preprocessed = preprocess_attendance(
        source_path
    )

    # Group by "First event" and "Referral" and count the number of people
    referrals_summary = (
        new_people_preprocessed.groupby(["First event", "Referral"])
        .size()
        .reset_index(name="People")
    )

    # Rename columns to match the desired output
    referrals_summary.rename(columns={"First event": "Date"}, inplace=True)

    # Save to CSV
    referrals_summary.to_csv(newcomer_referral_path, index=False)

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

    all_dates = {}

    for date in attendance_preprocessed["Date"].unique():
        new_people = new_people_preprocessed["First event"].value_counts().get(date, 0)
        total_people = attendance_preprocessed[attendance_preprocessed["Date"] == date][
            "Name"
        ].nunique()
        recurring_people = total_people - new_people
        all_dates[date] = {
            "New": int(new_people),
            "Recurring": int(recurring_people),
            "Total": int(total_people),
            "Retained3": 0,
            "RetainedAll": 0,
        }

    all_dates_keys = sorted(all_dates.keys())

    for date_index, date in enumerate(all_dates_keys):
        people = attendance_preprocessed[attendance_preprocessed["Date"] == date][
            "Name"
        ].unique()
        for person in people:
            for next_date_index in range(date_index + 1, len(all_dates_keys)):
                next_date = all_dates_keys[next_date_index]
                if (
                    person
                    in attendance_preprocessed[
                        attendance_preprocessed["Date"] == next_date
                    ]["Name"].unique()
                ):
                    if next_date_index - date_index <= 3:
                        all_dates[date]["Retained3"] += 1
                    all_dates[date]["RetainedAll"] += 1
                    break

    out_df = pd.DataFrame.from_dict(all_dates, orient="index").reset_index()
    out_df.rename(columns={"index": "Date"}, inplace=True)
    out_df.sort_values(by="Date", inplace=True)
    out_df = out_df[["Date", "Recurring", "New", "Total", "Retained3", "RetainedAll"]]
    out_df.to_csv(attendance_per_event_path, index=False)

    # Calculate retention per referral type
    retention_per_referral_type = (
        new_people_preprocessed.groupby("Referral")["Name"]
        .nunique()
        .reset_index(name="New")
    )
    # rename new to people
    retention_per_referral_type.rename(columns={"New": "People"}, inplace=True)
    # add retained column
    retention_per_referral_type["Retained3"] = 0
    retention_per_referral_type["RetainedAll"] = 0

    for date_index, date in enumerate(all_dates_keys):
        # choose only new people for this date
        people = new_people_preprocessed[
            new_people_preprocessed["First event"] == date
        ]["Name"].unique()
        for person in people:
            for next_date_index in range(date_index + 1, len(all_dates_keys)):
                next_date = all_dates_keys[next_date_index]
                if (
                    person
                    in attendance_preprocessed[
                        attendance_preprocessed["Date"] == next_date
                    ]["Name"].unique()
                ):
                    if next_date_index - date_index <= 3:
                        retention_per_referral_type.loc[
                            retention_per_referral_type["Referral"]
                            == new_people_preprocessed[
                                new_people_preprocessed["Name"] == person
                            ]["Referral"].values[0],
                            "Retained3",
                        ] += 1
                    retention_per_referral_type.loc[
                        retention_per_referral_type["Referral"]
                        == new_people_preprocessed[
                            new_people_preprocessed["Name"] == person
                        ]["Referral"].values[0],
                        "RetainedAll",
                    ] += 1
                    break

    retention_per_referral_type.to_csv(retention_per_referral_type_path, index=False)

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

    attendance_per_event_path = Path("data", "attendance_per_event.csv")
    events_per_person_path = Path("data", f"events_per_person_{YEAR}.csv")
    newcomer_referral_path = Path("data", "newcomer_referral.csv")
    retention_per_referral_type_path = Path(
        "data", f"retention_per_referral_type_{YEAR}.csv"
    )
    feedback_path = Path("data", f"feedback{YEAR}.csv")
    generate_attendance_files(
        source_attendance_path,
        attendance_per_event_path,
        events_per_person_path,
        newcomer_referral_path,
        retention_per_referral_type_path,
    )
    generate_feedback_file(
        source_feedback_de_path, source_feedback_en_path, feedback_path
    )


if __name__ == "__main__":
    main()
