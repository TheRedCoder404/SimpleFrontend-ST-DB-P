# Scooteq Database Web Interface

A web-based CRUD interface for managing MySQL database tables, built with NiceGUI and Python.

## Features

- Full CRUD operations (Create, Read, Update, Delete) for database tables
- Paginated table views with customizable entries per page
- Smart form fields with dropdowns for foreign keys
- Dark mode with persistent user preferences
- Responsive design with Quasar components
- Docker deployment support

## Quick Start with Docker

### Prerequisites

- Docker
- Docker Compose

### Configuration

1. Navigate to the docker directory:
   ```bash
   cd docker
   ```

2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` to customize your configuration:
   ```bash
   # Database Configuration
   DB_HOST=mysql
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_secure_password_here
   DB_NAME=scooteq_database

   # Application Configuration
   APP_PORT=8081
   STORAGE_SECRET=your_random_secret_key_here
   ```

4. (Optional) If you need to initialize the database with a schema, edit `init.sql`:
   ```bash
   # Uncomment and modify the SQL statements in init.sql
   nano init.sql
   ```

### Deployment

1. From the docker directory, build and start the containers:
   ```bash
   docker-compose up -d
   ```

2. Check the logs to ensure everything started correctly:
   ```bash
   docker-compose logs -f
   ```

3. Access the application at: http://localhost:8081

### Managing the Deployment

- **Stop the containers:**
  ```bash
  docker-compose down
  ```

- **Stop and remove volumes (WARNING: This deletes your database data):**
  ```bash
  docker-compose down -v
  ```

- **Restart the containers:**
  ```bash
  docker-compose restart
  ```

- **View logs:**
  ```bash
  docker-compose logs -f web    # Web application logs
  docker-compose logs -f mysql  # Database logs
  ```

- **Rebuild after code changes:**
  ```bash
  docker-compose up -d --build
  ```

## Local Development (Without Docker)

### Prerequisites

- Python 3.14+
- MySQL 8.0+

### Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure database connection by setting environment variables or editing `database.py`:
   ```bash
   export DB_HOST=localhost
   export DB_PORT=3306
   export DB_USER=root
   export DB_PASSWORD=secret
   export DB_NAME=scooteq_database
   ```

4. Run the application:
   ```bash
   python main.py
   ```

5. Access the application at: http://localhost:8081

## Database Schema

The application expects the following tables:
- `devices` - Device inventory
- `devices_issued` - Device assignment records
- `device_types` - Device type categories
- `departments` - Department information
- `manufacturer` - Manufacturer information
- `employees` - Employee records

See `init.sql` for the complete schema definition.

## Environment Variables

### Database Configuration
- `DB_HOST` - Database hostname (default: localhost)
- `DB_PORT` - Database port (default: 3306)
- `DB_USER` - Database username (default: root)
- `DB_PASSWORD` - Database password (default: secret)
- `DB_NAME` - Database name (default: scooteq_database)

### Application Configuration
- `APP_PORT` - Application port (default: 8081)
- `STORAGE_SECRET` - Secret key for session storage (change in production!)

## Architecture

- **Frontend**: NiceGUI (Python-based web framework)
- **Backend**: Python with MySQL connector
- **Database**: MySQL 8.0
- **Deployment**: Docker + Docker Compose

## File Structure

```
.
├── main.py                    # Main application file with UI logic
├── database.py                # Database connection and operations
├── README.md                  # This file
├── DEVELOPMENT_DIARY.md       # Development progress log
└── docker/                    # Docker deployment files
    ├── Dockerfile             # Docker image definition
    ├── docker-compose.yml     # Docker Compose configuration
    ├── requirements.txt       # Python dependencies
    ├── init.sql              # Database initialization script
    ├── .env.example          # Example environment variables
    └── .dockerignore         # Files to exclude from Docker build
```

## Security Notes

**IMPORTANT**: Before deploying to production:

1. Change `STORAGE_SECRET` to a random, secure value
2. Use a strong `DB_PASSWORD`
3. Consider using Docker secrets instead of environment variables for sensitive data
4. Review and restrict network access to the database
5. Enable SSL/TLS for database connections in production

## Troubleshooting

### Web application can't connect to database

1. Check that the database container is healthy:
   ```bash
   docker-compose ps
   ```

2. Verify the database credentials in `.env`

3. Check the web application logs:
   ```bash
   docker-compose logs web
   ```

### Database data not persisting

Ensure you haven't removed the Docker volume:
```bash
docker volume ls | grep mysql_data
```

### Port already in use

If port 8081 or 3306 is already in use, change the ports in `.env`:
```bash
APP_PORT=8082
DB_PORT=3307
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

## License

MIT License - feel free to use and modify as needed.
