# Setup Guide for Zambia Digital Hygiene Assessment Tool

## For Development

### Quick Start (5 minutes)

1. **Clone & navigate**

   ```bash
   git clone https://github.com/sakhile-bit/sakhile_final-_year_pro.git
   cd sakhile_final-_year_pro
   ```

2. **Activate virtual environment**

   ```bash
   .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests**

   ```bash
   pytest -q
   ```

5. **Start the app**
   ```bash
   python src/web/app.py
   ```
   Open http://localhost:5000 → Login with `admin` / `admin123`

## For MySQL Production

### Prerequisites

- MySQL 8.0+ running
- MySQL Workbench or mysql CLI tool

### Setup

1. **Create the database**

   ```sql
   CREATE DATABASE digital_hygiene CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **Create a MySQL user (optional but recommended)**

   ```sql
   CREATE USER 'dhassess'@'localhost' IDENTIFIED BY 'SecurePassword123!';
   GRANT ALL PRIVILEGES ON digital_hygiene.* TO 'dhassess'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Set environment variables**

   ```bash
   set DB_HOST=localhost
   set DB_PORT=3306
   set DB_NAME=digital_hygiene
   set DB_USER=dhassess
   set DB_PASSWORD=SecurePassword123!
   set DEBUG=false
   set SECRET_KEY=your-random-secret-key
   ```

4. **Start the application**
   ```bash
   python src/web/app.py
   ```
   The database tables will be created automatically on first run.

## Architecture Overview

```
src/
├── web/
│   ├── app.py              # Flask application and routes
│   └── templates/          # HTML templates
├── assessment/
│   └── assessor.py         # Assessment logic (5 controls)
├── reporting/
│   └── generator.py        # Report generation (HTML/JSON/CSV)
├── database/
│   └── connection.py       # Database models and session management
├── utils/
│   ├── config.py           # Environment-aware configuration
│   └── logging_config.py   # Logging setup
└── tests/
    └── test_web.py         # Web app tests
```

## Key Features

- **5 Security Controls**: OS Updates, Antivirus, Firewall, Password Policy, Backups
- **4 Certification Levels**: Gold (≥80%), Silver (60-79%), Bronze (40-59%), Not Certified (<40%)
- **Multiple Export Formats**: HTML, PDF, JSON, CSV
- **User Authentication**: Login system with role support
- **REST API**: Programmatic assessment access
- **Environment-driven Config**: Easy dev/prod switching

## Testing

```bash
# Run all tests
pytest -q

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src

# Run specific test file
pytest src/tests/test_web.py -v
```

## Troubleshooting

**Issue**: "ModuleNotFoundError: No module named 'mysql'"

- **Solution**: Install MySQL connector: `pip install mysql-connector-python`
- Or use SQLite (default) by omitting `DB_HOST` env var

**Issue**: "Cannot connect to MySQL"

- Verify MySQL is running: `mysql -u root`
- Check credentials in `.env` file
- Ensure database exists: `CREATE DATABASE digital_hygiene;`

**Issue**: Tests fail on Windows

- Run tests with: `.venv\Scripts\python.exe -m pytest`
- Ensure virtual environment is activated

## Support

For issues or questions:

1. Check test output: `pytest -v`
2. Review logs in `logs/app.log`
3. Verify configuration in `.env` or environment variables
