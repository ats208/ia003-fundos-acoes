import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import norm
import streamlit as st
from comum import iniciar, carregar, grafico, num, pct, pp, intervalo, intervalo_pp, data_br, json_arquivo, DADOS, NOMES

j = iniciar('Painel 3 — Inferência')
pop, amostra, ind, res = carregar(j)
st.write(f"Quatro hipóteses bilaterais, com α = {num(res['alfa'] * 100, 0)}%: duas de proporção (P1 e P2) e duas de média (M1, uma média, e M2, a diferença entre duas médias).")
st.info(f"Um IC de {num(res['dimensionamento']['confianca'] * 100, 0)}% usa um método que cobre o parâmetro em {num(res['dimensionamento']['confianca'] * 100, 0)}% das amostras repetidas, sob as condições do método. Não é uma probabilidade de {num(res['dimensionamento']['confianca'] * 100, 0)}% atribuída ao parâmetro fixo neste intervalo.")
st.write('Quando n/N > 10%, o IC principal usa a correção finita √((N−n)/(N−1)). Os testes usam o erro padrão sem correção, como no livro-texto. Isso deixa o teste um pouco mais exigente: se ele rejeita H0 sem a correção, rejeitaria também com ela. Wilson e bootstrap são análises de robustez sem correção finita. O M2 (dois grupos, teste de Welch) não usa correção finita.')
m2 = res['hipoteses'].get('M2', {})
conf = num(res['dimensionamento']['confianca'] * 100, 0)
param = ['**Por que esses parâmetros**',
         f"- **p₀ = {num(res['hipoteses'].get('P1', {}).get('p0', 0.5), 1)} nas hipóteses de proporção (P1 e P2):** bater o índice seria \"cara ou coroa\", isto é, sem habilidade. Se metade dos fundos vence, o resultado é compatível com acaso.",
         f"- **μ₀ = {num(res['hipoteses'].get('M1', {}).get('mu0', 0), 0)} na hipótese de média (M1):** o fundo médio só empata com o índice; um excesso médio diferente de zero indica vantagem ou desvantagem sistemática."]
if 'condicao_a' in m2:
    param += [f"- **Diferença = {num(m2['mu0'], 0)} no M2:** compara dois grupos independentes da amostra, público geral e investidor qualificado, no mesmo excesso sobre o Ibovespa. Diferença zero significa que os dois grupos rendem o mesmo, em média. O público profissional fica de fora porque a pergunta compara só esses dois públicos.",
              f"- **Teste t de Welch no M2:** os dois grupos não precisam ter a mesma variância (desvios padrão da amostra: {pct(m2['condicao_a']['s'])} no público geral e {pct(m2['condicao_b']['s'])} no qualificado). O erro padrão soma a variância de cada grupo e os graus de liberdade vêm da fórmula de Welch."]
st.markdown('\n'.join(param))
# Pergunta de cada hipótese, no formato do teste (o empate é a hipótese nula).
PERGUNTAS = {'P1': 'Metade dos fundos supera o Ibovespa?', 'P2': 'Metade dos fundos supera o CDI?', 'M1': 'O excesso médio sobre o Ibovespa é zero (empate com o índice)?', 'M2': 'O excesso médio sobre o Ibovespa é igual no público geral e no qualificado?'}
ROTULOS_IC = {'ic_wald_fpc': 'Wald, com correção para população finita', 'ic_t_fpc': 't, com correção para população finita', 'ic_wald': 'Wald, sem correção para população finita', 'ic_t': 't, sem correção para população finita', 'ic_wilson': 'Wilson', 'ic_bootstrap': 'bootstrap', 'ic_welch': 'Welch'}


def pvalor_txt(p): return '< 0,0001' if p < 0.0001 else num(p, 4)


