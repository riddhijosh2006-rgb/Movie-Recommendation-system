from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = "cinematch_secret"

# ✅ ADD YOUR OMDb API KEY HERE
API_KEY = "---"

GENRES = {
    "Action": "action",
    "Romance": "romance",
    "Sci-Fi": "sci-fi",
    "Horror": "horror",
    "Drama": "drama",
    "Mystery": "mystery"
}

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()


# ================= SAFE REQUEST FUNCTION =================
def fetch_movies(url):
    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("Response") == "True":
            return data.get("Search", [])
        else:
            return []

    except requests.exceptions.RequestException as e:
        print("API Error:", e)
        return []


# ================= HELPER FUNCTION =================
def format_movies(results):
    movies = []

    for movie in results:
        poster = movie.get("Poster")

        movies.append({
            "title": movie.get("Title"),
            "genre": movie.get("Year", "Unknown"),
            "poster": poster if poster != "N/A" else "https://via.placeholder.com/300x450?text=No+Image"
        })

    return movies


# ================= HOME =================
@app.route("/")
@app.route("/home")
def home():

    if "user" not in session:
        return redirect(url_for("login"))

    url = f"https://www.omdbapi.com/?apikey={API_KEY}&s=avengers"

    results = fetch_movies(url)
    trending = format_movies(results)

    return render_template("index.html", trending=trending)


# ================= WEB SERIES =================
@app.route("/webseries")
def webseries():

    if "user" not in session:
        return redirect(url_for("login"))

    trending_url = f"https://www.omdbapi.com/?apikey={API_KEY}&s=stranger&type=series"
    top_url = f"https://www.omdbapi.com/?apikey={API_KEY}&s=game&type=series"
    popular_url = f"https://www.omdbapi.com/?apikey={API_KEY}&s=money&type=series"

    trending = format_movies(fetch_movies(trending_url))
    top_series = format_movies(fetch_movies(top_url))
    popular = format_movies(fetch_movies(popular_url))

    return render_template("webseries.html",
                           trending=trending,
                           top_series=top_series,
                           popular=popular)


# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users(username,password) VALUES (?,?)",
                (username, password)
            )
            conn.commit()

            session["user"] = username
            return redirect(url_for("home"))

        except:
            return "Username already exists!"

    return render_template("signup.html")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        cur = conn.cursor()

        user = cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if user:
            session["user"] = username
            return redirect(url_for("home"))

        return "Invalid username or password"

    return render_template("login.html")


# ================= SEARCH =================
@app.route("/search", methods=["POST"])
def search():

    if "user" not in session:
        return redirect(url_for("login"))

    query = request.form["search"]

    url = f"https://www.omdbapi.com/?apikey={API_KEY}&s={query}"

    movies = format_movies(fetch_movies(url))

    return render_template("index.html", movies=movies)


# ================= RECOMMEND =================
@app.route("/recommend/<genre>")
def recommend(genre):

    if "user" not in session:
        return redirect(url_for("login"))

    search_term = GENRES.get(genre, "movie")

    url = f"https://www.omdbapi.com/?apikey={API_KEY}&s={search_term}"

    movies = format_movies(fetch_movies(url))

    return render_template("index.html", movies=movies)


# ================= AI =================
@app.route("/ai", methods=["GET", "POST"])
def ai():

    if "user" not in session:
        return redirect(url_for("login"))

    movies = []

    if request.method == "POST":

        mood = request.form["mood"]

        if mood == "happy":
            query = "comedy"
        elif mood == "sad":
            query = "drama"
        elif mood == "excited":
            query = "action"
        elif mood == "romantic":
            query = "romance"
        else:
            query = "movie"

        url = f"https://www.omdbapi.com/?apikey={API_KEY}&s={query}"

        movies = format_movies(fetch_movies(url))

    return render_template("ai_recommend.html",
                           user=session.get("user"),
                           movies=movies)


# ================= CHATBOT =================
@app.route("/chatbot", methods=["POST"])
def chatbot():

    data = request.get_json()
    message = data.get("message","").lower()

    if "sad" in message:
        reply = "Try watching Drama or Romance movies ❤️"
    elif "action" in message:
        reply = "🔥 You should watch Action movies!"
    elif "happy" in message:
        reply = "Comedy movies are perfect for happy mood 😄"
    elif "scifi" in message or "sci-fi" in message:
        reply = "🚀 Sci-Fi movies coming right up!"
    else:
        reply = "Tell me your mood like sad, action, romantic, happy!"

    return jsonify({"reply": reply})


# ================= WATCHLIST =================
@app.route("/watchlist")
def watchlist():
    movies = session.get("watchlist", [])
    return render_template("watchlist.html", movies=movies)


@app.route("/add_watchlist", methods=["POST"])
def add_watchlist():

    movie = {
        "title": request.form["title"],
        "poster": request.form["poster"],
        "genre": request.form["year"]
    }

    watchlist = session.get("watchlist", [])
    watchlist.append(movie)
    session["watchlist"] = watchlist

    return redirect(url_for("watchlist"))


@app.route("/profile")
def profile():

    watchlist = session.get("watchlist", [])

    return render_template(
        "profile.html",
        movies=watchlist[:4],
        watchlist_count=len(watchlist)
    )


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)