#!/usr/bin/env python3

"""
This script generates a markdown page suitable for Hugo containing tables with data and plots.
The data is read from multiple CSV files exported from Google Forms and LibreOffice Calc.
That data is cleaned up (e.g. names are removed) and then written into the other CSV files
that are stored alongside this script in the current directory. You can therefore always
execute the script to generate markdown out of the box.
The CSV files that were exported from Google Forms and LibreOffice Calc are deleted after
the conversion, if they exist.
If you wanted to you could also manually edit the CSV files you'll find next to this script.
However, these CSV files are always overwritten when performing a conversion from the
exported CSV files.
Look for "Filenames" below for a little more information.
"""

from pathlib import Path
import re
import pytz
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from plotly import express as px
import plotly.io as pio
import argparse

from ratfr_statistics.helper import get_event_metadata, get_page_metadata
from ratfr_statistics import questions

POSTS_WEBDIR = Path("../website/content/posts/")
EVENTS_WEBDIR = Path("../website/content/events/")

FEEDBACK_CLEANED = Path("data", "feedback.csv")
ATTENDANCE_CLEANED = Path("data", "attendance.csv")
NEWCOMER_CLEANED = Path("data", "newcomer.csv")

REMOVE_SOURCE_FILES = True


def main():
    """
    This function is the entry point of the script.
    """
    # Create the parser
    parser = argparse.ArgumentParser(
        description=(
            "This script generates a markdown page suitable for Hugo "
            "containing tables with data and plots."
        )
    )

    # Add the arguments
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help=(
            "If given, the script will replace the existing markdown "
            "files with new ones."
        ),
        default=False,
    )

    parser.add_argument(
        "--year",
        type=int,
        help="The year for which to generate the statistics.",
        default=datetime.now().year,
    )

    # Parse the arguments
    args = parser.parse_args()

    generate_output(FEEDBACK_CLEANED, ATTENDANCE_CLEANED, args.year, args.regenerate)


