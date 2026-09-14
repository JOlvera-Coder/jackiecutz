import os

filepath = 'app/templates/booking.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Strip out the entire Rate Your Recent Visit HTML block
review_start = content.find('<div class="my-6 bg-zinc-950')
if review_start != -1:
    review_end = content.find('</script>', review_start) + 9
    content = content[:review_start] + content[review_end:]
    print("Stripped top review banner from booking.html")

# 2. Check actual images on disk in static/img
static_img_dir = 'app/static/img'
available_files = os.listdir(static_img_dir) if os.path.exists(static_img_dir) else []
print("Actual files in app/static/img:", available_files)

# Choose the verified logo/flyer asset present in the directory
valid_img = 'img/card_bg.jpg' if 'card_bg.jpg' in available_files else ('img/flyer.jpg' if 'flyer.jpg' in available_files else 'img/logo.png')

# Fix broken image src tags
content = content.replace("filename='img/jackiecutz_logo.png'", f"filename='{valid_img}'")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated app/templates/booking.html cleanly.")