import hashlib

def calcular_sha256(caminho, algoritmo):
    if algoritmo != "sha256":
        raise ValueError(f"Algoritmo de hash não suportado: {algoritmo}")
    hash_arquivo = hashlib.new(algoritmo)

    with caminho.open("rb") as arquivo:
        bloco = arquivo.read(8192)
        while bloco:
            hash_arquivo.update(bloco)
            bloco = arquivo.read(8192)

    return hash_arquivo.hexdigest()