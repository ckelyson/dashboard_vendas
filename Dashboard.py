import streamlit as st 
import requests
import pandas as pd
import plotly.express as px 
import locale
st.set_page_config(layout= 'wide')


## Função para formatar valores no formato brasileiro
def formatar_valor(valor):
    if valor >= 1e6:
        valor_formatado = f"R$ {valor / 1:,.2f} "
    else:
        valor_formatado = f"R$ {valor / 1:,.2f} "
    
    # Trocar os separadores das casas decimais para vírgula e os milhares para ponto
    return valor_formatado.replace(',', 'X').replace('.', ',').replace('X', '.')


## Função para formatar a quantidade de vendas
def formatar_quantidade(valor):
    if valor >= 1e6:
        valor_formatado = f"{valor / 1:,.2f} milhões"
    else:
        valor_formatado = f"{valor / 1:,.2f} mil"
    return valor_formatado.replace(',', 'X').replace('.', ',').replace('X', '.')



st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''
    
todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao':regiao.lower(), 'ano':ano}
response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

# Formatação das métricas
receita = formatar_valor(dados['Preço'].sum())
quantidade_vendas = formatar_quantidade(dados.shape[0])

## Tabelas
### Tabelas de Receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados['PreçoFormatado'] = receita_estados['Preço'].apply(formatar_valor)
receita_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)
receita_estados['PreçoFormatado'] = receita_estados['Preço'].apply(formatar_valor)

dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'])
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()
receita_mensal['ValorFormatado'] = receita_mensal['Preço'].apply(formatar_valor_brasileiro)

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)
receita_categorias['PreçoFormatado'] = receita_categorias['Preço'].apply(formatar_valor)

### Tabelas de quantidade de vendas

### Tabelas Vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))
vendedores['Receita'] = vendedores['sum'].apply(lambda x: f'R${x:,.2f}')

# region Tabelas Desafio
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)

vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False))
# endregion

#  Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados,
                                   lat = 'lat',
                                   lon = 'lon',
                                   scope = 'south america',
                                   size = 'Preço',
                                   template = 'seaborn',
                                   hover_name = 'Local da compra',
                                   hover_data = {'lat':False,'lon':False, 'PreçoFormatado':True},
                                   title = 'Receita por Estado')
fig_mapa_receita.update_layout(yaxis_title = 'Receita')
fig_mapa_receita.update_traces(
    hovertemplate='<b>Local:</b> %{hovertext}<br><b>Receita:</b> %{customdata}<extra></extra>',
    customdata=receita_estados['PreçoFormatado']
)


fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers= True,
                             range_y=(0, receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Recita Mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Receita', dragmode=False, hovermode='x unified')
fig_receita_mensal.for_each_trace(lambda trace: trace.update(
    customdata=receita_mensal.loc[receita_mensal['Ano'] == int(trace.name), 'ValorFormatado'],  # Filtra por ano
    hovertemplate='<b>Mês:</b> %{x}<br><b>Receita:</b> R$ %{customdata}<extra></extra>'
))



fig_receita_estados = px.bar(receita_estados.head(5), 
                             x = 'Local da compra',
                             y = 'Preço',
                             text='PreçoFormatado',
                             title='Top estados(receita)',
                             hover_data={'PreçoFormatado': True})
fig_receita_estados.update_layout(yaxis_title='Receita', dragmode=False)
fig_receita_estados.update_traces( texttemplate='%{text}', textposition='inside', hovertemplate='<b>%{x}</b><br>Receita: %{customdata[0]}<extra></extra>', customdata=receita_estados.head(5)[['PreçoFormatado']] )




fig_receita_categorias = px.bar(receita_categorias,
                                text='PreçoFormatado',
                                title='Receita por categoria',
                                hover_data={'PreçoFormatado': True})
fig_receita_categorias.update_layout(yaxis_title='Receita', dragmode=False)
fig_receita_categorias.update_traces(texttemplate='%{text}', textposition='outside', hovertemplate='<b>%{x}</b><br>Receita: %{customdata[0]}<extra></extra>', customdata=receita_categorias[['PreçoFormatado']] )

# region Gráficos Desafio
fig_mapa_vendas = px.scatter_geo(vendas_estados, 
                     lat = 'lat', 
                     lon= 'lon', 
                     scope = 'south america', 
                     #fitbounds = 'locations', 
                     template='seaborn', 
                     size = 'Preço', 
                     hover_name ='Local da compra', 
                     hover_data = {'lat':False,'lon':False},
                     title = 'Vendas por estado',
                     )
fig_mapa_vendas.update_traces(
    hovertemplate='<b>%{hovertext}</b><br>Quantidade de vendas: %{marker.size}<extra></extra>'
)

fig_vendas_mensal = px.line(
    vendas_mensal, 
    x='Mes',
    y='Preço',
    color='Ano',         
    line_dash='Ano',     
    markers=True, 
    title='Quantidade de vendas mensal'
)
fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas', hovermode='x unified')
fig_vendas_mensal.update_traces(
    hovertemplate='<b>%{x}</b><br>Ano: %{fullData.name}<br>Quantidade de vendas: %{y}<extra></extra>'
)

fig_vendas_estados = px.bar(vendas_estados.head(),
                             x ='Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 estados'
)
fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')
fig_vendas_estados.update_traces(
    hovertemplate='<b>%{x}</b><br>Quantidade de vendas: %{y}<extra></extra>'
)



fig_vendas_categorias = px.bar(vendas_categorias, 
                                text_auto = True,
                                title = 'Vendas por categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')
fig_vendas_categorias.update_traces(
    hovertemplate='<b>%{x}</b><br>Quantidade de vendas: %{y}<extra></extra>'
)
# endregion

##Visualização no streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])


with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', receita)
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', quantidade_vendas)
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)
        
with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', receita)  
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_estados, use_container_width = True) 
    with coluna2:
        st.metric('Quantidade de vendas', quantidade_vendas)
        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_categorias, use_container_width = True)
        
with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', receita)
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index, 
                                        text_auto=True,
                                        title= f'Top {qtd_vendedores} vendedores (receita)') 
        fig_receita_vendedores.update_traces(hovertemplate='<b>%{y}</b><br>Receita: %{x}<extra></extra>')
        fig_receita_vendedores.update_traces( hovertemplate='<b>%{y}</b><br>Receita: %{customdata}<extra></extra>', 
                                             customdata=[formatar_valor(val) for val in vendedores.sort_values('sum', ascending=False).head(qtd_vendedores)['sum']] 
                                            )
        fig_receita_vendedores.update_traces(
                                             text=[formatar_valor(val) for val in vendedores.sort_values('sum', ascending=False).head(qtd_vendedores)['sum']],
                                             texttemplate='%{text}',  # Exibindo o valor formatado dentro das barras
                                             textposition='inside'    # Posicionando o texto dentro das barras
                                            )
        st.plotly_chart(fig_receita_vendedores)
        
        
        
    with coluna2:
        st.metric('Quantidade de vendas', quantidade_vendas)
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index, 
                                        text_auto=True,
                                        title= f'Top {qtd_vendedores} vendedores (quantidade de vendas)')  
        fig_vendas_vendedores.update_traces(hovertemplate='<b>%{y}</b><br>Quantidade de vendas: %{x}<extra></extra>') 
        st.plotly_chart(fig_vendas_vendedores) 
        
# Formatar os preços na DataFrame
dados['Preço'] = dados['Preço'].apply(formatar_valor)
st.dataframe(dados)
