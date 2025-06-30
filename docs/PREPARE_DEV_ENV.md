## Development

### Requirements

- Python >=3.12
- Poetry
- Pre-commit
- Docker

### Setup Instructions

After cloning the repository, follow these steps to set up your development environment:

1. **Install Python and Poetry**

   Make sure you have Python 3.12 or higher installed.  
   Install [Poetry](https://python-poetry.org/docs/#installation) if you haven't already.

2. **Install Dependencies**

   In the project root directory, run:

   ```
   poetry install --no-root
   ```

   This will install all dependencies specified in `pyproject.toml`.

3. **Install and run pre-commit Hooks**

   Install pre-commit and set up the hooks:

   ```
   poetry add --group dev pre-commit
   ```

   Setup and run the pre-commit hooks
   ```
   poetry run pre-commit install
   poetry run pre-commit run --all-files
   ```

   This ensures code quality checks run automatically before each commit.

4. **Copy and Configure Environment Variables**

   Copy the example environment file and adjust as needed:

   ```
   cp .env.example app/core/.env
   ```

   Edit `.env` to set up your local configuration (database, secrets, etc).

5. **Set Up the Database**

   You can use Docker to run a local database, or connect to your own instance.  
   For advanced auditing capabilities (required for the application), follow the instructions in [DATABASE_SETUP.md](./DATABASE_SETUP.md) to set up PostgreSQL with pgaudit using Docker.

   Seed the database with initial data and a super-admin user

   ./seed_db.sh <username> <email> <password>


6. **Run the Application**

   Start the development server:

   ```
   ./dev_start_app.sh
   ```

7. ** Run Tests**

   To run the test suite:

   ```
   ./run_all_tests.sh
   ```

You're now ready to start developing!
