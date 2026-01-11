import sqlite3
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from pathlib import Path
import urllib.parse

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
EXCEL_PATH = BASE_DIR / "data" / "ListaPresentes.xlsx"
DB_PATH = BASE_DIR / "database.db"

def carregar_presentes():
    """
    Lê o Excel e retorna uma lista de dicionários
    """
    df = pd.read_excel(EXCEL_PATH)

    df = df.fillna("")  # evita NaN no HTML

    presentes = []
    for _, row in df.iterrows():
        presentes.append({
            "presente": row["Presentes"],
            "link1": normalizar_link(row["Sugestão 1"]),
            "link2": normalizar_link(row["Sugestão 2"]),
            "cores": row["Cores"]
        })

    return presentes

def normalizar_link(valor):
    """
    Garante que o link seja navegável.
    Se não for URL, transforma em busca no Google.
    """
    if not valor:
        return ""

    valor = str(valor).strip()

    if valor.startswith("http://") or valor.startswith("https://"):
        return valor

    # vira busca no Google
    query = urllib.parse.quote(valor)
    return f"https://www.google.com/search?q={query}"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            presente TEXT,
            link1 TEXT,
            link2 TEXT,
            cores TEXT
        )
    """)

    conn.commit()
    conn.close()

def popular_banco_se_vazio():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM presentes")
    total = cursor.fetchone()[0]

    if total == 0:
        df = pd.read_excel(EXCEL_PATH).fillna("")

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO presentes (presente, link1, link2, cores)
                VALUES (?, ?, ?, ?)
            """, (
                row["Presentes"],
                row["Sugestão 1"],
                row["Sugestão 2"],
                row["Cores"]
            ))

        conn.commit()

    conn.close()

@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM presentes")
    presentes = cursor.fetchall()

    conn.close()

    return render_template("index.html", presentes=presentes)

criar_tabela()
popular_banco_se_vazio()

if __name__ == "__main__":
    app.run(debug=True)
