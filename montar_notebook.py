"""Monta um notebook autocontido a partir do código legível do repositório."""

import base64
import gzip
import hashlib
from pathlib import Path

import nbformat as nbf

PASTA = Path(__file__).resolve().parent


def codigo_modulo(nome):
    fonte = (PASTA / nome).read_text(encoding='utf-8')
    linhas = [linha for linha in fonte.splitlines()
              if not linha.startswith(('from dados import ', 'from modelagem import ', 'from recomendacoes import '))]
    return '\n'.join(linhas).split("if __name__ == '__main__':")[0].rstrip()


def montar_notebook():
    codigo, markdown = nbf.v4.new_code_cell, nbf.v4.new_markdown_cell
    base = (PASTA / 'alpha4_sinisa_ibge_municipios.csv').read_bytes()
    compactada = base64.b64encode(gzip.compress(base, mtime=0)).decode('ascii')
    sha256 = hashlib.sha256(base).hexdigest()
    celulas = [
        markdown('''# Alpha4: missões sustentáveis por contexto municipal

**FIAP · Artificial Intelligence & Chatbot · Sprint 4 · Turma 1TDSPW**

Vinicius de Oliveira (561862), Robison Custodio Junior (572866), Lucas Fernando Silva (564848), Thiago Shimizu Sodré dos Santos (572867) e Arthur Mendes Garcia (571703).

O objetivo é **agrupar municípios por indicadores ambientais**, comparando K-Means e Gaussian Mixture. Os grupos orientam categorias de missões da Soul Up por regras explícitas. Não há rótulos de missão aceita, nem previsão de engajamento individual.

A cópia compactada abaixo é o CSV original fornecido pelo grupo, não dados sintéticos. O notebook contém todo o código de preparação, treinamento, avaliação, serialização e API; não precisa dos módulos `.py` do repositório.'''),
        markdown('''## Como executar

Use Python 3.12 e um kernel com as dependências abaixo. Em um terminal, na pasta dos quatro arquivos:

```text
python -m venv .venv
.venv\\Scripts\\python -m pip install numpy==2.5.4 pandas==3.1.0 scikit-learn==1.9.1 Flask==3.1.3 joblib==1.6.0 nbformat==5.11.1 nbclient==0.11.0 ipykernel==7.4.0 matplotlib==3.11.2
```

Selecione esse ambiente no editor de notebooks e execute todas as células, em ordem. Não instale pacotes automaticamente ao executar o notebook. A API já funciona com o modelo entregue, sem executar o treinamento novamente.

Dados: SINISA, ano ambiental 2023, com cadastro municipal do IBGE. Fontes informadas na Sprint 3: [resultados SINISA](https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/saneamento/sinisa/resultados-sinisa) e [API de localidades IBGE](https://servicodados.ibge.gov.br/api/docs/localidades). A base tem viés de resposta municipal e não representa os municípios excluídos por ausência ou inconsistência dos dados.'''),
        codigo(f'''import base64
import gzip
import hashlib
from pathlib import Path

CSV_COMPACTADO = {compactada!r}
SHA256_ESPERADO = {sha256!r}
arquivo = Path('alpha4_sinisa_ibge_municipios.csv')
conteudo = gzip.decompress(base64.b64decode(CSV_COMPACTADO))
assert hashlib.sha256(conteudo).hexdigest() == SHA256_ESPERADO
if arquivo.exists():
    assert hashlib.sha256(arquivo.read_bytes()).hexdigest() == SHA256_ESPERADO, 'CSV local difere da base fornecida; preserve-o em outra pasta antes de executar.'
else:
    arquivo.write_bytes(conteudo)
print('Base original verificada. SHA-256:', SHA256_ESPERADO)''', metadata={'jupyter': {'source_hidden': True}}),
        markdown('''## 1. Base real e qualidade

São 4.775 municípios e 31 colunas. Códigos e nomes são contexto, não medidas de distância. Não usamos os indicadores binários derivados nem o gap entre coberturas, para evitar redundância. Escolhemos oito indicadores numéricos do dicionário. A inspeção de consistência não comprova exatidão dos valores declarados por cada município.'''),
        codigo(codigo_modulo('dados.py')),
        codigo('''from IPython.display import display, Markdown

dados = carregar_dados()
display(dados[['municipio', 'uf', *FEATURES]].head())
display(dados[FEATURES].describe().round(3))
print('Dimensão:', dados.shape)
print('Ausentes:', dados.isna().sum().sum(), '| Códigos duplicados:', dados.codigo_ibge.duplicated().sum())
print('Ano:', dados.ano_referencia_sinisa.unique(), '| UFs:', dados.uf.nunique())'''),
    ]
    notebook = nbf.v4.new_notebook(cells=celulas, metadata={
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.12.14'},
    })
    nbf.write(notebook, PASTA / 'Alpha4_Modelos.ipynb')


if __name__ == '__main__':
    montar_notebook()
