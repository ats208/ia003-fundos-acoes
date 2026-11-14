from pathlib import Path
import datetime
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yaml

RAIZ = Path(__file__).resolve().parent
DADOS = RAIZ / 'dados' / 'processados'
QUANT = ['ret', 'exc_ibov', 'pl_fim']
EM_PERCENTUAL = ['ret', 'exc_ibov']
QUAL = ['bateu_ibov', 'bateu_cdi', 'publico_alvo', 'estrutura']
NOMES = {'ret': 'Retorno', 'exc_ibov': 'Excesso sobre o Ibovespa', 'pl_fim': 'Patrimônio líquido final (R$)', 'bateu_ibov': 'Bateu o Ibovespa', 'bateu_cdi': 'Bateu o CDI', 'publico_alvo': 'Público-alvo', 'estrutura': 'Estrutura'}


def num(x, casas=2):
    if x is None or pd.isna(x): return 'PREENCHER'
    return f'{x:,.{casas}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def pct(x): return num(x * 100) + '%'
def pp(x, casas=2): return num(x * 100, casas) + ' p.p.'
def intervalo(v): return '[' + '; '.join(pct(x) for x in v) + ']'
def intervalo_pp(v): return '[' + '; '.join(pp(x) for x in v) + ']'


def data_br(d):
    if isinstance(d, (datetime.date, datetime.datetime)): return d.strftime('%d/%m/%Y')
    d = str(d or '').strip()
    if not d: return 'PREENCHER'
    try: return datetime.date.fromisoformat(d[:10]).strftime('%d/%m/%Y')
    except ValueError: return d


def config():
    with open(RAIZ / 'config.yaml', encoding='utf-8') as f: return yaml.safe_load(f)


@st.cache_data
def csv(nome): return pd.read_csv(DADOS / nome, dtype={'cnpj': str})


@st.cache_data
def json_arquivo(caminho):
    with open(caminho, encoding='utf-8') as f: return json.load(f)


def iniciar(titulo):
    st.set_page_config(page_title=titulo, layout='wide')
    janela = st.sidebar.selectbox('Janela', ['2026', '2025'], key='janela')
    st.sidebar.caption('Uma observação por fundo.')
    st.title(titulo)
    return janela


def carregar(j):
    try:
        return csv(f'populacao_{j}.csv'), csv(f'amostra_{j}.csv'), json_arquivo(DADOS / 'indices.json')[j], json_arquivo(RAIZ / 'saida' / f'resultados_{j}.json')
    except (FileNotFoundError, KeyError, ValueError) as e:
        st.error(f'Dados indisponíveis para {j}: {e}. PREENCHER.')
        st.stop()


def grafico(fig):
    fig.update_layout(separators=',.', legend_title_text='', margin=dict(t=45, b=30))
    st.plotly_chart(fig, use_container_width=True)


def cartoes(df, ind, amostra=False):
    cols = st.columns(4)
    for c, (nome, valor) in zip(cols, [('n' if amostra else 'N', num(len(df), 0)), ('PL total', 'R$ ' + num(df.pl_fim.sum())), ('Ibovespa na janela', pct(ind['ibov_ret'])), ('CDI na janela', pct(ind['cdi_acumulado']))]): c.metric(nome, valor)


