import sqlite3
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from pathlib import Path
import urllib.parse

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
EXCEL_PATH = BASE_DIR / "data" / "ListaPresentes.xlsx"
DB_PATH = BASE_DIR / "database.db"
ADMIN_KEY = "acesso_admin"

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
            cores TEXT,
            escolhido_por TEXT
        )
    """)

    conn.commit()
    conn.close()

def sincronizar_presentes_excel():
    conn = get_db()
    cursor = conn.cursor()

    # garante unicidade
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_presente_unique
        ON presentes(presente)
    """)

    df = pd.read_excel(EXCEL_PATH).fillna("")

    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO presentes (presente, link1, link2, cores)
                VALUES (?, ?, ?, ?)
            """, (
                row["Presentes"],
                row["Sugestão 1"],
                row["Sugestão 2"],
                row["Cores"]
            ))
        except sqlite3.IntegrityError:
            # presente já existe → ignora
            pass

    conn.commit()
    conn.close()

@app.route("/escolher", methods=["POST"])
def escolher():
    presente_id = request.form["presente_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE presentes
        SET escolhido_por = 'Presente Escolhido'
        WHERE id = ? AND escolhido_por IS NULL
    """, (presente_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("index"))

@app.route("/admin/desfazer/<int:presente_id>", methods=["POST"])
def desfazer(presente_id):
    if request.args.get("admin") != ADMIN_KEY:
        return "Acesso negado", 403

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE presentes
        SET escolhido_por = NULL
        WHERE id = ?
    """, (presente_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("index", admin=ADMIN_KEY))

@app.route("/")
def index():
    is_admin = request.args.get("admin") == ADMIN_KEY

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM presentes")
    presentes = cursor.fetchall()

    conn.close()

    return render_template("index.html", presentes=presentes, is_admin=is_admin)

criar_tabela()
sincronizar_presentes_excel()

if __name__ == "__main__":
    app.run()
