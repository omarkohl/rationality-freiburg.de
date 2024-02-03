#!/usr/bin/env python3

"""
This script generates a markdown page suitable for Hugo containing tables with data and plots.
The data is read from a CSV file.
"""

import os
import re
from typing import Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Filenames
FEEDBACK_DE_SOURCE = 'Experiment - Event Feedback (Responses) - DE.csv' # TODO
FEEDBACK_EN_SOURCE = 'Experiment - Event Feedback (Responses) - EN.csv' # TODO
FEEDBACK_CLEANED = 'feedback2024.csv'
ATTENDANCE_SOURCE = 'attendance-statistics.csv'
ATTENDANCE_CLEANED = 'attendance2024.csv'
REFERRAL_CLEANED = 'referrals2024.csv'

QUESTIONS = {
    1: '1. Practical use: For my life, what we did today will have ...',
    2: '2. The atmosphere / vibe was ...',
    3: '3. The amount of content / exercises covered was ...',
    4: '4. The difficulty level of the content / discussion was ...',
    5: '5. Structure: On the whole the event needed ...',
    6: '6. The moderation should have been ...',
    7: '7. Host preparation: The content / exercises were ...',
    8: '8. Changing your mind: The event made me ...',
    9: '9. Do you think you will come to one (or more) of the next three events?',
    10: '10. If you answered "probably no" in the previous question or are very uncertain, why is that?',
    11: '11. What did you like the most today? What did you like the least?',
}

QUESTIONS_DE = {
    QUESTIONS[1]: '1. Was wir heute getan haben wird für mich ... praktischen Nutzen haben.',
    QUESTIONS[2]: '2. Die Atmosphäre / Stimmung war ...',
    QUESTIONS[3]: '3. Die Menge an Inhalt / Übungen war ...',
    QUESTIONS[4]: '4. Das Schwierigkeitsniveau des Inhalts / der Diskussion war ...',
    QUESTIONS[5]: '5. Struktur: Insgesamt brauchte die Veranstaltung ...',
    QUESTIONS[6]: '6. Die Moderation hätte ... sein sollen.',
    QUESTIONS[7]: '7. Der Inhalt / die Übungen waren ... vorbereitet.',
    QUESTIONS[8]: '8. Die Veranstaltung hat mich dazu gebracht ... zu hinterfragen.',
    QUESTIONS[9]: '9. Glaubst du, dass du zu einer (oder mehreren) der nächsten drei Veranstaltungen kommen wirst?',
    QUESTIONS[10]: '10. Wenn du die vorherige Frage mit „eher nein“ beantwortet hast oder sehr unsicher bist, warum?',
    QUESTIONS[11]: '11. Was hat dir heute am besten gefallen? Was hat dir am wenigsten gefallen?',
}

QUESTION_RESPONSE_OPTIONS = {
    QUESTIONS[1]: [
        'a lot of practical use',
        'quite a bit of practical use',
        'some practical use',
        'little practical use',
        'very little practical use',
    ],
    QUESTIONS[2]: [
        'fantastic',
        'good',
        'okay',
        'bad',
        'horrible',
    ],
    QUESTIONS[3]: [
        'way too much',
        'too much',
        'just right',
        'too little',
        'way too little',
    ],
    QUESTIONS[4]: [
        'much too easy',
        'too easy',
        'just right',
        'too difficult',
        'much too difficult',
    ],
    QUESTIONS[5]: [
        'much more structure',
        'more structure',
        '(was just right)',
        'less structure',
        'much less structure',
    ],
    QUESTIONS[6]: [
        'much more relaxed',
        'more relaxed',
        '(was just right)',
        'more assertive',
        'much more assertive',
    ],
    QUESTIONS[7]: [
        'very well prepared',
        'well prepared',
        'okay prepared',
        'not well prepared',
        'not well prepared at all',
    ],
    QUESTIONS[8]: [
        'question many things',
        'question some things',
        'question few things',
        'question very few things',
        'not question anything',
    ],
}

Q09_RESPONSES = [
    'probably yes',
    'probably no',
]

Q09_RESPONSES_DE = {
    'probably yes': 'eher ja',
    'probably no': 'eher nein',
}

