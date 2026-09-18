import os
import re

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session
)

from dotenv import load_dotenv

from database import (
    init_database,
    get_subjects,
    get_units,
    get_topics,
    get_topic
)

from retriever import (
    retrieve,
    build_context
)

from ai_service import (
    generate_answer,
    generate_learn,
    generate_notes,
    generate_practice_question,
    evaluate_practice,
    text_to_braille
)


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "academic_ai_bot_secret_2026"
)

MAX_QUESTIONS = 5

# Score below this means:
# revise + retry SAME question
PASS_SCORE = 6


# ============================================================
# DATABASE
# ============================================================

try:
    init_database()
except Exception as e:
    print("Database initialization warning:", e)


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


# ============================================================
# SUBJECTS
# ============================================================

@app.route("/api/subjects")
def api_subjects():

    try:
        subjects = get_subjects()

        return jsonify({
            "success": True,
            "subjects": subjects
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# UNITS
# ============================================================

@app.route("/api/units")
def api_units():

    subject = request.args.get("subject")

    if not subject:

        return jsonify({
            "success": False,
            "error": "Subject is required."
        }), 400

    try:

        units = get_units(subject)

        return jsonify({
            "success": True,
            "units": units
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# TOPICS
# ============================================================

@app.route("/api/topics")
def api_topics():

    subject = request.args.get("subject")
    unit = request.args.get("unit")

    if not subject or not unit:

        return jsonify({
            "success": False,
            "error": "Subject and unit are required."
        }), 400

    try:

        topics = get_topics(
            subject,
            unit
        )

        return jsonify({
            "success": True,
            "topics": topics
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# GET TOPIC CONTEXT
# ============================================================

def get_topic_context(
    subject,
    unit,
    topic_code,
    query
):

    topic = get_topic(
        subject,
        unit,
        topic_code
    )

    if not topic:
        raise ValueError(
            "Selected topic was not found."
        )

    chunks = retrieve(
        topic["id"],
        query,
        top_k=8
    )

    context = build_context(chunks)

    return topic, context, chunks


# ============================================================
# LEARN
# ============================================================

@app.route("/api/learn", methods=["POST"])
def api_learn():

    try:

        data = request.get_json() or {}

        subject = data.get("subject")
        unit = data.get("unit")
        topic_code = data.get("topic_code")

        if not subject or not unit or not topic_code:

            return jsonify({
                "success": False,
                "error": "Subject, unit and topic are required."
            }), 400

        topic, context, chunks = get_topic_context(
            subject,
            unit,
            topic_code,
            topic_code
        )

        answer = generate_learn(
            f"{topic_code} {topic['topic_name']}",
            context
        )

        sources = sorted(
            list({
                chunk["page_number"]
                for chunk in chunks
            })
        )

        return jsonify({
            "success": True,
            "topic": topic["topic_name"],
            "answer": answer,
            "sources": sources
        })

    except Exception as e:

        print("LEARN ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# NOTES
# ============================================================

@app.route("/api/notes", methods=["POST"])
def api_notes():

    try:

        data = request.get_json() or {}

        subject = data.get("subject")
        unit = data.get("unit")
        topic_code = data.get("topic_code")

        if not subject or not unit or not topic_code:

            return jsonify({
                "success": False,
                "error": "Subject, unit and topic are required."
            }), 400

        topic, context, chunks = get_topic_context(
            subject,
            unit,
            topic_code,
            topic_code
        )

        answer = generate_notes(
            f"{topic_code} {topic['topic_name']}",
            context
        )

        sources = sorted(
            list({
                chunk["page_number"]
                for chunk in chunks
            })
        )

        return jsonify({
            "success": True,
            "topic": topic["topic_name"],
            "answer": answer,
            "sources": sources
        })

    except Exception as e:

        print("NOTES ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# ACCESSIBLE ASK AI
# ============================================================

@app.route("/api/ask", methods=["POST"])
def api_ask():
    try:
        data = request.get_json() or {}

        subject = data.get("subject")
        unit = data.get("unit")
        topic_code = data.get("topic_code")
        question = (data.get("question") or "").strip()

        if not question:
            return jsonify({
                "success": False,
                "error": "A question is required."
            }), 400

        if not subject or not unit or not topic_code:
            return jsonify({
                "success": False,
                "error": "Subject, unit and topic are required."
            }), 400

        topic, context, chunks = get_topic_context(
            subject,
            unit,
            topic_code,
            question
        )

        answer = generate_answer(
            f"{topic_code} {topic['topic_name']}",
            question,
            context
        )

        sources = sorted(
            list({
                chunk["page_number"]
                for chunk in chunks
            })
        )

        return jsonify({
            "success": True,
            "topic": topic["topic_name"],
            "answer": answer,
            "sources": sources
        })
    except Exception as e:
        print("ASK AI ERROR:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/braille", methods=["POST"])
def api_braille():
    try:
        data = request.get_json() or {}
        text = data.get("text") or ""
        return jsonify({
            "success": True,
            "braille": text_to_braille(text)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# PRACTICE - START
# ============================================================

@app.route(
    "/api/practice/start",
    methods=["POST"]
)
def practice_start():

    try:

        data = request.get_json() or {}

        subject = data.get("subject")
        unit = data.get("unit")
        topic_code = data.get("topic_code")

        if not subject or not unit or not topic_code:

            return jsonify({
                "success": False,
                "error": "Subject, unit and topic are required."
            }), 400

        topic, context, chunks = get_topic_context(
            subject,
            unit,
            topic_code,
            topic_code
        )

        question = generate_practice_question(
            f"{topic_code} {topic['topic_name']}",
            context,
            1
        )

        # Store only small information in Flask session.
        # Do NOT store the full PDF context in the cookie.
        session["practice"] = {

            "subject": subject,

            "unit": unit,

            "topic_code": topic_code,

            "topic_name": topic["topic_name"],

            "question_number": 1,

            "score": 0,

            "total": 0,

            "question": question,

            "attempt": 1,

            "accepted_questions": 0
        }

        return jsonify({
            "success": True,

            "question": question,

            "question_number": 1,

            "total_questions": MAX_QUESTIONS,

            "attempt": 1
        })

    except Exception as e:

        print("PRACTICE START ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# EXTRACT SCORE
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

        score = int(match.group(1))

        return max(
            0,
            min(score, 10)
        )

    return 0


# ============================================================
# EXTRACT FIELD
# ============================================================

def extract_field(
    text,
    field_name,
    next_fields=None
):

    if not text:
        return ""

    pattern = rf"{re.escape(field_name)}\s*:\s*(.*)"

    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )

    if not match:
        return ""

    value = match.group(1).strip()

    if next_fields:

        for field in next_fields:

            marker = re.search(
                rf"\n\s*{re.escape(field)}\s*:",
                value,
                re.IGNORECASE
            )

            if marker:

                value = value[
                    :marker.start()
                ].strip()

                break

    return value


# ============================================================
# PRACTICE - ANSWER
# ============================================================

@app.route(
    "/api/practice/answer",
    methods=["POST"]
)
def practice_answer():

    try:

        data = request.get_json() or {}

        student_answer = (
            data.get("answer") or ""
        ).strip()

        if not student_answer:

            return jsonify({
                "success": False,
                "error": "No spoken answer was received."
            }), 400

        practice = session.get("practice")

        if not practice:

            return jsonify({
                "success": False,
                "error": "Practice session expired. Please start again."
            }), 400

        subject = practice["subject"]
        unit = practice["unit"]
        topic_code = practice["topic_code"]
        topic_name = practice["topic_name"]

        question_number = practice["question_number"]

        question = practice["question"]

        # ----------------------------------------------------
        # GET TEXTBOOK CONTEXT AGAIN
        # ----------------------------------------------------

        topic, context, chunks = get_topic_context(
            subject,
            unit,
            topic_code,
            question
        )

        # ----------------------------------------------------
        # AI EVALUATION
        # ----------------------------------------------------

        evaluation = evaluate_practice(
            f"{topic_code} {topic_name}",
            context,
            question,
            student_answer
        )

        score = extract_score(
            evaluation
        )

        retry_value = extract_field(
            evaluation,
            "RETRY",
            [
                "NEXT_FOCUS"
            ]
        ).upper()

        retry_required = (
            retry_value.startswith("YES")
            or score < PASS_SCORE
        )

        # ----------------------------------------------------
        # FIELDS FOR FRONTEND
        # ----------------------------------------------------

        result = extract_field(
            evaluation,
            "RESULT",
            ["SCORE"]
        )

        feedback = extract_field(
            evaluation,
            "FEEDBACK",
            ["WHAT_WAS_GOOD"]
        )

        what_was_good = extract_field(
            evaluation,
            "WHAT_WAS_GOOD",
            ["MISSING_POINTS"]
        )

        missing_points = extract_field(
            evaluation,
            "MISSING_POINTS",
            ["WRONG_POINTS"]
        )

        wrong_points = extract_field(
            evaluation,
            "WRONG_POINTS",
            ["CORRECT_ANSWER"]
        )

        correct_answer = extract_field(
            evaluation,
            "CORRECT_ANSWER",
            ["RETRY"]
        )

        next_focus = extract_field(
            evaluation,
            "NEXT_FOCUS"
        )

        # ----------------------------------------------------
        # RETRY SAME QUESTION
        # ----------------------------------------------------

        if retry_required:

            practice["attempt"] = (
                practice.get("attempt", 1) + 1
            )

            session["practice"] = practice

            retry_message = (
                "Please revise the topic and answer "
                "the same question again."
            )

            if correct_answer and (
                correct_answer.lower()
                != "not required."
            ):

                retry_message = (
                    "Please revise this correct answer "
                    "and try the same question again."
                )

            return jsonify({

                "success": True,

                "finished": False,

                "retry_required": True,

                "question_number":
                    question_number,

                "attempt":
                    practice["attempt"],

                "question":
                    question,

                "evaluation":
                    evaluation,

                "result":
                    result,

                "score":
                    score,

                "feedback":
                    feedback,

                "what_was_good":
                    what_was_good,

                "missing_points":
                    missing_points,

                "wrong_points":
                    wrong_points,

                "correct_answer":
                    correct_answer,

                "next_focus":
                    next_focus,

                "retry_message":
                    retry_message
            })

        # ----------------------------------------------------
        # ACCEPT ANSWER
        # ----------------------------------------------------

        practice["score"] += score

        practice["total"] += 10

        practice["accepted_questions"] += 1

        # Reset attempt for next question.
        practice["attempt"] = 1

        # ----------------------------------------------------
        # FIVE QUESTIONS COMPLETED
        # ----------------------------------------------------

        if practice["accepted_questions"] >= MAX_QUESTIONS:

            final_score = practice["score"]

            final_total = practice["total"]

            percentage = round(
                (
                    final_score /
                    final_total
                ) * 100
            ) if final_total else 0

            if percentage >= 80:

                performance = (
                    "Strong performance. "
                    "You demonstrated a good understanding "
                    "of the selected topic."
                )

            elif percentage >= 60:

                performance = (
                    "Good attempt. "
                    "Revise the important concepts once more."
                )

            elif percentage >= 40:

                performance = (
                    "You understood some parts. "
                    "Review the topic and practice again."
                )

            else:

                performance = (
                    "More revision is recommended. "
                    "Study the topic again and retry."
                )

            session.pop(
                "practice",
                None
            )

            return jsonify({

                "success": True,

                "finished": True,

                "retry_required": False,

                "question_number":
                    question_number,

                "evaluation":
                    evaluation,

                "result":
                    result,

                "score":
                    score,

                "feedback":
                    feedback,

                "what_was_good":
                    what_was_good,

                "missing_points":
                    missing_points,

                "wrong_points":
                    wrong_points,

                "correct_answer":
                    correct_answer,

                "next_focus":
                    next_focus,

                "final_score":
                    final_score,

                "final_total":
                    final_total,

                "percentage":
                    percentage,

                "performance":
                    performance
            })

        # ----------------------------------------------------
        # GENERATE NEXT QUESTION
        # ----------------------------------------------------

        next_question_number = (
            practice["accepted_questions"] + 1
        )

        next_question = generate_practice_question(
            f"{topic_code} {topic_name}",
            context,
            next_question_number
        )

        practice["question_number"] = (
            next_question_number
        )

        practice["question"] = (
            next_question
        )

        session["practice"] = practice

        return jsonify({

            "success": True,

            "finished": False,

            "retry_required": False,

            "question_number":
                next_question_number,

            "attempt": 1,

            "evaluation":
                evaluation,

            "result":
                result,

            "score":
                score,

            "feedback":
                feedback,

            "what_was_good":
                what_was_good,

            "missing_points":
                missing_points,

            "wrong_points":
                wrong_points,

            "correct_answer":
                correct_answer,

            "next_focus":
                next_focus,

            "next_question":
                next_question
        })

    except Exception as e:

        print("PRACTICE ANSWER ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# HEALTH
# ============================================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "success",
        "message": "Academic AI Bot backend is running.",
        "model": os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b"
        )
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )