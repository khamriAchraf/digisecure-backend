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

5. **Download the MaxMind GeoLite2 City Database**

   **Note:** The GeoLite2 City database is not included in the repository due to its size and MaxMind's license restrictions. Each developer/server must download it individually.

   - Register for a free MaxMind account: https://www.maxmind.com/en/geolite2/signup
   - Download the latest GeoLite2 City database (`GeoLite2-City.mmdb`) from: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
   - Place the `.mmdb` file in the `data/` directory (or the path specified by `GEOLITE2_DB_PATH` in your `.env`)
   - **Do not commit the `.mmdb` file to git!** It is already included in `.gitignore`.

6. **Set Up the Database**

   You can use Docker to run a local database, or connect to your own instance.  
   For advanced auditing capabilities (required for the application), follow the instructions in [DATABASE_SETUP.md](./DATABASE_SETUP.md) to set up PostgreSQL with pgaudit using Docker.

   Seed the database with initial data and a super-admin user

   ./seed_db.sh <username> <email> <password>


7. **Run the Application**

   Start the development server:

   ```
   ./dev_start_app.sh
   ```

8. ** Run Tests**

   To run the test suite:

   ```
   ./run_all_tests.sh
   ```

You're now ready to start developing!