def generate_output(
    feedback_file: Path, attendance_file: Path, year: int, regenerate: bool = False
):
    """
    This function reads the cleaned data and generates a markdown page containing tables with data and plots.
    """
    now = datetime.now(pytz.timezone("CET"))
    summary_webdir = POSTS_WEBDIR / f"statistics-feedback-{year}"
    summary_webdir.mkdir(parents=True, exist_ok=True)

    # Read the cleaned data into a dataframe
    if not feedback_file.is_file():
        raise FileNotFoundError(f"The file {feedback_file} does not exist")

    feedback_df = pd.read_csv(feedback_file, parse_dates=["Date of the event"])
    attendance_df = pd.read_csv(attendance_file, parse_dates=["Date"])
    newcomer = pd.read_csv(NEWCOMER_CLEANED, parse_dates=["Date"])
    # Filter the data for the selected year
    feedback_df = feedback_df[
        feedback_df["Date of the event"].apply(lambda x: x.year) == year
    ]
    attendance_df = attendance_df[attendance_df["Date"].apply(lambda x: x.year) == year]
    newcomer = newcomer[newcomer["Date"].apply(lambda x: x.year) == year]

    # q10 in feedback_df is a string representing a list of strings.
    # I want to convert it to a list of strings.
    feedback_df[questions.QUESTIONS[10]] = (
        feedback_df[questions.QUESTIONS[10]].dropna().map(eval)
    )

    all_event_stats_links = ""
    # All event dates for the selected year
    dates = feedback_df["Date of the event"].sort_values().unique()
    for d in dates:
        dirs = [
            f
            for f in EVENTS_WEBDIR.iterdir()
            if str(f.name).startswith(d.strftime("%Y-%m-%d"))
        ]
        if len(dirs) == 0:
            raise ValueError(f"No directory for {d} exists")
        elif len(dirs) > 1:
            raise ValueError(f"More than one directory for {d} exists")

        event_dir = dirs[0]
        event_stats_dir = event_dir / "statistics"
        event_stats_dir.mkdir(parents=True, exist_ok=True)
        event_stats_page = Path(event_stats_dir, "index.md")

        event_data = get_page_metadata(Path(event_dir, "_index.md"))
        event_title = event_data["title"]
        event_link = '{{< ref "events/' + event_dir.name + '" >}}'
        event_stats_link = '{{< ref "events/' + event_dir.name + '/statistics" >}}'
        all_event_stats_links += f"* [{event_title}]({event_stats_link})\n"
        summary_link = '{{< ref "posts/' + summary_webdir.name + '" >}}'

        if not regenerate and event_stats_page.exists():
            # If the page already exists, skip it
            continue

        # Get the creation date of the event's statistics page so as not to
        # overwrite it if the page already exists
        event_stats_page_creation_date = now.strftime("%Y-%m-%dT%H:%M:%S%z")
        if event_stats_page.exists():
            event_stats_data = get_page_metadata(event_stats_page)
            if "date" in event_stats_data:
                event_stats_page_creation_date = event_stats_data["date"]
        page_content = f"""---
title: "Statistics: {event_title}"
date: {event_stats_page_creation_date}
type: "default"
toc: true
usePlotly: true
summary: "Statistics for the '{event_title}' event."
---

Read more about [this event]({event_link}).

See also the [{year} summary]({summary_link}).

## Attendees

"""
        # Filter the dataframe for the current date
        feedback_filtered_df = feedback_df[feedback_df["Date of the event"] == d]
        attendance_filtered_df = attendance_df[attendance_df["Date"] == d]
        recurring_participants = attendance_filtered_df.iloc[0]["Recurring"]
        new_participants = attendance_filtered_df.iloc[0]["New"]
        total_participants = attendance_filtered_df.iloc[0]["Total"]

        page_content += f"* **Total:** {pluralize_people(total_participants)}\n"
        page_content += f"* **Recurring:** {pluralize_people(recurring_participants)}\n"
        page_content += f"* **New:** {pluralize_people(new_participants)}\n\n"

        page_content += generate_feedback_output(
            feedback_filtered_df, total_participants, event_stats_dir
        )
        # Generate the markdown page
        with open(event_stats_page, "w") as f:
            f.write(page_content)

    summary_page = Path(summary_webdir, "index.md")
    total_participants = attendance_df["Total"].sum()
    summary_page_creation_date = now.strftime("%Y-%m-%dT%H:%M:%S%z")
    if summary_page.exists():
        summary_page_data = get_page_metadata(summary_page)
        if "date" in summary_page_data:
            summary_page_creation_date = summary_page_data["date"]

    page_content = f"""---
title: "Statistics & Feedback {year}"
date: {summary_page_creation_date}
toc: true
usePlotly: true
summary: "In {year} there were {len(dates)} public events (so far),
  not counting book club, statistics study group and meta-meetup.
  Some interesting facts and graphs."
---

**Note that this page will be updated through {year}.**

This page contains a summary of all events. You can see the statistics
for the individual events here:

{all_event_stats_links}

## Attendees

* {len(dates)} events.
* {total_participants / len(dates):.2f} people per event on average (σ={attendance_df['Total'].std():.2f}).
* {attendance_df['New'].mean():.2f} newcomers per event (σ={attendance_df['New'].std():.2f}).
* Maximum number of attendees was {attendance_df['Total'].max()} and minimum was {pluralize_people(attendance_df['Total'].min())}.

**Recurring** is any person coming for the second, third etc. time whereas
**New** is anyone coming for the first time to a Rationality Freiburg event.

"""

    all_dates = [d for d in attendance_df["Date"]]
    event_metadata = get_event_metadata(all_dates)
    attendance_df["Event"] = attendance_df["Date"].apply(
        lambda date: event_metadata.get(date, {}).get("title", "No title")
    )

    page_content += "### Attendance\n\n"
    attendance_fig = plot_attendance(attendance_df, year)
    attendance_html = pio.to_html(
        attendance_fig, include_plotlyjs=False, full_html=False
    )
    page_content += "<div>" + attendance_html + "</div>\n\n"

    page_content += "### Referrals\n\n"
    referrals_fig = plot_referrals(newcomer)
    referrals_html = pio.to_html(referrals_fig, include_plotlyjs=False, full_html=False)
    page_content += "<div>" + referrals_html + "</div>\n\n"

    page_content += "## Feedback\n\n"
    page_content += f"* **Responses:** {pluralize_people(len(feedback_df))} ({len(feedback_df) / total_participants * 100:.2f}% of attendees)\n\n"
    feedback_fig = plot_feedback_frequency(feedback_df, attendance_df, year)
    feedback_html = pio.to_html(feedback_fig, include_plotlyjs=False, full_html=False)
    page_content += "<div>" + feedback_html + "</div>\n\n"

    page_content += generate_feedback_output(
        feedback_df, total_participants, summary_webdir
    )
    with open(summary_page, "w") as f:
        f.write(page_content)


