# google-form-filler

This project allows you to automate the process of filling out Google Forms by submitting responses programmatically. It uses Python and Flask to run a local web application where users can input form URLs, field IDs, and options with chances.

## Requirements

Before running the application, make sure you have the required dependencies.

### 1. Install Dependencies

```bash
pip install -r requirements.txt
2. Running the Application
After installing the dependencies, run the application by executing the following command:

bash
Copy
Edit
python main.py
Once the server starts, it will open the following URL in your web browser:

text
Copy
Edit
http://127.0.0.1:5000
Setting Up Your Google Form
To use this tool with your own Google Form, follow these steps:

1. Get Your Google Form URL
Go to your Google Form and click the "Send" button at the top-right. Copy the URL that looks something like this:

text
Copy
Edit
https://docs.google.com/forms/d/e/1FAIpQLSecqAlWvp6HmCer9VdfPcuQ1mHaEi0HUMgQlPZz_SGlAgqCvg/formResponse
2. Extract Your Form's ID
The part of the URL that looks like 1FAIpQLSecqAlWvp6HmCer9VdfPcuQ1mHaEi0HUMgQlPZz_SGlAgqCvg is your form ID. Replace the existing ID in the URL when you enter it into the application.

3. Inspecting Your Google Form
To find the input field names (IDs) and associated values, follow these steps:

Open the Google Form in your browser.
Press F12 (or right-click and select "Inspect") to open the Developer Tools.
In the "Elements" tab, press Ctrl + F and search for entry. to find the form field IDs.
Note the entry.xxxxxxx field IDs and their corresponding values (e.g., selected values or options for a dropdown).
For example, you may find an entry like this:

html
Copy
Edit
<input type="radio" name="entry.123456" value="Option1" checked>
Here, entry.123456 is the form field ID, and "Option1" is the selected value.

Using the Web Interface
Once the application is running, go to http://127.0.0.1:5000 in your web browser to interact with the form submission interface.

1. Enter the Google Form URL
Enter the form URL you copied earlier, ensuring it includes your form's ID.
2. Configure Form Submission
Number of Runs: Specify how many times you want to submit the form.
Break Time: Specify how much time (in seconds) the application should wait before submitting another form.
3. Input Dynamic Question IDs and Options
For each question, input the question ID (e.g., entry.xxxxxxx) and the options with their chances (e.g., Option1: 75, Option2: 25).

You can add more questions by clicking the "Add More Questions" button.
4. Submit the Form
Click "Submit" to start the form filling process. The application will submit the form and display the result (success or failure).

Troubleshooting
Common Issues
Form URL not found: Ensure the URL is correctly entered, including the /formResponse endpoint and the correct form ID.
Missing or Incorrect Field IDs: Double-check the field IDs from your Google Form by inspecting the HTML using the steps mentioned above.
License
This project is licensed under the MIT License - see the LICENSE file for details.

Contributing
Feel free to fork the repository, create a branch, and submit pull requests with improvements, bug fixes, or new features.

pgsql
Copy
Edit

This README includes all necessary instructions, including setup, usage, troubleshooting, and contributing. It is formatted to be clean and informative for GitHub users.