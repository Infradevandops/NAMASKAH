#!/bin/bash
# Generate simple SVG-based icons without PIL

cd "static/icons"

for size in 72 96 128 144 152 192 384 512; do
    cat > "icon-${size}x${size}.svg" << EOF
<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0077B5;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#005885;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" rx="$((size/5))" fill="url(#grad)"/>
  <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="$((size/2))" font-weight="bold" fill="white" text-anchor="middle" dominant-baseline="central">N</text>
</svg>
EOF
    
    # Convert SVG to PNG if ImageMagick is available
    if command -v convert &> /dev/null; then
        convert "icon-${size}x${size}.svg" "icon-${size}x${size}.png"
        rm "icon-${size}x${size}.svg"
        echo "Created icon-${size}x${size}.png"
    else
        # Keep SVG if no ImageMagick
        mv "icon-${size}x${size}.svg" "icon-${size}x${size}.png.svg"
        # Create a simple placeholder PNG using base64
        echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > "icon-${size}x${size}.png"
        echo "Created placeholder icon-${size}x${size}.png"
    fi
done

echo "✅ Icons generated!"