Q10_RESPONSES = [
    "I live too far away.",
    "Friday evening is a bad timeslot for me.",
    "I can't fit another activity into my life.",
    "I'm not very interested in your usual topics.",
    "I did not like today's venue.",
    "I did not like (some of) the people here.",
    "The level of English is too advanced for me.",
]

Q10_RESPONSES_DE = {
    "I live too far away.": "Ich wohne zu weit weg.",
    "Friday evening is a bad timeslot for me.": "Freitagabend ist unpassend für mich.",
    "I can't fit another activity into my life.": "Ich kann keine weitere Tätigkeit in mein Leben einbauen.",
    "I'm not very interested in your usual topics.": "Ich bin nicht sehr an euren üblichen Themen interessiert.",
    "I did not like today's venue.": "Ich mochte den heutigen Veranstaltungsort nicht.",
    "I did not like (some of) the people here.": "Ich mochte einige der Leute hier nicht.",
    "The level of English is too advanced for me.": "Das Englischniveau ist zu hoch für mich.",
}


def main():
    """
    This function is the entry point of the script.
    """
    generate_feedback_file(FEEDBACK_DE_SOURCE, FEEDBACK_EN_SOURCE, FEEDBACK_CLEANED)
    generate_attendance_files(ATTENDANCE_SOURCE, ATTENDANCE_CLEANED, REFERRAL_CLEANED)
    # TODO generate data about the source of newcomers
    generate_output(FEEDBACK_CLEANED, ATTENDANCE_CLEANED)


def generate_feedback_file(de_source: str, en_source: str, cleaned: str):
    """
    This function reads the feedback data from the source files, cleans it up and writes it out into a new file.
    The source files are then removed.
    """
    if not os.path.isfile(de_source) or not os.path.isfile(en_source):
        return
    # First we clean up the data after download it from Google forms
    df_de = pd.read_csv(de_source)
    df_en = pd.read_csv(en_source)

    # Rename the columns of the German dataframe to the English column names
    df_de.columns = df_en.columns

    df = pd.concat([df_de, df_en], axis=0, ignore_index=True)

    # Remove the timestamp and name columns
    df.drop(['Timestamp', '12. (optional) Name'], axis=1, inplace=True)

    df['Date of the event'] = pd.to_datetime(df['Date of the event'], format='%d/%m/%Y')
    q09_mapping = {v: k for k, v in Q09_RESPONSES_DE.items()}
    q09_mapping.update({v: v for v in Q09_RESPONSES})
    df[QUESTIONS[9]] = df[QUESTIONS[9]].map(q09_mapping)
    df[QUESTIONS[10]] = df[QUESTIONS[10]].map(_map_q10_responses)

    df.sort_values(by=['Date of the event'] + list(df.columns[1:]), inplace=True)

    # Write the data out into a CSV file named data2024.csv
    df.to_csv(cleaned, index=False)
    # Remove the original files
    os.remove(de_source)
    os.remove(en_source)

def _map_q10_responses(response: Optional[str]) -> Optional[Tuple[str]]:
    """
    This function converts the responses to question 10 to a list of strings
    and translates them to English if they are in German.
    """
    q10_mapping = {v: k for k, v in Q10_RESPONSES_DE.items()}
    q10_mapping.update({v: v for v in Q10_RESPONSES})
    if pd.isna(response):
        return response
    res = []
    # Google forms exports the data as a comma-separated string and the
    # user is allowed to input their own response, which could contain
    # a comma. Therefore we split the string by '.,'. We then append
    # the missing dot.
    for i in response.split('.,'):
        i = i.strip()
        if i and i[-1] not in '.!?':
            i += '.'
        res.append(q10_mapping.get(i, i))
    return tuple(res) if res else None

