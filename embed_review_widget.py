with open('app/templates/booking.html', 'r', encoding='utf-8') as f:
    content = f.read()

review_widget = """
<!-- GOOGLE & PRIVATE REVIEW ROUTING WIDGET -->
<div class="my-6 bg-zinc-950 border border-amber-500/40 rounded-3xl p-5 space-y-3 shadow-[0_0_20px_rgba(245,158,11,0.15)]">
    <div class="flex items-center justify-between">
        <span class="text-xs font-black uppercase text-[#f7e3af] block">⭐ RATE YOUR RECENT VISIT</span>
        <span class="px-2 py-0.5 bg-amber-500/10 text-amber-400 text-[10px] font-bold rounded-full">Jackiecutz Suite 105</span>
    </div>
    <p class="text-xs text-zinc-400">How was your service with Ivonne today?</p>
    <form method="POST" action="/submit_review" class="space-y-3">
        <div class="flex justify-center space-x-2 text-2xl py-1">
            <input type="hidden" name="rating" id="rating-val" value="5">
            <button type="button" onclick="setRating(1)" class="star text-amber-400">★</button>
            <button type="button" onclick="setRating(2)" class="star text-amber-400">★</button>
            <button type="button" onclick="setRating(3)" class="star text-amber-400">★</button>
            <button type="button" onclick="setRating(4)" class="star text-amber-400">★</button>
            <button type="button" onclick="setRating(5)" class="star text-amber-400">★</button>
        </div>
        <input type="text" name="client_name" placeholder="Your Name (Optional)" class="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-2.5 text-xs text-white">
        <textarea name="feedback" rows="2" placeholder="Leave comments or feedback..." class="w-full bg-zinc-900 border border-zinc-800 rounded-xl p-2.5 text-xs text-white"></textarea>
        <button type="submit" class="w-full py-2.5 bg-[#f7e3af] text-black font-extrabold text-xs rounded-xl hover:bg-amber-300 transition">
            SUBMIT RATING & FEEDBACK ⭐
        </button>
    </form>
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
"""

if 'submit_review' not in content:
    content = content.replace("{% block content %}", "{% block content %}\n" + review_widget)
    with open('app/templates/booking.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Embedded review widget into booking.html!")
else:
    print("Widget already present in booking.html.")