# IA003 - Probabilidade e Estatística: Fundos de Ações × Ibovespa

Este é o aplicativo interativo (painel) desenvolvido como trabalho final da disciplina de Probabilidade e Estatística da Especialização em Inteligência Artificial da UFRGS (2026).

O trabalho investiga empiricamente se os fundos de investimento em ações (FIAs) no Brasil superam o índice de mercado (Ibovespa) e o custo de oportunidade (CDI). Uma base regulatória oficial da CVM é tratada como a **população finita** ($N = 2.691$ fundos) na janela principal de 2026, sendo então extraída uma **Amostra Aleatória Simples** sem reposição ($n = 337$). O painel permite comparar as estimativas amostrais e a inferência estatística completa com os parâmetros verdadeiros da população original.

## Como Rodar Localmente

Certifique-se de ter o Python 3.12 ou 3.13 instalado.

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Execute o aplicativo Streamlit:
   ```bash
   streamlit run Inicio.py
   ```

3. (Opcional) Rode a suíte de testes do app:
   ```bash
   python teste_app.py
   ```

## Variáveis analisadas nos painéis

- **Quantitativas:** `ret`, `exc_ibov`, `pl_fim`.
- **Qualitativas:** `bateu_ibov`, `bateu_cdi`, `publico_alvo`, `estrutura`.

Os CSV de `dados/processados/` mantêm outras colunas, que não aparecem nos painéis.

## Fontes de Dados e Atribuição

- **Fundos de Investimento:** Portal de Dados Abertos da Comissão de Valores Mobiliários (CVM), disponibilizados sob licença **ODbL (Open Data Commons Open Database License)**. Os dados formam a base de todas as análises populacionais e amostrais deste estudo. Informe diário: https://dados.cvm.gov.br/dataset/fi-doc-inf_diario · Cadastro: https://dados.cvm.gov.br/dataset/fi-cad .
- **Ibovespa:** Fechamentos diários do Yahoo Finance (`^BVSP`), conferidos nas [estatísticas históricas da B3](https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-ibovespa-ibovespa-estatisticas-historicas.htm).
- **CDI:** Série temporal (12) extraída do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil (BCB).

## Publicação

Publicar com Python 3.12 ou 3.13 (opções avançadas do Streamlit Community Cloud).