def bloco_m2(h, c, amostra, ident):
    ga, gb = h['grupo_a'], h['grupo_b']
    ca, cb = h['condicao_a'], h['condicao_b']
    col = h['coluna_grupo']
    st.write(f"Variável: {NOMES.get(h['variavel'], h['variavel'])}. Parâmetro: μ({ga}) − μ({gb}). H₀: diferença = {num(h['mu0'], 0)}; H₁: diferença ≠ {num(h['mu0'], 0)}; α = {pct(h['alfa'])}. Teste t de Welch (variâncias diferentes), com graus de liberdade de Welch.")
    fora = ', '.join(f"{num(v, 0)} {k.lower()}" for k, v in h['n_fora_por_categoria'].items())
    st.write(f"Só a amostra entra na inferência. Grupos: {ga} (n = {num(h['n_a'], 0)}) e {gb} (n = {num(h['n_b'], 0)}). Ficam fora deste teste {num(h['n_fora_do_teste'], 0)} fundos da amostra ({fora}).")
    st.write(f"Médias da amostra: {ga} = {pct(h['media_a'])}; {gb} = {pct(h['media_b'])}. Diferença estimada: {pp(h['diferenca'])}; IC {conf}% (Welch): {intervalo_pp(h['ic_welch'])}.")
    st.write(f"Estatística t = {num(h['t'], 4)}; gl de Welch = {num(h['gl'], 2)}; valor-p = {pvalor_txt(h['valor_p'])}; decisão: {h['decisao']}.")
    st.write('Correção de população finita: não aplicada neste teste.')
    cond = h['condicoes']
    st.write(f"{'✓' if cond['ok'] else '✗'} Condições: n de cada grupo ≥ {num(cond['n_minimo_por_grupo'], 0)} e, em cada grupo, normalidade aproximada ou n grande. Regra: {cond['regra']}.")
    colunas = st.columns(2)
    for coluna, nome, cg in zip(colunas, (ga, gb), (ca, cb)):
        with coluna:
            sw = pvalor_txt(cg['shapiro_p']) if cg['shapiro_p'] is not None else 'não calculado'
            st.write(f"**{nome}:** {'✓' if cg['n_ao_menos_30'] else '✗'} n = {num(cg['n'], 0)}; assimetria = {num(cg['assimetria'], 3)}; mínimo sugerido = {num(cg['n_minimo_sugerido'])}; p de Shapiro = {sw}; {'✓' if cg['n_grande'] else '✗'} n grande.")
            v = pd.to_numeric(amostra.loc[amostra[col] == nome, h['variavel']], errors='coerce').dropna().to_numpy()
            grafico(px.histogram(x=v * 100, nbins=30, labels={'x': 'Excesso (%)', 'y': 'Frequência'}, title=f'Histograma da amostra: {nome}'))
    dfg = amostra[amostra[col].isin([ga, gb])].assign(valor=lambda d: pd.to_numeric(d[h['variavel']], errors='coerce') * 100)
    fig = px.box(dfg, x=col, y='valor', color=col, points='outliers', category_orders={col: [ga, gb]}, title=f'Box plot da amostra: {ga} × {gb}', labels={'valor': 'Excesso sobre o Ibovespa (%)', col: ''})
    fig.update_layout(showlegend=False)
    grafico(fig)
    st.caption('As caixas mostram a mediana e os 50% centrais de cada grupo. Quando elas se sobrepõem quase por inteiro, a diferença entre os grupos é pequena perto da dispersão dentro de cada um.')
    st.write(f"Na população: média {ga} ={pct(c['media_a_populacao'])} (N = {num(c['n_a_populacao'], 0)}); média {gb} = {pct(c['media_b_populacao'])} (N = {num(c['n_b_populacao'], 0)}). Diferença real: {pp(c['valor_populacao'])}")
    st.write(f"IC cobriu o valor real: {'sim' if c['ic_cobriu'] else 'não'}. Decisão do teste: {c['decisao_teste']}; população: {c['decisao_populacao']}; {c['veredito']}. A decisão do teste {'bate' if (c['decisao_teste'] == 'rejeita H0') == c['decisao_populacao'].startswith('H0 falsa') else 'não bate'} com o que a população diz.")


