import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    my_ip = os.environ["MY_IP"]
    step1 = os.environ["STEP1"]
    step2 = os.environ["STEP2"]
    step3 = os.environ["STEP3"]
    step4 = os.environ["STEP4"]
    return (
        f"Hello, this is my IP address: {my_ip}<br>\n"
        f"1: {step1}<br>\n"
        f"2: {step2}<br>\n"
        f"3: {step3}<br>\n"
        f"3: {step4}<br>\n"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0")
