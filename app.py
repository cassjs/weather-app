from flask import Flask, render_template

app = Flask(
    __name__,
    instance_relative_config= False,
    template_folder= "templates",
    static_folder= "static"
    )

@app.route("/")
def index():
    return render_template("base.html")