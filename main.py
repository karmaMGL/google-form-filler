from flask import Flask, render_template, request, jsonify
import random
import time
import requests

app = Flask(__name__)

def select_entry(options):
    rand_value = random.random()
    cumulative_probability = 0.0
    for option, probability in options.items():
        cumulative_probability += probability
        if rand_value < cumulative_probability:
            return option
    return None

@app.route('/')
def index():
    return render_template('index.html')  # Serve the index.html file

@app.route('/submit', methods=['POST'])
def submit():
    request_data = request.get_json()
    form_url = request_data.get('form_url')
    data_structure = request_data.get('data_structure', {})
    runs = request_data.get('runs', 1)
    break_time = request_data.get('break_time', 1)
    
    if not form_url or not data_structure:
        return jsonify({"error": "Missing form_url or data_structure"}), 400
    
    for _ in range(runs):
        data = {}
        
        for question in data_structure.get("selectable_questions", []):
            selected_entry = select_entry(question["options"])
            data[question["question"]] = selected_entry
        
        for question in data_structure.get("text_field_questions", []):
            selected_text = select_entry(question["options"])
            data[question["question"]] = selected_text
        
        response = requests.post(form_url, data=data)
        
        if response.status_code == 200:
            print("Form submitted successfully!")
        else:
            print("Failed to submit form. Status code:", response.status_code)
        
        time.sleep(break_time)
    
    return jsonify({"message": "Form submission process completed"})

if __name__ == '__main__':
    app.run(debug=True)
