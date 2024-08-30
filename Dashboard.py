import streamlit as st  # type: ignore
import requests
import pandas as pd   # type: ignore
import plotly.express as px  # type: ignore

st.set_page_config(layout='wide') 

def number_format(value, pref=''):
  for unit in ['', 'mil']:
    if value <1000:
      return f'{pref} {value:.2f} {unit}'
    value /=1000
  return f'{pref} {value:.2f} milhões'

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos'
# Criando filtro de região e ano antes da leitura
regioes = ['Brasil', 'Centro-Oestes', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)
if regiao == 'Brasil':
  regiao = ''
  
todos_anos = st.sidebar.checkbox('Dados de todos os anos', value=True)
if todos_anos:
  ano = ''
else:
  ano = st.sidebar.slider('Ano', 2020, 2023)

# Colocando os filtros na url
query_string = {'regiao': regiao.lower(), 'ano': ano}
response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

# Criando o Filtro para os Vendedores
filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
  dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## TABELAS ##

### Tabela Receitas
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
  receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

### Tabela Qntd de Vendas
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados,
                                                                                                           left_on = 'Local da compra',
                                                                                                           right_index = True).sort_values('Preço',
                                                                                                                                           ascending = False)

vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False))                                                                                                          


### Tabela Vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

## GRÁFICOS

fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por Estado')

fig_receita_mensal = px.line(receita_mensal,
                             x='Mes',
                             y='Preço',
                             markers=True,
                             range_y = (0, receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Receita Mensal')

fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_estados = px.bar(receita_estados.head(),
                             x= 'Local da compra',
                             y= 'Preço',
                             text_auto = True,
                             title='Top estados (receita)')
fig_receita_estados.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto=True,
                                title='Receita por categoria')
fig_receita_categorias.update_layout(yaxis_title='Receita')

# Gráfico Qntd de Vendas
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
fig_vendas_mensal = px.line(vendas_mensal, 
              x = 'Mes',
              y='Preço',
              markers = True, 
              range_y = (0,vendas_mensal.max()), 
              color = 'Ano', 
              line_dash = 'Ano',
              title = 'Quantidade de vendas mensal')

fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_estados = px.bar(vendas_estados.head(),
                             x ='Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 estados'
)

fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_categorias = px.bar(vendas_categorias, 
                                text_auto = True,
                                title = 'Vendas por categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')

## VISUALIZAÇÃO NO STREAMLIT##

# Construindo as abas
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

# Colocando as colunas nas abas que quero
with aba1:
  # Criando as colunas pra por as métricas
  coluna1, coluna2 = st.columns(2)

  # Colocando as Métricas nas colunas que quero
  with coluna1:
    st.metric('Receita', number_format(dados['Preço'].sum(), 'R$'))
    st.plotly_chart(fig_mapa_receita)
    st.plotly_chart(fig_receita_estados)
  with coluna2:
    st.metric('Quantidade de Vendas', number_format(dados.shape[0]))
    st.plotly_chart(fig_receita_mensal)
    st.plotly_chart(fig_receita_categorias)
    
with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', number_format(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_estados, use_container_width = True)

    with coluna2:
        st.metric('Quantidade de vendas', number_format(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_categorias, use_container_width = True)

    
with aba3:
  
  qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
  
  coluna1, coluna2 = st.columns(2)

  with coluna1:
    st.metric('Receita', number_format(dados['Preço'].sum(), 'R$'))
    # Criando o gráfico aqui pois preciso do valor d einput de qtd_vendedores desta aba
    fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                    x='sum',
                                    y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                    text_auto=True,
                                    title=f'Top {qtd_vendedores} vendedores (receita)')
    st.plotly_chart(fig_receita_vendedores)

  with coluna2:
    st.metric('Quantidade de Vendas', number_format(dados.shape[0]))
    fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                    x='count',
                                    y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                    text_auto=True,
                                    title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
    st.plotly_chart(fig_vendas_vendedores)


# Colocando o Dataframe na API
#st.dataframe(dados)