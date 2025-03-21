# Stock-Smart Backend API

This is where we implement the backend Flask API logic for **Stock-Smart**.

## Repository Structure

This repository contains the backend code for the Stock-Smart system, built using Flask.

## Backend Setup (Flask)

### Prerequisites

Ensure you have the following installed:

- **Python 3.x**
- **Virtual Environment (venv)**
- **pip** (Python package manager)

### Installation Steps

#### 1. Clone the repository:

```sh
git clone https://github.com/StockSart/stock-smart-backend.git
cd stock-smart-backend
```

#### 2. Create and activate a virtual environment:

```sh
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

#### 3. Install dependencies:

```sh
pip install -r requirements.txt
```

#### 4. Set up environment variables:

(Configure necessary environment variables as needed.)

#### 5. Run the application:

```sh
flask run
```

The API will be available at: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## API Endpoints

### 1. **Signup a New User**

**Endpoint:** `POST /auth/signup`

**Request Body:**
```json
{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "password": "password123",
    "phone": "1234567890",
    "role": "employee"  // Optional, defaults to "employee"
}
```

**Response:**
```json
{
    "message": "User created successfully"
}
```

### 2. **Login**

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
    "email": "john.doe@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "access_token": "your_jwt_token",
    "role": "employee"
}
```

### 3. **Send OTP**

**Endpoint:** `POST /auth/send-otp`

**Request Body:**
```json
{
    "email": "john.doe@example.com"
}
```

**Response:**
```json
{
    "message": "OTP sent successfully"
}
```

### 4. **Verify OTP**

**Endpoint:** `POST /auth/verify-otp`

**Request Body:**
```json
{
    "email": "john.doe@example.com",
    "otp": "123456"
}
```

**Response:**
```json
{
    "message": "Login successful!",
    "role": "employee",
    "access_token": "your_jwt_token"
}
```

### 5. **Get All Products**

**Endpoint:** `GET /products/`

**Headers:**
```http
Authorization: Bearer your_jwt_token
```

**Response:**
```json
[
    {
        "id": "product_id",
        "name": "Product Name",
        "shop_id": "shop_id",
        "price": 100.0,
        "quantity": 10,
        "threshold": 5,
        "description": "Product Description",
        "category": "Product Category",
        "barcode": "1234567890"
    },
    ...
]
```

### 6. **Get Product by ID**

**Endpoint:** `GET /products/{product_id}`

**Headers:**
```http
Authorization: Bearer your_jwt_token
```

**Response:**
```json
{
    "id": "product_id",
    "name": "Product Name",
    "shop_id": "shop_id",
    "price": 100.0,
    "quantity": 10,
    "threshold": 5,
    "description": "Product Description",
    "category": "Product Category",
    "barcode": "1234567890"
}
```

### 7. **Get Product by Barcode**

**Endpoint:** `GET /products/barcode/{barcode}`

**Headers:**
```http
Authorization: Bearer your_jwt_token
```

**Response:**
```json
{
    "id": "product_id",
    "name": "Product Name",
    "shop_id": "shop_id",
    "price": 100.0,
    "quantity": 10,
    "threshold": 5,
    "description": "Product Description",
    "category": "Product Category",
    "barcode": "1234567890"
}
```

### 8. **Add Product**

**Endpoint:** `POST /products/add`

**Headers:**
```http
Authorization: Bearer your_jwt_token
```

**Request Body:**
```json
{
    "name": "Product Name",
    "shop_id": "shop_id",
    "price": 100.0,
    "quantity": 10,
    "threshold": 5,
    "description": "Product Description",
    "category": "Product Category",
    "barcode": "1234567890"
}
```

**Response:**
```json
{
    "message": "Product added successfully",
    "product_id": "product_id"
}
```

### 9. **Update Product**

**Endpoint:** `PUT /products/update/{product_id}`

**Headers:**
```http
Authorization: Bearer your_jwt_token
```

**Request Body:**
```json
{
    "name": "Updated Product Name",
    "shop_id": "shop_id",
    "price": 120.0,
    "quantity": 15,
    "threshold": 10,
    "description": "Updated Product Description",
    "category": "Updated Product Category",
    "barcode": "1234567890"
}
```

**Response:**
```json
{
    "message": "Product updated successfully"
}
```

### 10. **Delete Product**

**Endpoint:** `DELETE /products/delete/{product_id}`

**Headers:**
```http
Authorization: Bearer your_jwt_token
```