def generate_attendance_files(source: str, cleaned_attendance: str, newcomer_referral: str):
    """
    This function reads the attendance data from the source file, cleans it up
    and writes it out into two new files.
    The source file is then removed.
    TODO This function could generate another file with number of events
    attended per participant e.g. 10 people came to 2 events, 5 people came to
    3 events, etc..
    """
    if not os.path.isfile(source):
        return
    df = pd.read_csv(source, sep=';')

    referrals = df['How did you find RatFr?'].value_counts()
    referrals.sort_index(ascending=True, inplace=True)
    referrals.to_csv(newcomer_referral, index=True)

    df.drop(['How did you find RatFr?', 'Abs. Attendance', 'Rel. Attendance', ], axis=1, inplace=True)
    df.drop(df.columns[0], axis=1, inplace=True)
    out_df = pd.DataFrame(columns=['Date', 'Recurring participants', 'New participants', 'Total participants'])
    for c in df.columns:
        # count the number of 1s in the column, that's the number of recurring participants
        recurring = df[c].value_counts().get(1, 0)
        # count the number of 2s in the column, that's the number of new participants
        new = df[c].value_counts().get(2, 0)
        total = recurring + new
        out_row = pd.DataFrame({
            'Date': [pd.to_datetime(c, dayfirst=True)],
            'Recurring participants': [recurring],
            'New participants': [new],
            'Total participants': [total]},
            )
        out_df = pd.concat([out_df, out_row], ignore_index=True)
    out_df.to_csv(cleaned_attendance, index=False)
    os.remove(source)


def generate_output(feedback_file: str, attendance_file: str):
    """
    This function reads the cleaned data and generates a markdown page containing tables with data and plots.
    """
    # Read the cleaned data into a dataframe
    if not os.path.isfile(feedback_file):
        raise FileNotFoundError(f'The file {feedback_file} does not exist')

    feedback_df = pd.read_csv(feedback_file)
    attendance_df = pd.read_csv(attendance_file)

    # q10 in feedback_df is a string representing a list of strings.
    # I want to convert it to a list of strings.
    feedback_df[QUESTIONS[10]] = feedback_df[QUESTIONS[10]].dropna().map(eval)

    # Display all unique values of 'Date of the event'
    dates = feedback_df['Date of the event'].unique()
    dates = sorted(dates)

    print('Unique dates of the event:', dates)

    # create a directory 'output' if it doesn't exist
    OUTPUT_DIR = 'output'
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for d in dates:
        # create a directory for the current date if it doesn't exist
        date_dir = os.path.join(OUTPUT_DIR, str(d))
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)
        # Filter the dataframe for the current date
        feedback_filtered_df = feedback_df[feedback_df['Date of the event'] == d]
        attendance_filtered_df = attendance_df[attendance_df['Date'] == d]
        recurring_participants = attendance_filtered_df.iloc[0]['Recurring participants']
        new_participants = attendance_filtered_df.iloc[0]['New participants']
        total_participants = attendance_filtered_df.iloc[0]['Total participants']

        print(f'### {d}\n')
        print(f"Number of recurring participants: {recurring_participants}")
        print(f"Number of new participants: {new_participants}")
        print(f"Total number of participants: {total_participants}\n")
        generate_feedback_output(feedback_filtered_df, total_participants, date_dir)

    # Create a directory for aggregated data if it doesn't exist
    aggregated_events_dir = os.path.join(OUTPUT_DIR, 'aggregated')
    if not os.path.exists(aggregated_events_dir):
        os.makedirs(aggregated_events_dir)

    total_participants = attendance_df['Total participants'].sum()
    print(f'### Total\n')
    generate_feedback_output(feedback_df, total_participants, aggregated_events_dir)

    # Generate the markdown page
    with open('feedback.md', 'w') as f:
        f.write('---\n')
        f.write('title: "Feedback"\n')
        f.write('date: 2020-06-29T18:00:00+02:00\n')
        f.write('draft: false\n')
        f.write('---\n\n')

        f.write('## Feedback\n\n')

        # Generate the tables
        f.write('### Summary\n\n')
        f.write(feedback_df.describe().to_markdown() + '\n\n')

        f.write('### Data\n\n')
        f.write(feedback_df.to_markdown() + '\n\n')

        # Generate the plots
        f.write('### Plots\n\n')
        f.write('#### Rating\n\n')
        f.write('![Rating](/img/feedback-rating.png)\n\n')

        f.write('#### Comments\n\n')
        f.write('![Comments](/img/feedback-comments.png)\n\n')

    print('Generated feedback.md')


