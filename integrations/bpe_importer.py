import xml.etree.ElementTree as ET


NAMESPACE = {"bpe": "http://www.portalfiscal.inf.br/bpe"}


def pegar_texto(raiz, caminho):
    elemento = raiz.find(caminho, NAMESPACE)
    if elemento is not None and elemento.text is not None:
        return elemento.text.strip()
    return ""


def ler_bpe_xml(caminho_arquivo):
    tree = ET.parse(caminho_arquivo)
    raiz = tree.getroot()

    inf_bpe = raiz.find(".//bpe:infBPe", NAMESPACE)

    if inf_bpe is None:
        raise ValueError("Arquivo XML inválido: não foi encontrada a tag infBPe.")

    id_bpe = inf_bpe.attrib.get("Id", "")
    chave_bpe = id_bpe.replace("BPe", "")

    dados = {
        "chave_bpe": chave_bpe,
        "numero_bpe": pegar_texto(raiz, ".//bpe:ide/bpe:nBP"),
        "serie": pegar_texto(raiz, ".//bpe:ide/bpe:serie"),
        "data_emissao": pegar_texto(raiz, ".//bpe:ide/bpe:dhEmi"),
        "data_viagem": pegar_texto(raiz, ".//bpe:infViagem/bpe:dhViagem"),
        "origem": pegar_texto(raiz, ".//bpe:infPassagem/bpe:xLocOrig"),
        "destino": pegar_texto(raiz, ".//bpe:infPassagem/bpe:xLocDest"),
        "percurso": pegar_texto(raiz, ".//bpe:infViagem/bpe:xPercurso"),
        "prefixo": pegar_texto(raiz, ".//bpe:infViagem/bpe:prefixo"),
        "poltrona": pegar_texto(raiz, ".//bpe:infViagem/bpe:poltrona"),
        "plataforma": pegar_texto(raiz, ".//bpe:infViagem/bpe:plataforma"),
        "valor_pago": pegar_texto(raiz, ".//bpe:infValorBPe/bpe:vPgto"),
        "forma_pagamento": pegar_texto(raiz, ".//bpe:pag/bpe:xPag"),
        "agencia": pegar_texto(raiz, ".//bpe:agencia/bpe:xNome"),
        "status": pegar_texto(raiz, ".//bpe:protBPe/bpe:infProt/bpe:xMotivo"),
    }

    try:
        dados["valor_pago"] = float(dados["valor_pago"]) if dados["valor_pago"] else 0.0
    except ValueError:
        dados["valor_pago"] = 0.0

    return dados