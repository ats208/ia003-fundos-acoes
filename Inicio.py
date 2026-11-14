import pandas as pd
import streamlit as st
from comum import iniciar, carregar, csv, num, NOMES, QUANT, DADOS, json_arquivo, config, data_br

j = iniciar('Fundos de ações × Ibovespa')
pop, amostra, ind, res = carregar(j)
st.header('Os fundos de ações batem o Ibovespa e o CDI?')
st.write('O Ibovespa mede a bolsa; o CDI, a renda fixa sem risco de bolsa. A pergunta é quantos fundos superam cada um e, em média, por quanto ficam acima ou abaixo do Ibovespa.')
st.write('Comparamos a população observada com uma amostra aleatória simples, para avaliar como a inferência se aproxima dos valores conhecidos da população. Cada fundo entra com um valor por variável na janela; não analisamos uma série temporal no painel.')
st.subheader('Fontes e contexto')
st.markdown('[CVM — informe diário](https://dados.cvm.gov.br/dataset/fi-doc-inf_diario) e [cadastro](https://dados.cvm.gov.br/dataset/fi-cad) (dados abertos, ODbL) · [Banco Central — CDI, série 12](https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json) · [B3 — Ibovespa](https://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/ibovespa.htm) · [Yahoo Finance (^BVSP)](https://finance.yahoo.com/quote/%5EBVSP/history/)')
st.caption('Ibovespa: fechamentos diários do Yahoo Finance (^BVSP), conferidos nas estatísticas históricas da B3.')
cfg = config()
cob = num(cfg['populacao']['cobertura_minima_fim'] * 100, 0)
if j == '2026':
    periodo = f"A janela vai de {data_br(ind['data_ini'])} a {data_br(ind['data_fim'])}, o último dia em que pelo menos {cob}% dos fundos já tinham informado a cota."
else:
    periodo = f"A janela vai de {data_br(ind['data_ini'])} a {data_br(ind['data_fim'])}, do último dia de cota de 2024 ao último de 2025."
st.write(f"{periodo} O Ibovespa usa {data_br(ind['ibov_data_ini_usada'])} (último pregão antes do início) e {data_br(ind['ibov_data_fim_usada'])}. A janela de 2025 serve de comparação.")
st.subheader('Recorte e funil')
bruta = json_arquivo(DADOS / 'base_bruta.json')
inf, cad = bruta['informe_diario'], bruta['cadastro']
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
def mes_ano(aaaamm): return f"{MESES[int(aaaamm[4:]) - 1]}/{aaaamm[:4]}"
st.markdown('**Tamanho da base bruta**')
c1, c2, c3, c4 = st.columns(4)
c1.metric('Arquivos mensais do informe', num(inf['arquivos_mensais'], 0))
c2.metric('Linhas do informe', num(inf['linhas'], 0))
c3.metric('Colunas do informe', num(inf['colunas'], 0))
c4.metric('Fundos distintos no informe', num(inf['classes_distintas'], 0))
st.write(f"Informe diário da CVM, de {mes_ano(inf['primeiro_mes'])} a {mes_ano(inf['ultimo_mes'])}: {num(inf['arquivos_mensais'], 0)} arquivos mensais, {num(inf['linhas'], 0)} linhas, {num(inf['colunas'], 0)} colunas e {num(inf['classes_distintas'], 0)} fundos distintos (todos os fundos do Brasil, não só de ações).")
st.write(f"Cadastro da CVM: {num(cad['registro_classe']['classes_distintas'], 0)} fundos registrados e {num(cad['registro_classe']['colunas'], 0)} colunas. O cadastro antigo (cad_fi), usado como complemento, tem {num(cad['cad_fi']['classes_distintas'], 0)} fundos e {num(cad['cad_fi']['colunas'], 0)} colunas.")
st.write(f"A base bruta tem {num(inf['linhas'] / 1e6, 1)} milhões de linhas; a população é o recorte de fundos de ações, como pediu a professora para bases grandes.")
st.write(f"Fundos de ações em funcionamento normal, não exclusivos, com cota nas duas pontas e PL final de pelo menos R$ {num(cfg['populacao']['pl_minimo'] / 1e6, 0)} milhão. Exclusividade não informada permanece no recorte. A situação é a atual do cadastro.")
st.caption('Fundo, neste trabalho, é a classe de cotas do cadastro da CVM (Resolução CVM 175): cada uma tem CNPJ, carteira e cota próprios. As subclasses, que dividem a mesma carteira, não são contadas à parte.')
funil = csv(f'funil_{j}.csv')
tab_funil = funil[~funil.etapa.astype(str).str.startswith('info')].fillna('').astype(str).rename(columns={'etapa': 'Etapa', 'filtro': 'Filtro', 'antes': 'Antes', 'depois': 'Depois', 'removidas': 'Removidas'})
# Só exibição: datas no formato brasileiro e texto do filtro de exclusividade (o CSV não muda).
tab_funil['Filtro'] = (tab_funil['Filtro']
    .str.replace("Não exclusiva (exclui só 'S'; vazio fica)", 'Não exclusivo (exclusividade não informada permanece)', regex=False)
    .str.replace('>=', '≥', regex=False)
    .str.replace(r'(\d{4})-(\d{2})-(\d{2})', r'\3/\2/\1', regex=True))
st.dataframe(tab_funil, hide_index=True)
sumiram = funil.loc[funil.etapa == 'info_sumiram_pop', 'depois'].iloc[0]
st.write(f'{num(sumiram, 0)} fundos elegíveis tinham cota no início e não tinham na data final; isso não prova encerramento.')
st.write(f'População observada: {num(len(pop), 0)} fundos. Unidade amostral: o fundo (CNPJ). Amostra: {num(len(amostra), 0)} fundos. Há {num(len(NOMES), 0)} variáveis analisadas, descritas abaixo.')
st.subheader('Dicionário de variáveis')
desc = ['Cota final / cota inicial − 1', 'Retorno menos Ibovespa', 'PL na data final', 'Sim se excesso sobre Ibovespa > 0', 'Sim se o retorno superou o CDI acumulado na janela', 'Público-alvo do cadastro', 'FIC ou direto, aproximação pelo cadastro']
st.dataframe(pd.DataFrame([{'Variável': k, 'Nome': v, 'Tipo': 'Quantitativa' if i < len(QUANT) else 'Qualitativa', 'Definição': desc[i]} for i,(k,v) in enumerate(NOMES.items())]), hide_index=True)
st.info('**Nota sobre os tipos de fundos:** A **Estrutura** indica se o fundo compra ações no mercado (*direto*) ou se compra cotas de outros fundos (*FIC*). O **Público-alvo** reflete a exigência do fundo: *Público Geral* atende investidores comuns do varejo; *Qualificado* atende quem tem mais de R$ 1 milhão investido; e *Profissional* destina-se a bancos, instituições e investidores com mais de R$ 10 milhões.')
