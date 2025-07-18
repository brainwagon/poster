import sys
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

def split_image_to_letter_overlap(image_path, output_pdf, poster_width=20, poster_height=30, dpi=300, overlap_in=0.5):
    letter_w, letter_h = 8.5, 11
    overlap_px = int(overlap_in * dpi)
    poster_px_w = int(poster_width * dpi)
    poster_px_h = int(poster_height * dpi)
    sheet_px_w = int(letter_w * dpi)
    sheet_px_h = int(letter_h * dpi)

    im = Image.open(image_path)
    im = im.convert('RGB')
    im = im.resize((poster_px_w, poster_px_h), Image.LANCZOS)

    cols = (poster_px_w - overlap_px) // (sheet_px_w - overlap_px)
    rows = (poster_px_h - overlap_px) // (sheet_px_h - overlap_px)
    if (poster_px_w - overlap_px) % (sheet_px_w - overlap_px) != 0:
        cols += 1
    if (poster_px_h - overlap_px) % (sheet_px_h - overlap_px) != 0:
        rows += 1

    c = canvas.Canvas(output_pdf, pagesize=letter)

    for row in range(rows):
        for col in range(cols):
            left = col * (sheet_px_w - overlap_px)
            upper = row * (sheet_px_h - overlap_px)
            right = min(left + sheet_px_w, poster_px_w)
            lower = min(upper + sheet_px_h, poster_px_h)
            box = (left, upper, right, lower)
            segment = im.crop(box)

            # Draw segment on PDF page using drawInlineImage
            c.drawInlineImage(
                segment,
                0, 0,
                width=letter_w * 72,
                height=letter_h * 72
            )

            # Draw prominent alignment lines
            c.setStrokeColor(Color(0, 0, 0, alpha=0.8))  # nearly opaque black
            c.setLineWidth(1)
            c.setDash()  # solid line

            if col > 0:
                x = overlap_in * 72
                c.line(x, 0, x, letter_h * 72)
            if col < cols - 1:
                x = (letter_w - overlap_in) * 72
                c.line(x, 0, x, letter_h * 72)
            if row > 0:
                y = overlap_in * 72
                c.line(0, y, letter_w * 72, y)
            if row < rows - 1:
                y = (letter_h - overlap_in) * 72
                c.line(0, y, letter_w * 72, y)

            c.showPage()

    c.save()
    print(f"PDF saved as: {output_pdf}")
    print(f"Sliced into {rows} rows and {cols} columns with {overlap_in}\" overlap.")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python poster_split_overlap.py input_image output_pdf [dpi] [overlap_in]")
        sys.exit(1)
    image_path = sys.argv[1]
    output_pdf = sys.argv[2]
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    overlap_in = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    split_image_to_letter_overlap(image_path, output_pdf, dpi=dpi, overlap_in=overlap_in)
