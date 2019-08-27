from flask import Flask, request, abort

app = Flask (__name__, static_folder = None)

@app.before_first_request
def before_first_request ():
    print ("runs on first request")

@app.before_request
def before_request ():
    print ("runs before request")

@app.after_request
def after_request (response):
    print ("runs after request, response: " + str (response))
    return response

@app.route ("/")
def root ():
    print ("runs during request")
    print ("the request according to flask: " + str (request))
    return "it works lul"

@app.route ("/<int:number>")
def number_handler (number):
    print ("the number: {}".format (number))
    return "fat yeet!"

@app.route ("/error")
def error ():
    foobar (7130851759)
    abort (418) # I'm a teapot

if __name__ == "__main__":
    app.run (host = "0.0.0.0", port = 42069, debug = True)