def generate_feedback_output(feedback_df, total_participants, output_dir: str):
    print(f'Number of responses: {len(feedback_df)}')
    print(f'Response rate: {len(feedback_df) / total_participants * 100:.2f}%\n')
    for q in [QUESTIONS[i] for i in range(1, 9)]:
        print(q)
        print(f'  Number of responses: {feedback_df[q].count()}')
        print(f'  Response rate: {feedback_df[q].count() / total_participants * 100:.2f}%')
        print(f'  Average: {feedback_df[q].mean():.2f}')
        print(f'  Standard deviation: {feedback_df[q].std():.2f}\n')
        data = feedback_df[q].value_counts().sort_index()
        # if any index from 1 to 5 is missing, add it with a value of 0
        for i in range(1, 6):
            if i not in data.index:
                data[i] = 0
        data = data.sort_index()
        plot_bar_chart(data, q, output_dir)

    # Question 9
    q09_data = feedback_df[QUESTIONS[9]].value_counts()
    for i in Q09_RESPONSES:
        if i not in q09_data.index:
            q09_data[i] = 0
    q09_data = q09_data.sort_index()
    print(QUESTIONS[9])
    print(f'  Number of responses: {q09_data.sum()}')
    print(f'  Response rate: {q09_data.sum() / total_participants * 100:.2f}%')
    print('  --')
    for value, count in q09_data.items():
        print(f'  {value}: {count}')
    print()
    plot_bar_chart(q09_data, QUESTIONS[9], output_dir)

    # Question 10
    q10_responses = []
    for sublist in feedback_df[QUESTIONS[10]].dropna().tolist():
        q10_responses.extend(sublist)
    q10_responses = pd.Series(q10_responses)
    q10_data = q10_responses.value_counts().sort_index()
    for i in Q10_RESPONSES:
        if i not in q10_data.index:
            q10_data[i] = 0
    q10_data = q10_data.sort_index()
    print(QUESTIONS[10])
    print(f'  Number of responses: {q10_data.sum()}')
    print(f'  Response rate: {q10_data.sum() / total_participants * 100:.2f}%')
    print('  --')
    for value, count in q10_data.items():
        print(f'  {value}: {count}')
    print()
    plot_bar_chart_horizontal(q10_data, QUESTIONS[10], output_dir)

    # Question 11
    print(QUESTIONS[11])
    print(f'  Number of responses: {feedback_df[QUESTIONS[11]].count()}')
    print(f'  Response rate: {feedback_df[QUESTIONS[11]].count() / total_participants * 100:.2f}%')
    print('  --')
    comments = feedback_df[QUESTIONS[11]].dropna().values
    print('  ' + '\n  --\n  '.join(comments))
    print()
    print()


def plot_bar_chart(data, q, output_dir):
    """
    This function plots a bar chart based on the given data and question.
    """
    # Increase font sizes
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10

    # Create a bar chart where the x-axis is the index of the data and the y-axis is the value of the data
    plt.figure(figsize=(10, 7))
    plt.bar(data.index, data.values, color='navy', zorder=2)

    # Add gridlines
    plt.grid(axis='y', zorder=1)
    plt.xlabel('Answer')
    plt.ylabel('Number of people')
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
    if q in QUESTION_RESPONSE_OPTIONS:
        labels = [f'{label} ({i})' for i, label in zip(data.index, QUESTION_RESPONSE_OPTIONS[q])]
        plt.xticks(data.index, labels, rotation=45)
    plt.subplots_adjust(bottom=0.3)
    plt.savefig(f'{output_dir}/{question_to_filename(q)}.png')
    plt.close()


def plot_bar_chart_horizontal(data, q, output_dir):
    # plot question 10
    plt.figure(figsize=(20, 16))
    # Create a horizontal bar chart
    plt.barh(data.index, data.values, color='navy', zorder=2)
    plt.grid(axis='x', zorder=1)
    plt.ylabel('Answer')
    plt.xlabel('Number of people')
    xtick_step = 1
    xtick_max = data.max() + 1
    if data.max() > 15:
        xtick_step = 5
    elif data.max() > 10:
        xtick_step = 2
    elif data.max() < 5:
        xtick_max = 6
    plt.xticks(range(0, xtick_max, xtick_step))
    plt.title(QUESTIONS[10], pad=20)
    plt.yticks(rotation=0)
    plt.subplots_adjust(left=0.2)
    plt.savefig(f'{output_dir}/{question_to_filename(QUESTIONS[10])}.png')
    plt.close()


def question_to_filename(q):
    """
    This function converts a 'question' to a reasonable filename.
    """
    filename = re.sub('\W+', '-', q).lower()
    filename = filename.strip('-')
    return filename


if __name__ == '__main__':
    main()
