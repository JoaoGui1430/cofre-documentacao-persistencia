from contextlib import contextmanager
from core.repositorio import trava


@contextmanager
def operacao_armazenamento():
    with trava:
        yield