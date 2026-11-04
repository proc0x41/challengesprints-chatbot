# Verificação da entrega de IA

Verificações executadas em 03/11/2026, antes da revisão independente:

- Dois modelos realmente treinados sobre a base recebida. Dez candidatos comparados, com partições disjuntas de 2.865/955/955 municípios.
- Pré-processamento de cada candidato ajustado somente no treino. Escolha pela validação; teste reservado para avaliar os finalistas fixados.
- 12 testes automatizados passaram: base, partições, normalização, serialização, seleção, regras e rotas. Casos HTTP incluem código válido/inválido, indicador ausente, NaN, infinito, inteiro de 401 dígitos, tipo incorreto, conteúdo malformado, corpo excessivo e modelo ausente.
- Previsões de todas as 4.775 linhas executadas a partir do artefato reaberto. Nenhuma chamada a `Pipeline.fit` permitida no teste de consulta GET/POST.
- Notebook validado por nbformat, com 12 células de código executadas e sem erro. Nenhum import dos módulos locais de modelagem/dados/recomendação.
- Reprodução adicional em uma pasta temporária inicialmente contendo somente os quatro arquivos: o notebook restaurou o CSV embutido, retreinou os modelos, gerou o artefato e verificou a API.
- Servidor Flask real iniciado nessa pasta isolada: GET saúde 200, POST previsão 200 e POST inválido 422. Processo encerrado após a verificação.
- API também verificada em cópia isolada antes de restaurar o CSV, usando somente o modelo e `api.py`.
- Gráfico PCA inspecionado visualmente: título, eixos e legenda legíveis. A projeção mostra sobreposição e é descrita como exploratória.
- `pip check` passou no ambiente local.
- ZIP validado com `testzip()`, quatro nomes exatos e tamanho inferior a 1 MB. Pasta `entrega/` contém notebook, modelo, API e explicações.
- Identidades Git locais conferidas por e-mail; grafia de Thiago Shimizu Sodré dos Santos corrigida para UTF-8. Mínimo de cinco commits relevantes por integrante atingido.

O `.gitattributes` preserva os bytes do CSV original e evita que conversões de fim de linha no checkout invalidem sua verificação SHA-256. O arquivo serializado foi regenerado pela execução final do notebook; suas métricas e previsões foram novamente conferidas.

A revisão por outro agente ainda é necessária antes de considerar o trabalho concluído. Não houve publicação remota nem submissão ao portal acadêmico.
