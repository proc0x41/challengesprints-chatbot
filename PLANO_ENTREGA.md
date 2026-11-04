# Alpha4: aceite da entrega de IA

Fonte: `ChatBot.md` fornecido pelo grupo. Identidades: `Alpha4_Sprint3.pdf`. Base e dicionário da Sprint 3 fornecidos pelo grupo. Projetos frontend e IA independentes.

| Exigência | Evidência atual |
|---|---|
| Dois modelos treinados | Notebook executado: K-Means e Gaussian Mixture, dez candidatos reais |
| Base da Sprint 3 | CSV de 4.775 municípios × 31 colunas; cópia exata compactada no notebook com SHA-256 |
| Discussão em Markdown | Notebook: comparação numérica, perfis, justificativas, acertos/limitações e ausência de rótulos reais |
| Arquivo do modelo | `modelo_alpha4.joblib`, pipeline K-Means vencedor e dados de suporte |
| API REST | `api.py` independente, GET e POST, validações, carregamento único sem fit por requisição |
| Integrantes e explicações | `integrantes.txt`, cinco nomes/RMs/turma e guia completo de execução |
| Quatro arquivos exatos | `preparar_entrega.py` cria `entrega/` e ZIP, valida notebook, integridade e API isolada |
| Código simples e legível | Módulos pequenos separados por responsabilidade; API standalone |
| Dependências reproduzíveis | `requirements.txt`, lock completo e versões mínimas de execução em `integrantes.txt` |
| GitFlow e rodízio | `main`, `develop`, `feature/modelos`; identidades locais alternadas e commits convencionais em português |
| Revisão independente | Ainda será realizada por outro agente antes da conclusão |
| Publicação remota | Destino da IA não informado; nenhuma publicação realizada |

O melhor candidato pela validação foi K-Means k=6; a silhouette do teste reservado foi 0,22938, contra 0,13455 do GMM k=3. Esses valores são métricas geométricas internas modestas, não eficácia das missões. O vencedor foi reajustado na base completa somente depois da avaliação. Regras de recomendação são heurísticas auditáveis separadas do modelo.

O script de empacotamento não apaga arquivos extras encontrados em `entrega/`: solicita movê-los para evitar perda de trabalho. A pasta deve conter somente os quatro arquivos pedidos.

A aprovação de modelos e stack foi dada pelo usuário: K-Means + Gaussian Mixture, scikit-learn e API Flask. Não foram inventados dados, rótulos ou métricas de engajamento.
