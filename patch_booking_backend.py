with open('app/routes.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add get_slots API endpoint if missing
slots_api_code = """
@main_bp.route('/api/get_slots')
def get_slots():
    date_str = request.args.get('date', '')
    # Generates standard operating slots for selected date
    slots = ["10:00 AM", "10:45 AM", "11:30 AM", "12:15 PM", "01:00 PM", "01:45 PM", "02:30 PM", "03:15 PM", "04:00 PM", "04:45 PM", "05:30 PM"]
    return jsonify({'slots': slots, 'status': 'open'})
"""

if '/api/get_slots' not in code:
    code += "\n" + slots_api_code

with open('app/routes.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Added /api/get_slots endpoint to app/routes.py!")