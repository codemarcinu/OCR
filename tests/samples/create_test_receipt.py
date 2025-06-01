#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

# Create samples directory if it doesn't exist
samples_dir = Path(__file__).parent
samples_dir.mkdir(parents=True, exist_ok=True)

# Create a new image with white background
width = 1200  # Increased width
height = 1600  # Increased height
image = Image.new('RGB', (width, height), 'white')
draw = ImageDraw.Draw(image)

# Try to load a monospace font
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 32)  # Increased font size
except:
    try:
        font = ImageFont.truetype('/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf', 32)  # Increased font size
    except:
        font = ImageFont.load_default()

# Sample receipt text
receipt_text = """
LIDL Sp. z o.o. sp.k.
ul. Poznańska 48
62-080 Tarnowo Podgórne
NIP: 123-45-67-890

PARAGON FISKALNY

Mleko UHT 3.2% 1L        A      3.99
Chleb Wiejski 500g       B      4.50
Masło Extra 200g         A      6.99
Ser Gouda 300g           A      8.99
Jogurt Naturalny         A      2.49
Jajka 10szt             B      7.99
Pomidory Luz kg         B      6.99
Banan Luz kg            B      5.99
Woda Mineralna 1.5L      A      2.29
Sok Pomarańczowy 1L      A      4.99

SUMA PLN                      54.21
Zapłacono KARTA              54.21

PTU A 23%                     3.89
PTU B 8%                      1.92

Nr sys.: ABC123
Nr par.: 123456
Data: 2024-03-15
Godz.: 14:30
Kasjer: ANNA"""

# Draw the text
y_position = 100  # Increased starting position
line_height = 40  # Increased line height
for line in receipt_text.split('\n'):
    # Draw white background behind text for better contrast
    text_bbox = draw.textbbox((100, y_position), line, font=font)  # Increased x position
    draw.rectangle([text_bbox[0]-5, text_bbox[1]-2, text_bbox[2]+5, text_bbox[3]+2], fill='white')
    # Draw text in pure black
    draw.text((100, y_position), line, fill=(0,0,0), font=font)  # Increased x position
    y_position += line_height

# Add a black border around the receipt
border_width = 3  # Increased border width
draw.rectangle([0, 0, width-1, height-1], outline=(0,0,0), width=border_width)

# Save the image with high quality and no compression
output_path = samples_dir / 'test_receipt.jpg'
image.save(output_path, 'JPEG', quality=100, optimize=False)
print(f"Created test receipt at: {output_path}") 