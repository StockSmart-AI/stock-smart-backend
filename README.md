This is where we implement the backend Flask API logics for Stock-smart
Repository Structure

This repository contains the backend code for the Stock Smart system, built using Flask.

Backend Setup (Flask)

Prerequisites

Ensure you have the following installed:

Python 3.x

Virtual Environment (venv)


pip (Python package manager)

Installation Steps

Clone the repository:

git clone https://github.com/StockSart/stock-smart-backend.git
cd stock-smart-backend

Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Set up environment variables:

Initialize the database:

flask db init
flask db migrate -m "Initial migration."
flask db upgrade

Run the application:

flask run

The API will be available at http://127.0.0.1:5000/

Collaboration Guidelines

Branching Strategy

We use Git Flow to manage development:

main: Stable production-ready code.

develop: Latest development features.

feature/branch-name: For new features.

bugfix/branch-name: For fixing bugs.

How to Contribute

Pull the latest changes:

git pull origin develop

Create a feature branch:

git checkout -b feature/your-feature

Write clean and modular code.

Commit and push:

git add .
git commit -m "Add feature: your feature description"
git push origin feature/your-feature

Create a Pull Request (PR) to develop.