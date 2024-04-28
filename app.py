from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import fitz  # PyMuPDF
import os

app = Flask(__name__, static_url_path='/static')

client = MongoClient('mongodb://localhost:27017/')
db = client['job_portal']
jobs_collection = db['jobs']
resumes_collection = db['resumes']
keywords_collection = db['keywords']

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# # Load the English language model
# nlp = spacy.load('en_core_web_sm')

def categorize_keywords(resume_keywords):
    categories = {
        'education': [],
        'links': [],
        'experience': [],
        'projects': [],
        'skills': [],
        'coursework': [],
        'achievements': [],
        # Add more categories as needed
    }

    current_category = None  # Track the current category being processed

    for keyword in resume_keywords:
        if keyword.lower() == 'education':
            current_category = 'education'
        elif keyword.lower() == 'experience':
            current_category = 'experience'
        elif keyword.lower() == 'links':
            current_category = 'links'
        elif keyword.lower() == 'projects':
            current_category = 'projects'
        elif keyword.lower() == 'skills':
            current_category = 'skills'
        elif keyword.lower() == 'coursework':
            current_category = 'coursework'
        elif keyword.lower() == 'achievements':
            current_category = 'achievements'
        else:
            if current_category is not None:
                categories[current_category].append(keyword)

    return categories


def extract_keywords_from_resume(pdf_path, job_description):
    resume_text = extract_text_from_pdf(pdf_path)
    
    # Tokenize the resume text and job description
    resume_tokens = word_tokenize(resume_text.lower())
    job_tokens = word_tokenize(job_description.lower())

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    resume_keywords = [word for word in resume_tokens if word.isalnum() and word not in stop_words]
    job_keywords = [word for word in job_tokens if word.isalnum() and word not in stop_words]

    categories = categorize_keywords(resume_keywords)
    print(categories)

    # Define keywords related to software development
    software_dev_keywords = ['software', 'developer', 'programmer', 'coding', 'programming', 'agile', 'frameworks',
                             'javascript', 'c++', 'java', 'angularjs', 'git', 'databases', 'orm', 'hibernate']

    # Find common keywords related to software development
    jobKey=set(job_keywords) & set(software_dev_keywords)
    common_keywords = set(resume_keywords) & set(job_keywords) & set(software_dev_keywords)
    matching_count = len(common_keywords)
    total_count = len(jobKey)

    print(job_keywords);
    print(resume_keywords)

    return matching_count, total_count

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as pdf_file:
        for page_num in range(len(pdf_file)):
            page = pdf_file[page_num]
            text += page.get_text()
    return text
@app.route('/')
def index():
    jobs = list(jobs_collection.find())
    return render_template('index.html', jobs=jobs)



@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        job_name = request.form['job_name']
        job_description = request.form['job_description']
        keywords = request.form['keywords'].split(',')
        job_id = jobs_collection.insert_one({'name': job_name, 'description': job_description, 'keywords': keywords}).inserted_id
        return redirect(url_for('admin'))
    
    jobs = list(jobs_collection.find())
    return render_template('admin.html', jobs=jobs)

@app.route('/apply/<job_id>', methods=['GET'])
def apply(job_id):
    job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    return render_template('apply.html', job=job, job_id=job_id)



@app.route('/job/<job_id>', methods=['POST'])
def submit_application(job_id):
    name = request.form['name']
    email = request.form['email']
    job_id = ObjectId(job_id)
    resume_file = request.files['resume']

    # Save resume file to a temporary location
    temp_filename = f'temp_{resume_file.filename}'
    resume_file.save(temp_filename)

    # Extract text from the resume file
    resume_text = extract_text_from_pdf(temp_filename)

    # Tokenize the resume text
    resume_tokens = word_tokenize(resume_text.lower())

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    resume_keywords = [word for word in resume_tokens if word.isalnum() and word not in stop_words]

    # Categorize the keywords
    categories = categorize_keywords(resume_keywords)

    # Save resume and categories to the database
    with open(temp_filename, 'rb') as resume_file:
        resumes_collection.insert_one({'job_id': ObjectId(job_id), 'name': name, 'email': email, 'resume': resume_file.read(), 'categories': categories})

    # Remove the temporary file
    os.remove(temp_filename)
    
    return redirect(url_for('index'))



from bson import ObjectId

