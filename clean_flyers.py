import os
from PIL import Image, ImageDraw

files = ['flyer.jpg', 'flyer_es.jpg']

for filename in files:
    filepath = os.path.join('app', 'static', 'img', filename)
    if not os.path.exists(filepath):
        continue

    img = Image.open(filepath).convert('RGB')
    draw = ImageDraw.Draw(img)
    w, h = img.width, img.height

    # Only erase the printed hours lines below services (from 60% down to 78% of flyer height)
    start_y = int(h * 0.60)
    end_y = int(h * 0.78)

    for y in range(start_y, end_y):
        # Precise linear interpolation of the flyer's vertical gray gradient
        factor = (y - start_y) / max(1, (end_y - start_y))
        gray_val = int(84 + (74 - 84) * factor)
        draw.line([(0, y), (w, y)], fill=(gray_val, gray_val, gray_val))

    img.save(filepath, quality=95)
    print(f"Cleaned {filename} successfully.")

print("All flyer images updated without text overlays!")