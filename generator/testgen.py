import json
import re
from pathlib import Path


# Treat hyphenated words such as "U-Bahn" as a single word.
WORD_PATTERN = re.compile(
    r'\b[A-Za-zÄÖÜäöüßÀ-ÿ]+(?:-[A-Za-zÄÖÜäöüßÀ-ÿ]+)*\b'
)


def split_sentences(text):
    """Split text into sentences while preserving punctuation."""

    sentences = re.findall(
        r'[^.!?]+[.!?]+',
        text.strip()
    )

    consumed = ''.join(sentences)

    remainder = text.strip()[len(consumed):].strip()

    if remainder:
        sentences.append(remainder)

    return [
        s.strip()
        for s in sentences
        if s.strip()
    ]


def truncate_word(word):
    """
    Apply C-test truncation.

    Keeps the first half of the word and replaces the
    remaining characters with underscores.

    Returns:
        (truncated_word, missing_part)

    Words shorter than 2 characters are left unchanged
    and produce no answer.
    """

    # Do not truncate one-character words.
    if len(word) < 2:
        return word, None

    keep = len(word) // 2

    truncated = word[:keep] + "___"
    missing_part = word[keep:]

    return truncated, missing_part


def generate_ctest(title, text):
    """
    Generate a C-test where every other word is truncated.

    Counting starts with the SECOND word of the SECOND sentence.

    The first and last sentences remain unchanged.

    Hyphenated words such as "U-Bahn" are treated as one word.
    """

    sentences = split_sentences(text)

    if len(sentences) < 3:
        raise ValueError(
            "The text must contain at least three sentences."
        )

    middle_sentences = sentences[1:-1]

    answers = []
    modified_sentences = []

    word_index = 0

    for sentence in middle_sentences:

        def replace_word(match):
            nonlocal word_index

            word = match.group(0)

            # Every other word is truncated.
            if word_index % 2 == 1:

                replacement, answer = truncate_word(word)

                # If the word is too short, leave it unchanged
                # and do not create an answer.
                if answer is not None:
                    answers.append(answer)
                else:
                    replacement = word

            else:
                replacement = word

            word_index += 1

            return replacement

        modified_sentence = WORD_PATTERN.sub(
            replace_word,
            sentence
        )

        modified_sentences.append(
            modified_sentence
        )

    output_sentences = (
        [sentences[0]]
        + modified_sentences
        + [sentences[-1]]
    )

    result_text = " ".join(
        output_sentences
    )

    # Safety check: every ___ must have exactly one answer.
    blank_count = result_text.count("___")

    if blank_count != len(answers):
        raise ValueError(
            f"Generated {blank_count} blanks but "
            f"{len(answers)} answers."
        )

    return {
        "title": title,
        "text": result_text,
        "answers": answers,
        "original": text,
    }


def save_ctest(title, text, output_file):
    """Generate and save the C-test as JSON."""

    ctest = generate_ctest(
        title,
        text
    )

    with Path(output_file).open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            ctest,
            f,
            ensure_ascii=False,
            indent=2
        )

    return ctest


def process_text_file(input_file, output_dir):
    """
    Read one TXT file, generate a C-test, and save it as JSON.

    The filename without the .txt extension is used as the title.
    """

    input_file = Path(input_file)
    output_dir = Path(output_dir)

    text = input_file.read_text(
        encoding="utf-8"
    ).strip()

    title = input_file.stem

    output_file = (
        output_dir /
        f"{input_file.stem}_ctest.json"
    )

    save_ctest(
        title=title,
        text=text,
        output_file=output_file
    )

    return output_file


def process_directory(input_dir, output_dir):
    """
    Process every .txt file in the input directory.
    """

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    txt_files = sorted(
        input_dir.glob("*.txt")
    )

    if not txt_files:
        print(
            f"No .txt files found in {input_dir}"
        )
        return

    for input_file in txt_files:

        try:

            output_file = process_text_file(
                input_file,
                output_dir
            )

            print(
                f"Created: {output_file}"
            )

        except ValueError as e:

            print(
                f"Skipping {input_file.name}: {e}"
            )


if __name__ == "__main__":

    input_directory = "input"

    output_directory = "output"

    process_directory(
        input_directory,
        output_directory
    )