def generate_feedback_output(feedback_df, total_participants, img_dir: Path):
    page_content = ""
    for q in [questions.QUESTIONS[i] for i in range(1, 9)]:
        page_content += f"### {q}\n\n"
        page_content += f"* **Responses:** {pluralize_people(feedback_df[q].count())} ({feedback_df[q].count() / total_participants * 100:.2f}% of attendees)\n"
        page_content += "* **Answers:**\n"
        for i, label in enumerate(questions.QUESTION_RESPONSE_OPTIONS[q], start=1):
            page_content += f"  * {label} ({i}): {pluralize_people(feedback_df[q].value_counts().get(i, 0))}\n"
        page_content += f"* **Average answer:** {feedback_df[q].mean():.2f} (σ={feedback_df[q].std():.2f})\n\n"
        data = feedback_df[q].value_counts().sort_index()
        # if any index from 1 to 5 is missing, add it with a value of 0
        for i in range(1, 6):
            if i not in data.index:
                data[i] = 0
        data = data.sort_index()
        plot_bar_chart(data, q, img_dir)
        page_content += f"![{q}](./{question_to_filename(q)}.png)\n\n"

    # Question 9
    q09_data = feedback_df[questions.QUESTIONS[9]].value_counts()
    for i in questions.Q09_RESPONSES:
        if i not in q09_data.index:
            q09_data[i] = 0
    q09_data = q09_data.sort_index()
    page_content += f"### {questions.QUESTIONS[9]}\n\n"
    page_content += f"* **Responses:** {pluralize_people(q09_data.sum())} ({q09_data.sum() / total_participants * 100:.2f}% of attendees)\n"
    page_content += "* **Answers:**\n"
    page_content += (
        "\n".join([f"  * {k}: {pluralize_people(v)}" for k, v in q09_data.items()])
        + "\n\n"
    )
    plot_bar_chart(q09_data, questions.QUESTIONS[9], img_dir)
    page_content += f"![{questions.QUESTIONS[9]}](./{question_to_filename(questions.QUESTIONS[9])}.png)\n\n"

    # Question 10
    q10_responses = []
    for sublist in feedback_df[questions.QUESTIONS[10]].dropna().tolist():
        q10_responses.extend(sublist)
    q10_responses = pd.Series(q10_responses)
    q10_data = q10_responses.value_counts().sort_index()
    for i in questions.Q10_RESPONSES:
        if i not in q10_data.index:
            q10_data[i] = 0
    q10_data = q10_data.sort_index()
    plot_bar_chart_horizontal(q10_data, questions.QUESTIONS[10], img_dir)
    page_content += f"### {questions.QUESTIONS[10]}\n\n"
    page_content += f"* **Responses:** {pluralize_people(q10_data.sum())} ({q10_data.sum() / total_participants * 100:.2f}% of attendees)\n"
    page_content += "* **Answers:**\n"
    page_content += (
        "\n".join([f"  * {k}: {pluralize_people(v)}" for k, v in q10_data.items()])
        + "\n\n"
    )
    page_content += f"![{questions.QUESTIONS[10]}](./{question_to_filename(questions.QUESTIONS[10])}.png)\n\n"

    # Question 11
    comments_best = feedback_df[questions.QUESTIONS[11]].dropna().values
    page_content += f"### {questions.QUESTIONS[11]}\n\n"
    page_content += f"* **Responses:** {pluralize_people(feedback_df[questions.QUESTIONS[11]].count())} ({feedback_df[questions.QUESTIONS[11]].count() / total_participants * 100:.2f}% of attendees)\n\n"
    page_content += "**Note:** Anything contained in square brackets [] is an edit by the organizers.\n\n"
    if len(comments_best) > 0:
        quoted_comments = []
        for c in comments_best:
            quoted_comments.append("> " + c.replace("\n", "  \n> "))
        page_content += "\n\n".join(quoted_comments) + "\n"

    # Question 12
    comments_worst = feedback_df[questions.QUESTIONS[12]].dropna().values
    page_content += f"### {questions.QUESTIONS[12]}\n\n"
    page_content += f"* **Responses:** {pluralize_people(feedback_df[questions.QUESTIONS[12]].count())} ({feedback_df[questions.QUESTIONS[12]].count() / total_participants * 100:.2f}% of attendees)\n\n"
    page_content += "**Note:** Anything contained in square brackets [] is an edit by the organizers.\n\n"
    if len(comments_worst) > 0:
        quoted_comments = []
        for c in comments_worst:
            quoted_comments.append("> " + c.replace("\n", "  \n> "))
        page_content += "\n\n".join(quoted_comments) + "\n"

    return page_content


def plot_bar_chart(data, q, output_dir: Path):
    """
    This function plots a bar chart based on the given data and question.
    """
    # Increase font sizes
    plt.rcParams["font.size"] = 12
    plt.rcParams["axes.labelsize"] = 14
    plt.rcParams["axes.titlesize"] = 16
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10

    # Create a bar chart where the x-axis is the index of the data and the y-axis is the value of the data
    plt.figure(figsize=(10, 7))
    plt.bar(data.index, data.values, color="navy", zorder=2)

    # Add gridlines
    plt.grid(axis="y", zorder=1)
    plt.xlabel("Answer")
    plt.ylabel("Number of people")
    ytick_step = 1
    ytick_max = data.max() + 1
    if data.max() > 15:
        ytick_step = 5
    elif data.max() > 10:
        ytick_step = 2
    elif data.max() < 5:
        ytick_max = 6
    plt.yticks(range(0, ytick_max, ytick_step))
    plt.title(q, pad=20)
    if q in questions.QUESTION_RESPONSE_OPTIONS:
        labels = [
            f"{label} ({i})"
            for i, label in zip(data.index, questions.QUESTION_RESPONSE_OPTIONS[q])
        ]
        plt.xticks(data.index, labels, rotation=45)
    plt.subplots_adjust(bottom=0.3)
    plt.savefig(output_dir / f"{question_to_filename(q)}.png")
    plt.close()


