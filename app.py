from flask import Flask, render_template
from db import init_db, list_wishes

app = Flask(__name__)
init_db()


@app.route("/")
def home():
    return "Amazon Payday Planner is running"


@app.route("/wishes")
def wishes():
    return render_template("wishes.html", wishes=list_wishes())