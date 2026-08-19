import json
import re
from pathlib import Path


WORD_PATTERN = re.compile(r'\b[A-Za-zÄÖÜäöüßÀ-ÿ]+\b')


def split_sentences(text):
    """Split text into sentences while preserving punctuation."""
    sentences = re.findall(r'[^.!?]+[.!?]+', text.strip())

    consumed = ''.join(sentences)
    remainder = text.strip()[len(consumed):].strip()

    if remainder:
        sentences.append(remainder)

    return [s.strip() for s in sentences if s.strip()]


def truncate_word(word):
    """
    Apply C-test truncation.

    Keeps the first half of the word and replaces the remaining
    characters with underscores.

    Returns both the displayed word and the missing characters.
    """

    keep = len(word) // 2

    if keep < 1:
        return word, ""

    truncated = word[:keep] + "___"
    missing_part = word[keep:]

    return truncated, missing_part


def generate_ctest(title, text):
    """
    Generate a C-test where every other word is truncated.

    Counting starts with the SECOND word of the SECOND sentence.

    The first and last sentences remain unchanged.
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

            if word_index % 2 == 1:
                replacement, answer = truncate_word(word)
                answers.append(answer)
            else:
                replacement = word

            word_index += 1
            return replacement

        modified_sentence = WORD_PATTERN.sub(
            replace_word,
            sentence
        )

        modified_sentences.append(modified_sentence)

    output_sentences = (
        [sentences[0]]
        + modified_sentences
        + [sentences[-1]]
    )

    return {
        "title": title,
        "text": " ".join(output_sentences),
        "answers": answers,
    }


def save_ctest(title, text, output_file):
    """Generate and save the C-test as JSON."""

    ctest = generate_ctest(title, text)

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

    # Read the text file
    text = input_file.read_text(encoding="utf-8").strip()

    # Use filename as title
    title = input_file.stem

    # Output filename
    output_file = output_dir / f"{input_file.stem}_ctest.json"

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

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    txt_files = sorted(input_dir.glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {input_dir}")
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

    # Folder containing the .txt files
    input_directory = "input"

    # Folder where the .json files will be created
    output_directory = "output"

    process_directory(
        input_directory,
        output_directory
    )