def analises(pop, ind, amostra=None):
    atual = pop if amostra is None else amostra
    cartoes(atual, ind, amostra is not None)
    st.subheader('Distribuições quantitativas')
    for var in ['ret', 'exc_ibov']:
        frames = [pd.DataFrame({'valor': pop[var], 'Grupo': 'População'})]
        if amostra is not None: frames.append(pd.DataFrame({'valor': amostra[var], 'Grupo': 'Amostra'}))
        df = pd.concat(frames, ignore_index=True)
        # Retornos em percentuais; frequência relativa permite comparar tamanhos distintos.
        df['valor'] = df['valor'] * 100
        fig = px.histogram(df, x='valor', color='Grupo', barmode='overlay', opacity=0.6, histnorm='probability', nbins=60, title=NOMES[var], labels={'valor': 'Valor (%)', 'probability': 'Proporção'})
        if var == 'ret':
            refs = sorted([(ind['ibov_ret'] * 100, 'Ibovespa'), (ind['cdi_acumulado'] * 100, 'CDI')])
            for (x, nome), pos in zip(refs, ['top left', 'top right']): fig.add_vline(x=x, line_dash='dash', line_color='red', annotation_text=nome, annotation_position=pos)
        else:
            fig.add_vline(x=0, line_dash='dash', line_color='red', annotation_text='Zero')
        grafico(fig)
    st.subheader('Box plots: centro, dispersão e valores extremos')
    for var in ['ret', 'exc_ibov']:
        frames = [pd.DataFrame({'valor': pop[var] * 100, 'Grupo': 'População'})]
        if amostra is not None: frames.append(pd.DataFrame({'valor': amostra[var] * 100, 'Grupo': 'Amostra'}))
        df = pd.concat(frames, ignore_index=True)
        fig = px.box(df, x='Grupo', y='valor', color='Grupo', points='outliers', title=NOMES[var], labels={'valor': 'Valor (%)', 'Grupo': ''})
        fig.update_layout(showlegend=False)
        grafico(fig)
    st.caption('A linha dentro da caixa é a mediana. A caixa vai do 1º ao 3º quartil (os 50% centrais dos fundos). Os bigodes vão até 1,5 vez a distância entre os quartis, e os pontos além deles são valores extremos. Como os extremos puxam a média, as tabelas mostram a média e a mediana.')
    st.subheader('Distribuição de patrimônio líquido')
    escala = st.radio('Escala do eixo horizontal', ['Logarítmica', 'Normal'], horizontal=True, key='escala_pl')
    for var in ['pl_fim']:
        frames = [pd.DataFrame({'valor': pop[var], 'Grupo': 'População'})]
        if amostra is not None: frames.append(pd.DataFrame({'valor': amostra[var], 'Grupo': 'Amostra'}))
        df = pd.concat(frames, ignore_index=True)
        rotulos = {'valor': NOMES[var], 'probability': 'Proporção'}
        if escala == 'Logarítmica':
            # Histograma de log10(valor), com rótulos em potências de 10; PL é positivo na base.
            df = df[df['valor'] > 0].assign(valor=lambda d: np.log10(d['valor']))
            fig = px.histogram(df, x='valor', color='Grupo', barmode='overlay', opacity=0.6, histnorm='probability', nbins=40, title=NOMES[var] + ' (escala logarítmica)', labels=rotulos)
            lo, hi = int(np.floor(df['valor'].min())), int(np.ceil(df['valor'].max()))
            ticks = list(range(lo, hi + 1))
            fig.update_xaxes(tickvals=ticks, ticktext=[num(10.0 ** k, 0) for k in ticks])
        else:
            fig = px.histogram(df, x='valor', color='Grupo', barmode='overlay', opacity=0.6, histnorm='probability', nbins=60, title=NOMES[var] + ' (escala normal)', labels=rotulos)
        grafico(fig)
    st.caption('Na escala logarítmica cada divisão do eixo é 10 vezes a anterior; as barras agrupam fundos por ordem de grandeza. Na escala normal, poucos fundos muito grandes concentram a maior parte das barras na primeira faixa.')
    st.subheader('Variáveis qualitativas: frequência e proporção')
    for var in QUAL:
        partes = []
        for nome, df in ([('População', pop)] if amostra is None else [('População', pop), ('Amostra', amostra)]):
            freq = df[var].fillna('Não informado').astype(str).value_counts(dropna=False)
            partes.extend({'Grupo': nome, 'Categoria': k, 'Frequência': int(v), 'Proporção (%)': 100*v/len(df)} for k,v in freq.items())
        tab = pd.DataFrame(partes)
        st.markdown('**' + NOMES[var] + '**')
        grafico(px.bar(tab, x='Categoria', y='Proporção (%)', color='Grupo', barmode='group', hover_data=['Frequência']))
        st.dataframe(tab.assign(**{'Proporção (%)': tab['Proporção (%)'].map(num)}), hide_index=True)
    st.subheader('Estatísticas descritivas')
    linhas = []
    for var in QUANT:
        for grupo, df in ([('População', pop)] if amostra is None else [('População', pop), ('Amostra', amostra)]):
            s = pd.to_numeric(df[var], errors='coerce').dropna()
            f = (lambda x: num(x * 100) + '%') if var in EM_PERCENTUAL else num
            linhas.append({'Variável': NOMES[var], 'Grupo': grupo, 'Média': f(s.mean()), 'Mediana': f(s.median()), 'Desvio padrão': f(s.std()), '1º quartil': f(s.quantile(.25)), '3º quartil': f(s.quantile(.75)), 'Mínimo': f(s.min()), 'Máximo': f(s.max())})
    st.caption('Retornos e excessos em percentual; PL em reais.')
    st.dataframe(pd.DataFrame(linhas), hide_index=True)
    if amostra is not None:
        st.subheader('População × amostra × diferença')
        linhas = []
        for v in QUANT:
            p, a = pop[v].mean(), amostra[v].mean()
            if v in EM_PERCENTUAL: linhas.append({'Indicador': NOMES[v] + ' — média', 'População': pct(p), 'Amostra': pct(a), 'Diferença (amostra − população)': pp(a - p)})
            else: linhas.append({'Indicador': NOMES[v] + ' — média', 'População': num(p, 2), 'Amostra': num(a, 2), 'Diferença (amostra − população)': num(a - p, 2)})
        for v in QUAL:
            categorias = sorted(set(pop[v].fillna('Não informado').astype(str)) | set(amostra[v].fillna('Não informado').astype(str)))
            for cat in categorias:
                p = (pop[v].fillna('Não informado').astype(str) == cat).mean()
                a = (amostra[v].fillna('Não informado').astype(str) == cat).mean()
                linhas.append({'Indicador': f'{NOMES[v]}: {cat} — proporção', 'População': pct(p), 'Amostra': pct(a), 'Diferença (amostra − população)': num((a-p)*100) + ' p.p.'})
        st.dataframe(pd.DataFrame(linhas), hide_index=True)
