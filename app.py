from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Amazon Payday Planner is running"