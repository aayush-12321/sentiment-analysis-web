"""
wsgi.py — WSGI entry point for Gunicorn

Production usage:
    gunicorn wsgi:application \
        --workers 4 \
        --worker-class sync \
        --bind 0.0.0.0:5000 \
        --timeout 120 \
        --access-logfile - \
        --error-logfile -
"""

from app import create_app

application = create_app()

# print("Wsgi.py")

for rule in application.url_map.iter_rules():
    print(rule)

# Temp route to verify server is runnig
@application.route("/")
def index():
    return "Flask factory app is running!"

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=False)