**Response:**
```json
{
    "message": "Product deleted successfully"
}
```

### 11. **Scan Barcode**

**Endpoint:** `POST /products/scan-barcode`

**Headers:**
```http
Authorization: Bearer your_jwt_token
```

**Request Body:**
```json
{
    "barcode": "1234567890"
}
```

**Response:**
```json
{
    "product_id": "product_id",
    "name": "Product Name",
    "shop_id": "shop_id",
    "price": 100.0,
    "quantity": 10,
    "threshold": 5,
    "description": "Product Description",
    "category": "Product Category",
    "barcode": "1234567890"
}
```

## Authentication

All endpoints that require authentication must include the `Authorization` header with the JWT token received after logging in.

```http
Authorization: Bearer your_jwt_token
```

Replace `your_jwt_token` with the actual JWT token you receive after logging in.

## Running the Application

To run the application locally, follow these steps:

1. Clone the repository.
2. Create a virtual environment and activate it.
3. Install the dependencies using `pip install -r requirements.txt`.
4. Create a `.env` file with the necessary environment variables.
5. Run the application using `flask run`.

```sh
git clone https://github.com/your-repo/stock-smart-backend.git
cd stock-smart-backend
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
cp .env.example .env  # Create a .env file and fill in the necessary environment variables
flask run
```

This will start the application on `http://127.0.0.1:5000/`.

## Deployment

To deploy the application on Render, follow the Render deployment guide and ensure that the environment variables are set correctly in the Render dashboard.

```plaintext
MONGO_URI="your_mongo_uri"
SECRET_KEY="your_secret_key"
mongodb_database_name="your_database_name"
mongodb_db_pass="your_database_password"
mongodb_db_user="your_database_user"
```

Replace the placeholder values with your actual MongoDB URI, secret key, and database credentials.

## Contribution Guidelines

To ensure a smooth workflow for our mobile app project, please follow these conventions when contributing.

---

## 1. Branching Strategy

- **Never Push Directly to `main` (or `master`):**  
  All changes should go through feature branches and pull requests to ensure proper code review and testing.

- **Branch Types:**
  - **Feature Branches:** For new features.  
    **Example:** `feature/login-screen`
  - **Bugfix Branches:** For bug fixes.  
    **Example:** `bugfix/crash-on-load`
  - **Hotfix Branches:** For urgent fixes on production code.  
    **Example:** `hotfix/fix-payment-error`
  - **Release Branches (Optional):** For preparing a release.  
    **Example:** `release/v1.2.0`

---

## 2. Branch Naming Conventions

- **Use Lowercase and Hyphens:**  
  This improves readability and consistency.  
  **Examples:**
  - `feature/user-authentication`
  - `bugfix/navigation-error`

- **Keep it Descriptive:**  
  Include a short description of the change so others can easily understand the purpose.

---

## 3. Commit Message Conventions

Use a consistent commit message format to maintain a clear project history. We follow the **Conventional Commits** standard:

- **Format:**  
  `type(scope): description`

- **Types:**
  - `feat:` — for new features
  - `fix:` — for bug fixes
  - `docs:` — for documentation changes
  - `style:` — for formatting changes (no code logic changes)
  - `refactor:` — for code refactoring
  - `test:` — for adding or modifying tests
  - `chore:` — for changes to build process, auxiliary tools, etc.

- **Examples:**
   - `feat(auth): add login screen with validation`
   - `fix(api): resolve crash when fetching user data`
   - `docs(readme): update installation instructions`

- **Additional Guidelines:**
   - Keep the subject line concise (preferably under 50 characters).
   - Include a longer description in the commit body if needed.

---

## 4. Pull Requests & Code Reviews

- **Always Open a Pull Request (PR):**  
   - When your feature or fix is ready, open a PR to merge your branch into `main`.

- **Review Process:**
   - At least one other team member should review the PR.
   - Ensure tests pass and code style guidelines are met.
   - Link related issues in the PR description.

- **Merge Strategy:**
   - **Prefer Squash Merging:** Keeps a clean history by consolidating commits.
   - **Rebase Regularly:** Keep your branch up-to-date with the base branch to avoid conflicts.

---

## 5. Additional Best Practices

- **Keep Commits Atomic:**  
   - Each commit should represent a single logical change.

- **Descriptive PR Titles and Descriptions:**  
   - Use clear titles and detailed descriptions to help others understand the purpose of the changes.

- **Document Your Workflow:**  
   - New team members should refer to these guidelines to get up to speed quickly.

---
