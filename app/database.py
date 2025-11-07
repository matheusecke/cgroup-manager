import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = "/var/lib/cgroup-manager/database.db"

def get_connection():
    """Retorna uma conexão com o banco SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
    return conn

def init_db():
    """Inicializa o banco de dados criando a tabela se não existir"""
    # Criar diretório se não existir
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            cpu_limit REAL NOT NULL,
            memory_mb INTEGER NOT NULL,
            io_weight INTEGER NOT NULL,
            script_content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            process_id INTEGER
        )
    """)
    
    conn.commit()
    conn.close()

def insert_environment(name, cpu_limit, memory_mb, io_weight, script_content, process_id):
    """Insere um novo ambiente no banco e retorna o id gerado"""
    conn = get_connection()
    cursor = conn.cursor()
    
    created_at = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO environments 
        (name, status, cpu_limit, memory_mb, io_weight, script_content, created_at, process_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, "RUNNING", cpu_limit, memory_mb, io_weight, script_content, created_at, process_id))
    
    # Pegar o ID gerado automaticamente
    env_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return env_id

def get_all_environments():
    """Retorna todos os ambientes como lista de dicionários"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM environments ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    conn.close()
    
    # Converter para lista de dicionários
    environments = []
    for row in rows:
        env = dict(row)
        environments.append(env)
    
    return environments

def get_environment(env_id):
    """Retorna um ambiente específico pelo env_id (número)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM environments WHERE id = ?", (env_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        env = dict(row)
        return env
    return None

def update_status(env_id, status):
    """Atualiza o status de um ambiente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE environments SET status = ? WHERE id = ?", (status, env_id))
    
    conn.commit()
    conn.close()

def update_process_id(env_id, process_id):
    """Atualiza o PID de um ambiente"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE environments SET process_id = ? WHERE id = ?", 
                  (process_id, env_id))
    
    conn.commit()
    conn.close()

def delete_environment(env_id):
    """Remove um ambiente do banco"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM environments WHERE id = ?", (env_id,))
    
    conn.commit()
    conn.close()
