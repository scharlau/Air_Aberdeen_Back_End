import flask
from flask import request, render_template

# this file is only needed if you need to point to a local version of the file
# instead of the one at GitHub

app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route("/")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run('0.0.0.0',80)