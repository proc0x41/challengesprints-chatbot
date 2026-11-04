"""Empacota somente os quatro arquivos exigidos e verifica a API fora do repo."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import nbformat

PASTA = Path(__file__).resolve().parent
ARQUIVOS = ['Alpha4_Modelos.ipynb', 'modelo_alpha4.joblib', 'api.py', 'integrantes.txt']


def preparar_entrega():
    notebook = nbformat.read(PASTA / ARQUIVOS[0], as_version=4)
    nbformat.validate(notebook)
    for celula in notebook.cells:
        if celula.cell_type == 'code':
            assert celula.execution_count is not None, 'Notebook precisa estar executado.'
            assert all(saida.output_type != 'error' for saida in celula.outputs)
    destino = PASTA / 'entrega'
    destino.mkdir(exist_ok=True)
    extras = {item.name for item in destino.iterdir()} - set(ARQUIVOS)
    if extras:
        raise ValueError(f'Preserve os arquivos extras em outra pasta antes de empacotar: {sorted(extras)}')
    for nome in ARQUIVOS:
        shutil.copy2(PASTA / nome, destino / nome)
    with tempfile.TemporaryDirectory(prefix='alpha4-entrega-') as temporaria:
        for nome in ARQUIVOS:
            shutil.copy2(destino / nome, Path(temporaria) / nome)
        verificacao = '''
from pathlib import Path
import api
assert Path(api.__file__).parent == Path.cwd()
assert not Path('alpha4_sinisa_ibge_municipios.csv').exists()
cliente = api.app.test_client()
assert cliente.get('/saude').status_code == 200
resposta = cliente.post('/prever', json={'codigo_ibge': '1100015'})
assert resposta.status_code == 200 and resposta.json['recomendacoes']
assert cliente.post('/prever', json={'indicadores': {}}).status_code == 422
print('API isolada funciona sem CSV ou módulos do repositório.')
'''
        subprocess.run([sys.executable, '-c', verificacao], cwd=temporaria, check=True)
    arquivo_zip = PASTA / 'Alpha4_IA_Sprint4.zip'
    with zipfile.ZipFile(arquivo_zip, 'w', compression=zipfile.ZIP_DEFLATED) as pacote:
        for nome in ARQUIVOS:
            pacote.write(destino / nome, arcname=nome)
    with zipfile.ZipFile(arquivo_zip) as pacote:
        assert sorted(pacote.namelist()) == sorted(ARQUIVOS)
        assert pacote.testzip() is None
    hashes = {nome: hashlib.sha256((destino / nome).read_bytes()).hexdigest() for nome in ARQUIVOS}
    print('Quatro arquivos verificados:', json.dumps(hashes, indent=2))
    print('ZIP válido:', arquivo_zip.name, '| bytes:', arquivo_zip.stat().st_size)


if __name__ == '__main__':
    preparar_entrega()
