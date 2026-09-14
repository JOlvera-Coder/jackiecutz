customer_app_html = """{% extends 'base.html' %}

{% block content %}
<div class="min-h-screen bg-black text-white p-4 sm:p-6 max-w-xl mx-auto space-y-6">

    <!-- HEADER -->
    <div class="flex items-center justify-between border-b border-zinc-800 pb-4">
        <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-xl bg-zinc-900 border border-amber-500/40 p-1 flex items-center justify-center">
                <img src="{{ url_for('static', filename='img/card_bg.jpg') }}" alt="Jackiecutz Logo" class="w-full h-full object-contain">
            </div>
            <div>
                <h1 class="text-base font-black uppercase text-[#f7e3af]">JACKIECUTZ CLIENT PORTAL</h1>
                <p class="text-xs text-zinc-400">Divine Salon Suite 105 • Houston, TX</p>
            </div>
        </div>
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

    <!-- SERVICE REVIEW MODAL / CARD -->
    <div class="bg-zinc-950 border border-amber-500/40 rounded-3xl p-5 space-y-4 shadow-[0_0_20px_rgba(245,158,11,0.15)]">
        <span class="text-xs font-black uppercase text-[#f7e3af] block">⭐ RATE YOUR RECENT EXPERIENCE</span>
        <p class="text-xs text-zinc-400">How was your haircut & service at Jackiecutz today?</p>

        <form method="POST" action="{{ url_for('main.submit_review') }}" class="space-y-4">
            <div class="flex justify-center space-x-2 text-2xl" id="star-rating">
                <input type="hidden" name="rating" id="rating-val" value="5">
                <button type="button" onclick="setRating(1)" class="star text-amber-400">★</button>
                <button type="button" onclick="setRating(2)" class="star text-amber-400">★</button>
                <button type="button" onclick="setRating(3)" class="star text-amber-400">★</button>
                <button type="button" onclick="setRating(4)" class="star text-amber-400">★</button>
                <button type="button" onclick="setRating(5)" class="star text-amber-400">★</button>
            </div>

            <input type="text" name="client_name" placeholder="Your Name (Optional)" class="w-full bg-zinc-900 border border-zinc-700 rounded-xl p-2.5 text-xs text-white">
            <textarea name="feedback" rows="3" placeholder="Leave comments or feedback..." class="w-full bg-zinc-900 border border-zinc-700 rounded-xl p-2.5 text-xs text-white"></textarea>

            <button type="submit" class="w-full py-2.5 bg-[#f7e3af] text-black font-extrabold text-xs rounded-xl hover:bg-amber-300 transition">
                SUBMIT RATING & FEEDBACK ⭐
            </button>
        </form>
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
    f.write(customer_app_html)

print("Updated app/templates/customer_app.html with review routing system!")