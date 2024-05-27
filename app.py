from flask import Flask, request, jsonify, session
import pandas as pd
import json
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
import random
from flask_cors import CORS

data_folder = 'data'
diseases_df = pd.read_excel(f'{data_folder}/disease.xlsx')
with open(f'{data_folder}/symptoms_questions.json', 'r', encoding='utf-8') as f:
    symptoms_questions = json.load(f)

stop_words = set(stopwords.words('arabic'))

app = Flask(__name__)
app.secret_key = 'your_secret_key'

CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS", "DELETE", "PUT"], "allow_headers": "*"}})
def extract_symptoms(user_response):
    words = word_tokenize(user_response.lower())
    filtered_words = [word for word in words if word not in stop_words]
    return filtered_words

def calculate_disease_probabilities(symptoms, diseases_df):
    disease_probabilities = defaultdict(int)
    for symptom in symptoms:
        for index, row in diseases_df.iterrows():
            disease_symptoms = row['اعراضه'].lower().split(',')
            if any(symptom in ds for ds in disease_symptoms):
                disease_probabilities[row['اسم المرض']] += 1
    return disease_probabilities

@app.route('/')
def index():
    session.clear()
    session['asked_questions'] = []
    session['user_symptoms'] = []
    symptom = random.choice(list(symptoms_questions['questions'].keys()))
    questions = symptoms_questions['questions'][symptom]
    question = random.choice(questions)
    return jsonify({"question": question})

@app.route('/chat2', methods=['POST'])
def chat2():
    data = request.get_json()
    user_response = data.get('user_response', '')
    question = data.get('question', '')

    user_symptoms = session.get('user_symptoms', [])
    asked_questions = set(session.get('asked_questions', []))

    if user_response:

        extracted_symptoms = extract_symptoms(user_response)
        user_symptoms.extend(extracted_symptoms)
        session['user_symptoms'] = user_symptoms

    question_count = len(asked_questions)
    max_questions = 5

    if question_count < max_questions:
        while question_count < max_questions:
            symptom = random.choice(list(symptoms_questions['questions'].keys()))
            while symptom in asked_questions:
                symptom = random.choice(list(symptoms_questions['questions'].keys()))
            asked_questions.add(symptom)
            questions = symptoms_questions['questions'][symptom]
            question = random.choice(questions)
            session['asked_questions'] = list(asked_questions)
            return jsonify({"question": question})

    else:
        disease_probabilities = calculate_disease_probabilities(user_symptoms, diseases_df)
        if disease_probabilities:
            max_prob = max(disease_probabilities.values())
            probable_diseases = [disease for disease, prob in disease_probabilities.items() if prob == max_prob]
            return jsonify({"result": f'Based on your symptoms, you may have: {", ".join(probable_diseases)}'})
        else:
            return jsonify({"result": 'No matching diseases found.'})

@app.route('/session_values')
def session_values():
    return jsonify(dict(session))

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=True)
