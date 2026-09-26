import os
import mysql.connector
from mysql.connector import Error

# Database connection configuration
# You can change these details or set environment variables if needed
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "your mysql password"),
    "database": os.environ.get("DB_NAME", "hospital_db"),
    "port": int(os.environ.get("DB_PORT", 3306))
}


def get_connection():
    """
    Creates and returns a new MySQL database connection using DB_CONFIG.
    Raises mysql.connector.Error if connection fails.
    """
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn


def get_server_connection():
    """
    Creates and returns a connection to MySQL server without specifying a database.
    Used by db_setup.py to create hospital_db if it does not exist.
    """
    server_config = DB_CONFIG.copy()
    if "database" in server_config:
        del server_config["database"]
    
    conn = mysql.connector.connect(**server_config)
    return conn