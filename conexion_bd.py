import mysql.connector
from mysql.connector import Error
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno desde .env

def get_connection():
    try:
        connection = mysql.connector.connect(
            host='192.168.56.101',
            database='importaciones_sim_db',
            user='pythonapp',
            password='inacap.2024'  
        )
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None