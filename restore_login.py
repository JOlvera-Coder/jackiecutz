login_html = """{% extends 'base.html' %}

{% block content %}
<div class="min-h-screen bg-black text-white flex flex-col items-center justify-center p-4">

    <!-- LOGO HEADER SECTION -->
    <div class="text-center mb-6 space-y-2 max-w-sm">
        <div class="w-48 sm:w-56 mx-auto">
            <img src="{{ url_for('static', filename='img/card_bg.jpg') }}" alt="Jackiecutz Hair Studio - Ivonne Gonzalez" class="w-full h-auto object-contain drop-shadow-[0_0_15px_rgba(247,227,175,0.2)]">
        </div>
    </div>

    <!-- MAIN LOGIN CARD -->
    <div class="w-full max-w-md bg-black/90 border-2 border-[#f7e3af]/60 rounded-3xl p-6 sm:p-8 space-y-5 shadow-[0_0_30px_rgba(247,227,175,0.15)] backdrop-blur-md">
        
        <!-- FLASH MESSAGES -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="p-3 bg-amber-500/10 border border-amber-500/40 text-amber-300 rounded-xl text-xs font-bold text-center">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <form method="POST" action="{{ url_for('main.login') }}" class="space-y-4">
            
            <!-- USERNAME FIELD -->
            <div class="space-y-1">
                <label class="block text-[10px] sm:text-xs font-black uppercase tracking-wider text-[#f7e3af]">
                    USERNAME, NAME, OR PHONE
                </label>
                <input type="text" name="username" required
                       class="w-full px-4 py-3 bg-[#fffde8] text-black font-semibold rounded-2xl border border-[#f7e3af] focus:outline-none focus:ring-2 focus:ring-amber-400 text-sm">
            </div>

            <!-- PASSWORD FIELD -->
            <div class="space-y-1">
                <label class="block text-[10px] sm:text-xs font-black uppercase tracking-wider text-[#f7e3af]">
                    PASSWORD (STYLISTS / REGISTERED)
                </label>
                <input type="password" name="password"
                       class="w-full px-4 py-3 bg-[#fffde8] text-black font-semibold rounded-2xl border border-[#f7e3af] focus:outline-none focus:ring-2 focus:ring-amber-400 text-sm">
            </div>

            <!-- REMEMBER & FORGOT PASSWORD ROW -->
            <div class="flex items-center justify-between text-xs pt-1">
                <label class="flex items-center space-x-2 cursor-pointer text-zinc-300">
                    <input type="checkbox" name="remember" class="w-4 h-4 accent-amber-400 rounded">
                    <span class="text-[11px] font-medium">Remember Me</span>
                </label>
                <a href="{{ url_for('main.login') }}" class="text-[11px] font-bold text-zinc-300 hover:text-[#f7e3af] transition">
                    Forgot Password?
                </a>
            </div>

            <!-- LOG IN BUTTON -->
            <button type="submit" 
                    class="w-full py-3.5 bg-gradient-to-r from-[#e6c280] via-[#f7e3af] to-[#caa055] hover:brightness-110 text-black font-black uppercase tracking-widest text-sm rounded-2xl shadow-[0_0_20px_rgba(230,194,128,0.3)] transition transform active:scale-95">
                LOG IN
            </button>
        </form>

        <!-- FOOTER LINKS -->
        <div class="border-t border-zinc-800/80 pt-4 text-center space-y-2">
            <p class="text-xs text-zinc-300">
                Need an account? 
                <a href="{{ url_for('main.customer_portal') }}" class="font-bold text-[#f7e3af] underline hover:text-amber-300">
                    Register
                </a>
            </p>
            <p class="text-[10px] text-zinc-400 leading-relaxed px-2">
                By logging in, you agree to our 
                <a href="#" class="underline hover:text-white">Terms & Conditions</a> 
                and 
                <a href="#" class="underline hover:text-white">Privacy Policy</a>.
            </p>
        </div>

    </div>

</div>
{% endblock %}"""

with open('app/templates/login.html', 'w', encoding='utf-8') as f:
    f.write(login_html)

print("Successfully restored exact login page template in app/templates/login.html!")