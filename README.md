# Smart Assessment and Question Generation System

## Table of Contents
1. [Setup Guide (Installation)](#setup-guide)
2. [User Guide](#user-guide)
3. [Technical Documentation](#technical-documentation)
4. [API Documentation](#api-documentation)
5. [Future Enhancements](#future-enhancements)
6. [Security & Optimization Notes](#security--optimization-notes)

---

## Setup Guide

To get this application running locally:

### 1. Prerequisites
- **Python 3.9+** installed on your system.
- **Git** (optional, to manage versions).

### 2. Installation Steps
1. **Clone/Download the repository:**
   Navigate to your desired folder and open a terminal.
2. **Create a Virtual Environment:**
   Run `python -m venv venv`
3. **Activate the Virtual Environment:**
   - On Windows: `.\venv\Scripts\activate`
   - On Mac/Linux: `source venv/bin/activate`
4. **Install Dependencies:**
   Run `pip install -r requirements.txt`
   *(Ensure dependencies like `django`, `google-generativeai`, etc., are installed)*
5. **Set up Environment Variables:**
   Create a `.env` file in the project root directory and add your Google Gemini API Key:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```
6. **Apply Database Migrations:**
   Run `python manage.py migrate`
7. **Create a Superuser (Optional but Recommended):**
   Run `python manage.py createsuperuser` and follow the prompts.
8. **Run the Server:**
   Run `python manage.py runserver`
   Access the application at `http://127.0.0.1:8000/`.

---

## User Guide

This system allows users to generate custom quizzes using AI, take them, and review their performance.

### How to use the system:
1. **Registration & Login:**
   Create an account using the registration page, or login if you already have one.
2. **Dashboard:**
   Upon logging in, you'll be presented with a modern dashboard displaying your total quizzes taken, average score, a dynamic heatmap showing your participation history, and a graph of your activity over the last 14 days. You can also resume incomplete quizzes directly from here.
3. **Profile Updates:**
   Click on the "Profile" link in the navbar (or the avatar icon). Here you can upload a profile picture, update your full name, add a bio, and toggle whether you wish to appear on the public Leaderboards.
4. **Generating Quizzes:**
   Navigate to the "Categories" page. Select a Category -> Subcategory (e.g., Programming -> Python). You will be prompted to choose settings:
   - **Difficulty:** Easy, Medium, or Hard.
   - **Questions:** How many questions to generate (e.g., 5, 10, 15).
   - **Timer:** Enable/disable a timer for taking the quiz.
   - **Custom Prompt:** Add specific instructions for the AI on what to focus on.
5. **Taking Quizzes:**
   Answer the multiple-choice questions. Your progress is asynchronously saved. You can close the tab and return later to resume from where you left off. Submit the quiz when finished.
6. **Viewing Results:**
   Once submitted, you'll instantly see your score, a detailed breakdown of correct/incorrect answers with the AI's explanations, and a list of recommended learning resources linked directly to external platforms.
7. **Leaderboard:**
   Compete with others! You can view Global Leaderboards, Highest Streaks, or filter by specific academic categories to see who performs best.

---

## Technical Documentation

### Architecture
The project follows the standard **Django MVT (Model-View-Template)** architecture:
- **Models:** Define the SQL database structure (SQLite by default).
- **Views:** Handle the logic, processing requests, talking to the models and the external LLM API.
- **Templates:** Handle the UI rendering. The application uses Django templating language mixed with modern CSS and vanilla Javascript for dynamic AJAX requests.

### Models Explanation
The application is split across two main apps: **Dashboard** and **Quizzes**.

**Dashboard Models (`dashboard/models.py`):**
- `Profile`: Holds user-specific extended data beyond Django's base Auth `User` model (e.g., avator, bio, total_score, avg_accuracy, highest_streak).
- `Category` & `Subcategory`: Organizes topics users can get quizzed on.
- `UserCategoryStats`: Tracks a player's performance partitioned by specific categories for detailed leaderboards.

**Quizzes Models (`quizzes/models.py`):**
- `QuizAttempt`: Represents a specific instance of a generated quiz. It links to the User and Subcategory, and stores metadata like `score`, `timer_enabled`, `is_completed`, and `learning_resources`.
- `QuizQuestion`: Represents a single question within an attempt. Contains `options` (JSON string), `correct_answer`, `user_answer`, `explanation`, and tracks if the user answered it correctly. 

### Views Explanation
- **`dashboard.views.dashboard`**: Highly optimized dashboard using Django `annotate` and `aggregate` to avoid N+1 slow queries. It builds a heatmap and graph using `TruncDate`.
- **`dashboard.views.generate_quiz_api`**: Takes AJAX requests from the frontend, securely retrieves session rules, calls Gemini API asynchronously, parses JSON, and stores it in the session to avoid db clutter until the user explicitly begins taking it.
- **`quizzes.views.save_progress`**: AJAX endpoint that uses `bulk_update` to asynchronously persist the user's answers to the database while they take the quiz so they don't lose data if their browser crashes.
- **`quizzes.views.submit_quiz`**: Calculates the final score, evaluates true/false logic, stores the metadata, and passes a signal to update the User's overall Profile metrics (via `update_leaderboard_stats`).

---

## API Documentation

The application tightly integrates with **Google's Gemini Generative AI** (`google-generativeai` package) to synthesize distinct questions dynamically.

### AI Integration Flow (`dashboard/utils.py`)
1. View triggers the `generate_quiz_questions(topic, difficulty, count, extra_comments)` local utility function.
2. We initialize the client via `genai.configure(api_key=settings.GEMINI_API_KEY)`.
3. We construct a multi-shot instructional prompt demanding the AI return raw JSON exclusively.
   - Example prompt constraints:
     *"Return JSON with 'questions' as a list... each having 'options', 'answer' matching an option exactly, and 'explanation'. Return 'learning_resources' as a list of strings."*
4. `client.generate_content` is invoked with `response_mime_type='application/json'` and `temperature=0` (to maintain deterministic, predictable structured output and prevent hallucination).
5. The method parses the `.text` string into a Python Dictionary natively and passes it to the caller view.
6. The views parse the data into database `QuizQuestion` objects.

---

## Future Enhancements
Based on the current architecture, here are actionable expansions for V2:
1. **Multiplayer Challenges:** Allow users to challenge a friend to the same generated quiz. Give both users a unique join-link referencing the exact same `QuizAttempt` seed.
2. **Audio / Image Generation:** Leverage multimodal LLMs to generate images alongside questions or allow users to speak to answer.
3. **Advanced Analytics Dashboard:** Break down the User's accuracy further based on historical timestamps to prove learning efficacy. 
4. **Adaptive Difficulty Models:** Track what sub-topics a user frequently misses inside Python (e.g. Iterators vs Lists) and specifically inject those vulnerabilities into the system prompt for the next generated quiz. 
5. **Caching Layer:** Integrate Redis for leaderboard generation, as tracking thousands of users continuously updating profiles could slow down PostgreSQL/SQLite.

---

## Security & Optimization Notes
- **Optimizations Applied:** Major `N+1` DB bottlenecks have been resolved across `quizzes/views.py` and `dashboard/views.py` utilizing `prefetch_related('questions')`, `select_related()`, and batch row transactions natively via `bulk_update(['is_correct'])` limiting thousands of IO roundtrips into a single rapid execution block.
- **Security Check:** Application uses Django's `@login_required` decorators everywhere, blocks brute-forcing ID parameters by evaluating `user=request.user` on `get_object_or_404`, and leverages standard CSRF token security. No raw queries exist in the deployment flow, preventing SQL Injection vulnerabilities naturally.

**(For Production Deployment, ensure you set `DEBUG=False` and supply `ALLOWED_HOSTS` inside `settings.py`).**
