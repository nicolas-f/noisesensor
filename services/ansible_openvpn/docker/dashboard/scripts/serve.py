from flask import Flask
app = Flask(__name__)


@app.route('/')
def home():
    return """
<!doctype html>
<html>
  <head>
    <title>NoiseSensor dashboard default page</title>
  </head>
  <body>
    <p>Please run the Ansible playbook named deploy_elastic_web_dashboard.yml</p>
  </body>
</html>"""


def main():
    from waitress import serve
    import hupper
    reloader = hupper.start_reloader('scripts.serve.main')
    reloader.watch_files(['app_git_hash.txt'])
    serve(app, host="0.0.0.0", port=8000)
