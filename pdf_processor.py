import os
import re
import fitz

from database import (
    clear_unit,
    save_unit,
    get_topic_id,
    save_chunk
)


TOPIC_PATTERN = re.compile(
    r"^\s*(\d+\.\d+)\s*[:.\-]?\s*(.+?)\s*$"
)


def clean_line(line):
    line = line.replace("\x00", " ")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def detect_topics(text):
    topics = []

    for line in text.splitlines():
        line = clean_line(line)

        if not line:
            continue

        match = TOPIC_PATTERN.match(line)

        if match:
            code = match.group(1)
            name = match.group(2).strip()

            if len(name) > 2:
                topics.append({
                    "code": code,
                    "name": name
                })

    unique = {}

    for topic in topics:
        unique[topic["code"]] = topic

    return list(unique.values())


def split_into_chunks(text, max_words=180, overlap=40):
    words = text.split()

    if not words:
        return []

    chunks = []

    start = 0

    while start < len(words):
        end = min(start + max_words, len(words))

        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk.strip())

        if end >= len(words):
            break

        start = end - overlap

    return chunks


def process_pdf(subject_name, unit_number, pdf_path):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    clear_unit(subject_name, unit_number)

    document = fitz.open(pdf_path)

    all_pages = []

    for page_index, page in enumerate(document):
        text = page.get_text("text")

        all_pages.append({
            "page": page_index + 1,
            "text": text
        })

    document.close()

    full_text = "\n".join(
        page["text"] for page in all_pages
    )

    detected_topics = detect_topics(full_text)

    if not detected_topics:
        raise ValueError(
            "No numbered topics such as 1.1, 1.2, 1.3 were detected in the PDF."
        )

    unit_id = save_unit(
        subject_name,
        unit_number,
        pdf_path,
        detected_topics
    )

    topic_lookup = {
        topic["code"]: topic
        for topic in detected_topics
    }

    current_topic = None

    for page_data in all_pages:

        page_number = page_data["page"]
        page_text = page_data["text"]

        lines = page_text.splitlines()

        current_text = []

        for line in lines:

            cleaned = clean_line(line)

            match = TOPIC_PATTERN.match(cleaned)

            if match:

                if current_topic and current_text:

                    topic_id = get_topic_id(
                        unit_id,
                        current_topic
                    )

                    chunks = split_into_chunks(
                        "\n".join(current_text)
                    )

                    for chunk in chunks:
                        save_chunk(
                            topic_id,
                            page_number,
                            chunk
                        )

                current_topic = match.group(1)

                current_text = [
                    topic_lookup[current_topic]["name"]
                ]

            else:

                if current_topic:
                    current_text.append(cleaned)

        if current_topic and current_text:

            topic_id = get_topic_id(
                unit_id,
                current_topic
            )

            chunks = split_into_chunks(
                "\n".join(current_text)
            )

            for chunk in chunks:
                save_chunk(
                    topic_id,
                    page_number,
                    chunk
                )

    return detected_topics