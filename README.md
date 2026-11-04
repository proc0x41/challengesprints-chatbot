# Alpha4: recomendação de missões para a Soul Up

Dois modelos de agrupamento usam indicadores de resíduos de 4.775 municípios para orientar categorias de missões sustentáveis. Projeto independente do frontend, sem previsão de engajamento individual.

## Entrega e uso

`python preparar_entrega.py` prepara **exatamente quatro arquivos** em `entrega/` e o ZIP correspondente: notebook executado, modelo treinado, `api.py` e `integrantes.txt`. A base original está no notebook; o catálogo municipal está no modelo. A API funciona sem os demais módulos do repositório.

Instalação, endpoints, exemplos, resultados, limitações, fontes e integrantes estão em [integrantes.txt](integrantes.txt). Para usar o modelo entregue, instale suas dependências e inicie `api.py`; não precisa treinar novamente.

## Desenvolvimento

Python 3.12, NumPy, pandas, scikit-learn, Flask e joblib. No PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe api.py
```

Para reproduzir o notebook a partir dos módulos:

```powershell
.venv/Scripts/python.exe treinar.py
.venv/Scripts/python.exe montar_notebook.py
.venv/Scripts/python.exe executar_notebook.py
.venv/Scripts/python.exe preparar_entrega.py
```

No Linux/macOS use `.venv/bin/python`. `requirements.txt` fixa dependências diretas; `requirements-lock.txt` registra o ambiente executado.

## Organização

| Arquivo | Responsabilidade |
|---|---|
| `dados.py` | Leitura, validação e oito features |
| `modelagem.py` | Partições, pipelines e comparação |
| `recomendacoes.py` | Perfis e regras auditáveis |
| `treinar.py` | Treinamento offline e serialização |
| `api.py` | API Flask independente, sem treino por requisição |
| `Alpha4_Modelos.ipynb` | Código autocontido, execução e discussão |
| `metricas.json`, `perfis_grupos.json` | Evidências dos resultados |
| `tests/` | Dados, prevenção de vazamento, artefato e HTTP |
| `preparar_entrega.py` | Pacote dos quatro arquivos e verificação isolada |

## Resultados e limites

K-Means k=6 venceu pela validação. Silhouette no teste reservado: **0,22938**, contra **0,13455** do Gaussian Mixture k=3. São métricas internas modestas, sem equivalência com taxa de acerto de missões. O notebook discute perfis, sobreposição, extremos, viés e ausência de validação humana.

Missões vêm de heurísticas explícitas separadas do aprendizado. O ano ambiental é 2023; confirme serviços locais.

## Autores, créditos e contato

Vinicius de Oliveira (561862), Robison Custodio Junior (572866), Lucas Fernando Silva (564848), Thiago Shimizu Sodré dos Santos (572867) e Arthur Mendes Garcia (571703), turma 1TDSPW. Contato acadêmico solicitado: `rm{RM}@fiap.com.br`.

Dados e explicação da Sprint 3 fornecidos pelo grupo, com origem SINISA e IBGE. Implementação e verificações assistidas pelo Codex. O rodízio de identidades Git atende à solicitação e não comprova execução manual individual por cada pessoa.

## Versionamento e publicação

GitFlow: `main`, `develop`, `feature/modelos` e `release/v0.1.0`, com Conventional Commits em português. A versão revisada está na tag `v0.1.0`; veja [notas da versão](RELEASE_NOTES.md). Repositório independente: https://github.com/proc0x41/challengesprints-chatbot. Flask inicia localmente em `127.0.0.1:5000`.
