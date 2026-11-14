import streamlit as st
from comum import iniciar, carregar, analises, num, pct
j = iniciar('Painel 2 — Amostra')
pop, amostra, ind, res = carregar(j)
d = res['dimensionamento']
st.subheader('Como a amostra foi dimensionada e sorteada')
st.latex(r'n_0=\frac{z^2p(1-p)}{E^2},\quad n=\left\lceil\frac{n_0}{1+n_0/N}\right\rceil')
st.write(f"Confiança {pct(d['confianca'])}, z = {num(d['z'])}, margem E = {pct(d['margem'])} e p = {num(d['p'])}: proporção conservadora que maximiza o tamanho quando p é desconhecida. n₀ = {num(d['n0'])}; N = {num(res['N'], 0)}; n = {num(res['n'], 0)}; n/N = {pct(res['n_sobre_N'])}; semente = {num(res['semente'], 0)}.")
st.markdown(f"""**Por que esses parâmetros**
- **Confiança de {num(d['confianca'] * 100, 0)}% e margem de {num(d['margem'] * 100, 0)}%:** valores usuais, os mesmos usados em aula. Equilibram precisão e tamanho da amostra: mais confiança ou margem menor exigiriam mais fundos, e menos confiança ou margem maior dariam estimativas pouco informativas. Aqui isso resulta em n = {num(res['n'], 0)} de N = {num(res['N'], 0)} fundos.
- **p = {num(d['p'])} no tamanho da amostra:** a variância p(1−p) é máxima em p = {num(d['p'])}. Como a proporção verdadeira é desconhecida antes da coleta, é a escolha conservadora: o n calculado é suficiente para qualquer proporção real.
- Este p = 0,5 serve só para calcular o tamanho da amostra. Não é a hipótese do P1, que usa o mesmo valor por outro motivo (bater o índice como cara ou coroa).""")
st.write('AAS sem reposição, sobre a população ordenada por CNPJ, com numpy.random.default_rng. Cada fundo tem a mesma chance de seleção; a mesma semente foi usada nas duas janelas.')
analises(pop, ind, amostra)
