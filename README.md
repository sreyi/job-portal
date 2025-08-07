Project Overview
The Job Portal Web Application is a full-stack project designed to streamline the hiring process by connecting job seekers with employers and providing a central management hub for administrators. Built with Python's Flask framework, the application features a dynamic and responsive user interface, secure authentication, and a file management system for handling resume submissions.
This project showcases expertise in building a robust web application from the ground up, highlighting key skills in backend development, database management, and modern frontend design.
________________________________________
Key Features and User Flows
The application is built around three distinct user roles, each with a tailored experience and specific permissions.
•	Job Seekers:
o	Can register and log in to their accounts.
o	Can browse and search all available job listings on the platform.
o	Can apply for jobs directly from the job details page by submitting an application form and uploading a resume file.
o	The system intelligently prevents them from applying to the same job more than once, and they can easily view a list of their applied jobs on their personal dashboard.
•	Employers:
o	Can register and log in to their accounts.
o	Can post new job listings with detailed information (title, company, salary, location, description).
o	Can edit or delete only the jobs they have posted.
o	Can view all applicants for their jobs, including their name, email, and a secure link to download their submitted resume.

•	Admins:
o	Have full control over the platform.
o	Can perform all the actions of an employer, including posting and editing jobs.
o	Have a dedicated admin dashboard to manage all users and delete any job listing on the site.
o	Can view applicants for any job, regardless of who posted it.
________________________________________
Technical Stack and Implementation Details
The project's architecture is clean, modular, and built with modern best practices in mind.
•	Backend & Framework:
o	The application's core logic is powered by Python and the lightweight Flask web framework.
o	It uses a modular file structure, with separate routes for user authentication, job management, and admin controls.
o	The code is well-commented and follows a logical flow, making it easy to understand and extend.
•	Database Management:
o	Data is stored in a SQLite database, managed by the Flask-SQLAlchemy Object-Relational Mapper (ORM).
o	The database schema includes models for User, Job, and Application, with clear relationships established between them to maintain data integrity.
•	User Authentication and Security:
o	Flask-Login is used to handle all aspects of user sessions, from logging in and out to protecting restricted pages with the @login_required decorator.
o	User passwords are not stored in plain text. Instead, they are securely hashed using Werkzeug's generate_password_hash function, protecting sensitive user data.



•	Frontend Design and Usability:
o	The user interface is built with standard HTML and styled with a custom CSS file for a modern, professional look.
o	Bootstrap 5 provides a responsive grid system and pre-built components, ensuring the application is accessible and visually appealing on all devices, from mobile phones to desktops.
o	Custom CSS transitions and animations create a dynamic and smooth user experience, making navigation and interactions feel fluid and modern.
•	File Uploads:
o	The application includes robust functionality for handling file uploads using Werkzeug's file utilities.
o	Resumes are saved to a dedicated resumes/ folder with secure filenames to prevent conflicts and ensure data integrity.
o	Secure routes and role-based permissions ensure that only authorized users (employers and admins) can download these files.