def plot_bar_chart_horizontal(data, q, output_dir: Path):
    # plot question 10
    plt.figure(figsize=(20, 16))
    # Create a horizontal bar chart
    plt.barh(data.index, data.values, color="navy", zorder=2)
    plt.grid(axis="x", zorder=1)
    plt.ylabel("Answer")
    plt.xlabel("Number of people")
    xtick_step = 1
    xtick_max = data.max() + 1
    if data.max() > 15:
        xtick_step = 5
    elif data.max() > 10:
        xtick_step = 2
    elif data.max() < 5:
        xtick_max = 6
    plt.xticks(range(0, xtick_max, xtick_step))
    # To ensure it stays ordered alphabetically top to bottom
    plt.gca().invert_yaxis()
    plt.title(q, pad=20)
    plt.yticks(rotation=0)
    plt.subplots_adjust(left=0.2)
    plt.savefig(output_dir / f"{question_to_filename(q)}.png")
    plt.close()


def plot_referrals(newcomer: pd.DataFrame):
    """
    Generate the referrals figure.
    """
    newcomer = newcomer.groupby("Referral").agg({"People": "sum"}).reset_index()
    fig = px.pie(
        newcomer,
        values="People",
        names="Referral",
        title="How did newcomers find RatFr?",
    )

    fig.update_traces(
        hovertemplate=None,
    )

    return fig


def plot_attendance(attendance: pd.DataFrame, year: int):
    """
    Generate the attendance figure.
    """
    attendance = attendance.drop(columns=["Retained3", "RetainedAll"])
    attendance = attendance.melt(
        id_vars=["Date", "Event"],
        var_name="Participant type",
        value_name="Participants",
    )

    fig = px.line(
        attendance,
        x="Date",
        y="Participants",
        color="Participant type",
        title="Attendance",
        color_discrete_map={"Recurring": "#ffd320", "New": "red", "Total": "darkblue"},
        custom_data=["Event", "Participant type"],
    )

    fig.update_traces(
        mode="markers+lines",
        marker=dict(size=10),
        hovertemplate="%{customdata[0]}<br>Date: %{x}<br>%{customdata[1]} participants: %{y}",
    )
    fig.update_layout(
        yaxis=dict(
            range=[0, attendance["Participants"].max() + 5], title="Participants"
        ),
        xaxis=dict(range=[f"{year}-01-01", f"{year}-12-31"], title="Date"),
    )

    return fig


def plot_feedback_frequency(
    feedback: pd.DataFrame, attendance: pd.DataFrame, year: int
):
    """
    Plot what percentage of participants gave feedback.
    Each line in 'feedback' for a specific 'Date of the event' is a feedback.
    """
    feedback = feedback.rename(columns={"Date of the event": "Date"})
    feedback["Feedback Count"] = 1
    feedback = feedback.groupby("Date").sum().reset_index()

    feedback = feedback.merge(attendance, on="Date", how="left")
    # as percentage, rounded

    feedback["Feedback percentage"] = round(
        feedback["Feedback Count"] / feedback["Total"] * 100, 2
    )

    fig = px.line(
        feedback,
        x="Date",
        y="Feedback percentage",
        title="Percentage of people that filled out the feedback form",
        color_discrete_sequence=["#ffd320"],
        custom_data=["Event", "Feedback Count", "Total"],
    )
    fig.update_traces(
        mode="markers+lines",
        marker=dict(size=10),
        hovertemplate="%{customdata[0]}<br>Date: %{x}<br>%{customdata[1]}/%{customdata[2]} participants gave feedback<br>%{y}%",
    )
    fig.update_layout(
        yaxis=dict(range=[0, 100], title="Feedback percentage"),
        xaxis=dict(range=[f"{year}-01-01", f"{year}-12-31"], title="Date"),
    )

    return fig


def question_to_filename(q):
    """
    This function converts a 'question' to a reasonable filename.
    """
    filename = re.sub("\W+", "-", q).lower()
    filename = filename.strip("-")
    return filename


def pluralize_people(n):
    """
    This function pluralizes the word 'people' in English.
    """
    return f'{n} {"person" if n == 1 else "people"}'


if __name__ == "__main__":
    main()
