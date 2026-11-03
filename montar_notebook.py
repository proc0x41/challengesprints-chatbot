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
    celulas.extend([
        markdown('''## 2. Preparação sem vazamento e comparação dos dois modelos

Separamos os municípios em treino (60%), validação (20%) e teste (20%), com semente 42 e estratificação pela grande região. A região só preserva representação nas partições; não entra no cálculo de distâncias. Não há divisão temporal: o único ano ambiental disponível é 2023.

Aplicamos `log1p` a densidade, pontos de entrega por mil habitantes e massa de resíduos, por suas caudas longas; percentuais preservam a escala original até a padronização. `StandardScaler` aprende médias e desvios somente do treino. Não excluímos valores extremos legítimos.

**K-Means** é a referência simples baseada em distância a centros. **Gaussian Mixture** permite covariâncias completas e grupos com formatos distintos. Ambos possuem `predict`, útil para a API. Comparamos k de 2 a 6. Para evitar selecionar partições com um grupo residual, exigimos convergência e pelo menos 2% da validação em cada grupo, um critério de projeto definido antes da avaliação.

Selecionamos pela maior silhouette na validação. Também relatamos Davies-Bouldin (menor é melhor) e Calinski-Harabasz (maior é melhor). Essas são métricas internas de geometria, não acurácia nem utilidade comprovada das missões. Silhouette favorece grupos compactos, o que pode favorecer K-Means; não é uma avaliação neutra de todos os objetivos possíveis.'''),
        codigo(codigo_modulo('modelagem.py')),
        markdown('''## 3. Perfis e regras auditáveis

Os nomes dos grupos descrevem suas médias observadas, sem inventar rótulos sociais. Os limiares de 30% para cobertura seletiva, 5% para recuperação, 1 kg/habitante/dia e 50% para disposição inadequada são **heurísticas de projeto**, não parâmetros aprendidos ou padrões oficiais. São pontos de partida a validar com especialistas e usuários.

A presença de PEV no perfil não garante sua existência em cada município. A API filtra missões de entrega voluntária quando o indicador municipal informado é zero. Endereços, materiais aceitos e funcionamento precisam de confirmação local.'''),
        codigo(codigo_modulo('recomendacoes.py')),
        markdown('''## 4. Treinamento, teste reservado e serialização

Cada família fixa seu k pela validação antes de consultar o teste. O vencedor geral também é escolhido apenas pela validação. Depois de avaliar esses pipelines no teste, reajustamos somente o vencedor em toda a base para disponibilização. As métricas de teste não são atribuídas ao reajuste final.

O único arquivo `.joblib` inclui pipeline, perfis, regras, versões, hash da base e catálogo dos indicadores municipais. Isso permite usar a API com somente os quatro arquivos da entrega, sem CSV externo. Carregue apenas o modelo produzido por este projeto e de origem confiável.'''),
        codigo(codigo_modulo('treinar.py')),
        codigo('''dados, tabela, artefato = executar_treinamento()
display(tabela.round(5))
display(pd.DataFrame(artefato['metricas']['finalistas_teste']).T)
print('Partições:', artefato['metricas']['particao'])
print('Selecionado pela validação:', artefato['modelo'], '| k =', artefato['k'])'''),
        codigo('''perfis = pd.DataFrame({grupo: {
    'municipios': perfil['municipios'], **perfil['medias']
} for grupo, perfil in artefato['perfis'].items()}).T
display(perfis.round(3))
display(pd.DataFrame(artefato['regras']))'''),
        markdown('''## 5. Visualização exploratória

PCA em duas dimensões é usado apenas para visualizar o reajuste na base completa. Sobreposição ou separação no gráfico não substitui as métricas do teste, nem comprova relevância das missões. Os números de grupo são identificadores arbitrários e podem mudar em um novo treinamento.'''),
        codigo('''import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

valores = artefato['pipeline'].named_steps['preparo'].transform(dados[FEATURES])
pca = PCA(n_components=2, random_state=SEMENTE)
projecao = pca.fit_transform(valores)
grupos = artefato['pipeline'].predict(dados[FEATURES])
figura, eixo = plt.subplots(figsize=(9, 5))
for grupo in sorted(np.unique(grupos)):
    mascara = grupos == grupo
    eixo.scatter(projecao[mascara, 0], projecao[mascara, 1], s=10, alpha=0.45, label=f'Grupo {grupo}')
eixo.set(xlabel='Componente principal 1', ylabel='Componente principal 2', title='Contextos municipais: projeção exploratória')
eixo.legend(ncol=2)
figura.tight_layout()
plt.show()
print('Variância explicada pelas duas componentes:', round(pca.explained_variance_ratio_.sum(), 4))'''),
        markdown('''## 6. Reabertura do modelo e API REST completa

O código abaixo é o conteúdo integral de `api.py`. A API carrega o modelo uma vez na inicialização, valida entradas e nunca chama `fit` durante uma requisição. A inicialização do servidor fica protegida pelo bloco `__main__`; os exemplos seguintes usam o cliente de testes do Flask.

Rotas: `GET /saude`, `GET /modelo`, `GET /municipios/<codigo_ibge>` e `POST /prever`. O POST recebe somente `codigo_ibge` textual de sete dígitos ou `indicadores` contendo exatamente as oito features. Erros de domínio retornam 422, município ausente 404 e artefato indisponível 503.'''),
        codigo(codigo_modulo('api.py')),
        codigo("API_CODIGO = " + repr((PASTA / 'api.py').read_text(encoding='utf-8')) + "\nPath('api.py').write_text(API_CODIGO, encoding='utf-8')\nprint('api.py gerado com o código completo mostrado nesta célula.')"),
        codigo('''reaberto = joblib.load('modelo_alpha4.joblib')
assert np.array_equal(reaberto['pipeline'].predict(dados[FEATURES]), artefato['pipeline'].predict(dados[FEATURES]))
namespace = {'__name__': 'alpha4_api_notebook', '__file__': str(Path('api.py').resolve())}
exec(compile(API_CODIGO, 'api.py', 'exec'), namespace)
cliente = namespace['app'].test_client()
resposta = cliente.post('/prever', json={'codigo_ibge': '1100015'})
assert resposta.status_code == 200
display(resposta.json)
assert cliente.post('/prever', json={'indicadores': {}}).status_code == 422
print('Modelo reaberto e previsão HTTP validados sem retreinar.')'''),
        markdown('''## 7. Discussão dos resultados e limites

Os números e perfis calculados acima devem ser interpretados como contexto ambiental municipal. O agrupamento não produz um rótulo verdadeiro de “melhor missão”. A associação a categorias vem das regras auditáveis, e não de aprendizado de preferências individuais.

- Os dados declarados podem conter extremos e erros não detectados; a transformação logarítmica reduz influência, mas não garante eliminar esse problema.
- A base contém apenas municípios respondentes válidos e usa 2023 como referência ambiental. Não inferimos indicadores ausentes de municípios não representados.
- A partição aleatória por região não mede generalização temporal ou para estados inteiramente novos.
- Há somente uma divisão com semente fixa e uma faixa pequena de k. O vencedor é o melhor entre esses candidatos, não um ótimo global comprovado.
- Não há avaliação humana das recomendações, teste A/B, dado de missão aceita ou evidência causal de mudança de hábitos. Esses são próximos passos, junto de atualização da base.
- Nenhuma missão deve incentivar manipular resíduos perigosos ou entrar em áreas de descarte.

Referências técnicas: [avaliação de agrupamentos scikit-learn](https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation), [misturas gaussianas](https://scikit-learn.org/stable/modules/mixture.html) e [testes Flask](https://flask.palletsprojects.com/en/stable/testing/).'''),
    ])
    notebook = nbf.v4.new_notebook(cells=celulas, metadata={
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
        'language_info': {'name': 'python', 'version': '3.12.14'},
    })
    nbf.write(notebook, PASTA / 'Alpha4_Modelos.ipynb')


if __name__ == '__main__':
    montar_notebook()