linhas = []
for ident in ['P1', 'P2', 'M1', 'M2']:
    h = res['hipoteses'].get(ident, {})
    c = res['comparacao'].get(ident, {})
    st.subheader(f"{ident} — {PERGUNTAS.get(ident, h.get('pergunta', 'PREENCHER'))}")
    if not h or 'ic_principal' not in h or not c:
        st.warning('Resultado pendente: PREENCHER.'); continue
    if h['tipo'] == 'diferenca_medias':
        bloco_m2(h, c, amostra, ident)
        linhas.append({'Hipótese': ident, 'População': pp(c['valor_populacao']), 'Estimativa': pp(c['estimativa']), 'IC principal': intervalo_pp(h[h['ic_principal']]), 'Cobriu?': 'Sim' if c['ic_cobriu'] else 'Não', 'Teste': c['decisao_teste'], 'População vs H₀': c['decisao_populacao'], 'Veredito': c['veredito']})
        continue
    prop = h['tipo'] == 'proporcao'
    simbolo, zero = ('p', num(h['p0'], 1)) if prop else ('μ', num(h['mu0'], 0))
    st.write(f"Variável: {NOMES.get(h['variavel'], h['variavel'])}. H₀: {simbolo} = {zero}; H₁: {simbolo} ≠ {zero}; α = {pct(h['alfa'])}.")
    st.write(f"Estimativa: {pct(c['estimativa'])}; valor real da população: {pct(c['valor_populacao'])}; IC principal {conf}% ({ROTULOS_IC.get(h['ic_principal'], h['ic_principal'])}): {intervalo(h[h['ic_principal']])}.")
    chave = 'z' if prop else 't'
    pvalor = h['valor_p']
    st.write(f"Estatística {chave} = {num(h[chave], 4)}" + (f"; gl = {num(h['gl'], 0)}" if not prop else '') + f"; valor-p = {pvalor_txt(pvalor)}; decisão: {h['decisao']}.")
    alternativas = ['ic_wald', 'ic_wilson'] if prop else ['ic_t', 'ic_bootstrap']
    st.write('Outros métodos de intervalo, para conferir se o resultado se mantém: ' + ' · '.join(f'{ROTULOS_IC[ch]}: {intervalo(h[ch])}' for ch in alternativas if h.get(ch)))
    cond = h['condicoes']; sinal = '✓' if cond['ok'] else '✗'
    if prop:
        st.write(f"{sinal} Condição: n·p₀ = {num(cond['n_p0'])} e n·(1−p₀) = {num(cond['n_1_menos_p0'])}; ambos devem ser ≥ {num(cond['minimo'], 0)}.")
    else:
        shapiro = pvalor_txt(h['shapiro_p'])
        st.write(f"{sinal} Condição da média: {'✓' if cond['aprox_normal_shapiro'] else '✗'} normalidade pelo Shapiro-Wilk; {'✓' if cond['n_grande'] else '✗'} n grande. n = {num(h['n'], 0)}, mínimo sugerido = {num(cond['n_minimo_sugerido'])}, assimetria = {num(h['assimetria'], 3)}, p de Shapiro = {shapiro}. Regra: {cond['regra']}.")
        valores = pd.to_numeric(amostra[h['variavel']], errors='coerce').dropna().sort_values().to_numpy()
        grafico(px.histogram(x=valores * 100, nbins=40, labels={'x': 'Excesso (%)', 'y': 'Frequência'}, title='Histograma da amostra'))
        # Quantis normais teóricos padronizados; gráfico diagnóstico, sem novo teste.
        q = norm.ppf((pd.Series(range(len(valores))) + 0.5) / len(valores))
        fig = go.Figure(go.Scatter(x=q, y=valores * 100, mode='markers', name='Observações'))
        # Reta de referência: onde os pontos ficariam se os dados fossem normais (média e desvio padrão da amostra).
        fig.add_trace(go.Scatter(x=q, y=(valores.mean() + valores.std(ddof=1) * q) * 100, mode='lines', name='Normal de referência', line=dict(color='red', dash='dash')))
        fig.update_layout(title='Q-Q plot normal', xaxis_title='Quantis normais teóricos', yaxis_title='Quantis observados (%)')
        grafico(fig)
        if cond['aprox_normal_shapiro']:
            st.write('Leitura: os pontos ficam perto da reta, então os dados são aproximadamente normais, e o teste t vale diretamente.')
        else:
            st.write(f"Leitura: nas pontas, os pontos se afastam da reta. Os dados de cada fundo não seguem uma normal (assimetria e caudas pesadas), e o Shapiro-Wilk confirma. Mesmo assim, com n = {num(h['n'], 0)}, o Teorema Central do Limite garante que a média da amostra tem distribuição aproximadamente normal. Por isso o teste t é válido.")
    st.write(f"IC cobriu o valor real: {'sim' if c['ic_cobriu'] else 'não'}. População: {c['decisao_populacao']}; {c['veredito']}.")
    linhas.append({'Hipótese': ident, 'População': pct(c['valor_populacao']), 'Estimativa': pct(c['estimativa']), 'IC principal': intervalo(h[h['ic_principal']]), 'Cobriu?': 'Sim' if c['ic_cobriu'] else 'Não', 'Teste': c['decisao_teste'], 'População vs H₀': c['decisao_populacao'], 'Veredito': c['veredito']})
