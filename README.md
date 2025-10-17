# poster.py - Poster Generator

`poster.py` is a Python script that allows you to split large images into multiple letter-sized PDF pages, which can then be printed and assembled to create a large poster. It provides various options for customization, including poster size, print resolution, page overlap, and line colors.

## Features

*   **Image Splitting:** Divides a large image into smaller segments that fit on standard letter-sized pages.
*   **Custom Poster Sizes:** Specify your desired poster dimensions (e.g., `20x30`, `24x36`).
*   **Configurable DPI:** Set the Dots Per Inch (DPI) for the output, affecting print quality and file size.
*   **Adjustable Overlap:** Define the overlap area between pages to facilitate seamless assembly.
*   **Black and White Conversion:** Option to convert the input image to black and white.
*   **Automatic Rotation:** Automatically rotates the image to minimize the number of pages required.
*   **Customizable Line Color:** Choose the color for the overlap alignment lines using named colors (e.g., `red`, `blue`) or hexadecimal codes (e.g., `#336699`).
*   **Preview Mode:** See how many pages will be needed without generating the PDF.

## Usage

```bash
python3 poster.py [OPTIONS] <INPUT_IMAGE> <OUTPUT_PDF>
```

### Arguments

*   `<INPUT_IMAGE>`: The path to the input image file (e.g., `image.jpg`, `image.png`).
*   `<OUTPUT_PDF>`: The desired name for the output PDF file (e.g., `poster.pdf`).

### Options

*   `-s <WIDTH>x<HEIGHT>`, `--size <WIDTH>x<HEIGHT>`:
    *   Poster size in inches (e.g., `20x30`).
    *   Default: `20x30`
*   `--dpi <DPI>`:
    *   Dots per inch resolution.
    *   Default: `300`
*   `--overlap <INCHES>`:
    *   Overlap between pages in inches.
    *   Default: `0.125`
*   `-b`, `--black-and-white`:
    *   Convert the image to black and white.
*   `--line-color <COLOR>`:
    *   Color of the overlap alignment lines. Can be a named color (e.g., `red`, `white`, `black`) or a hexadecimal color code (e.g., `#336699`).
    *   Default: `black`
*   `--preview`:
    *   Show how many pages will be needed without processing the image or generating the PDF.
*   `--no-rotate`:
    *   Disable automatic rotation of the image for fewer pages.

## Requirements

*   Python 3.x
*   Pillow (`PIL`)
*   ReportLab (`reportlab`)

## Installation

1.  **Clone the repository (if applicable) or download `poster.py`:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
    (If you just have the file, navigate to its directory.)

2.  **Install the required Python packages:**
    ```bash
    pip install Pillow reportlab
    ```

## Example

To create a 24x36 inch poster from `my_image.jpg` with a DPI of 300, 0.5 inches of overlap, and red alignment lines, save it as `my_poster.pdf`:

```bash
python3 poster.py -s 24x36 --dpi 300 --overlap 0.5 --line-color red my_image.jpg my_poster.pdf
```