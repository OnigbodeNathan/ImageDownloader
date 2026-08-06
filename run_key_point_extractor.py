import sys

from key_point_extractor import extract_key_points


def main() -> None:
    print("Enter text to extract key points from (press Enter on an empty line to finish):")
    paragraphs = []
    while True:
        line = input()
        if line.strip() == "":
            break
        paragraphs.append(line)

    text = "\n".join(paragraphs).strip()
    if not text:
        print("No input provided.")
        return

    points = extract_key_points(text, top_n=10)
    print("\nExtracted key points:")
    if not points:
        print("No key points found.")
    else:
        for index, point in enumerate(points, start=1):
            print(f"{index}. {point}")


if __name__ == "__main__":
    main()
