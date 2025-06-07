import pandas as pd
from typing import Optional, Tuple

QUESTIONS = {
    1: "1. Practical use: For my life, what we did today will have ...",
    2: "2. The atmosphere / vibe was ...",
    3: "3. The amount of content / exercises covered was ...",
    4: "4. The difficulty level of the content / discussion was ...",
    5: "5. Structure: On the whole the event needed ...",
    6: "6. The moderation should have been ...",
    7: "7. Host preparation: The content / exercises were ...",
    8: "8. Changing your mind: The event made me ...",
    9: "9. Do you think you will come to one (or more) of the next three events?",
    10: '10. If you answered "probably no" in the previous question or are very uncertain, why is that?',
    11: "11. What did you like the most today?",
    12: "12. What did you like the least?",
}


QUESTIONS_DE = {
    QUESTIONS[
        1
    ]: "1. Was wir heute getan haben wird für mich ... praktischen Nutzen haben.",
    QUESTIONS[2]: "2. Die Atmosphäre / Stimmung war ...",
    QUESTIONS[3]: "3. Die Menge an Inhalt / Übungen war ...",
    QUESTIONS[4]: "4. Das Schwierigkeitsniveau des Inhalts / der Diskussion war ...",
    QUESTIONS[5]: "5. Struktur: Insgesamt brauchte die Veranstaltung ...",
    QUESTIONS[6]: "6. Die Moderation hätte ... sein sollen.",
    QUESTIONS[7]: "7. Der Inhalt / die Übungen waren ... vorbereitet.",
    QUESTIONS[8]: "8. Die Veranstaltung hat mich dazu gebracht ... zu hinterfragen.",
    QUESTIONS[
        9
    ]: "9. Glaubst du, dass du zu einer (oder mehreren) der nächsten drei Veranstaltungen kommen wirst?",
    QUESTIONS[
        10
    ]: "10. Wenn du die vorherige Frage mit „eher nein“ beantwortet hast oder sehr unsicher bist, warum?",
    QUESTIONS[11]: "11. Was hat dir heute am besten gefallen?",
    QUESTIONS[12]: "12. Was hat dir am wenigsten gefallen?",
}

QUESTION_RESPONSE_OPTIONS = {
    QUESTIONS[1]: [
        "a lot of practical use",
        "quite a bit of practical use",
        "some practical use",
        "little practical use",
        "very little practical use",
    ],
    QUESTIONS[2]: [
        "fantastic",
        "good",
        "okay",
        "bad",
        "horrible",
    ],
    QUESTIONS[3]: [
        "way too much",
        "too much",
        "just right",
        "too little",
        "way too little",
    ],
    QUESTIONS[4]: [
        "much too easy",
        "too easy",
        "just right",
        "too difficult",
        "much too difficult",
    ],
    QUESTIONS[5]: [
        "much more structure",
        "more structure",
        "(was just right)",
        "less structure",
        "much less structure",
    ],
    QUESTIONS[6]: [
        "much more relaxed",
        "more relaxed",
        "(was just right)",
        "more assertive",
        "much more assertive",
    ],
    QUESTIONS[7]: [
        "very well prepared",
        "well prepared",
        "okay prepared",
        "not well prepared",
        "not well prepared at all",
    ],
    QUESTIONS[8]: [
        "question many things",
        "question some things",
        "question few things",
        "question very few things",
        "not question anything",
    ],
}

Q09_RESPONSES = [
    "probably yes",
    "probably no",
]

Q09_RESPONSES_DE = {
    "probably yes": "eher ja",
    "probably no": "eher nein",
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


def map_q10_responses(response: Optional[str]) -> Optional[Tuple[str]]:
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
    for i in response.split(".,"):
        i = i.strip()
        if i and i[-1] not in ".!?":
            i += "."
        res.append(q10_mapping.get(i, i))
    return tuple(res) if res else None
