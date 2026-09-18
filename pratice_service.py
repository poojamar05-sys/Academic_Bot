"""
Practice Service
----------------
Voice-based AI viva/practice system.

Flow:
1. Generate question
2. Student answers by voice
3. Evaluate answer
4. Give score + feedback
5. If weak answer:
      - explain mistake
      - give correct answer
      - ask student to revise
      - allow reattempt
6. If acceptable:
      - move to next question
"""

import re

from ai_service import (
    generate_practice_question,
    evaluate_practice
)


MAX_QUESTIONS = 5

# Minimum score required to move to the next question
PASS_SCORE = 6


# ============================================================
# START PRACTICE
# ============================================================

def start_practice(topic_name, context):

    if not topic_name:
        raise ValueError(
            "Topic name is required."
        )

    if not context or not context.strip():
        raise ValueError(
            "No study material was found for this topic."
        )

    question = generate_practice_question(
        topic_name,
        context,
        1
    )

    return {
        "success": True,
        "question": question,
        "question_number": 1,
        "total_questions": MAX_QUESTIONS,
        "attempt": 1
    }


# ============================================================
# EVALUATE ANSWER
# ============================================================

def evaluate_answer(
    topic_name,
    context,
    question,
    student_answer
):

    if not student_answer:
        raise ValueError(
            "Student answer is empty."
        )

    evaluation = evaluate_practice(
        topic_name,
        context,
        question,
        student_answer
    )

    score = extract_score(
        evaluation
    )

    # Determine answer quality
    if score >= 8:

        result = "correct"

    elif score >= PASS_SCORE:

        result = "partial"

    else:

        result = "weak"

    return {
        "success": True,
        "evaluation": evaluation,
        "score": score,
        "result": result,
        "retry_required": score < PASS_SCORE
    }


# ============================================================
# NEXT QUESTION
# ============================================================

def generate_next_question(
    topic_name,
    context,
    question_number
):

    if question_number > MAX_QUESTIONS:

        return {
            "finished": True
        }

    question = generate_practice_question(
        topic_name,
        context,
        question_number
    )

    return {
        "finished": False,
        "question": question,
        "question_number": question_number
    }


# ============================================================
# SCORE EXTRACTION
# ============================================================

def extract_score(evaluation):

    if not evaluation:
        return 0

    match = re.search(
        r"SCORE\s*:\s*(\d+)\s*/\s*10",
        evaluation,
        re.IGNORECASE
    )

    if match:

        score = int(
            match.group(1)
        )

        return max(
            0,
            min(score, 10)
        )

    return 0


# ============================================================
# PERCENTAGE
# ============================================================

def calculate_percentage(
    score,
    total
):

    if total <= 0:
        return 0

    return round(
        (score / total) * 100
    )


# ============================================================
# PERFORMANCE MESSAGE
# ============================================================

def get_performance_message(
    percentage
):

    if percentage >= 80:

        return (
            "Good performance. "
            "You have a strong understanding "
            "of this topic."
        )

    if percentage >= 60:

        return (
            "Good attempt. "
            "Revise the important concepts "
            "and try again."
        )

    if percentage >= 40:

        return (
            "You have understood some parts. "
            "Review the topic carefully "
            "and practice again."
        )

    return (
        "More revision is recommended. "
        "Study the topic once again "
        "and then retry the practice."
    )