"""Executa todas as células no Python atual e só salva se a execução for válida."""

import sys
from pathlib import Path

import nbformat
from jupyter_client import KernelManager
from nbclient import NotebookClient

PASTA = Path(__file__).resolve().parent


def executar(caminho=PASTA / 'Alpha4_Modelos.ipynb'):
    notebook = nbformat.read(caminho, as_version=4)
    gerenciador = KernelManager(kernel_name='python3')
    gerenciador.kernel_spec.argv[0] = sys.executable
    cliente = NotebookClient(
        notebook, km=gerenciador, timeout=600,
        resources={'metadata': {'path': str(Path(caminho).parent)}},
    )
    cliente.execute()
    nbformat.validate(notebook)
    for celula in notebook.cells:
        if celula.cell_type == 'code':
            assert celula.execution_count is not None
            assert not any(saida.output_type == 'error' for saida in celula.outputs)
    nbformat.write(notebook, caminho)
    print('Notebook executado e validado:', Path(caminho).name)


if __name__ == '__main__':
    executar()
