from flask import Flask, render_template
import pandas as pd
from pathlib import Path
import urllib.parse

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
EXCEL_PATH = BASE_DIR / "data" / "ListaPresentes.xlsx"


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


@app.route("/")
def index():
    presentes = carregar_presentes()
    return render_template("index.html", presentes=presentes)


if __name__ == "__main__":
    app.run(debug=True)
