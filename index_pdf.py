from pdf_processor import process_pdf


if __name__ == "__main__":

    subject = "Cloud Computing"
    unit = 1

    pdf_path = r"knowledge\cloud_computing\unit1.pdf"

    print()
    print("=" * 60)
    print("INDEXING PDF")
    print("=" * 60)

    topics = process_pdf(
        subject,
        unit,
        pdf_path
    )

    print()
    print("Detected topics:")

    for topic in topics:
        print(
            f"{topic['code']} - {topic['name']}"
        )

    print()
    print("PDF indexing completed.")