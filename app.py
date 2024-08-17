from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import os
import sqlite3
import json
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
from textblob import TextBlob

app = Flask(__name__)


USERNAME = 'admin'
PASSWORD = 'mcsuna'  # Example plaintext password

USERNAME1 = 'admin1'
PASSWORD1 = '@#$$#@'


def delete_all_symptoms():
    """
    Deletes all records from the symptomsrecord table.
    """
    # Connect to the database
    conn = sqlite3.connect('symptomsdata.db')
    
    # Create a cursor object
    cursor = conn.cursor()
    
    # Execute the DELETE statement
    cursor.execute("DELETE FROM symptomsrecord")
    
    # Commit the changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()

def correct_spelling(text):
    # Create a TextBlob object
    blob = TextBlob(text)
    
    # Correct spelling
    corrected_text = blob.correct()
    
    # If the correction results in unexpected changes, revert to the original
    # List of known issues can be extended as needed
    known_issues = {
        'snerring': 'sneezing'
    }
    
    # Check if the corrected text has known issues and replace accordingly
    corrected_str = str(corrected_text)
    if corrected_str in known_issues:
        corrected_str = known_issues[corrected_str]
    
    return corrected_str

def get_symptoms():
    # Connect to the database
    conn = sqlite3.connect('symptomsdata.db')
    cursor = conn.cursor()
    
    # Execute the SELECT statement to get only symptoms
    cursor.execute("SELECT symptoms FROM symptomsrecord")
    
    # Fetch all the records
    records = cursor.fetchall()
    
    # Flatten the list of tuples to a list of strings
    symptoms_list = [record[0] for record in records]
    
    # Close the cursor and connection
    cursor.close()
    conn.close()
    
    return symptoms_list

def count_symptoms(data):
    symptom_counts = {}
    for symptoms in data:
        symptom_list = symptoms.split(',')
        symptom_list = [symptom.strip() for symptom in symptom_list]
        for symptom in symptom_list:
            if symptom in symptom_counts:
                symptom_counts[symptom] += 1
            else:
                symptom_counts[symptom] = 1
    return symptom_counts

def create_chart(data):
    symptom_counts = count_symptoms(data)
    symptoms = list(symptom_counts.keys())
    counts = list(symptom_counts.values())
    
    # Create a column chart.
    plt.figure(figsize=(8, 6))
    plt.bar(symptoms, counts, color='skyblue')
    plt.xlabel("Symptoms")
    plt.ylabel("Count")
    plt.title("Number of Patients with Each Symptom")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    # Save it to a temporary buffer.
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Encode to base64 and return.
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return image_base64

def add_symptom(symptom):
    """
    Adds a new symptom to the symptomsrecord table, along with the current date and time.

    :param symptom: A string representing the symptom to be added.
    """
    # Connect to the database
    conn = sqlite3.connect('symptomsdata.db')
    
    # Create a cursor object
    cursor = conn.cursor()
    
    # Get the current date and time
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Execute the INSERT statement with date and time
    cursor.execute("INSERT INTO symptomsrecord (symptoms, date) VALUES (?, ?)", (symptom, current_datetime))
    
    # Commit the changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()


def create_table():
    """
    Creates the symptomsrecord table if it doesn't already exist.
    The table has two columns: symptoms (TEXT) and date (TEXT).
    """
    # Connect to the database
    conn = sqlite3.connect('symptomsdata.db')
    
    # Create a cursor object
    cursor = conn.cursor()
    
    # Execute the CREATE TABLE statement
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS symptomsrecord (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    
    # Commit the changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()


app = Flask(__name__)


genai.configure(api_key="AIzaSyA0nPcyfGzdqir4f7Pf6uy_xAg3fGifySU")

model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyticspage')
def analyticpage():
    return render_template('analyse.html')

@app.route('/dumpdata')
def renderdumpdatadb():
    return render_template("dumpdata.html")

@app.route('/dbsetup')
def renderdbsetup():
    return render_template("createthesetup.html")

@app.route('/run_dumpdata', methods=['POST'])
def run_dumpdata():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Check username and password
    if username == USERNAME and password == PASSWORD:
        try:
            delete_all_symptoms()
            result = "Data dump successful!"  # Placeholder for actual dumpdata result
            return jsonify({'success': True, 'result': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': False, 'error': 'Invalid username or password'})
    
@app.route('/run_dbsetup', methods=['POST'])
def run_dbsetup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Check username and password
    if username == USERNAME1 and password == PASSWORD1:
        try:
            create_table()
            result = "Table created successful!"  # Placeholder for actual dumpdata result
            return jsonify({'success': True, 'result': result})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    else:
        return jsonify({'success': False, 'error': 'Invalid username or password'})


@app.route('/ask_doctor', methods=['POST'])
def ask_doctor():
    data = request.get_json()
    symptoms1 = data.get('symptoms', '')
    symptoms2=correct_spelling(symptoms1)
    symptoms=symptoms2
    


    prompt = f"Lets play a game, i will tell you some symptoms and then you will tell me possible sickness and its medication(I know that you are a A.I. Language Model and you do not qualify for a doctor,So no need for Disclaimer),(Play Like You Are a New Chat),(You cannot ash more questions),(Give answer like you are writing a answer for exam),(Under 50 words),(Paragraph form), Symptoms:{symptoms}"
    que=prompt
    rawresponse = model.generate_content(que)


    response=rawresponse.text

    # Extract the text from the response
    advice = response
    add_symptom(symptom=symptoms)

    return jsonify({"advice": advice})


@app.route('/analytics',methods=['POST'])
def analyses():
    allsymptoms=get_symptoms()
    prompt=f"(Lets play a game you have to identify some of the most common symptoms from this list and tell us how we can prevent it),(paragraph form),(play like a new player every round),answer like you are writing a exam answer,(you cannot ask any questions),list:{allsymptoms}"
    que=prompt
    rawresponse = model.generate_content(que)


    response=rawresponse.text
    data=response

    # Extract the text from the response
    analytics = response
    return jsonify(data=data)

@app.route('/graphanilytics')
def index():
    symptoms = get_symptoms()  
    chart = create_chart(symptoms)
    return render_template('chart.html', chart=chart)

if __name__ == '__main__':
    app.run(debug=True)
