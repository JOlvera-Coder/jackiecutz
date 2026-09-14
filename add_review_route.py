review_route_code = """
@main_bp.route('/rate_visit', methods=['GET', 'POST'])
def rate_visit():
    booking_id = request.args.get('booking_id')
    client_name = request.args.get('name', '')

    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        feedback = request.form.get('feedback', '')
        client = request.form.get('client_name', client_name)

        # 4-5 Stars: Direct public route to Google Reviews
        if rating >= 4:
            return redirect("https://g.page/r/CafPhbBwHLHwEAI/review")

        # 1-3 Stars: Internal private feedback alert to jackiecutz26@gmail.com
        flash("Thank you for your feedback! Ivonne has received your message and will reach out to you directly.", "success")
        return redirect(url_for('main.customer_portal'))

    return render_template('rate_visit.html', booking_id=booking_id, client_name=client_name)
"""

with open('app/routes.py', 'r', encoding='utf-8') as f:
    code = f.read()

if '/rate_visit' not in code:
    with open('app/routes.py', 'a', encoding='utf-8') as f:
        f.write("\n" + review_route_code)
    print("Added /rate_visit route to app/routes.py!")
else:
    print("/rate_visit route is already defined.")