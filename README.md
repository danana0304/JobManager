# Job Manager Application

A full-stack job management application developed as the final project for the **Mthree training course** by **Madelyn Gotceitas** and **Daun Lee**.

The application provides separate experiences for **Users** and **Administrators**, allowing users to manage their job applications while administrators can manage job postings and application data.

## Tech Stack

### Frontend

- React
- JavaScript
- HTML/CSS

### Backend

- Python
- Flask
- SQLAlchemy
- PostgreSQL

### Deployment

- Render

## Features

### User

- Create and manage an account
- Browse available job postings
- Apply to jobs
- Manage and track job applications
- View application information

### Admin

- Manage job postings
- View and manage users
- Manage job applications
- Access administrative functionality through a dedicated interface

## Getting Started

### Prerequisites

Make sure you have the following installed:

- [Node.js](https://nodejs.org/)
- Python 3
- MySQL

### Frontend

Navigate to the frontend directory:

```bash
cd frontend
```

Install the dependencies:

```bash
npm install
```

Start the frontend development server:

```bash
npm start
```

The frontend will be available at:

```text
http://localhost:3000
```

### Backend

From the project directory, start the Flask API:

```bash
npm run start-api
```

The backend server will run alongside the frontend and provide the API endpoints used by the application.

## Deployment

The application is deployed as a full-stack application using **Render**.

Both the frontend and backend are deployed through Render, allowing the application to be accessed without running the development servers locally.

## Project Structure

```text
JobManager/
├── frontend/          # React frontend
├── api/           # Flask backend
├── README.md
└── ...
```

## Authors

**Madelyn Gotceitas**
**Daun Lee**

Developed as the final full-stack application project for the **Mthree training course**.
