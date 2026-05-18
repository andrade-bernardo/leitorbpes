from database import db


class Viagem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    data = db.Column(db.String(20), nullable=False)

    linha_codigo = db.Column(db.String(20), nullable=False)
    linha_nome = db.Column(db.String(150), nullable=False)

    horario_saida = db.Column(db.String(20), nullable=True)
    horario_chegada = db.Column(db.String(20), nullable=True)

    veiculo = db.Column(db.String(50), nullable=True)
    motorista = db.Column(db.String(100), nullable=True)

    passageiros = db.Column(db.Integer, nullable=True)
    receita = db.Column(db.Float, nullable=True)

    observacoes = db.Column(db.Text, nullable=True)


class VendaBPe(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    chave_bpe = db.Column(db.String(80), unique=True, nullable=False)
    numero_bpe = db.Column(db.String(30), nullable=True)
    serie = db.Column(db.String(20), nullable=True)

    data_emissao = db.Column(db.String(30), nullable=True)
    data_viagem = db.Column(db.String(30), nullable=True)

    origem = db.Column(db.String(100), nullable=True)
    destino = db.Column(db.String(100), nullable=True)

    percurso = db.Column(db.String(150), nullable=True)
    prefixo = db.Column(db.String(30), nullable=True)
    poltrona = db.Column(db.String(20), nullable=True)
    plataforma = db.Column(db.String(20), nullable=True)

    valor_pago = db.Column(db.Float, nullable=True)
    forma_pagamento = db.Column(db.String(50), nullable=True)

    agencia = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(100), nullable=True)