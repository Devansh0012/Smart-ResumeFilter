import pymongo
import plotly.graph_objects as go

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["job_portal"]
collection = db["resumes"]

# Define a list of 100 programming and technology-related keywords
keywords = ["python", "java", "javascript", "html", "css", "react", "angular", "nodejs", "mongodb", "sql", "django",
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
