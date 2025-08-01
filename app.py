# app.py
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Initialize the Flask application
app = Flask(__name__)
# Set a secret key for session management and security
app.config["SECRET_KEY"] = os.urandom(24)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobs.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Configure file upload settings
UPLOAD_FOLDER = os.path.join(app.root_path, 'resumes')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="job_seeker")

    jobs_posted = db.relationship("Job", backref="employer", lazy="dynamic")
    applications = db.relationship("Application", backref="job_seeker", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.String(50))
    location = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    employer_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    applications = db.relationship("Application", backref="job", lazy="dynamic")

    def __repr__(self):
        return f"<Job {self.title}>"

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    applicant_name = db.Column(db.String(80), nullable=False)
    applicant_email = db.Column(db.String(120), nullable=False)
    resume_filename = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    job_id = db.Column(db.Integer, db.ForeignKey("job.id"))
    job_seeker_id = db.Column(db.Integer, db.ForeignKey("user.id"))

# --- User Loader for Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("login"))

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "employer" or current_user.role == "admin":
        if current_user.role == "employer":
            jobs = Job.query.filter_by(employer_id=current_user.id).all()
        else:
            jobs = Job.query.order_by(Job.timestamp.desc()).all()
        return render_template("dashboard.html", jobs=jobs)
    else:  # current_user.role == "job_seeker"
        applied_jobs = [app.job for app in current_user.applications]
        applied_job_ids = [job.id for job in applied_jobs]
        
        # Fetch all other jobs, excluding those the user has already applied for
        all_jobs = Job.query.filter(Job.id.notin_(applied_job_ids)).order_by(Job.timestamp.desc()).all()
        
        return render_template("dashboard.html", applied_jobs=applied_jobs, all_jobs=all_jobs)

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Access denied. You are not an admin.", "danger")
        return redirect(url_for("index"))

    users = User.query.all()
    jobs = Job.query.all()
    # Also fetch jobs posted by the admin
    posted_jobs = Job.query.filter_by(employer_id=current_user.id).all()

    return render_template("admin_dashboard.html", users=users, jobs=jobs, posted_jobs=posted_jobs)


@app.route("/job_form", methods=["GET", "POST"])
@login_required
def job_form():
    if current_user.role not in ["employer", "admin"]:
        flash("You must be an employer or admin to post jobs.", "danger")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        salary = request.form.get("salary")
        location = request.form.get("location")
        company = request.form.get("company")

        new_job = Job(
            title=title,
            description=description,
            salary=salary,
            location=location,
            company=company,
            employer_id=current_user.id,
        )
        db.session.add(new_job)
        db.session.commit()
        flash("Job posted successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("job_form.html")


@app.route("/edit_job/<int:job_id>", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)

    # Check if the current user is the employer who posted the job or an admin
    if current_user.id != job.employer_id and current_user.role != 'admin':
        flash("Access denied. You can only edit jobs you have posted or as an admin.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        job.title = request.form.get("title")
        job.description = request.form.get("description")
        job.salary = request.form.get("salary")
        job.location = request.form.get("location")
        job.company = request.form.get("company")
        db.session.commit()
        flash("Job updated successfully!", "success")
        return redirect(url_for("dashboard"))

    return render_template("job_form.html", job=job)


@app.route("/jobs", methods=["GET"])
def jobs():
    query = request.args.get("query")
    location = request.args.get("location")

    jobs_query = Job.query.order_by(Job.timestamp.desc())

    if query:
        jobs_query = jobs_query.filter(
            Job.title.ilike(f"%{query}%")
            | Job.description.ilike(f"%{query}%")
            | Job.company.ilike(f"%{query}%")
        )

    if location:
        jobs_query = jobs_query.filter(Job.location.ilike(f"%{location}%"))

    job_listings = jobs_query.all()
    return render_template("jobs.html", jobs=job_listings)

@app.route("/job/<int:job_id>")
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    has_applied = False
    if current_user.is_authenticated and current_user.role == 'job_seeker':
        existing_application = Application.query.filter_by(
            job_id=job_id, job_seeker_id=current_user.id
        ).first()
        if existing_application:
            has_applied = True
    return render_template("job_detail.html", job=job, has_applied=has_applied)


@app.route("/job/<int:job_id>/applicants")
@login_required
def view_applicants(job_id):
    job = Job.query.get_or_404(job_id)

    if current_user.id != job.employer_id and current_user.role != 'admin':
        flash("Access denied. You can only view applicants for your own jobs or as an admin.", "danger")
        return redirect(url_for("dashboard"))

    applicants = job.applications.all()
    return render_template("applicants.html", job=job, applicants=applicants)

@app.route("/apply_job/<int:job_id>", methods=["POST"])
@login_required
def apply_job(job_id):
    if current_user.role != "job_seeker":
        flash("Only job seekers can apply for jobs.", "danger")
        return redirect(url_for("job_detail", job_id=job_id))

    job = Job.query.get_or_404(job_id)
    # Check if the user has already applied for this job
    existing_application = Application.query.filter_by(
        job_id=job_id, job_seeker_id=current_user.id
    ).first()
    
    if existing_application:
        flash("You have already applied for this job.", "info")
        return redirect(url_for("job_detail", job_id=job_id))

    # Handle file upload
    if 'resume' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('job_detail', job_id=job_id))
    
    file = request.files['resume']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('job_detail', job_id=job_id))

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.username}_{job.company}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_application = Application(
            applicant_name=current_user.username,
            applicant_email=current_user.email,
            resume_filename=filename,
            job_id=job_id,
            job_seeker_id=current_user.id
        )
        db.session.add(new_application)
        db.session.commit()
        flash("Application submitted successfully!", "success")
    else:
        flash('Invalid file type. Allowed types are PDF, DOC, DOCX.', 'danger')

    return redirect(url_for("job_detail", job_id=job_id))

@app.route('/uploads/<filename>')
@login_required
def download_resume(filename):
    application = Application.query.filter_by(resume_filename=filename).first_or_404()
    job = application.job

    if current_user.id != job.employer_id and current_user.role != 'admin':
        flash("Access denied. You can only download resumes for your own jobs or as an admin.", "danger")
        return redirect(url_for("dashboard"))
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    user_to_delete = User.query.get_or_404(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    flash(f"User {user_to_delete.username} has been deleted.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete_job/<int:job_id>", methods=["POST"])
@login_required
def delete_job(job_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("index"))

    job_to_delete = Job.query.get_or_404(job_id)
    db.session.delete(job_to_delete)
    db.session.commit()
    flash(f"Job '{job_to_delete.title}' has been deleted.", "success")
    return redirect(url_for("admin_dashboard"))

def create_db():
    with app.app_context():
        db.drop_all()
        db.create_all()

        admin_user = User(
            username="Admin", email="admin@example.com", role="admin"
        )
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()
        print("Database created and default admin user added.")

if __name__ == "__main__":
    # Check for the database file and create it if it doesn't exist
    if not os.path.exists('instance/jobs.db'):
        create_db()
    # In a production environment, Gunicorn will be used to run the app.
    # This block is for local development only.
    app.run(debug=True)
