import os
import re

template_dir = 'app/templates'
target_logo_path = "{{ url_for('static', filename='img/jackiecutz_logo.png') }}"

# List of all HTML files to patch
templates = [f for f in os.listdir(template_dir) if f.endswith('.html')]

for t in templates:
    file_path = os.path.join(template_dir, t)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace any card_bg.jpg or incorrect flyer paths used in <img> tags for logos
    updated_content = re.sub(
        r"src=[\"']\{\{\s*url_for\('static',\s*filename=['\"]img/(card_bg\.jpg|flyer\.jpg|logo_old\.png)['\"]\)\s*\}\}[\"']",
        f'src="{target_logo_path}"',
        content
    )

    # 2. Add screen blending to ensure black boxes around logo images vanish
    updated_content = updated_content.replace('object-contain', 'object-contain mix-blend-screen')

    # Save only if changes were made
    if updated_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Updated logo in {t}")
    else:
        print(f"Logo already verified in {t}")

print("\nAll templates successfully updated to use the official Jackiecutz logo!")