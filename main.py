from flask import Flask, render_template, request, jsonify, redirect, url_for
import random
import time
import requests
import re
from bs4 import BeautifulSoup
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def extract_form_data(form_url):
    """Extract form data from Google Form URL."""
    try:
        # Clean and standardize the URL
        if 'viewform' not in form_url:
            if form_url.endswith('/edit'):
                form_url = form_url.replace('/edit', '/viewform')
            else:
                form_url = form_url.rstrip('/') + '/viewform'
        
        logging.info(f"Fetching form from URL: {form_url}")
        
        # Get the form page with headers that mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        # IMPORTANT: Use allow_redirects=True to follow redirects
        response = requests.get(form_url, headers=headers, allow_redirects=True)
        if response.status_code != 200:
            return {"error": f"Failed to load form. Status code: {response.status_code}"}
        
        # Get the final URL after redirects
        final_url = response.url
        logging.info(f"Final URL after redirects: {final_url}")
        
        # Extract the form ID from the FINAL URL
        form_id_match = re.search(r'/e/([a-zA-Z0-9_-]+)/', final_url)
        if not form_id_match:
            return {"error": "Could not extract form ID from URL"}
        
        form_id = form_id_match.group(1)
        logging.info(f"Extracted form ID: {form_id}")
        
        # Set up the action URL for submission using the FINAL form ID
        action_url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
        logging.info(f"Action URL: {action_url}")
        
        # Save the HTML for debugging
        with open('form_debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # Find form fields directly in HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Create lists for different question types
        selectable_questions = []
        text_field_questions = []
        checkbox_questions = []
        
        # Find hidden sentinel inputs which indicate form fields
        sentinel_inputs = soup.find_all('input', {'name': re.compile(r'entry\.\d+_sentinel')})
        
        for sentinel in sentinel_inputs:
            entry_name = sentinel.get('name', '')
            entry_id_match = re.search(r'entry\.(\d+)_sentinel', entry_name)
            
            if entry_id_match:
                entry_id = f"entry.{entry_id_match.group(1)}"
                logging.info(f"Found question with ID: {entry_id}")
                
                # Find parent container
                parent = sentinel.parent
                for _ in range(5):  # Check up to 5 levels up
                    if parent:
                        # Look for heading
                        heading = parent.find(['div', 'h3', 'h4'], role='heading')
                        if heading:
                            question_text = heading.get_text(strip=True)
                            logging.info(f"Found question text: {question_text}")
                            break
                        parent = parent.parent
                    else:
                        break
                
                # If no heading found, use a placeholder
                if not 'question_text' in locals() or not question_text:
                    question_text = f"Question (ID: {entry_id})"
                
                # Check what type of question this is
                is_checkbox = False
                is_radio = False
                
                # Look for role="checkbox" elements
                checkbox_elements = []
                if parent:
                    # Check if this is a checkbox group
                    checkbox_group = parent.find(attrs={'role': 'list'})
                    if checkbox_group:
                        checkboxes = parent.find_all(attrs={'role': 'checkbox'})
                        if checkboxes:
                            is_checkbox = True
                            checkbox_elements = checkboxes
                
                # Look for role="radiogroup" elements
                radio_group = None
                if parent and not is_checkbox:
                    radio_group = parent.find(attrs={'role': 'radiogroup'})
                    if radio_group:
                        is_radio = True
                
                # Create question object based on type
                if is_checkbox:
                    # This is a checkbox question
                    options = {}
                    
                    for checkbox in checkbox_elements:
                        # Get option value
                        option_value = checkbox.get('data-answer-value') or checkbox.get('aria-label')
                        if not option_value:
                            # Try to find in span
                            span = checkbox.find_next('span', class_=re.compile(r'aDTYNe|snByac'))
                            if span:
                                option_value = span.get_text(strip=True)
                        
                        if option_value:
                            options[option_value] = 1  # Default weight
                    
                    if options:
                        checkbox_questions.append({
                            "question": entry_id,
                            "text": question_text,
                            "options": options,
                            "type": "checkbox"
                        })
                
                elif is_radio:
                    # This is a radio button question
                    options = {}
                    
                    # Find all options
                    option_elements = radio_group.find_all(attrs={'data-value': True}) or radio_group.find_all(attrs={'data-answer-value': True})
                    
                    for option in option_elements:
                        option_value = option.get('data-value') or option.get('data-answer-value') or option.get('aria-label')
                        if not option_value:
                            # Try to find in span
                            span = option.find_next('span', class_=re.compile(r'aDTYNe|snByac'))
                            if span:
                                option_value = span.get_text(strip=True)
                        
                        if option_value:
                            options[option_value] = 1  # Default weight
                    
                    if options:
                        selectable_questions.append({
                            "question": entry_id,
                            "text": question_text,
                            "options": options,
                            "type": "radio"
                        })
                    else:
                        # No options found, treat as text field
                        text_field_questions.append({
                            "question": entry_id,
                            "text": question_text,
                            "options": {},
                            "type": "text"
                        })
                else:
                    # No specific type identified, assume text field
                    text_field_questions.append({
                        "question": entry_id,
                        "text": question_text,
                        "options": {},
                        "type": "text"
                    })
        
        # If we didn't find any questions, try direct regex approach
        if not selectable_questions and not checkbox_questions and not text_field_questions:
            logging.info("No questions found using sentinel method, trying regex approach")
            
            # Find all entry IDs
            entry_ids = re.findall(r'entry\.([0-9]+)', response.text)
            unique_entries = set(entry_ids)
            
            for entry_num in unique_entries:
                entry_id = f"entry.{entry_num}"
                text_field_questions.append({
                    "question": entry_id,
                    "text": f"Question (ID: {entry_id})",
                    "options": {},
                    "type": "text"
                })
        
        return {
            "form_id": form_id,
            "action_url": action_url,
            "form_url": final_url,  # Use the final URL after redirects
            "data_structure": {
                "selectable_questions": selectable_questions,
                "checkbox_questions": checkbox_questions,
                "text_field_questions": text_field_questions
            }
        }
    
    except Exception as e:
        logging.exception("Error in extract_form_data")
        return {"error": str(e)}


def distribute_entries(options, runs):
    """Distribute options based on integer counts."""
    entries = []
    for option, count in options.items():
        count_int = int(count)
        if count_int > 0:
            entries.extend([option] * count_int)
    
    if not entries:
        return []
    
    random.shuffle(entries)
    return (entries * (runs // len(entries) + 1))[:runs]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/parse-form', methods=['POST'])
def parse_form():
    data = request.get_json()
    form_url = data.get('form_url')
    
    if not form_url:
        return jsonify({"error": "Missing form URL"}), 400
    
    # Extract form data
    form_data = extract_form_data(form_url)
    
    if "error" in form_data and not form_data.get("manual_entry_required", False):
        return jsonify(form_data), 400
    
    return jsonify(form_data)


@app.route('/submit', methods=['POST'])
def submit():
    request_data = request.get_json()
    action_url = request_data.get('action_url')
    data_structure = request_data.get('data_structure', {})
    runs = int(request_data.get('runs', 1))
    break_time = float(request_data.get('break_time', 1))
    
    logging.info(f"Submitting to: {action_url}")
    
    if not action_url or not data_structure:
        return jsonify({"error": "Missing action_url or data_structure"}), 400
    
    results = {
        "total": runs,
        "successful": 0,
        "failed": 0,
        "details": []
    }
    
    # Prepare distributions for regular selectable questions
    selectable_distributions = {}
    for q in data_structure.get("selectable_questions", []):
        if q.get("options"):
            selectable_distributions[q["question"]] = distribute_entries(q["options"], runs)
    
    # Prepare distributions for checkbox questions
    checkbox_distributions = {}
    for q in data_structure.get("checkbox_questions", []):
        if q.get("options"):
            # For each checkbox question, create a list of selected options for each run
            checkbox_distributions[q["question"]] = []
            
            # For each run, determine which checkboxes will be selected
            for i in range(runs):
                selected_options = []
                
                # Go through each option and decide if it will be selected for this run
                for option, weight in q["options"].items():
                    weight_int = int(weight)
                    # Higher weight = higher chance of being selected
                    if weight_int > 0 and random.randint(1, 10) <= weight_int:
                        selected_options.append(option)
                
                # Make sure we have at least one option selected if options exist
                if not selected_options and q["options"]:
                    # Select one random option
                    selected_options.append(random.choice(list(q["options"].keys())))
                
                checkbox_distributions[q["question"]].append(selected_options)
    
    # Prepare distributions for text field questions
    text_field_distributions = {}
    for q in data_structure.get("text_field_questions", []):
        if q.get("options"):
            text_field_distributions[q["question"]] = distribute_entries(q["options"], runs)
    
    # Submit the form for each run
    for i in range(runs):
        try:
            data = {}
            
            # Add regular selectable question answers
            for question, choices in selectable_distributions.items():
                if i < len(choices):
                    data[question] = choices[i]
            
            # Add checkbox question answers (special handling required)
            for question, choices_list in checkbox_distributions.items():
                if i < len(choices_list):
                    selected_options = choices_list[i]
                    
                    # For checkboxes, Google Forms expects the same parameter multiple times
                    # We need to handle this specially
                    if selected_options:
                        # If we have multiple options, we need to use a list
                        if len(selected_options) > 1:
                            data[question] = selected_options
                        else:
                            # Just one option
                            data[question] = selected_options[0]
            
            # Add text field question answers
            for question, choices in text_field_distributions.items():
                if i < len(choices):
                    data[question] = choices[i]
            
            logging.info(f"Run {i+1}: Submitting with data: {data}")
            
            # Submit the form
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://docs.google.com',
                'Referer': action_url.replace('/formResponse', '/viewform'),
            }
            
            # Handle special case for checkbox data
            form_data = {}
            for key, value in data.items():
                if isinstance(value, list):
                    # For checkbox questions, add each selected option as a separate entry
                    for item in value:
                        if key in form_data:
                            if not isinstance(form_data[key], list):
                                form_data[key] = [form_data[key]]
                            form_data[key].append(item)
                        else:
                            form_data[key] = item
                else:
                    form_data[key] = value
            
            response = requests.post(action_url, data=form_data, headers=headers, allow_redirects=True)
            
            # Log response status
            logging.debug(f"Response status: {response.status_code}, URL: {response.url}")
            
            # Google form submissions often return 200 even on success
            success = response.status_code in [200, 302, 303]
            
            # Check for actual success by looking for success messages or confirmation page
            if success and ('Thankyou' in response.url or 'formResponse' in response.url):
                success = True
            elif success and ('error' in response.text.lower() or 'try again' in response.text.lower()):
                success = False
            
            run_result = {
                "run": i+1,
                "status": response.status_code,
                "success": success,
                "url": response.url
            }
            
            if success:
                results["successful"] += 1
                run_result["message"] = "Form submitted successfully"
                logging.info(f"Run {i+1}: Form submitted successfully!")
            else:
                results["failed"] += 1
                run_result["message"] = f"Failed to submit form. Status code: {response.status_code}"
                logging.error(f"Run {i+1}: Failed with status code {response.status_code}")
            
            results["details"].append(run_result)
            
        except Exception as e:
            logging.exception(f"Error in run {i+1}")
            results["failed"] += 1
            results["details"].append({
                "run": i+1,
                "status": "Error",
                "success": False,
                "message": str(e)
            })
        
        if i < runs - 1:  # Don't sleep after the last run
            time.sleep(break_time)
    
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True)