import os
import json
import re
import shutil
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from home.models import SignGesture

dist_dir = 'dist'
os.makedirs(dist_dir, exist_ok=True)
dist_static = os.path.join(dist_dir, 'static')
if not os.path.exists(dist_static):
    shutil.copytree('static', dist_static)

# 2. Export all 212 active gestures to dist/static/gestures.json
qs = SignGesture.objects.filter(is_active=True)
gestures = list(qs.values(
    'id', 'slug', 'name', 'category', 'hand_type', 'icon', 
    'spoken_text', 'description', 'audio_key', 'finger_pattern'
))
gestures_data = {
    'status': 'success',
    'count': len(gestures),
    'gestures': gestures
}
with open(os.path.join(dist_static, 'gestures.json'), 'w', encoding='utf-8') as f:
    json.dump(gestures_data, f, ensure_ascii=False, indent=2)

print(f"Exported {len(gestures)} gestures to {dist_static}/gestures.json")

# 3. Compile templates/camera.html to dist/index.html
with open('templates/camera.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace Django template tags
html = re.sub(r'{%\s*load\s+static\s*%}', '', html)
html = re.sub(r'{%\s*static\s+[\'\"]([^\'\"]+)[\'\"]\s*%}', r'/static/\1', html)

# Route /api/gestures/ to /static/gestures.json for static CDN speed
html = html.replace("fetch('/api/gestures/')", "fetch('/static/gestures.json')")

with open(os.path.join(dist_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(html)

# 4. Compile templates/widget_demo.html to dist/widget-demo.html
if os.path.exists('templates/widget_demo.html'):
    with open('templates/widget_demo.html', 'r', encoding='utf-8') as f:
        demo_html = f.read()
    with open(os.path.join(dist_dir, 'widget-demo.html'), 'w', encoding='utf-8') as f:
        f.write(demo_html)
    print("Generated dist/widget-demo.html successfully!")

print("Generated dist/index.html successfully!")
