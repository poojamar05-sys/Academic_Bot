import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b"
)

client = Groq(api_key=API_KEY) if API_KEY else None

BRAILLE_MAP = {
    "a": "⠁", "b": "⠃", "c": "⠉", "d": "⠙", "e": "⠑",
    "f": "⠋", "g": "⠛", "h": "⠓", "i": "⠊", "j": "⠚",
    "k": "⠅", "l": "⠇", "m": "⠍", "n": "⠝", "o": "⠕",
    "p": "⠏", "q": "⠟", "r": "⠗", "s": "⠎", "t": "⠞",
    "u": "⠥", "v": "⠧", "w": "⠺", "x": "⠭", "y": "⠽",
    "z": "⠵",
    "1": "⠁", "2": "⠃", "3": "⠉", "4": "⠙",
    "5": "⠑", "6": "⠋", "7": "⠛", "8": "⠓",
    "9": "⠊", "0": "⠚",
    " ": " ",
    ".": "⠲", ",": "⠂", ";": "⠆", ":": "⠒",
    "!": "⠖", "?": "⠦", "-": "⠤", "(": "⠣", ")": "⠜",
    "/": "⠌", "'": "⠄", '"': "⠢", "*": "⠔",
    "_": "⠸", "#": "⠼", "+": "⠖", "=": "⠶",
    "%": "⠩", "&": "⠯"
}


# ============================================================
# GROQ CORE
# ============================================================

def ask_groq(system_prompt, user_prompt):

    if client is None:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.2,
        max_tokens=4000
    )

    return response.choices[0].message.content.strip()


def text_to_braille(text):
    if text is None:
        return ""

    result = []
    for ch in str(text):
        if ch.isupper():
            result.append("⠠")
            result.append(BRAILLE_MAP.get(ch.lower(), ch))
            continue

        if ch.isdigit():
            result.append("⠼")
            result.append(BRAILLE_MAP.get(ch, ch))
            continue

        result.append(BRAILLE_MAP.get(ch, ch))

    return "".join(result).strip()


# ============================================================
# LEARN
# ============================================================

def generate_learn(topic, context):

    system_prompt = """
You are Academic AI Bot, a Computer Science Engineering
study assistant.

Your task is to teach the selected academic topic.

IMPORTANT RULES:

1. Use the supplied textbook material as the primary source.
2. Stay strictly focused on the selected topic.
3. Do not invent textbook facts.
4. Do not introduce unrelated concepts.
5. Explain difficult concepts in simple English.
6. Use headings and bullet points.
7. Use simple analogies when appropriate.
8. Use real-world examples only when consistent with
   the supplied textbook.
9. Mention textbook page numbers when available.
10. If something is not available in the supplied material,
    clearly say that it is not available in the supplied
    textbook material.
"""

    user_prompt = f"""
SELECTED TOPIC:
{topic}

TEXTBOOK MATERIAL:
{context}

Create an easy-to-understand learning lesson.

Use this structure:

# {topic}

## 1. What is it?

Give a simple explanation.

## 2. Main Concepts

Explain the important concepts.

## 3. How It Works

Explain step by step.

## 4. Easy Analogy

Give one simple analogy.

## 5. Real-World Example

Give an understandable example.

## 6. Important Points

List the important points to remember.

## 7. Quick Check

Ask exactly 3 short comprehension questions.

## 8. Revision

Give a short final recap.
"""

    return ask_groq(
        system_prompt,
        user_prompt
    )


# ============================================================
# GENERAL TEXTBOOK-GROUNDED ANSWER
# ============================================================

def generate_answer(topic, question, context):
    system_prompt = """
You are a textbook-grounded AI tutor designed for visually impaired
college students.

Answer using the supplied textbook material only.
Do not invent academic facts.
If the answer is not in the textbook, say so clearly.
Keep explanations clear, supportive, and easy to understand.
Preserve technical terms and mention pages when available.
Use structured sections with simple headings.
"""

    user_prompt = f"""
TOPIC:
{topic}

QUESTION:
{question}

TEXTBOOK MATERIAL:
{context}

Provide a clear answer for a college student. Use a predictable format:

# Topic

## Definition

## Simple Explanation

## Example

## Key Points

## Exam Point

If the textbook does not contain enough information, say:
I could not find this information in the available textbook.
"""

    return ask_groq(system_prompt, user_prompt)


# ============================================================
# NOTES
# ============================================================

