import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def reset_database():
    # Conectar a MySQL sin especificar base de datos
    conn = pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        charset='utf8mb4'
    )

    try:
        with conn.cursor() as cur:
            # Eliminar base de datos si existe
            cur.execute("DROP DATABASE IF EXISTS tienda_canelitos")

            # Crear base de datos nueva
            cur.execute("CREATE DATABASE tienda_canelitos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cur.execute("USE tienda_canelitos")

            # Leer y ejecutar el archivo schema_final.sql
            with open('schema_final.sql', 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Ejecutar cada statement por separado
            statements = sql_content.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cur.execute(statement)
                    except Exception as stmt_error:
                        print(f"Error ejecutando statement: {statement[:100]}...")
                        print(f"Error: {str(stmt_error)}")
                        # Continuar con el siguiente statement
                        continue

        conn.commit()
        print("Base de datos reseteada correctamente con schema_final.sql")

    except Exception as e:
        print(f"Error al resetear la base de datos: {str(e)}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == '__main__':
    reset_database()
