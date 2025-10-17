#!/usr/bin/env python3
"""Generate PWA icons using PIL"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create a simple icon with N logo"""
    # Create image with gradient background
    img = Image.new('RGB', (size, size), '#0077B5')
    draw = ImageDraw.Draw(img)
    
    # Draw circle background
    margin = size // 10
    draw.ellipse([margin, margin, size-margin, size-margin], fill='#005885')
    
    # Draw N letter
    try:
        font_size = size // 2
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except:
        font = ImageFont.load_default()
    
    text = "N"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - size // 20
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Save
    img.save(output_path, 'PNG')
    print(f"Created {output_path}")

if __name__ == '__main__':
    icons_dir = 'static/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        create_icon(size, f'{icons_dir}/icon-{size}x{size}.png')
    
    print("✅ All icons generated!")
