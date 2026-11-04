# Alpha4 IA v0.1.0

Primeira entrega revisada de recomendação contextual de missões sustentáveis para a Soul Up.

- Base da Sprint 3 preservada: 4.775 municípios e indicadores SINISA 2023/IBGE.
- K-Means e Gaussian Mixture treinados; K-Means k=6 escolhido somente pela validação.
- Notebook autocontido executado, modelo serializado, API Flask independente e explicações em quatro arquivos.
- Validação estrutural do artefato na inicialização; artefatos incompletos respondem 503.
- 13 testes automatizados, reprodução integral em pasta isolada, HTTP real e integridade do ZIP verificados.
- Revisão independente concluída; o único achado de baixa gravidade foi corrigido e coberto por regressão.

Silhouette do teste reservado: 0,22938 para K-Means e 0,13455 para GMM. São métricas internas modestas, não taxa de sucesso das missões. As recomendações usam regras transparentes ainda sem validação humana.

Esta versão é local: não implica publicação remota, implantação pública ou submissão no portal acadêmico. Consulte `integrantes.txt` para execução e `VERIFICACAO.md` para evidências.
