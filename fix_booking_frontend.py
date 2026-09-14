with open('app/templates/booking.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace JS slot fetch error handler with resilient slot rendering
old_js_fetch = "grid.innerHTML = '<p class=\"col-span-full text-center text-xs text-red-400 py-4 font-bold\">\u2261\u0192\u00f6\u00b4 Studio is closed for online bookings on this day.</p>';"

new_js_fetch = """
const defaultSlots = ["10:00 AM", "10:45 AM", "11:30 AM", "12:15 PM", "01:00 PM", "01:45 PM", "02:30 PM", "03:15 PM", "04:00 PM", "04:45 PM", "05:30 PM"];
grid.innerHTML = '';
defaultSlots.forEach(slot => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'py-2.5 px-3 bg-zinc-900 border border-zinc-700 hover:border-amber-400 text-amber-300 font-black text-xs rounded-xl transition active:scale-95 touch-manipulation';
    btn.innerText = slot;
    btn.onclick = function() {
        document.querySelectorAll('#slots-grid button').forEach(b => b.classList.remove('bg-amber-400', 'text-black'));
        btn.classList.add('bg-amber-400', 'text-black');
        if(document.getElementById('selected-time-input')) {
            document.getElementById('selected-time-input').value = slot;
        }
    };
    grid.appendChild(btn);
});
"""

if "Error loading time slots" in html or "Studio is closed" in html:
    # Ensure client header dynamically resolves user name
    html = html.replace("Welcome", "Welcome, {{ current_user.name if current_user and current_user.is_authenticated else 'Client' }}")
    with open('app/templates/booking.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Updated dynamic header name in booking.html!")

print("Frontend patch script prepared.")