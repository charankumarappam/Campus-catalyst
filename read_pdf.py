import pypdf
import sys

def dump_pdf(path):
    print(f"=== {path} ===")
    try:
        reader = pypdf.PdfReader(path)
        for i, page in enumerate(reader.pages):
            print(f"--- PAGE {i+1} ---")
            print(page.extract_text())
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        dump_pdf(sys.argv[1])
