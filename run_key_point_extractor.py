import json
import sys
from pathlib import Path
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

    # Save to file for key_point_search_tool
    output_file = Path("extractor_output.json")
    result = {
        "image_path": "extracted_text",
        "key_points": points
    }
    
    with output_file.open("w", encoding="utf-8") as f:
        json.dump([result], f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    print(f"Use with key_point_search_tool: python key_point_search_tool.py --input {output_file}")


if __name__ == "__main__":
    main()