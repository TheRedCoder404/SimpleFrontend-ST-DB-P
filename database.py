import mysql.connector
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import os

class Database:
    """Database connection and operations handler"""

    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'secret'),
            'database': os.getenv('DB_NAME', 'scooteq_database')
        }

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = mysql.connector.connect(**self.config)
        try:
            yield conn
        finally:
            conn.close()

    def get_table_data(self, table_name: str, limit: int = 25, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
        """
        Get paginated data from a table
        Returns: (data, total_count)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Get total count
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            total_count = cursor.fetchone()['count']

            # Get paginated data
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
            data = cursor.fetchall()

            cursor.close()
            return data, total_count

    def get_row_by_id(self, table_name: str, row_id: int) -> Optional[Dict[str, Any]]:
        """Get a single row by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (row_id,))
            data = cursor.fetchone()
            cursor.close()
            return data

    def insert_row(self, table_name: str, data: Dict[str, Any]) -> int:
        """Insert a new row and return the ID"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(data.values()))
            conn.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id

    def update_row(self, table_name: str, row_id: int, data: Dict[str, Any]) -> bool:
        """Update an existing row"""
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE id = %s"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(list(data.values()) + [row_id]))
            conn.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success

    def delete_row(self, table_name: str, row_id: int) -> bool:
        """Delete a row by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (row_id,))
            conn.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success

    def get_table_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get column information for a table"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            cursor.close()
            return columns

    def get_manufacturers(self) -> List[Dict[str, Any]]:
        """Get all manufacturers for dropdown"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name FROM manufacturer ORDER BY name")
            data = cursor.fetchall()
            cursor.close()
            return data

    def get_device_types(self) -> List[Dict[str, Any]]:
        """Get all device types for dropdown"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, device_type FROM device_types ORDER BY device_type")
            data = cursor.fetchall()
            cursor.close()
            return data

    def get_device_type_by_id(self, device_type_id: int) -> Optional[Dict[str, Any]]:
        """Get a device type by ID with specification"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, device_type, specification, description FROM device_types WHERE id = %s", (device_type_id,))
            data = cursor.fetchone()
            cursor.close()
            return data

    def get_departments(self) -> List[Dict[str, Any]]:
        """Get all departments for dropdown"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name FROM departments ORDER BY name")
            data = cursor.fetchall()
            cursor.close()
            return data

    def get_employees(self) -> List[Dict[str, Any]]:
        """Get all employees for dropdown"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, first_name, last_name FROM employees ORDER BY last_name, first_name")
            data = cursor.fetchall()
            cursor.close()
            return data

    def get_employee_by_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Get an employee by ID with their department"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, first_name, last_name, department_id FROM employees WHERE id = %s", (employee_id,))
            data = cursor.fetchone()
            cursor.close()
            return data

    def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices for dropdown"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, model, serial_number FROM devices ORDER BY model")
            data = cursor.fetchall()
            cursor.close()
            return data

    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get devices that are not currently issued"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT d.id, d.model, d.serial_number
                FROM devices d
                WHERE d.id NOT IN (SELECT device_id FROM devices_issued)
                ORDER BY d.model
            """)
            data = cursor.fetchall()
            cursor.close()
            return data
