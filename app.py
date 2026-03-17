from flask import Flask, request, redirect, session, render_template_string
import sqlite3, os, random

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT, score INTEGER)")
    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template_string("""
    <h1>🚀 AI Talent Analyzer</h1>
    <a href="/login">Login</a> | <a href="/register">Register</a>
    """)

# ---------------- REGISTER ----------------
@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?,?,?)",(u,p,0))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template_string("""
    <h2>Register</h2>
    <form method="POST">
        <input name="username"><br><br>
        <input name="password" type="password"><br><br>
        <button>Register</button>
    </form>
    """)

# ---------------- LOGIN ----------------
@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = u
            return redirect('/dashboard')
        else:
            return "❌ Invalid Login"

    return render_template_string("""
    <h2>Login</h2>
    <form method="POST">
        <input name="username"><br><br>
        <input name="password" type="password"><br><br>
        <button>Login</button>
    </form>
    """)

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT score FROM users WHERE username=?", (session['user'],))
    score = c.fetchone()[0]
    conn.close()

    if score >= 3:
        level = "Advanced 🚀"
    elif score >= 1:
        level = "Intermediate ⚡"
    else:
        level = "Beginner 📚"

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>

<body class="bg-dark text-white">
<div class="container mt-5">

<h1 class="text-center">📊 Dashboard</h1>

<div class="row text-center">

<div class="col-md-4">
<div class="card bg-primary p-3">
<h4>User</h4>
<h2>{{user}}</h2>
</div>
</div>

<div class="col-md-4">
<div class="card bg-success p-3">
<h4>Score</h4>
<h2>{{score}}</h2>
</div>
</div>

<div class="col-md-4">
<div class="card bg-warning text-dark p-3">
<h4>Level</h4>
<h2>{{level}}</h2>
</div>
</div>

</div>

<div class="mt-4">
<h4>Progress</h4>
<div class="progress">
<div class="progress-bar bg-info" style="width: {{score*30}}%">
{{score*30}}%
</div>
</div>
</div>

<div class="mt-5">
<canvas id="chart"></canvas>
</div>

<div class="text-center mt-4">
<a href="/quiz" class="btn btn-info m-2">Quiz</a>
<a href="/upload" class="btn btn-secondary m-2">Upload Resume</a>
<a href="/ai" class="btn btn-success m-2">AI Feedback</a>
<a href="/logout" class="btn btn-danger m-2">Logout</a>
</div>

</div>

<script>
new Chart(document.getElementById("chart"), {
type: "bar",
data: {
labels: ["Score"],
datasets: [{label:"Performance", data:[{{score}}]}]
}
});
</script>

</body>
</html>
""", user=session['user'], score=score, level=level)

# ---------------- QUIZ ----------------
questions = [
{"q":"Python is?", "a":"language"},
{"q":"HTML is?", "a":"markup"},
{"q":"2+2?", "a":"4"},
{"q":"CSS used for?", "a":"design"}
]

@app.route('/quiz', methods=["GET","POST"])
def quiz():
    if 'user' not in session:
        return redirect('/login')

    random.shuffle(questions)

    if request.method == "POST":
        score = 0
        for i,q in enumerate(questions):
            if request.form.get(f"q{i}") == q["a"]:
                score += 1

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("UPDATE users SET score=? WHERE username=?", (score, session['user']))
        conn.commit()
        conn.close()

        return redirect('/dashboard')

    html = "<form method='POST'>"
    for i,q in enumerate(questions):
        html += f"<p>{q['q']}</p><input name='q{i}'><br><br>"
    html += "<button>Submit</button></form>"

    return html

# ---------------- RESUME UPLOAD ----------------
@app.route('/upload', methods=["GET","POST"])
def upload():
    if 'user' not in session:
        return redirect('/login')

    if request.method == "POST":
        file = request.files['file']
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        session['resume'] = path
        return "✅ Uploaded"

    return """
    <h2>Upload Resume</h2>
    <form method="POST" enctype="multipart/form-data">
    <input type="file" name="file">
    <button>Upload</button>
    </form>
    """

# ---------------- AI FEEDBACK ----------------
@app.route('/ai')
def ai():
    if 'user' not in session:
        return redirect('/login')

    score = 0
    if 'resume' in session:
        score += 1

    if score >= 1:
        msg = "Good Resume 👍 Improve skills & projects"
    else:
        msg = "Upload resume + practice more"

    return f"<h2>🤖 AI Feedback</h2><p>{msg}</p><a href='/dashboard'>Back</a>"

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)