# app.py

from flask import Flask, render_template
from logic import get_data

app = Flask(__name__)

@app.route("/")
def index():
    rows_for_table, model_stats, model_names = get_data()
    return render_template(
        "index.html",
        rows_for_table=rows_for_table,
        model_stats=model_stats,
        model_names=model_names
    )

if __name__ == "__main__":
    app.run(debug=True)