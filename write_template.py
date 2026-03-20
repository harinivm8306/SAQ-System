import os

content = """{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Quizzes - IntelliQ</title>
    <link rel="icon" href="{% static 'images/favicon.png' %}" type="image/png">
    <link rel="stylesheet" href="/static/css/dashboard.css?v=4.0">
</head>
<body>
    <header class="navbar">
        <div class="nav-left">
            <div class="logo">IntelliQ</div>
            <nav class="nav-links">
                <a href="{% url 'dashboard' %}">Dashboard</a>
                <a href="{% url 'profile' %}">Profile</a>
                <a href="{% url 'categories' %}">Categories</a>
                <a href="{% url 'my_quizzes' %}" class="active">My Quizzes</a>
                <a href="{% url 'leaderboard' %}">Leaderboard</a>
            </nav>
        </div>
        <div class="nav-right">
            {% if user.is_authenticated %}
            <span class="nav-username">Hi, {{ user.username }}</span>
            <a href="{% url 'landing' %}" class="logout-btn">Logout</a>
            {% else %}
            <a href="{% url 'login' %}" class="login-btn">Login</a>
            {% endif %}
        </div>
    </header>

    <div class="main-content">
        <div class="dashboard-container" style="max-width: 1200px; margin: 0 auto;">
            <div class="quizzes-header">
                <div>
                    <h1>My Quizzes</h1>
                    <p>Track your performance and access AI recommendations</p>
                </div>
                <a href="{% url 'categories' %}" class="btn-primary" style="text-decoration: none;">New Assessment</a>
            </div>

            <div class="filter-section">
                <form method="GET" action="{% url 'my_quizzes' %}" class="filter-grid">
                    <div class="filter-group">
                        <label>Search Topic</label>
                        <input type="text" name="q" value="{{ search_query }}" class="filter-input" placeholder="Search topic...">
                    </div>
                    <div class="filter-group">
                        <label>Category</label>
                        <select name="category" class="filter-select">
                            <option value="">All Categories</option>
                            {% for c in categories %}
                            <option value="{{ c.id }}" {% if current_category == c.id|stringformat:"s" %}selected{% endif %}>
                                {{ c.name }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Subcategory</label>
                        <select name="subcategory" class="filter-select">
                            <option value="">All Subcategories</option>
                            {% for s in subcategories %}
                            <option value="{{ s.id }}" {% if current_subcategory == s.id|stringformat:"s" %}selected{% endif %}>
                                {{ s.name }}
                            </option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Date From</label>
                        <input type="date" name="start_date" value="{{ start_date }}" class="filter-input">
                    </div>
                    <div class="filter-group">
                        <label>Date To</label>
                        <input type="date" name="end_date" value="{{ end_date }}" class="filter-input">
                    </div>
                    <div class="filter-group">
                        <label>Sort By</label>
                        <select name="sort" class="filter-select">
                            <option value="-started_at" {% if current_sort == "-started_at" %}selected{% endif %}>Date (Newest)</option>
                            <option value="started_at" {% if current_sort == "started_at" %}selected{% endif %}>Date (Oldest)</option>
                            <option value="-score" {% if current_sort == "-score" %}selected{% endif %}>Score (High to Low)</option>
                            <option value="score" {% if current_sort == "score" %}selected{% endif %}>Score (Low to High)</option>
                            <option value="subcategory__name" {% if current_sort == "subcategory__name" %}selected{% endif %}>Topic (A-Z)</option>
                            <option value="-subcategory__name" {% if current_sort == "-subcategory__name" %}selected{% endif %}>Topic (Z-A)</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <button type="submit" class="btn-primary" style="width: 100%; height: 46px;">Apply Filter</button>
                    </div>
                </form>
            </div>

            {% if page_obj %}
            <div class="quiz-attempt-grid">
                {% for attempt in page_obj %}
                <div class="attempt-card">
                    <div class="attempt-card-top">
                        <div class="attempt-topic">
                            <h3>{{ attempt.subcategory.name }}</h3>
                            <span class="attempt-date">
                                📅 {{ attempt.started_at|date:"M d, Y" }}
                                <span style="margin-left: 10px;">{{ attempt.started_at|date:"g:i A" }}</span>
                            </span>
                        </div>
                        <div class="attempt-score-mini">
                            <span class="attempt-score-val">{{ attempt.score }}</span>
                            <span class="attempt-score-total">/ {{ attempt.total_questions }}</span>
                        </div>
                    </div>
                    <div class="attempt-resources-mini">
                        <span class="resource-label">Learning Path:</span>
                        <div class="resource-list-mini">
                            {% if attempt.learning_resources %}
                                {% for resource in attempt.learning_resources|slice:":3" %}
                                <span class="mini-tag">{{ resource|truncatechars:18 }}</span>
                                {% endfor %}
                            {% else %}
                                <span class="mini-tag" style="font-style: italic;">No resources yet</span>
                            {% endif %}
                        </div>
                    </div>
                    <a href="{% url 'quiz_result' attempt.id %}" class="attempt-btn">View Detailed Report</a>
                </div>
                {% endfor %}
            </div>

            {% if page_obj.has_other_pages %}
            <div class="pagination-wrapper">
                {% if page_obj.has_previous %}
                <a href="?page={{ page_obj.previous_page_number }}&q={{ search_query }}&category={{ current_category }}&subcategory={{ current_subcategory }}&start_date={{ start_date }}&end_date={{ end_date }}&sort={{ current_sort }}" class="page-link">Previous</a>
                {% endif %}
                {% for i in page_obj.paginator.page_range %}
                    {% if page_obj.number == i %}
                    <span class="page-link active">{{ i }}</span>
                    {% elif i > page_obj.number|add:"-3" and i < page_obj.number|add:"3" %}
                    <a href="?page={{ i }}&q={{ search_query }}&category={{ current_category }}&subcategory={{ current_subcategory }}&start_date={{ start_date }}&end_date={{ end_date }}&sort={{ current_sort }}" class="page-link">{{ i }}</a>
                    {% endif %}
                {% endfor %}
                {% if page_obj.has_next %}
                <a href="?page={{ page_obj.next_page_number }}&q={{ search_query }}&category={{ current_category }}&subcategory={{ current_subcategory }}&start_date={{ start_date }}&end_date={{ end_date }}&sort={{ current_sort }}" class="page-link">Next</a>
                {% endif %}
            </div>
            {% endif %}

            {% else %}
            <div style="text-align: center; padding: 80px; background: rgba(255, 255, 255, 0.03); border-radius: 30px; border: 2px dashed rgba(255, 140, 0, 0.2); animation: fadeUp 0.8s ease;">
                <h2 style="color: #fff; margin-bottom: 10px;">No Assessments Found</h2>
                <p style="color: #888; margin-bottom: 30px;">It looks like you haven't taken any quizzes matching your search criteria yet.</p>
                <a href="{% url 'categories' %}" class="btn-primary" style="text-decoration: none; padding: 15px 40px;">Get Started</a>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>"""

with open("templates/dashboard/my_quizzes.html", "w", encoding="utf-8") as f:
    f.write(content)
print("File written successfully.")
