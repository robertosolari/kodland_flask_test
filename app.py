from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import json

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), 'quiz.db')


def create_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (id INTEGER PRIMARY KEY, question TEXT, option1 TEXT, option2 TEXT, option3 TEXT, answer INTEGER)''')
    conn.commit()
    conn.close()


def add_question(question, option1, option2, option3, answer):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO questions (question, option1, option2, option3, answer) VALUES (?, ?, ?, ?, ?)",
              (question, option1, option2, option3, answer))
    conn.commit()
    conn.close()


def get_questions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM questions")
    questions = c.fetchall()
    conn.close()
    return questions


@app.before_request
def initialize_database():
    create_db()
    if not get_questions():
        add_question(
            "Qual è il linguaggio di programmazione principale utilizzato per lo sviluppo di intelligenza artificiale?",
            "Java", "Python", "C++", 2)
        add_question("Che cosa rappresenta l'acronimo 'NLP' nel contesto dell'intelligenza artificiale?",
                     "Natural Language Processing", "Neural Linguistic Programming", "Next Level Programming", 1)
        add_question(
            "Qual è il principale algoritmo di apprendimento supervisionato utilizzato in machine learning per la classificazione?",
            "SVM (Support Vector Machine)", "KNN (K-Nearest Neighbors)", "Decision Tree", 1)
        add_question("Qual è l'acronimo di 'CNN' nel contesto della visione artificiale?", "Common Neural Network",
                     "Convolutional Neural Network", "Central Neural Network", 2)
        add_question(
            "Quale delle seguenti non è una tecnica di pre-elaborazione comune utilizzata nella visione artificiale?",
            "Riduzione del rumore", "Normalizzazione", "Augmentation", 1)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/quiz')
def quiz():
    questions = get_questions()
    return render_template('quiz.html', questions=questions)


@app.route('/submit', methods=['POST'])
def submit():
    if request.is_json:
        data = request.get_json()
        answers = data
        questions = get_questions()
        correct_answers = {str(question[0]): str(question[5]) for question in questions}
        score = calculate_score(answers, correct_answers)

        # Save the score and user's answers to the database
        save_submission(score, answers)

        return jsonify({'score': score})
    else:
        return jsonify({'error': 'Invalid request'}), 400


def calculate_score(answers, correct_answers):
    num_correct = sum(1 for q_id, answer in answers.items() if answer == correct_answers.get(q_id))
    total_questions = len(answers)
    return (num_correct / total_questions) * 100


def save_submission(score, answers):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Create a table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS submissions
                     (id INTEGER PRIMARY KEY, user_id TEXT, score INTEGER, answers TEXT)''')
        # Insert the submission into the table
        c.execute("INSERT INTO submissions (user_id, score, answers) VALUES (?, ?, ?)",
                  ('user_id', score, json.dumps(answers)))
        conn.commit()
    except sqlite3.Error as e:
        print("Error saving submission:", e)
    finally:
        conn.close()


@app.route('/questions')
def questions():
    questions = get_questions()
    formatted_questions = {f'{index}': question for index, question in enumerate(questions, 1)}
    return jsonify(formatted_questions)


@app.route('/highscore')
def highscore():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT MAX(score) FROM submissions")
        highest_score = c.fetchone()[0]
    except sqlite3.OperationalError:
        highest_score = None  # Set highest_score to None if the table doesn't exist
    conn.close()
    return jsonify({'highest_score': highest_score})


if __name__ == '__main__':
    app.run(debug=True)
