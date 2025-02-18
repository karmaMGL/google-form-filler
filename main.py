from flask import Flask, render_template, request, jsonify
import random
import time
import requests
from collections import Counter

app = Flask(__name__)

def distribute_entries(options, runs):
    """Distribute options based on integer counts."""
    entries = []
    for option, count in options.items():
        entries.extend([option] * count)
    random.shuffle(entries)
    return (entries * (runs // len(entries) + 1))[:runs]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    request_data = request.get_json()
    form_url = "https://docs.google.com/forms/d/e/" + request_data.get('form_url') + '/formResponse'
    data_structure = request_data.get('data_structure', {})
    runs = request_data.get('runs', 1)
    break_time = request_data.get('break_time', 1)
    
    if not form_url or not data_structure:
        return jsonify({"error": "Missing form_url or data_structure"}), 400
    
    selectable_distributions = {
        q['question']: distribute_entries(q['options'], runs)
        for q in data_structure.get("selectable_questions", [])
    }
    
    text_field_distributions = {
        q['question']: distribute_entries(q['options'], runs)
        for q in data_structure.get("text_field_questions", [])
    }
    
    for i in range(runs):
        data = {}
        
        for question, choices in selectable_distributions.items():
            data[question] = choices[i]
        
        for question, choices in text_field_distributions.items():
            data[question] = choices[i]
        
        response = requests.post(form_url, data=data)
        
        if response.status_code == 200:
            print(f"Run {i+1}: Form submitted successfully!")
        else:
            print(f"Run {i+1}: Failed to submit form. Status code:", response.status_code)
        
        time.sleep(break_time)
    
    return jsonify({"message": "Form submission process completed"})

if __name__ == '__main__':
    app.run(debug=True)