def generate_notes(topic, context):

    system_prompt = """
You are an expert semester-exam answer generator
for Computer Science Engineering students.

Generate a structured 14-mark examination answer.

IMPORTANT RULES:

1. Use the supplied textbook material as the main source.
2. Do not invent unsupported textbook facts.
3. Stay focused on the selected topic.
4. Preserve important textbook terminology.
5. Make the answer easy to write in an examination.
6. Use clear headings and numbered subheadings.
7. Make diagrams simple and exam-drawable.
8. Do not create a diagram that contradicts the textbook.
9. Mention source pages when available.
"""

    user_prompt = f"""
TOPIC:
{topic}

TEXTBOOK MATERIAL:
{context}

Create a complete semester examination answer.

Use this structure:

# Question

Write a suitable 14-mark semester examination question.

# 14-Mark Answer

## 1. Introduction

## 2. Definition

## 3. Main Concept

## 4. Detailed Explanation

Use numbered subheadings.

## 5. Architecture / Diagram

If supported by the textbook, provide a simple
exam-drawable representation.

## 6. Example

## 7. Important Points

## 8. Conclusion

## Suggested Mark Distribution

Give a suggested preparation distribution totaling
exactly 14 marks.

## Source Pages

List the textbook pages used.
"""

    return ask_groq(
        system_prompt,
        user_prompt
    )


# ============================================================
# PRACTICE QUESTION
# ============================================================

def generate_practice_question(
    topic,
    context,
    question_number
):

    system_prompt = """
You are a Computer Science Engineering viva examiner.

You are conducting a voice-based academic practice session.

RULES:

1. Ask exactly ONE question.
2. The question must be answerable from the supplied
   textbook material.
3. Do not give the answer.
4. Do not ask multiple questions.
5. Use simple spoken English.
6. Difficulty should be suitable for a CSE semester student.
7. Stay strictly within the selected topic.
"""

    user_prompt = f"""
TOPIC:
{topic}

QUESTION NUMBER:
{question_number}

TEXTBOOK MATERIAL:
{context}

Generate exactly ONE oral examination question.

Return ONLY the question.
"""

    return ask_groq(
        system_prompt,
        user_prompt
    )


# ============================================================
# PRACTICE ANSWER EVALUATION
# ============================================================

def evaluate_practice(
    topic,
    context,
    question,
    answer
):

    system_prompt = """
You are a fair Computer Science Engineering viva evaluator.

Evaluate a student's spoken answer using the supplied
textbook material.

IMPORTANT RULES:

1. The supplied textbook is the authoritative source.
2. Do not require information that is not present
   in the supplied material.
3. Ignore minor grammar mistakes.
4. Understand speech-recognition mistakes where possible.
5. Focus on technical meaning.
6. Give partial credit when appropriate.
7. Do not be unnecessarily harsh.
8. Clearly identify missing concepts.
9. Clearly identify technically incorrect statements.
10. If the answer is significantly incorrect, provide
    the correct answer.
11. Score must be an integer from 0 to 10.

SCORING:

9-10 = Excellent understanding
7-8  = Correct with minor missing details
5-6  = Partially correct
3-4  = Limited understanding
0-2  = Mostly incorrect or irrelevant

RETRY RULE:

If score is below 6, RETRY must be YES.

If score is 6 or above, RETRY must be NO.

The student must retry the SAME question when RETRY is YES.
"""

    user_prompt = f"""
TOPIC:
{topic}

TEXTBOOK MATERIAL:
{context}

QUESTION:
{question}

STUDENT'S SPOKEN ANSWER:
{answer}

Evaluate the student's answer.

Return EXACTLY this structure:

RESULT: Correct / Partially Correct / Incorrect

SCORE: X/10

FEEDBACK:
Give a short voice-friendly explanation.
Say whether the answer is correct, partially correct,
or incorrect.

WHAT_WAS_GOOD:
Mention what the student explained correctly.

MISSING_POINTS:
Mention important textbook concepts that were missed.
If nothing important was missed, write:
None.

WRONG_POINTS:
Mention technically incorrect statements.
If there are no important errors, write:
None.

CORRECT_ANSWER:
Give the correct answer based ONLY on the textbook.
If the student's answer is already sufficiently correct,
write:
Not required.

RETRY:
Write YES if the student must revise and answer the
SAME question again.
Write NO if the student can continue.

NEXT_FOCUS:
Give one short improvement suggestion.
"""

    return ask_groq(
        system_prompt,
        user_prompt
    )