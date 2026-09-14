portal_html = """{% extends 'base.html' %}

{% block content %}
<div class="min-h-screen bg-black text-white p-4 sm:p-6 max-w-4xl mx-auto space-y-6">

    <!-- HEADER & NAVIGATION -->
    <div class="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div class="flex items-center space-x-3">
            <div class="w-12 h-12 rounded-2xl bg-zinc-900 border border-amber-500/40 p-1.5 flex items-center justify-center">
                <img src="{{ url_for('static', filename='img/card_bg.jpg') }}" alt="Jackiecutz Logo" class="w-full h-full object-contain">
            </div>
            <div>
                <h1 class="text-lg font-black uppercase text-[#f7e3af]">JACKIECUTZ CLIENT APP</h1>
                <p class="text-xs text-zinc-400">Divine Salon Suite 105 • Houston, TX 77073</p>
            </div>
        </div>
        <a href="{{ url_for('main.login') }}" class="px-3 py-1.5 bg-zinc-900 border border-zinc-700 text-xs font-bold rounded-xl hover:bg-zinc-800 transition">
            Staff Portal ↗
        </a>
    </div>

    <!-- FLASH MESSAGES -->
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="p-3 bg-amber-500/10 border border-amber-500/40 text-amber-300 rounded-xl text-xs font-bold">
                    {{ message }}
                </div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <!-- HERO / QUICK ACTIONS -->
    <div class="bg-gradient-to-r from-zinc-900 via-zinc-950 to-black border border-amber-500/30 rounded-3xl p-6 shadow-xl space-y-4">
        <div class="flex justify-between items-start">
            <div>
                <span class="text-xs font-extrabold text-amber-400 uppercase tracking-widest block">VIP CLIENT EXPERIENCE</span>
                <h2 class="text-xl font-black text-white mt-1">Book Your Next Cut & Style</h2>
            </div>
            <span class="px-3 py-1 bg-green-500/10 border border-green-500/40 text-green-400 text-xs font-bold rounded-full">
                Walk-Ins Welcome
            </span>
        </div>
        <p class="text-xs text-zinc-400 max-w-lg">
            Schedule appointments, view active queue status, or check into Divine Salon Suite 105 directly from your phone.
        </p>
        <div class="flex flex-wrap gap-3 pt-2">
            <a href="{{ url_for('main.walkin_kiosk') }}" class="px-4 py-2.5 bg-[#f7e3af] text-black font-extrabold text-xs rounded-xl hover:bg-amber-300 transition">
                🚀 Walk-In Kiosk Check-In
            </a>
            <a href="#services" class="px-4 py-2.5 bg-zinc-900 border border-zinc-700 text-white font-bold text-xs rounded-xl hover:bg-zinc-800 transition">
                📜 View Service Menu
            </a>
        </div>
    </div>

    <!-- MAIN TWO-COLUMN GRID -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6" id="services">
        
        <!-- SERVICE MENU -->
        <div class="bg-zinc-950 border border-zinc-800 rounded-3xl p-5 space-y-4">
            <h3 class="text-sm font-black text-[#f7e3af] uppercase tracking-wider">✂️ Popular Salon Services</h3>
            <div class="space-y-3">
                <div class="p-3 bg-zinc-900/60 rounded-2xl border border-zinc-800 flex justify-between items-center">
                    <div>
                        <h4 class="text-xs font-bold text-white">Men's Precision Cut & Beard Detail</h4>
                        <p class="text-[10px] text-zinc-400">Includes hot towel & razor lining</p>
                    </div>
                    <span class="text-xs font-black text-amber-400">$35.00+</span>
                </div>
                <div class="p-3 bg-zinc-900/60 rounded-2xl border border-zinc-800 flex justify-between items-center">
                    <div>
                        <h4 class="text-xs font-bold text-white">Women's Cut & Styling</h4>
                        <p class="text-[10px] text-zinc-400">Precision trim, blowout & style</p>
                    </div>
                    <span class="text-xs font-black text-amber-400">$55.00+</span>
                </div>
                <div class="p-3 bg-zinc-900/60 rounded-2xl border border-zinc-800 flex justify-between items-center">
                    <div>
                        <h4 class="text-xs font-bold text-white">Hydration & Color Treatment</h4>
                        <p class="text-[10px] text-zinc-400">Deep conditioning & scalp treatment</p>
                    </div>
                    <span class="text-xs font-black text-amber-400">$75.00+</span>
                </div>
            </div>
        </div>

        <!-- RECENT VISIT REVIEW MODAL CARD -->
        <div class="bg-zinc-950 border border-amber-500/40 rounded-3xl p-5 space-y-4 shadow-[0_0_20px_rgba(245,158,11,0.1)]">
            <div class="flex items-center justify-between">
                <span class="text-xs font-black uppercase text-[#f7e3af] block">⭐ RATE YOUR EXPERIENCE</span>
                <span class="text-[10px] text-zinc-500">Jackiecutz Suite 105</span>
            </div>
            <p class="text-xs text-zinc-400">How was your recent haircut or service with Ivonne?</p>

            <form method="POST" action="{{ url_for('main.submit_review') }}" class="space-y-3">
                <div class="flex justify-center space-x-2 text-2xl py-1" id="star-rating">
                    <input type="hidden" name="rating" id="rating-val" value="5">
                    <button type="button" onclick="setRating(1)" class="star text-amber-400 transition">★</button>
                    <button type="button" onclick="setRating(2)" class="star text-amber-400 transition">★</button>
                    <button type="button" onclick="setRating(3)" class="star text-amber-400 transition">★</button>
                    <button type="button" onclick="setRating(4)" class="star text-amber-400 transition">★</button>
                    <button type="button" onclick="setRating(5)" class="star text-amber-400 transition">★</button>
                </div>

                <input type="text" name="client_name" placeholder="Your Name (Optional)" class="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-amber-500">
                <textarea name="feedback" rows="2" placeholder="Leave comments or feedback..." class="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-amber-500"></textarea>

                <button type="submit" class="w-full py-2.5 bg-[#f7e3af] text-black font-extrabold text-xs rounded-xl hover:bg-amber-300 transition">
                    SUBMIT RATING & FEEDBACK ⭐
                </button>
            </form>
        </div>

    </div>

</div>

<script>
function setRating(val) {
    document.getElementById('rating-val').value = val;
    const stars = document.querySelectorAll('.star');
    stars.forEach((star, index) => {
        if (index < val) {
            star.classList.add('text-amber-400');
            star.classList.remove('text-zinc-600');
        } else {
            star.classList.add('text-zinc-600');
            star.classList.remove('text-amber-400');
        }
    });
}
</script>
{% endblock %}"""

with open('app/templates/customer_app.html', 'w', encoding='utf-8') as f:
    f.write(portal_html)

print("Restored full Jackiecutz Client App layout in app/templates/customer_app.html!")