@app.route('/admin/resumes/<job_id>', methods=['GET'])
def admin_resumes(job_id):
    # Retrieve the job from the database using the job_id
    job = jobs_collection.find_one({'_id': ObjectId(job_id)})
    # job keywords
    job_description = job.get('description', '')
    job_tokens = word_tokenize(job_description.lower())
    stop_words = set(stopwords.words('english'))
    job_keywords = [word for word in job_tokens if word.isalnum() and word not in stop_words]

    # Retrieve all resumes related to the job
    resumes = list(resumes_collection.find({'job_id': ObjectId(job_id)}))

    # Calculate matching percentage for each resume
    for resume in resumes:
        categories = resume.get('categories', {})
        matching_count = sum(1 for category in categories.values() for keyword in category if keyword in job_keywords)
        total_keywords = sum(len(category) for category in categories.values())
        resume['matching_percentage'] = matching_count / total_keywords * 100 if total_keywords > 0 else 0

        resume['matching_percentage'] += 30

    # Sort resumes by matching percentage in descending order
    sorted_resumes = sorted(resumes, key=lambda x: x['matching_percentage'], reverse=True)

    return render_template('admin_resumes.html', job=job, resumes=sorted_resumes)





from flask import send_file
from io import BytesIO


@app.route('/admin/resumes/<resume_id>/view', methods=['GET'])
def view_resume(resume_id):
    # Retrieve the resume from the database using the resume_id
    resume = resumes_collection.find_one({'_id': ObjectId(resume_id)})
    if not resume:
        abort(404)

    # Retrieve the resume data (assuming it's stored as a file in the database)
    resume_data = resume.get('resume', b'')
    
    # Return the resume file in a new tab
    return send_file(BytesIO(resume_data), as_attachment=False, mimetype='application/pdf')

import pymongo
import plotly.graph_objects as go

@app.route('/user_skill_graph', methods=['GET'])
def generate_skill_visualization():
    # Connect to MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["job_portal"]
    collection = db["resumes"]

    # Define a list of 100 programming and technology-related keywords
    keywords = ["python", "j    ava", "javascript", "html", "css", "react", "angular", "nodejs", "mongodb", "sql", "django",
                "flask", "rest", "api", "git", "github", "docker", "aws", "azure", "cloud", "linux", "unix", "agile",
                "scrum", "mysql", "postgresql", "nosql", "devops", "machine learning", "artificial intelligence",
                "data science", "big data", "tensorflow", "pytorch", "numpy", "pandas", "matplotlib", "seaborn",
                "scikit-learn", "keras", "deep learning", "neural networks", "computer vision", "natural language processing",
                "web development", "mobile development", "react native", "vue", "redux", "graphql", "jquery", "bootstrap",
                "sass", "less", "webpack", "babel", "storybook", "jest", "mocha", "chai", "cypress", "typescript",
                "java ee", "spring", "spring boot", "hibernate", "jpa", "maven", "gradle", "android", "ios", "swift",
                "kotlin", "objective-c", "unity", "unreal engine", "c++", "c#", ".net", "asp.net", "entity framework",
                "laravel", "php", "wordpress", "drupal", "joomla", "ruby", "ruby on rails", "sinatra", "scala", "clojure",
                "haskell", "rust", "go", "elixir", "erlang", "docker", "kubernetes", "terraform", "jenkins", "ansible",
                "puppet", "chef", "rabbitmq", "kafka", "redis", "memcached", "elasticsearch", "mongodb", "cassandra"]

    # Define the aggregation pipeline
    pipeline = [
        {"$unwind": "$categories"},  # Unwind the categories array
        {"$unwind": "$categories.skills"},  # Unwind the skills array
        {"$match": {"categories.skills": {"$in": keywords}}},  # Match skills that are in the keywords list
        {"$group": {"_id": "$categories.skills", "count": {"$sum": 1}}},  # Count the occurrences of each matched skill
        {"$sort": {"count": -1}}  # Sort by count in descending order
    ]

    # Execute the aggregation pipeline
    cursor = collection.aggregate(pipeline)

    # Extract skills and counts for plotting
    skills = []
    counts = []
    for doc in cursor:
        skills.append(doc["_id"])
        counts.append(doc["count"])

    # Create a bar chart using Plotly
    fig = go.Figure(data=go.Bar(x=skills, y=counts))
    fig.update_layout(title='Number of Users by Skill', xaxis_title='Skill', yaxis_title='Number of Users')

   # Save the plot as an HTML file
    fig.write_html("user_skill_graph.html")

    # Redirect to the generated visualization
    return redirect(url_for('static', filename='user_skill_graph.html'))



if __name__ == '__main__':
    app.run(debug=True)