st.subheader('Comparação das hipóteses')
st.dataframe(pd.DataFrame(linhas), hide_index=True)
st.subheader('Simulação de amostras')
st.write('As estimativas variam entre amostras. A cobertura é a fração dos intervalos simulados que contêm o valor populacional conhecido; não garante cobertura em cada amostra individual.')
for ident, s in res.get('simulacao', {}).items():
    if not s.get('estimativas'): continue
    dif = s['tipo'] == 'diferenca_medias'
    st.markdown(f'**{ident} — {num(s["repeticoes"], 0)} amostras**')
    fig = px.histogram(x=[x*100 for x in s['estimativas']], nbins=35, labels={'x': 'Diferença estimada (p.p.)' if dif else 'Estimativa (%)', 'y': 'Frequência'})
    fig.add_vline(x=s['parametro_populacao']*100, line_color='red', line_dash='dash', annotation_text='População')
    grafico(fig)
    if dif: st.write(f"Cobertura do IC de Welch (sem correção finita): {num(s['cobertura_sem_correcao_pct'])}%. Amostras em que o teste rejeita H₀: {num(s['rejeicao_h0_pct'])}%.")
    else: st.write(f"Cobertura sem correção finita: {num(s['cobertura_sem_correcao_pct'])}%; com correção: {num(s['cobertura_com_correcao_pct'])}%.")
st.subheader('Limitações')
st.warning('Sobrevivência: a seleção usa situação cadastral atual e exige cota nas duas pontas. Um único benchmark é aplicado a todos os fundos. A cota é líquida de custos do fundo, mas não representa todos os custos e tributos do investidor. Cada análise usa uma janela, não generaliza a outros períodos. FIC e fundo investido podem representar duas vezes a mesma estratégia.')
def nota_erro_tipo2(ident, tamanho):
    c, sm = res['comparacao'].get(ident, {}), res['simulacao'].get(ident, {})
    if c.get('veredito', '').startswith('erro tipo II') and sm:
        alfa, y = res['alfa'] * 100, sm['rejeicao_h0_pct']
        if y <= 2 * alfa:
            corpo = f"Mas ela é muito pequena ({tamanho(c)}): com uma diferença desse tamanho, o teste rejeita H₀ em só {num(y, 1)}% das amostras, quase o mesmo que o nível de {num(alfa, 0)}%."
        else:
            corpo = f"Ela é de {tamanho(c)}: com uma diferença desse tamanho, o teste rejeita H₀ em {num(y, 1)}% das amostras, bem acima do nível de {num(alfa, 0)}%, mas ainda deixa de rejeitar na maior parte delas."
        st.info(f"{ident}, janela {j}. Tecnicamente é um erro tipo II, porque a diferença real não é zero. {corpo} Diferença estatística e diferença que importa na prática não são a mesma coisa.")
nota_erro_tipo2('P1', lambda c: f"{pp(abs(c['valor_populacao'] - res['hipoteses']['P1']['p0']))}, de {pct(res['hipoteses']['P1']['p0'])} para {pct(c['valor_populacao'])}")
nota_erro_tipo2('M2', lambda c: pp(c['valor_populacao']))
if j == '2026':
    mov = json_arquivo(DADOS / 'ibov_movimentos.json')['2026']['maior_queda']
    no_dia = int((pop['data_maior_salto'] == mov['data']).sum())
    st.info(f"Movimentos fortes de mercado em poucos dias pesam no resultado da janela: a maior queda diária do Ibovespa foi de {pct(mov['variacao'])} em {data_br(mov['data'])} (de {num(mov['de'], 0)} para {num(mov['para'], 0)} pontos). Para {num(100 * no_dia / len(pop), 2)}% dos fundos da população, esse foi o dia de maior variação da cota na janela.")
