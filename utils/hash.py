import hashlib

def validar_algoritmo(algoritmo):
    if algoritmo != "sha256":
        raise ValueError(f"Algoritmo de hash não suportado: {algoritmo}")

def calcular_hash_conteudo(conteudo, algoritmo):
    validar_algoritmo(algoritmo)
    return hashlib.new(algoritmo, conteudo).hexdigest()

def calcular_sha256(caminho, algoritmo):
    validar_algoritmo(algoritmo)
    hash_arquivo = hashlib.new(algoritmo)

    with caminho.open("rb") as arquivo:
        bloco = arquivo.read(8192)
        while bloco:
            hash_arquivo.update(bloco)
            bloco = arquivo.read(8192)

    return hash_arquivo.hexdigest()