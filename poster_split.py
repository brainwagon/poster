import sys
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def split_image_to_letter(image_path, output_pdf, poster_width=20, poster_height=30, dpi=300):
    # Letter size in inches
    letter_w, letter_h = 8.5, 11
    # Calculate pixel dimensions for poster and letter sheets
    poster_px_w = int(poster_width * dpi)
    poster_px_h = int(poster_height * dpi)
    sheet_px_w = int(letter_w * dpi)
    sheet_px_h = int(letter_h * dpi)

    # Open and resize image to fit poster size
    im = Image.open(image_path)
    im = im.convert('RGB')
    im = im.resize((poster_px_w, poster_px_h), Image.LANCZOS)

    # How many sheets horizontally/vertically
    cols = poster_px_w // sheet_px_w
    rows = poster_px_h // sheet_px_h

    # If poster is not divisible perfectly, add another sheet for remainder
    if poster_px_w % sheet_px_w != 0:
        cols += 1
    if poster_px_h % sheet_px_h != 0:
        rows += 1

    # Prepare PDF
    c = canvas.Canvas(output_pdf, pagesize=letter)

    for row in range(rows):
        for col in range(cols):
            left = col * sheet_px_w
            upper = row * sheet_px_h
            right = min(left + sheet_px_w, poster_px_w)
            lower = min(upper + sheet_px_h, poster_px_h)
            box = (left, upper, right, lower)
            segment = im.crop(box)

            # Save segment to temporary file
            temp_file = f'_temp_segment_{row}_{col}.jpg'
            segment.save(temp_file, 'JPEG')

            # Draw segment on PDF page
            # ReportLab origin is at bottom-left, we want to fill the page
            c.drawImage(
                temp_file,
                0, 0,
                width=letter_w * 72,  # 1 inch = 72 pts
                height=letter_h * 72
            )
            c.showPage()
            os.remove(temp_file)

    c.save()
    print(f"PDF saved as: {output_pdf}")
    print(f"Sliced into {rows} rows and {cols} columns.")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python poster_split.py input_image output_pdf [dpi]")
        sys.exit(1)
    image_path = sys.argv[1]
    output_pdf = sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    split_image_to_letter(image_path, output_pdf, dpi=dpi)