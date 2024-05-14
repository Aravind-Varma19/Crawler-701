from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from elasticsearch7 import Elasticsearch
import subprocess
import os
import psutil
import sys

app = Flask(__name__)
app.secret_key = 'your_secret_key'

new_index_name = "privacy-policy"
new_cloud_id = "c83822bf9f204bd3928fb2b3deedf98a:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQzNDUyNGE2NzA3ZjI0NDM0YmRkM2E0ZWI1OTBhZDgzMCQ2ODg2ZjEwNWM4YzQ0ZWE0YjNjNzk1YzRlMDkwYWJmOQ=="
new_auth = ("elastic", "rCaLfA66eg7TNgaaqhRZd7AZ")
es = Elasticsearch(timeout=10000, cloud_id=new_cloud_id, http_auth=new_auth)



@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "admin":
            session['logged_in'] = True
            session['role'] = 'admin'
            return redirect(url_for('search'))
        elif username == "user" and password == "user":
            session['logged_in'] = True
            session['role'] = 'user'
            return redirect(url_for('search'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('role', None)
    return redirect(url_for('login'))



@app.route('/search', methods=['GET'])
def search():
    if not session.get('logged_in'):
        return render_template('index.html', error='Please enter a query.')
    query = request.args.get('query') if request.args.get('query') else ""
    user_role = session.get('role', 'user')
    # Search Elasticsearch index
    result = es.search(index=new_index_name, body={'query': {'match': {'terms': query}}}, size=10000)
    hits = result['hits']['hits']
    total_hits = len(hits)
    # Extract relevant information
    search_results = {}
    for hit in hits:
        doc_id = hit['_id']
        title = hit['_source']['title']
        terms = hit['_source']['terms']
        url = hit['_source']['url']
        versions = hit['_source']['url_version']  # Assuming 'url_versions' is a list of versions

        if url not in search_results:
            search_results[url] = {
                'url': url,
                'details': []
            }
        
        search_results[url]['details'].append({
                'title': title,
                'summary': terms[:250],
                'terms': terms,
                'version': versions
            })

    return render_template('index.html', hits=total_hits, query=query, search_results=search_results, role=user_role)

@app.route('/run-crawler', methods=['POST'])
def run_crawler():
    try:
        script_path = os.path.join(os.path.dirname(__file__), 'main_crawler.py')
        process = subprocess.Popen([sys.executable, script_path])
        # process = subprocess.Popen(['python3', 'main_crawler.py'])
        pid = process.pid
        return jsonify({"status": "success", "message": "Crawler started successfully", "pid": pid}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/check-crawler/<int:pid>', methods=['GET'])
def check_crawler(pid):
    try:
        if psutil.pid_exists(pid):
            return jsonify({"status": "running", "pid": pid}), 200
        else:
            return jsonify({"status": "not running", "pid": pid}), 200
    except Exception as e:
        print(e)
        return jsonify({"status": "error", "message": str(e)}), 500
    
    
if __name__ == '__main__':
    app.run(debug=True)
