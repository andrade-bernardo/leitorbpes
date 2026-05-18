import os

from flask import Flask, render_template, request, redirect, url_for, session

from database import db
from models import Viagem, VendaBPe
from integrations.bpe_importer import ler_bpe_xml


app = Flask(__name__)
app.secret_key = "chave_secreta_sistema_passageiros"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sistema_passageiros.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

db.init_app(app)


USUARIO_PADRAO = "admin"
SENHA_PADRAO = "1234"


linhas_rodoviarias = [
    {"codigo": "8", "origem": "Bagé", "destino": "Caçapava do Sul", "via": "Lavras do Sul"},
    {"codigo": "10", "origem": "Bagé", "destino": "São Gabriel", "via": "Dom Pedrito"},
    {"codigo": "26", "origem": "Cachoeira do Sul", "destino": "Caçapava do Sul", "via": ""},
    {"codigo": "568", "origem": "Uruguaiana", "destino": "Santiago", "via": ""},
    {"codigo": "579", "origem": "Uruguaiana", "destino": "São Borja", "via": ""},
    {"codigo": "621", "origem": "Uruguaiana", "destino": "Rio Grande", "via": "Bagé"},
    {"codigo": "802", "origem": "Bagé", "destino": "São Borja", "via": "Livramento / Uruguaiana"},
    {"codigo": "1121", "origem": "Uruguaiana", "destino": "Rio Grande", "via": "BR-290 / BR-392"},
    {"codigo": "1166", "origem": "Cachoeira do Sul", "destino": "Bagé", "via": "Caçapava do Sul"},
    {"codigo": "1504", "origem": "Santana do Livramento", "destino": "Caxias do Sul", "via": ""},
    {"codigo": "1606", "origem": "Cachoeira do Sul", "destino": "Bagé", "via": ""},
    {"codigo": "1928", "origem": "Santana do Livramento", "destino": "Caxias do Sul", "via": "Bagé"},
    {"codigo": "2023", "origem": "Itaqui", "destino": "Santiago", "via": ""},
    {"codigo": "2644", "origem": "Caçapava do Sul", "destino": "Bagé", "via": ""},
]


def buscar_linha_por_codigo(codigo):
    for linha in linhas_rodoviarias:
        if linha["codigo"] == codigo:
            return linha
    return None


@app.route("/", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")

        if usuario == USUARIO_PADRAO and senha == SENHA_PADRAO:
            session["usuario"] = usuario
            return redirect(url_for("dashboard"))

        erro = "Usuário ou senha inválidos."

    return render_template("login.html", erro=erro)


@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))

    total_linhas = len(linhas_rodoviarias)

    total_viagens = Viagem.query.count()
    total_passageiros = db.session.query(db.func.sum(Viagem.passageiros)).scalar() or 0
    total_receita_viagens = db.session.query(db.func.sum(Viagem.receita)).scalar() or 0

    total_bpes = VendaBPe.query.count()
    total_receita_bpe = db.session.query(db.func.sum(VendaBPe.valor_pago)).scalar() or 0

    return render_template(
        "dashboard.html",
        total_linhas=total_linhas,
        total_viagens=total_viagens,
        total_passageiros=total_passageiros,
        total_receita=total_receita_viagens,
        total_bpes=total_bpes,
        total_receita_bpe=total_receita_bpe,
    )


@app.route("/linhas")
def linhas():
    if "usuario" not in session:
        return redirect(url_for("login"))

    return render_template("linhas.html", linhas=linhas_rodoviarias)


@app.route("/viagens", methods=["GET", "POST"])
def viagens():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        data = request.form.get("data")
        linha_codigo = request.form.get("linha")
        horario_saida = request.form.get("saida")
        horario_chegada = request.form.get("chegada")
        veiculo = request.form.get("veiculo")
        motorista = request.form.get("motorista")
        passageiros = request.form.get("passageiros")
        receita = request.form.get("receita")
        observacoes = request.form.get("observacoes")

        linha = buscar_linha_por_codigo(linha_codigo)

        if linha:
            linha_nome = f'{linha["codigo"]} - {linha["origem"]} x {linha["destino"]}'
        else:
            linha_nome = "Linha não informada"

        nova_viagem = Viagem(
            data=data,
            linha_codigo=linha_codigo,
            linha_nome=linha_nome,
            horario_saida=horario_saida,
            horario_chegada=horario_chegada,
            veiculo=veiculo,
            motorista=motorista,
            passageiros=int(passageiros) if passageiros else 0,
            receita=float(receita) if receita else 0,
            observacoes=observacoes,
        )

        db.session.add(nova_viagem)
        db.session.commit()

        return redirect(url_for("viagens"))

    viagens_cadastradas = Viagem.query.order_by(Viagem.id.desc()).all()

    return render_template(
        "viagens.html",
        linhas=linhas_rodoviarias,
        viagens=viagens_cadastradas,
    )


@app.route("/importar-bpe", methods=["GET", "POST"])
def importar_bpe():
    if "usuario" not in session:
        return redirect(url_for("login"))

    mensagem = None
    erro = None

    if request.method == "POST":
        arquivos = request.files.getlist("arquivos_xml")

        if not arquivos or arquivos[0].filename == "":
            erro = "Selecione pelo menos um arquivo XML."
        else:
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

            importados = 0
            duplicados = 0
            erros = 0

            for arquivo in arquivos:
                if arquivo.filename == "":
                    continue

                if not arquivo.filename.lower().endswith(".xml"):
                    erros += 1
                    continue

                caminho_arquivo = os.path.join(app.config["UPLOAD_FOLDER"], arquivo.filename)
                arquivo.save(caminho_arquivo)

                try:
                    dados = ler_bpe_xml(caminho_arquivo)

                    venda_existente = VendaBPe.query.filter_by(
                        chave_bpe=dados["chave_bpe"]
                    ).first()

                    if venda_existente:
                        duplicados += 1
                        continue

                    nova_venda = VendaBPe(
                        chave_bpe=dados["chave_bpe"],
                        numero_bpe=dados["numero_bpe"],
                        serie=dados["serie"],
                        data_emissao=dados["data_emissao"],
                        data_viagem=dados["data_viagem"],
                        origem=dados["origem"],
                        destino=dados["destino"],
                        percurso=dados["percurso"],
                        prefixo=dados["prefixo"],
                        poltrona=dados["poltrona"],
                        plataforma=dados["plataforma"],
                        valor_pago=dados["valor_pago"],
                        forma_pagamento=dados["forma_pagamento"],
                        agencia=dados["agencia"],
                        status=dados["status"],
                    )

                    db.session.add(nova_venda)
                    importados += 1

                except Exception:
                    erros += 1

            db.session.commit()

            mensagem = (
                f"Importação concluída: {importados} XML(s) importado(s), "
                f"{duplicados} duplicado(s) e {erros} com erro."
            )

    vendas = VendaBPe.query.order_by(VendaBPe.id.desc()).all()

    total_vendas = VendaBPe.query.count()
    total_receita = db.session.query(db.func.sum(VendaBPe.valor_pago)).scalar() or 0

    return render_template(
        "importar_bpe.html",
        vendas=vendas,
        mensagem=mensagem,
        erro=erro,
        total_vendas=total_vendas,
        total_receita=total_receita,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)