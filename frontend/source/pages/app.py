from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    data = {
        "error": None,
        "message": "Hello from Flask!"
    }
    return render_template('landing.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)