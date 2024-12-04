# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 09:56:28 2024

@author: André
"""

from streamlit_option_menu import option_menu
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from fpdf import FPDF

# Função para salvar o gráfico como imagem
def save_image(fig, file_name):
    fig.write_image(file_name, format="png")


# Configuração inicial do app
st.set_page_config(
    page_title="MOMESSO Report Builder",
    page_icon="iconeMomesso.png",
    layout="wide"
)

# Lista inicial para armazenar os dosadores válidos
dosadores = []

# Adicionando o logotipo da empresa centralizado com colunas
st.sidebar.image("logoMomesso.png", width=255)

# Inicializa 'menu' no session_state, se ainda não estiver definido
if "menu" not in st.session_state:
    st.session_state["menu"] = "Carregar Dados"
    
# Define as opções e ícones do menu
menu_options = ["Carregar Dados", "Consumo", "Período", "Lote", "Produção"]
menu_icons = ["cloud-upload", "speedometer2", "calendar-week", "tag", "bar-chart"]

# Menu estilizado dentro do sidebar
with st.sidebar:
    # Renderiza o menu com o índice sincronizado com o session_state
    selected_menu = option_menu(
        menu_title=None,  # Deixe None para esconder o título
        options=menu_options,
        icons=menu_icons,  # Ícones do Bootstrap
        menu_icon="cast",  # Ícone do menu principal
        default_index=0,  # Usa o índice baseado no session_state["menu"]
        orientation="vertical",  # Modo lateral
        styles={
            "container": {"padding": "5px", "background-color": "#f8f9fa"},
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#ff9933"},  # Estilo aplicado ao selecionado
        },
        key="sidebar_menu"
    )

    # Atualiza o session_state para refletir o menu selecionado
    st.session_state["menu"] = selected_menu

# Carregar arquivo
if st.session_state["menu"] == "Carregar Dados":
    st.header("Carregar Dados")
    st.markdown("---")
    
    # Carregar múltiplos arquivos
    uploaded_files = st.file_uploader(
        "Envie seus arquivos CSV ou Excel", 
        type=["csv", "xlsx"], 
        accept_multiple_files=True
    )
    
    # Cria um placeholder
    placeholder = st.empty()
    
    # Dicionário de mapeamento para padronização de colunas
    colunas_padronizadas = {
        "Date": "data",
        "Time": "hora_fim",
        "Hora Inicial": "hora_ini",
        "Hora Final": "hora_fim",
        "Lote": "lote",
        "Espécie": "especie",
        "Especie": "especie",
        "Categoria":"categoria",
        "Cultivar": "cultivar",
        "Peneira":"peneira",
        "Ensaque":"ensaque",
        "Operador":"operador",
        "Observação": "observacao",
        "Observacao": "observacao",
        "Peso_Mil_Sementes": "pms",
        "Peso de Mil Sementes": "pms",
        "Qtd Batelada": "num_bat",
        "Núm. Batelada": "num_bat",
        "Núm. Bateladas": "num_bat",
        "Receita": "receita",
        "Receita Selecionada": "receita",
        "Tratamento Solicitado (Kg)": "sp_total", 
        "Sementes Tratadas (Kg)": "pv_total",
        "Qtd Batelada": "num_bat", 
        "SP Batelada (Kg)": "sp_bat", 
        "PV Batelada (Kg)": "pv_bat",
        "Tempo_Ciclo": "tmp_ciclo",
        "Tempo de Ciclo": "tmp_ciclo",
        "Tempo_Mistura": "tmp_mist",
        "Tempo de Mistura": "tmp_mist",
        "Tempo_Descarga": "tmp_desc",
        "Tempo de Descarga": "tmp_desc"     
    }
    
    if uploaded_files:
        dfs = []  # Lista para armazenar os DataFrames carregados
        
        placeholder.info("Processando arquivo, aguarde!")
        
        for uploaded_file in uploaded_files:
            try:
                # Verifica o tipo do arquivo e carrega
                if uploaded_file.name.endswith(".csv"):
                    df_load = pd.read_csv(uploaded_file)
                elif uploaded_file.name.endswith(".xlsx"):
                    df_load = pd.read_excel(uploaded_file)
                else:
                    st.warning(f"O arquivo {uploaded_file.name} não é um CSV ou Excel válido.")
                    continue  # Ignora arquivos inválidos
                                
                # Renomear colunas com base no mapeamento
                df_load.rename(columns=colunas_padronizadas, inplace=True)
                
                # Ajustar 'hora_fim' para extrair somente o horário
                df_load["hora_fim"] = df_load["hora_fim"].dt.components.apply(
                    lambda x: f"{x['hours']:02}:{x['minutes']:02}:{x['seconds']:02}", axis=1
                )

                # Verificar e converter colunas essenciais para o tipo correto
                if "data" in df_load.columns:
                    df_load["data"] = pd.to_datetime(df_load["data"], errors="coerce")
                if "hora_ini" in df_load.columns:
                    df_load["hora_ini"] = pd.to_datetime(df_load["hora_ini"], format="%H:%M:%S", errors="coerce")
                if "hora_fim" in df_load.columns:
                    df_load["hora_fim"] = pd.to_datetime(df_load["hora_fim"], format="%H:%M:%S", errors="coerce")

                dfs.append(df_load)  # Adiciona o DataFrame processado à lista
                
            except Exception as e:
                st.error(f"Erro ao processar o arquivo {uploaded_file.name}: {e}")
        
        # Combinar todos os DataFrames
        if dfs:
            df = pd.concat(dfs, ignore_index=True)  

            # Salvar no session_state
            st.session_state["df"] = df
            st.session_state['dosadores'] = dosadores
            
            st.write("Número de arquivos carregados:", len(uploaded_files))
            
            # Loop para verificar as colunas de SP Receita para ED01 a ED10
            for i in range(1, 11):  # ED01 a ED10
                # Lista de possíveis nomes de colunas para SP Receita EDxx
                nome_colunas_sp = {
                    f"SP Receita - ED{str(i).zfill(2)} (L)",
                    f"SP Receita ED{str(i).zfill(2)}",
                    f"SP Receita - ED{str(i).zfill(2)}",
                }
                # Verifica se alguma dessas colunas está no DataFrame
                colunas_presentes = [col for col in nome_colunas_sp if col in df.columns]
                if colunas_presentes:
                    for coluna in colunas_presentes:
                        # Renomeia para um padrão e adiciona à lista de dosadores
                        df.rename(columns={coluna: f"SP Receita ED{str(i).zfill(2)}"}, inplace=True)
                        if df[f"SP Receita ED{str(i).zfill(2)}"].sum() > 0:
                            dosadores.append(f"ED{str(i).zfill(2)}")
            # Loop para verificar as colunas de DP para DP01 a DP04
            for i in range(1, 5):  # DP01 a DP04
                # Lista de possíveis nomes de colunas para DPxx
                nome_colunas_dp = {
                    f"SP Receita - DP{str(i).zfill(2)} (Kg)",
                    f"SP Receita DP{str(i).zfill(2)}",
                    f"SP Receita - DP{str(i).zfill(2)}",
                }
                # Verifica se alguma dessas colunas está no DataFrame
                colunas_presentes = [col for col in nome_colunas_dp if col in df.columns]
                if colunas_presentes:
                    for coluna in colunas_presentes:
                        # Renomeia para um padrão e adiciona à lista de dosadores
                        df.rename(columns={coluna: f"SP Receita DP{str(i).zfill(2)}"}, inplace=True)
                        if df[f"SP Receita DP{str(i).zfill(2)}"].sum() > 0:
                            dosadores.append(f"DP{str(i).zfill(2)}")

            # Renomear colunas para dosadores válidos
            for idx, dosador in enumerate(dosadores, start=1):
                # Prefixos originais e novos nomes para cada tipo de coluna
                colunas_renomear = {
                    f"SP Receita - {dosador} (L)" if "ED" in dosador else f"SP Receita - {dosador} (Kg)": f"sp_rec{str(idx).zfill(2)}",
                    f"SP Receita {dosador}" if "ED" in dosador else f"SP Receita {dosador}": f"sp_rec{str(idx).zfill(2)}",
                    f"SP Receita - {dosador}" if "ED" in dosador else f"SP Receita - {dosador}": f"sp_rec{str(idx).zfill(2)}",
                    #f"SP Receita - {dosador} (L)" if "ED" in dosador else f"SP Receita - {dosador} (Kg)": f"sp_rec{str(idx).zfill(2)}",
                    f"SP Dosagem {dosador}" if "ED" in dosador else f"SP Dosagem {dosador}": f"sp_dos{str(idx).zfill(2)}",
                    f"SP Dosagem - {dosador}" if "ED" in dosador else f"SP Dosagem - {dosador}": f"sp_dos{str(idx).zfill(2)}",
                    f"SP Dosagem - {dosador} (L)" if "ED" in dosador else f"SP Dosagem - {dosador} (Kg)": f"sp_dos{str(idx).zfill(2)}",
                    #f"PV Dosagem - {dosador} (L)" if "ED" in dosador else f"PV Dosagem - {dosador} (Kg)": f"pv_dos{str(idx).zfill(2)}",
                    f"PV Dosagem {dosador}" if "ED" in dosador else f"PV Dosagem {dosador}": f"pv_dos{str(idx).zfill(2)}",
                    f"PV Dosagem - {dosador}" if "ED" in dosador else f"PV Dosagem - {dosador}": f"pv_dos{str(idx).zfill(2)}",
                    f"PV Dosagem - {dosador} (L)" if "ED" in dosador else f"PV Dosagem - {dosador} (Kg)": f"pv_dos{str(idx).zfill(2)}",
                    f"Erro Dosagem - {dosador} (%)": f"erro_dos{str(idx).zfill(2)}",
                    f"Erro Dosagem {dosador}": f"erro_dos{str(idx).zfill(2)}",
                    f"Produto {dosador}": f"nome_prod{str(idx).zfill(2)}",
                    f"Densidade {dosador}": f"dens_prod{str(idx).zfill(2)}",
                    f"Densidade - {dosador}": f"dens_prod{str(idx).zfill(2)}",
                    f"Unid medida {dosador}": f"unid_med{str(idx).zfill(2)}",
                    f"Unid. Medida - {dosador}": f"unid_med{str(idx).zfill(2)}",
                    f"Unid_Sementes_{dosador}": f"unid_med{str(idx).zfill(2)}"
                }
                # Verificar e renomear as colunas existentes no DataFrame
                for nome_original, novo_nome in colunas_renomear.items():
                    if nome_original in df.columns:
                        df.rename(columns={nome_original: novo_nome}, inplace=True)
                df[f"nome_prod{str(idx).zfill(2)}"] = df[f"nome_prod{str(idx).zfill(2)}"].astype("str")
                df[f"sp_rec{str(idx).zfill(2)}"] = df[f"sp_rec{str(idx).zfill(2)}"].astype("float")
                df[f"pv_dos{str(idx).zfill(2)}"] = df[f"pv_dos{str(idx).zfill(2)}"].astype("float")
                df[f"erro_dos{str(idx).zfill(2)}"] = df[f"erro_dos{str(idx).zfill(2)}"].astype("float")    
                df["hora_ini"] = pd.to_datetime(df["hora_ini"], format='%H:%M:%S')
                df["hora_fim"] = pd.to_datetime(df["hora_fim"], format='%H:%M:%S')
            
            # Converter 'data' para o tipo datetime
            df["data"] = pd.to_datetime(df["data"])
                
            # Atualizar as colunas hora_ini e hora_fim com as respectivas datas
            df["hora_ini"] = df.apply(lambda row: row["hora_ini"].replace(year=row["data"].year,
                                                                        month=row["data"].month,
                                                                        day=row["data"].day), axis=1)
            df["hora_fim"] = df.apply(lambda row: row["hora_fim"].replace(year=row["data"].year,
                                                                        month=row["data"].month,
                                                                        day=row["data"].day), axis=1)

            # Ajustar hora_ini se hora_fim for menor
            df["hora_ini"] = df.apply(
                lambda row: row["hora_ini"] - pd.Timedelta(days=1) if row["hora_fim"] < row["hora_ini"] else row["hora_ini"],
                axis=1
            )
            
            # Alterar o tipo das colunas
            df["lote"] = df["lote"].astype("str")
            df["especie"] = df["especie"].astype("str")
            df["categoria"] = df["categoria"].astype("str")
            df["cultivar"] = df["cultivar"].astype("str")
            df["peneira"] = df["peneira"].astype("str")
            df["ensaque"] = df["ensaque"].astype("str")
            df["operador"] = df["operador"].astype("str")
            df["observacao"] = df["observacao"].astype("str")
            df["receita"] = df["receita"].astype("str")
            df["sp_total"] = df["sp_total"].astype(float)
            df["pv_total"] = df["pv_total"].astype(float)
            df["num_bat"] = df["num_bat"].astype(int)
            df["sp_bat"] = df["sp_bat"].astype(float)
            df["pv_bat"] = df["pv_bat"].astype(float)
            df["pms"] = df["pms"].astype(float)    
                 
            # Iterar sobre os dosadores válidos e criar as colunas sp_dosXX
            for idx, dosador in enumerate(dosadores, start=1):
                # Nome das colunas relevantes
                sp_rec_col = f"sp_rec{str(idx).zfill(2)}"
                pv_dos_col = f"pv_dos{str(idx).zfill(2)}"
                erro_dos_col = f"erro_dos{str(idx).zfill(2)}"
                sp_dos_col = f"sp_dos{str(idx).zfill(2)}"
                    
                df[f"nome_prod{str(idx).zfill(2)}"] = df[f"nome_prod{str(idx).zfill(2)}"].astype("str")
                df[sp_rec_col] = df[sp_rec_col].astype("float")
                df[pv_dos_col] = df[pv_dos_col].astype("float")
                df[erro_dos_col] = df[erro_dos_col].astype("float")
                
                    
                # Verificar se as colunas necessárias existem no DataFrame
                if sp_rec_col in df.columns and pv_dos_col in df.columns and erro_dos_col in df.columns:
                    # Transforma a dosagem para ml se estiver em litros
                    
                    # Multiplicar valores de sp_rec_col por 1000 se estiverem entre 0 e 5
                    if df[sp_rec_col].between(0, 5).any():
                        df.loc[df[sp_rec_col].between(0, 5), sp_rec_col] *= 1000
                    
                    # Multiplicar valores de pv_dos_col por 1000 se estiverem entre 0 e 5
                    if df[pv_dos_col].between(0, 5).any():
                        df.loc[df[pv_dos_col].between(0, 5), pv_dos_col] *= 1000
                    
                    # Verificar se a coluna sp_dos_col existe; se não, criar com valores baseados em "pv_bat" e "sp_rec_col"
                    if sp_dos_col not in df.columns:
                        df[sp_dos_col] = df["pv_bat"] / 100 * df[sp_rec_col]
                    
                    # Verificar se valores de pv_dos_col estão fora do intervalo de 80%-120% de sp_dos_col
                    # Caso estejam fora, substituir pelos valores de sp_dos_col
                    if not df[pv_dos_col].between(df[sp_dos_col] * 0.8, df[sp_dos_col] * 1.2).all():
                        df.loc[~df[pv_dos_col].between(df[sp_dos_col] * 0.8, df[sp_dos_col] * 1.2), pv_dos_col] = df[sp_dos_col]
                                               
                    # Garantir que a coluna 'erro_dos_col' seja numérica e substituir valores não numéricos por NaN
                    df[erro_dos_col] = pd.to_numeric(df[erro_dos_col], errors='coerce')
                    
                    # Substituir NaN e Inf por 0
                    df[erro_dos_col] = df[erro_dos_col].replace([np.inf, -np.inf, np.nan], 0)
                    
                    # Multiplicar pv_dos_col pelo ajuste, caso erro_dos_col esteja entre -10 e 10
                    df.loc[df[erro_dos_col].between(-20, 20), pv_dos_col] *= (
                        1 + df.loc[df[erro_dos_col].between(-20, 20), erro_dos_col] / 100
                    )
                    
            # Criando uma nova coluna com a soma dos consumos
            df["total_sp"] = df[[f"sp_dos{str(idx).zfill(2)}" for idx in range(1, len(dosadores)+1)]].sum(axis=1)
                
            # Criando uma nova coluna com a soma dos consumos
            df["total_consumo"] = df[[f"pv_dos{str(idx).zfill(2)}" for idx in range(1, len(dosadores)+1)]].sum(axis=1)
                
            # Criando uma nova coluna com o tempo de ciclo
            df['tempo_ciclo'] = (df['hora_fim'] - df['hora_ini']).dt.total_seconds()
            
            # Remover duplicatas com base em todas as colunas
            df = df.drop_duplicates().reset_index(drop=True)   
            # st.text(df.shape)
            # st.dataframe(df)
            
            placeholder.success("Arquivo carregado com sucesso!")
            
        else:
            st.warning("Nenhum arquivo válido foi carregado ou processado.")
    
# Consumo
elif st.session_state["menu"] == "Consumo":
    st.header("Consumo")
    if 'dosadores' in  st.session_state:
        dosadores = st.session_state['dosadores']
    if 'df' in st.session_state:  # Verifica se o arquivo foi carregado
        df = st.session_state['df']
        
        df_consumo = df.groupby('receita').agg({'total_consumo': 'sum', 'pv_bat': 'sum'}).reset_index()
        df_consumo.rename(columns={'receita':'Receita', 'total_consumo': 'Consumo', 'pv_bat': 'Produção'}, inplace=True)
        df_consumo['Consumo'] = df_consumo['Consumo'] / 1000
        df_consumo['Produção'] = df_consumo['Produção'] / 1000
        df_consumo = df_consumo.sort_values(by="Consumo", ascending=False)
        
        # Criando o gráfico de pizza
        fig = px.pie(
            df_consumo,
            names="Receita",
            values="Consumo",
            title="Consumo por Receita",
            color_discrete_sequence=px.colors.sequential.Oranges,
            hole=0.3  # Gráfico do tipo donut
            )
        # Personalizando o conteúdo exibido ao passar o mouse
        fig.update_traces(
            textinfo='label+percent',  # Exibe rótulos e porcentagens
            textfont_size=10,
            hovertemplate=(
                'Receita: %{label}<br>'  # Nome da receita
                'Consumo: %{value:.2f} L<br>'  # Consumo com 2 casas decimais
                'Percentual: %{percent:.1%}'  # Percentual com 1 casa decimal
            )
        )
        # Layout do gráfico
        fig.update_layout(
            title_x=0.4,  # Centraliza o título
            font=dict(size=14)
            )
        
        # Gerar o HTML da tabela estilizada
        html_tb_cons_rec = (
            df_consumo.style
            .format({"Consumo": "{:.2f} L", "Produção": "{:.2f} Ton"})  # Formatação com 2 casas decimais
            .set_table_styles([            # Estilos gerais da tabela
                {"selector": "thead th", "props": [("font-weight", "bold"), ("text-align", "center"), ("font-size", "13px")]},
                {"selector": "tbody td", "props": [("text-align", "center"), ("font-size", "12px")]},  # Centralizar textos
                {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]}  # Fundo alternado
            ])
            .hide(axis='index')   # Remover o índice
            .to_html()  # Converter para HTML
        )
        
        st.markdown("---")
        col1, col2 = st.columns([2, 1], gap="large")  # Ajustar proporções das colunas e espaço

        with col1:
            st.plotly_chart(fig, use_container_width=True)
            # Salvar o gráfico como imagem
            # print ("gerando imagem")
            # fig.write_image("grafico_pizza.png")
            # print ("imagem OK")
        with col2:
            st.markdown(f"""
                <div style="
                    display: flex;
                    flex-direction: column;
                    justify-content: center;  /* Centraliza verticalmente */
                    align-items: flex-end;   /* Alinha à direita */
                    height: 100%;  /* Ocupa toda a altura disponível */
                    text-align: right;
                ">
                    <!-- Inserir quebras de linha para espaço acima da tabela -->
                    <br><br>
                    {html_tb_cons_rec}
            """, unsafe_allow_html=True)
            
        # Criar um DataFrame contendo os nomes dos produtos e a soma do consumo
        def criar_df_somatorio(df, dosadores):
            # Lista para armazenar os dados agregados
            dados_agregados = []
            # print("Após a definição, dosadores:", dosadores)
            # Iterar sobre os dosadores válidos
            for idx, dosador in enumerate(dosadores, start=1):
                # Definir os nomes das colunas relevantes
                nome_col = f"nome_prod{str(idx).zfill(2)}"
                pv_dos_col = f"pv_dos{str(idx).zfill(2)}"
        
                # Verificar se ambas as colunas existem
                if nome_col in df.columns and pv_dos_col in df.columns:
                    # Agrupar por produto e somar o consumo
                    df_agrupado = df.groupby(nome_col).agg({pv_dos_col: "sum"}).reset_index()
                    df_agrupado.rename(columns={nome_col: "Produto", pv_dos_col: "Consumo"}, inplace=True)
        
                    # Adicionar os dados ao conjunto final
                    dados_agregados.append(df_agrupado)
        
            # Verificar se há dados para concatenar
            if not dados_agregados:
                st.warning("Nenhum dosador válido foi encontrado no arquivo carregado.")
                return pd.DataFrame(columns=["Produto", "Consumo"])  # Retornar DataFrame vazio
        
            # Concatenar todos os DataFrames em um único DataFrame
            df_resultado = pd.concat(dados_agregados, ignore_index=True)
        
            # Agrupar novamente para consolidar os valores de consumo para o mesmo produto
            df_resultado = df_resultado.groupby("Produto").agg({"Consumo": "sum"}).reset_index()
        
            return df_resultado
        
        df_somatorio = criar_df_somatorio(df, dosadores)
        
        df_somatorio = df_somatorio.dropna()  # Remove todas as linhas com NaN em qualquer coluna
        df_somatorio = df_somatorio[df_somatorio['Consumo'] != 0]  # Filtra linhas onde Consumo é diferente de 0
        df_somatorio['Consumo'] = df_somatorio['Consumo'] / 1000
        df_somatorio = df_somatorio.sort_values(by="Consumo", ascending=True)
        
        # Criação do gráfico de barras horizontais
        fig1 = px.bar(
            df_somatorio,
            y="Produto",  # Coluna para o eixo y (nomes dos produtos)
            x="Consumo",  # Coluna para o eixo x (valores de consumo)
            title="Consumo por Produto",
            orientation="h",  # Gráfico de barras horizontais
            color="Consumo",  # A cor das barras será baseada no consumo
            color_continuous_scale=px.colors.sequential.Oranges  # Paleta de cores laranja
        )
        
        # Adicionando rótulos com valores nas barras
        fig1.update_traces(
            texttemplate='%{x:.0f}',  # Exibe os valores no final das barras
            textposition='outside',  # Coloca os valores fora das barras
            textfont_size=10
        )
        # Exibir o valor do consumo com até 2 casas decimais ao passar o mouse sobre a barra
        fig1.update_traces(
            hovertemplate='Produto: %{y}<br>Consumo: %{x:.2f} L'  # Exibe o valor do consumo com 2 casas decimais
        )
        
        # Layout do gráfico
        fig1.update_layout(
            title_x=0.4,  # Centraliza o título
            font=dict(size=14)
        )
        
        df_somatorio = df_somatorio.sort_values(by="Consumo", ascending=False)
        # Adicionar a linha com a somatória total
        total_consumo = df_somatorio["Consumo"].sum()
        
        # Gerar o HTML da tabela estilizada
        html_tb_cons_prod = (
            df_somatorio.style
            .format({"Consumo": "{:.2f} L"})  # Formatação com 2 casas decimais
            .set_table_styles([            # Estilos gerais da tabela
                {"selector": "thead th", "props": [("font-weight", "bold"), ("text-align", "center"), ("font-size", "13px")]},
                {"selector": "tbody td", "props": [("text-align", "center"), ("font-size", "12px")]},  # Centralizar textos
                {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]}  # Fundo alternado
            ])
            .hide(axis='index')   # Remover o índice
            .to_html()  # Converter para HTML
        )

        col1, col2 = st.columns([3, 1], gap="large")  # Ajustar proporções das colunas e espaço
        with col1:
            st.plotly_chart(fig1, use_container_width=True)
                      
        with col2:
            st.markdown(f"""
                <div style="
                    display: flex;
                    flex-direction: column;
                    justify-content: center;  /* Centraliza verticalmente */
                    align-items: flex-end;   /* Alinha à direita */
                    height: 100%;  /* Ocupa toda a altura disponível */
                    text-align: right;
                ">
                    <!-- Inserir quebras de linha para espaço acima da tabela -->
                    <br><br>
                    {html_tb_cons_prod}
            """, unsafe_allow_html=True)
            # Exibir o consumo total em um markdown separado, garantindo a formatação
            st.markdown(f"""
                <p style="text-align: center; font-weight: bold; font-size: 13px; margin-top: 20px;">
                    Consumo Total: {total_consumo:.2f} L
                </p>
            """, unsafe_allow_html=True)
        
        # Função para criar o PDF com o gráfico
        def create_pdf(image_file, pdf_file):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Relatório de Gráficos", ln=True, align='C')

        
            # Adicionar a imagem ao PDF
            pdf.image(image_file, x=10, y=30, w=180)  # Ajuste as dimensões conforme necessário
            pdf.output(pdf_file)
            print(f"PDF {pdf_file} criado com sucesso!")

        # Botão para exportar gráfico em PDF
        if st.button("Exportar Gráfico em PDF"):
            image_file = "grafico_pizza.png"
            pdf_file = "relatorio_grafico.pdf"
            
            # Salvar gráfico como imagem
            save_image(fig, image_file)
            
            # Criar o PDF
            create_pdf(image_file, pdf_file)
            
            # Oferecer download no Streamlit
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="Baixar PDF",
                    data=f,
                    file_name=pdf_file,
                    mime="application/pdf"
                )


        # def criar_grafico_matplotlib(df):
        #     fig, ax = plt.subplots(figsize=(8, 6))
        #     df = df.sort_values(by="Consumo", ascending=True)
        #     ax.barh(df["Produto"], df["Consumo"], color=plt.cm.Oranges(df["Consumo"] / df["Consumo"].max()))
        #     for i, v in enumerate(df["Consumo"]):
        #         ax.text(v + 0.1, i, f"{v:.2f} L", va="center", fontsize=10)
        #     ax.set_title("Consumo por Produto", fontsize=14)
        #     ax.set_xlabel("Consumo (L)", fontsize=12)
        #     ax.set_ylabel("Produto", fontsize=12)
        #     plt.tight_layout()
        #     return fig
        
        # # Criar gráfico
        # fig_matplotlib = criar_grafico_matplotlib(df_somatorio)
        
        # # Salvar gráfico como imagem temporária
        # grafico_path = "grafico_relatorio.png"
        # fig_matplotlib.savefig(grafico_path)
        # plt.close(fig_matplotlib)  # Fechar a figura para liberar memória
        
        
        # def criar_pdf_com_logo(grafico_path, logo_path):
        #     # Verificar se os arquivos existem
        #     if not os.path.exists(grafico_path):
        #         raise FileNotFoundError(f"Gráfico não encontrado: {grafico_path}")
        #     if not os.path.exists(logo_path):
        #         raise FileNotFoundError(f"Logotipo não encontrado: {logo_path}")
            
        #     pdf = FPDF()
        #     pdf.set_auto_page_break(auto=True, margin=15)
        #     pdf.add_page()
        
        #     # Inserir logotipo
        #     pdf.image(logo_path, x=10, y=8, w=30)  # Ajuste as coordenadas e tamanho conforme necessário
        #     pdf.set_font("Arial", size=12)
        #     pdf.cell(200, 10, txt="Relatório de Consumo por Produto", ln=True, align="C")
        #     pdf.ln(20)
        
        #     # Adicionar gráfico
        #     pdf.image(grafico_path, x=10, y=50, w=180)  # Ajuste as dimensões conforme necessário
        
        #     # Adicionar texto
        #     pdf.ln(100)
        #     pdf.set_font("Arial", size=10)
        #     pdf.multi_cell(0, 10, "Este relatório apresenta os dados de consumo por produto, conforme o gráfico acima.")
        
        #     # Retornar PDF como bytes
        #     pdf_output = io.BytesIO()
        #     pdf_content = pdf.output(dest='S').encode('latin1')  # Gera o PDF como uma string binária
        #     pdf_output.write(pdf_content)
        #     pdf_output.seek(0)
        #     return pdf_output
        
        # # Caminhos para os arquivos
        # grafico_path = "grafico_relatorio.png"
        # logo_path = "D:/Desenvolvimento/MomessoRepBuilder_App/MomessoRepBuilder_App/.spyproject/Imagens/logoMomesso.png"

        
        # # Criar PDF
        # try:
        #     pdf_file = criar_pdf_com_logo(grafico_path, logo_path)
        
        #     st.download_button(
        #         label="Baixar Relatório PDF",
        #         data=pdf_file,
        #         file_name="relatorio_consumo.pdf",
        #         mime="application/pdf"
        #     )
        # except FileNotFoundError as e:
        #     st.error(str(e))
        
        
    else:
        st.warning("Por favor, carregue um arquivo primeiro.")
        
# Período
elif st.session_state["menu"] == "Período":
    st.header("Período")
    if 'df' in st.session_state:  # Verifica se o arquivo foi carregado
        df = st.session_state['df']
        # Verifique se as colunas de data e hora existem no seu DataFrame
        if 'hora_ini' in df.columns and 'hora_fim' in df.columns:
            
            # Seletores para data/hora inicial e final
            col1, col2 = st.columns(2)
            with col1:
                # Selecionando data e hora para o Período Inicial
                periodo_inicio_date = st.date_input("Data Inicial", df['hora_ini'].min().date())
                periodo_inicio_time = st.time_input("Hora Inicial", df['hora_ini'].min().time())
                
            with col2:
                # Selecionando data e hora para o Período Final
                periodo_fim_date = st.date_input("Data Final", df['hora_fim'].max().date())
                periodo_fim_time = st.time_input("Hora Final", df['hora_fim'].max().time())
            
            # Combinar data e hora selecionadas em um único timestamp
            periodo_inicio = pd.to_datetime(f"{periodo_inicio_date} {periodo_inicio_time}")
            periodo_fim = pd.to_datetime(f"{periodo_fim_date} {periodo_fim_time}")
            
            # Filtrar os dados entre o período selecionado
            df_filtrado = df[(df['hora_ini'] >= periodo_inicio) & (df['hora_fim'] <= periodo_fim)]
            
            # Calcular valores exibidos no relatório
            tempo_total = df_filtrado['tempo_ciclo'].sum()
            producao = (df_filtrado['pv_bat'].sum()/1000)
            if tempo_total > 0:
                produtividade = round(producao / (tempo_total / 3600), 2)  # Em Ton/h
            else:
                produtividade = 0.0
            num_lotes = df_filtrado['lote'].nunique()
            num_receitas = df_filtrado['receita'].nunique()
            num_bateladas = len(df_filtrado)
            
            # Formatar as datas e horas
            periodo_inicio_formatado = periodo_inicio.strftime('%H:%M:%S / %d-%m-%Y')
            periodo_fim_formatado = periodo_fim.strftime('%H:%M:%S / %d-%m-%Y')
            
            # Convertendo o total de segundos para o formato horas:minutos:segundos
            horas = tempo_total // 3600  # Divisão inteira para obter as horas
            minutos = (tempo_total % 3600) // 60  # Resto da divisão por 3600 (horas), dividido por 60 para minutos
            segundos = tempo_total % 60  # Resto da divisão por 60 para segundos
            
            # Formatando no formato horas:minutos:segundos
            tempo_total_formatado = f"{int(horas):02}:{int(minutos):02}:{int(segundos):02}"
            
            media_bat = df_filtrado['pv_bat'].mean()
            tempo_med_bat = df_filtrado['tempo_ciclo'].mean()
 
            st.markdown("---")
            st.markdown("### Informações do Período")
                
            col1, col2 = st.columns(2)
            col1.metric("Inicio", periodo_inicio_formatado)
            col2.metric("Fim", periodo_fim_formatado)
            
            col3, col4, col5 = st.columns(3)
            col3.metric("Produção no Período", f"{producao:.2f} Ton")
            col4.metric("Tempo Efetivo", tempo_total_formatado)
            col5.metric("Produtividade Média", f"{produtividade} Ton/h")
            
            col6, col7, col8 = st.columns(3)
            col6.metric("Peso Médio / Batelada", f"{media_bat:.2f} Kg")
            col7.metric("Tempo Médio / Batelada", f"{tempo_med_bat:.1f} s")
            col8.metric("Número de Bateladas", num_bateladas)
            
            col9, col10, col11 = st.columns(3)
            col9.metric("Número de Lotes", num_lotes)
            col10.metric("Quantidade de Receitas", num_receitas)
            
            st.markdown("---")       
            st.markdown("### Resumo do Período")
            
            # Agrupando os dados por lote e Receita
            df_agrupado = df_filtrado.groupby(["lote", "receita"]).agg(
                hora_inicio=("hora_ini", "min"),
                hora_final=("hora_fim", "max"),
                sementes_tratadas=("pv_bat", "sum"),
                num_bateladas=("lote", "size"),
                qtd_necessaria=("total_sp", "sum"),
                qtd_dosada=("total_consumo", "sum")
            ).reset_index()

            # Convertendo as unidades para toneladas (divisão por 1000)
            df_agrupado["sementes_tratadas"] = df_agrupado["sementes_tratadas"] / 1000
            df_agrupado["qtd_necessaria"] = df_agrupado["qtd_necessaria"] / 1000
            df_agrupado["qtd_dosada"] = df_agrupado["qtd_dosada"] / 1000

            # Calculando Variação de Dosagem (%)
            df_agrupado["variacao_dosagem"] = ((df_agrupado["qtd_dosada"] / df_agrupado["qtd_necessaria"]) - 1) * 100
            
            # Formatando os valores com 2 casas decimais
            df_agrupado["sementes_tratadas"] = df_agrupado["sementes_tratadas"].map("{:.2f}".format)
            df_agrupado["qtd_necessaria"] = df_agrupado["qtd_necessaria"].map("{:.2f}".format)
            df_agrupado["qtd_dosada"] = df_agrupado["qtd_dosada"].map("{:.2f}".format)
            df_agrupado["variacao_dosagem"] = df_agrupado["variacao_dosagem"].map("{:.3f}".format)

            # Formatando as colunas de hora
            df_agrupado["hora_inicio"] = pd.to_datetime(df_agrupado["hora_inicio"]).dt.strftime("%d-%m-%Y / %H:%M:%S")
            df_agrupado["hora_final"] = pd.to_datetime(df_agrupado["hora_final"]).dt.strftime("%H:%M:%S")

            # Reordenando as colunas
            df_agrupado = df_agrupado[[
                "hora_inicio", "hora_final", "lote", "receita",
                "sementes_tratadas", "num_bateladas",
                "qtd_necessaria", "qtd_dosada", "variacao_dosagem"
            ]]

            # Renomeando colunas para exibição
            df_agrupado.rename(columns={
                "hora_inicio": "Início",
                "hora_final": "Fim",
                "lote": "Lote",
                "receita": "Receita",
                "sementes_tratadas": "Qtd. Tratada",
                "num_bateladas": "Núm. Bateladas",
                "qtd_necessaria": "Qtd. Necessária",
                "qtd_dosada": "Qtd. Dosada",
                "variacao_dosagem": "Variação Dosagem"
            }, inplace=True)

            # Ordenando pela coluna Início
            df_agrupado.sort_values(by="Início", inplace=True)
            
            # Garantir que a coluna 'Variação Dosagem' seja numérica
            df_agrupado['Variação Dosagem'] = pd.to_numeric(df_agrupado['Variação Dosagem'], errors='coerce')
            df_agrupado['Qtd. Tratada'] = pd.to_numeric(df_agrupado['Qtd. Tratada'], errors='coerce')
            
            # Definir uma função para aplicar o estilo com base na condição
            def colorir_linhas(row):
                if row['Variação Dosagem'] < -5 or row['Variação Dosagem'] > 5:
                    return ['background-color: lightsalmon'] * len(row)  # Aplica fundo vermelho a toda a linha
                else:
                    return [''] * len(row)  # Nenhum estilo, linha mantém o estilo original
            # Gerar o HTML da tabela estilizada
            html_tb_agrupado = (
                df_agrupado.style
                .apply(colorir_linhas, axis=1)  # Aplica a função de colorir as linhas
                .format({"Qtd. Tratada": "{:.2f} Ton","Variação Dosagem": "{:.3f} %"})  # Formatação com 2 casas decimais
                .set_table_styles([  # Estilos gerais da tabela
                    {"selector": "thead th", "props": [("font-weight", "bold"), ("text-align", "center"), ("font-size", "13px")]},
                    {"selector": "tbody td", "props": [("text-align", "center"), ("font-size", "12px")]},  # Centralizar textos
                    {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]},  # Fundo alternado
                    {"selector": "table", "props": [("border-collapse", "collapse"), ("width", "100%")]},  # Colapsar bordas
                    {"selector": "td, th", "props": [("border", "1px solid #ddd"), ("padding", "8px")]},  # Adicionar bordas e padding
                ])
                .hide(axis='index')  # Remover o índice
                .to_html()  # Converter para HTML
            )
            
            # Exibindo a tabela estilizada no Streamlit
            st.markdown(f"""
                <div style="
                    display: flex;
                    flex-direction: column;
                    justify-content: center;  /* Centraliza verticalmente */
                    align-items: flex-start;   /* Alinha à esquerda */
                    height: 100%;  /* Ocupa toda a altura disponível */
                    text-align: left;
                ">
                    <!-- Inserir quebras de linha para espaço acima da tabela -->
                    <br><br>
                    {html_tb_agrupado}
            """, unsafe_allow_html=True)
            
           
            # Garantir que 'Variação Dosagem' seja numérico
            df_agrupado['Variação Dosagem'] = pd.to_numeric(df_agrupado['Variação Dosagem'], errors='coerce')

            # Criando o gráfico de linha
            plt.figure(figsize=(10, 2))
            
            # Plotando a linha de variação de dosagem
            plt.plot(df_agrupado['Início'], df_agrupado['Variação Dosagem'], color='darkorange', linewidth=2)
            
            # Adicionando círculos em cada amostragem
            plt.scatter(df_agrupado['Início'], df_agrupado['Variação Dosagem'], color='darkorange', zorder=5)

            # Adicionando linhas pivot
            plt.axhline(y=5, color='lightcoral', linestyle='--', linewidth=1)
            plt.axhline(y=-5, color='lightcoral', linestyle='--', linewidth=1)
            
            # Definindo limites dinâmicos do eixo Y
            min_dosagem = df_agrupado['Variação Dosagem'].min()
            max_dosagem = df_agrupado['Variação Dosagem'].max()
            
            # Ajustando o limite inferior e superior do eixo Y
            if min_dosagem < -5.5:
                y_min = min_dosagem - 3
            else:
                y_min = -5.5
            
            if max_dosagem > 5.5:
                y_max = max_dosagem + 3
            else:
                y_max = 5.5
            
            # Ajustando o limite do eixo Y com base nos valores calculados
            plt.ylim(y_min, y_max)
            # Ajustando o título e os rótulos dos eixos
            #plt.title('Variação de Dosagem por lote', fontsize=10, loc='center')
            #plt.xlabel('Período', fontsize=10)
            #plt.ylabel('Variação', fontsize=10)
            
            # Ocultando os valores do eixo X e Y
            plt.xticks([])  # Remove os valores do eixo X
            plt.yticks([])  # Define as marcas do eixo Y entre -5 e 5
            
            # Adicionando uma linha central em 0
            plt.axhline(y=0, color='lightgrey', linewidth=1)
            
            # Exibindo o gráfico sem borda em volta
            plt.gca().spines['top'].set_visible(False)
            plt.gca().spines['right'].set_visible(False)
            plt.gca().spines['left'].set_visible(False)
            plt.gca().spines['bottom'].set_visible(False)
            
            
            # Exibindo o gráfico
            st.markdown("---")       
            st.markdown("### Variação de Dosagem")
            plt.grid(True, axis='x', linestyle='--', alpha=0.6)
            plt.tight_layout()
            st.pyplot(plt)
           
        else:
            st.warning("As colunas 'Data' e/ou 'Hora' não foram encontradas no DataFrame.")
    else:
        st.warning("Por favor, carregue um arquivo primeiro.")

# lote
elif st.session_state["menu"] == "Lote":
    st.header("Lote")
    if 'dosadores' in  st.session_state:
        dosadores = st.session_state['dosadores']
    if 'df' in st.session_state:  # Verifica se o arquivo foi carregado
        df = st.session_state['df']
        
        # Criando colunas de seleção para lote e Receita
        col1, col2 = st.columns(2)
        
        with col1:
            col_nome = st.selectbox("Selecione o lote", df['lote'].unique())
        
        # Filtrando as receitas com base no lote selecionado
        receitas_filtradas = df[df['lote'] == col_nome]['receita'].unique()
        
        with col2:
            col_valor = st.selectbox("Selecione a Receita", receitas_filtradas)
        
        # Filtrar o DataFrame original com base nas escolhas do usuário
        df_filtrado = df[(df['lote'] == col_nome) & (df['receita'] == col_valor)]
        
        if not df_filtrado.empty:
            # Exibir os cartões com informações principais
            st.markdown("---")
            st.markdown("### Informações do lote")
                
            col1, col2 = st.columns(2)
            col1.metric("Lote", col_nome)
            col2.metric("Tratamento", col_valor)
            
            col3, col4, col5, col6 = st.columns(4)
            col3.metric("Espécie", df_filtrado['especie'].iloc[0]) 
            col4.metric("Peneira", df_filtrado['peneira'].iloc[0])
            col5.metric("Categoria", df_filtrado['categoria'].iloc[0])
            col6.metric("Cultivar", df_filtrado['cultivar'].iloc[0])

            # Calculando e exibindo o resumo
            data_inicio = df_filtrado['hora_ini'].min()
            data_fim = df_filtrado['hora_fim'].max()
            tempo_total = df_filtrado['tempo_ciclo'].sum()
            producao = (df_filtrado['pv_bat'].sum()/1000)
            if tempo_total > 0:
                produtividade = round(producao / (tempo_total / 3600), 2)  # Em Ton/h
            else:
                produtividade = 0.0
            num_bateladas = len(df_filtrado)
            media_bat = df_filtrado['pv_bat'].mean()
            tempo_med_bat = df_filtrado['tempo_ciclo'].mean()
            tempo_corrido = data_fim - data_inicio

            # Obtendo dias, horas, minutos e segundos
            dias = tempo_corrido.days
            horas, resto = divmod(tempo_corrido.seconds, 3600)
            minutos, segundos = divmod(resto, 60)
            
            # Formatação condicional
            if dias > 0:
                tempo_corrido_formatado = f"{dias} dia{'s' if dias > 1 else ''}, {horas:02}:{minutos:02}:{segundos:02}"
            else:
                tempo_corrido_formatado = f"{horas:02}:{minutos:02}:{segundos:02}"
                
            # Formatar as datas e horas
            periodo_inicio_formatado = data_inicio.strftime('%H:%M:%S / %d-%m-%Y')
            periodo_fim_formatado = data_fim.strftime('%H:%M:%S / %d-%m-%Y')
            
            # Convertendo o total de segundos para o formato horas:minutos:segundos
            horas = tempo_total // 3600  # Divisão inteira para obter as horas
            minutos = (tempo_total % 3600) // 60  # Resto da divisão por 3600 (horas), dividido por 60 para minutos
            segundos = tempo_total % 60  # Resto da divisão por 60 para segundos
            
            # Formatando no formato horas:minutos:segundos
            tempo_total_formatado = f"{int(horas):02}:{int(minutos):02}:{int(segundos):02}"
            
            # Layout em colunas 
            st.markdown("---")
            st.markdown("### Dados do Tratamento")
                
            col1, col2 = st.columns(2)
            col1.metric("Inicio", periodo_inicio_formatado)
            col2.metric("Fim", periodo_fim_formatado)
            
            col3, col4, col5 = st.columns(3)
            col3.metric("Total Produzido", f"{producao:.2f} Ton")
            col4.metric("Tempo Efetivo", tempo_total_formatado)
            col5.metric("Produtividade Média", f"{produtividade} Ton/h")
            
            col6, col7, col8 = st.columns(3)
            col6.metric("Peso Médio / Batelada", f"{media_bat:.2f} Kg")
            col7.metric("Tempo Médio / Batelada", f"{tempo_med_bat:.1f} s")
            col8.metric("Número de Bateladas", num_bateladas)
            
            st.markdown("---")
            st.markdown("### Detalhes do Tratamento")

            

            def criar_df_somatorio(df_filtrado, dosadores):
                # Calcular a somatória da coluna 'pv_bat' no DataFrame filtrado
                soma_pv_bat = df_filtrado["pv_bat"].sum()
                
                # Verificar se a somatória é válida (não zero para evitar divisão por zero)
                if soma_pv_bat == 0:
                    st.warning("A quantidade de sementes tratadas é zero. Não é possível calcular a Receita.")
                    return pd.DataFrame(columns=["Produto", "Necessário", "Total Dosado", "Receita", "Dose", "Variação"])

                # Lista para armazenar os dados agregados
                dados_agregados = []
                
                # Iterar sobre os dosadores válidos
                for idx, dosador in enumerate(dosadores, start=1):
                    # Definir os nomes das colunas relevantes
                    nome_col = f"nome_prod{str(idx).zfill(2)}"
                    sp_dos_col = f"sp_dos{str(idx).zfill(2)}"
                    pv_dos_col = f"pv_dos{str(idx).zfill(2)}"
            
                    # Verificar se ambas as colunas existem
                    if nome_col in df.columns and sp_dos_col in df.columns and pv_dos_col in df.columns:
                        # Agrupar por produto e somar o consumo
                        df_agrupado = df_filtrado.groupby(nome_col).agg({
                            sp_dos_col: ["sum"],  # Soma e média para SP dosagem
                            pv_dos_col: ["sum"]  # Soma e média para PV dosagem
                        }).reset_index()
                                                
                        # Ajustar os nomes das colunas
                        df_agrupado.columns = ["Produto", "Necessário", "Total Dosado"]
                        
                        # Adicionar os dados ao conjunto final
                        dados_agregados.append(df_agrupado)
            
                # Verificar se há dados para concatenar
                if not dados_agregados:
                    st.warning("Nenhum dosador válido foi encontrado no arquivo carregado.")
                    return pd.DataFrame(columns=["Produto", "Necessário", "Total Dosado", "Receita", "Dose", "Variação"])

                # Concatenar todos os DataFrames em um único DataFrame
                df_resultado = pd.concat(dados_agregados, ignore_index=True)
            
                # Consolidar os valores de consumo para o mesmo produto
                df_resultado = df_resultado.groupby("Produto").agg({
                    "Necessário": "sum",
                    "Total Dosado": "sum",
                }).reset_index()
                
                # Adicionar a coluna de Variação
                df_resultado["Receita"] = (df_resultado["Necessário"] / soma_pv_bat)*100
                df_resultado["Dose"] = (df_resultado["Total Dosado"] / soma_pv_bat)*100
                df_resultado["Variação"] = ((df_resultado["Total Dosado"] / df_resultado["Necessário"])-1)*100

                return df_resultado
            
            df_somatorio = criar_df_somatorio(df_filtrado, dosadores)
            
            df_somatorio = df_somatorio.dropna()  # Remove todas as linhas com NaN em qualquer coluna
            df_somatorio = df_somatorio[df_somatorio['Necessário'] != 0]  # Filtra linhas onde Consumo é diferente de 0
            df_somatorio['Necessário'] = df_somatorio['Necessário'] / 1000
            df_somatorio['Total Dosado'] = df_somatorio['Total Dosado'] / 1000
            df_somatorio = df_somatorio.sort_values(by="Necessário", ascending=True)
            
            
            #sp receita, pv dosagem ml/100 kg, variação
            
            
            # Criando o gráfico de barras verticais
            fig1 = px.bar(
                df_somatorio,
                x="Produto",  # Coluna para o eixo x
                y=["Necessário", "Total Dosado"],  # Colunas para o eixo y
                title="Consumo por Produto",
                barmode="group",  # Barras agrupadas para comparar as variáveis
                labels={"value": "Volume (L)", "variable": "Tipo"},  # Personalizar os rótulos dos eixos
                color_discrete_map={"Total Dosado": "darkorange", "Necessário": "peachpuff"}  # Definir as cores para as categorias
            )
            
            # Adicionando rótulos com valores nas barras
            fig1.update_traces(
                texttemplate='%{y:.3f}',  # Exibe os valores no final das barras
                textposition='outside',  # Coloca os valores fora das barras
                textfont_size=10
            )
            # Exibir o valor do consumo com até 2 casas decimais ao passar o mouse sobre a barra
            fig1.update_traces(
                hovertemplate='Produto: %{x}<br>Volume (L): %{y:.3f}'  # Exibe o valor do consumo com 2 casas decimais
            )
            
            # Layout do gráfico
            fig1.update_layout(
                title_x=0.4,  # Centraliza o título
                xaxis_title="Produto",  # Rótulo do eixo x
                yaxis_title="Volume (L)",  # Rótulo do eixo y
                font=dict(size=14),  # Configuração de fonte
                legend_title_text="Volume Dosado"  # Título da legenda
            )
            
            # Adicionar a linha com a somatória total
            total_consumo = df_somatorio["Total Dosado"].sum()
            dose_media = df_somatorio["Dose"].sum()
            
            # Gerar o HTML da tabela estilizada
            html_tb_cons_prod = (
                df_somatorio.style
                .format({"Necessário": "{:.3f} L", "Total Dosado": "{:.3f} L", "Receita": "{:.1f} ml/100Kg", "Dose": "{:.1f} ml/100Kg", "Variação": "{:.3f} %"})  # Formatação com 2 casas decimais
                .set_table_styles([            # Estilos gerais da tabela
                    {"selector": "thead th", "props": [("font-weight", "bold"), ("text-align", "center"), ("font-size", "13px")]},
                    {"selector": "tbody td", "props": [("text-align", "center"), ("font-size", "12px")]},  # Centralizar textos
                    {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]}  # Fundo alternado
                ])
                .hide(axis='index')   # Remover o índice
                .to_html()  # Converter para HTML
            )

            st.plotly_chart(fig1, use_container_width=True)
            st.markdown(f"""
                <div style="
                    display: flex;
                    flex-direction: column;
                    justify-content: center;  /* Centraliza verticalmente */
                    align-items: flex-end;   /* Alinha à direita */
                    height: 100%;  /* Ocupa toda a altura disponível */
                    text-align: right;
                    ">
                    <!-- Inserir quebras de linha para espaço acima da tabela -->
                    <br><br>
                    {html_tb_cons_prod}
                """, unsafe_allow_html=True)
            # Exibir o consumo total em um markdown separado, garantindo a formatação
            st.markdown(f"""
                <p style="text-align: center; font-size: 13px; margin-top: 20px;">
                    <strong>Consumo Total:</strong> {total_consumo:.2f} L - <strong>Dosagem Média:</strong> {dose_media:.1f} ml/100Kg
                </p>
            """, unsafe_allow_html=True)

            # Obter valores únicos na coluna 'observacao'
            observacoes_unicas = df_filtrado['observacao'].dropna().unique()  # Remove NaN e pega os valores únicos
            
            if len(observacoes_unicas) > 1:
                # Exibir as observações únicas no Streamlit
                st.markdown(f"""
                    <p style="text-align: center; font-size: 13px; margin-top: 20px;">
                        <strong>OBSERVAÇÕES:</strong>
                        <br>
                        {'<br>'.join(observacoes_unicas)}  <!-- Exibe cada observação única em uma nova linha -->
                    </p>
                """, unsafe_allow_html=True)

        else:
            st.warning("Nenhum dado encontrado para as seleções.")
            
    else:
        st.warning("Por favor, carregue um arquivo primeiro.")

# Produção
elif st.session_state["menu"] == "Produção":
    st.header("Dashboard Produção")
    if 'dosadores' in  st.session_state:
        dosadores = st.session_state['dosadores']
    if 'df' in st.session_state:  # Verifica se o arquivo foi carregado
        df = st.session_state['df']
        # Verifique se as colunas de data e hora existem no seu DataFrame
        if 'hora_ini' in df.columns and 'hora_fim' in df.columns:
            with st.expander("Filtrar por Data", expanded=False):  # Pode ajustar 'expanded' para True ou False    
                # Seletores para data/hora inicial e final
                col1, col2 = st.columns(2)
    
                with col1:
                    # Selecionando data e hora para o Período Inicial
                    periodo_inicio_date = st.date_input("Data Inicial", df['hora_ini'].min().date())
                    periodo_inicio_time = "00:00:00"
                    
                with col2:
                    # Selecionando data e hora para o Período Final
                    periodo_fim_date = st.date_input("Data Final", df['hora_fim'].max().date())
                    periodo_fim_time = "23:59:59"
            
            # Combinar data e hora selecionadas em um único timestamp
            periodo_inicio = pd.to_datetime(f"{periodo_inicio_date} {periodo_inicio_time}")
            periodo_fim = pd.to_datetime(f"{periodo_fim_date} {periodo_fim_time}")
            
            # Filtrar os dados entre o período selecionado
            df_filtrado = df[(df['hora_ini'] >= periodo_inicio) & (df['hora_fim'] <= periodo_fim)]
            
            # Calcular valores exibidos no relatório
            tempo_total = df_filtrado['tempo_ciclo'].sum()
            producao = (df_filtrado['pv_bat'].sum()/1000)
            if tempo_total > 0:
                produtividade = round(producao / (tempo_total / 3600), 2)  # Em Ton/h
            else:
                produtividade = 0.0
            num_lotes = df_filtrado['lote'].nunique()
            num_receitas = df_filtrado['receita'].nunique()
            num_bateladas = len(df_filtrado)
            
            # Formatar as datas e horas
            periodo_inicio_formatado = periodo_inicio.strftime('%d-%m-%Y')
            periodo_fim_formatado = periodo_fim.strftime('%d-%m-%Y')
            
            # Convertendo o total de segundos para o formato horas:minutos:segundos
            horas = tempo_total // 3600  # Divisão inteira para obter as horas
            minutos = (tempo_total % 3600) // 60  # Resto da divisão por 3600 (horas), dividido por 60 para minutos
            segundos = tempo_total % 60  # Resto da divisão por 60 para segundos
            
            # Formatando no formato horas:minutos:segundos
            tempo_total_formatado = f"{int(horas):02}:{int(minutos):02}:{int(segundos):02}"
            
            st.markdown(f"""
                <p style="text-align: right; font-size: 13px;">
                    Período de <strong>{periodo_inicio_formatado}</strong> à <strong>{periodo_fim_formatado}</strong>
                </p>
            """, unsafe_allow_html=True)
            
            media_bat = df_filtrado['pv_bat'].mean()
            tempo_med_bat = df_filtrado['tempo_ciclo'].mean()
 
            st.markdown("---")
                
            # Função para criar um cartão de métrica
            def card_metrica(titulo, valor, unidade=None):
                return f"""
                <div style="
                    display: flex; 
                    align-items: center; 
                    background-color: #FFFFFF; 
                    border: 1px solid #FF9933; 
                    border-radius: 10px; 
                    padding: 10px; 
                    box-shadow: 4px 4px 8px rgba(0, 0, 0, 0.3); 
                    margin: 10px;">
                    <div style="
                        width: 10px; 
                        background-color: #FF9933; 
                        border-radius: 10px 0 0 10px;">
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <h4 style="color: #242221; margin: 0; font-size: 17px;">{titulo}</h4>
                        <h3 style="color: #FF9933; margin: 3px 0 5px 0; font-size: 35px;">
                            {valor} 
                            <span style="font-size: 20px; color: #FFC994;">{unidade or ''}</span>
                        </h3>
                    </div>
                </div>
                """
            # Layout dos cartões
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(card_metrica("Produção", f"{producao:.2f}", "Ton"), unsafe_allow_html=True)
            
            with col2:
                st.markdown(card_metrica("Tempo Efetivo", tempo_total_formatado), unsafe_allow_html=True)
            
            with col3:
                st.markdown(card_metrica("Produtividade Média", f"{produtividade}", "Ton/h"), unsafe_allow_html=True)
            
            col4, col5, col6 = st.columns(3)
            
            with col4:
                st.markdown(card_metrica("Peso Médio / Batelada", f"{media_bat:.2f}", "Kg"), unsafe_allow_html=True)
            
            with col5:
                st.markdown(card_metrica("Tempo Médio / Batelada", f"{tempo_med_bat:.1f}", "s"), unsafe_allow_html=True)
            
            with col6:
                st.markdown(card_metrica("Número de Bateladas", num_bateladas), unsafe_allow_html=True)
            
            col7, col8, col9 = st.columns(3)
            
            with col7:
                st.markdown(card_metrica("Número de lotes", num_lotes), unsafe_allow_html=True)
            
            with col8:
                st.markdown(card_metrica("Quantidade de Receitas", num_receitas), unsafe_allow_html=True)

            st.markdown("---")       
            
            df_filtrado['pv_bat']=df_filtrado['pv_bat']/1000
            
            # Criando o gráfico de pizza Produção x Operador
            fig = px.pie(
                df_filtrado,
                names="operador",
                values="pv_bat",
                title="Produção x Operador",
                color_discrete_sequence=px.colors.sequential.Oranges,
                hole=0.3  # Gráfico do tipo donut
                )
            # Personalizando o conteúdo exibido ao passar o mouse
            fig.update_traces(
                textinfo='label+percent',  # Exibe rótulos e porcentagens
                textfont_size=10,
                hovertemplate=(
                    'Operador: %{label}<br>'  # Nome da receita
                    'Produção: %{value:.2f} Ton<br>'  # Consumo com 2 casas decimais
                    'Percentual: %{percent:.1%}'  # Percentual com 1 casa decimal
                )
            )
            # Layout do gráfico
            fig.update_layout(
                title_x=0.2,  # Centraliza o título
                font=dict(size=14)
                )
            
           
            
            # Criando o gráfico de pizza Produção x Ensaque
            fig1 = px.pie(
                df_filtrado,
                names="ensaque",
                values="pv_bat",
                title="Produção x Ensaque",
                color_discrete_sequence=px.colors.sequential.Oranges,
                hole=0.3  # Gráfico do tipo donut
                )
            # Personalizando o conteúdo exibido ao passar o mouse
            fig1.update_traces(
                textinfo='label+percent',  # Exibe rótulos e porcentagens
                textfont_size=10,
                hovertemplate=(
                    'Ensaque: %{label}<br>'  # Nome da receita
                    'Produção: %{value:.2f} Ton<br>'  # Consumo com 2 casas decimais
                    'Percentual: %{percent:.1%}'  # Percentual com 1 casa decimal
                )
            )
            # Layout do gráfico
            fig1.update_layout(
                title_x=0.2,  # Centraliza o título
                font=dict(size=14)
                )
            
            # Criando o gráfico de pizza Produção x especie
            fig2 = px.pie(
                df_filtrado,
                names="especie",
                values="pv_bat",
                title="Produção x Espécie",
                color_discrete_sequence=px.colors.sequential.Oranges,
                hole=0.3  # Gráfico do tipo donut
                )
            # Personalizando o conteúdo exibido ao passar o mouse
            fig2.update_traces(
                textinfo='label+percent',  # Exibe rótulos e porcentagens
                textfont_size=10,
                hovertemplate=(
                    'especie: %{label}<br>'  # Nome da receita
                    'Produção: %{value:.2f} Ton<br>'  # Consumo com 2 casas decimais
                    'Percentual: %{percent:.1%}'  # Percentual com 1 casa decimal
                )
            )
            # Layout do gráfico
            fig2.update_layout(
                title_x=0.2,  # Centraliza o título
                font=dict(size=14)
                )
            
            # Criando o gráfico de pizza Produção x Peneira
            fig3 = px.pie(
                df_filtrado,
                names="peneira",
                values="pv_bat",
                title="Produção x Peneira",
                color_discrete_sequence=px.colors.sequential.Oranges,
                hole=0.3  # Gráfico do tipo donut
                )
            # Personalizando o conteúdo exibido ao passar o mouse
            fig3.update_traces(
                textinfo='label+percent',  # Exibe rótulos e porcentagens
                textfont_size=10,
                hovertemplate=(
                    'Peneira: %{label}<br>'  # Nome da receita
                    'Produção: %{value:.2f} Ton<br>'  # Consumo com 2 casas decimais
                    'Percentual: %{percent:.1%}'  # Percentual com 1 casa decimal
                )
            )
            # Layout do gráfico
            fig3.update_layout(
                title_x=0.2,  # Centraliza o título
                font=dict(size=14)
                )
            
            # Soma dos valores de produção por receita
            df_filtrado_agrupado = df_filtrado.groupby("receita", as_index=False)["pv_bat"].sum()
            
            # Classificando os dados em ordem crescente pela coluna 'pv_bat' (Produção)
            df_filtrado_agrupado = df_filtrado_agrupado.sort_values(by="pv_bat", ascending=True)

            # Criar uma lista de tons de laranja
            orange_scale = px.colors.sequential.Oranges
            
            # Mapeando as receitas para tons de laranja
            unique_receitas = df_filtrado_agrupado["receita"].unique()
            color_map = {receita: orange_scale[i % len(orange_scale)] for i, receita in enumerate(unique_receitas)}

            # Criação do gráfico de barras verticais com tons de laranja por receita
            fig4 = px.bar(
                df_filtrado_agrupado,
                x="receita",  # Eixo X será a Receita
                y="pv_bat",  # Eixo Y será a soma da Produção
                title="Produção x Receita",
                color="receita",  # As cores serão baseadas na Receita
                color_discrete_map=color_map  # Mapeamento de cores sequenciais
            )
            
            # Adicionando rótulos com valores nas barras
            fig4.update_traces(
                texttemplate='%{y:.2f}',  # Exibe os valores com 2 casas decimais no topo das barras
                textposition='outside',  # Coloca os rótulos fora das barras
                hovertemplate='Receita: %{x}<br>Produção: %{y:.2f} Ton'  # Personaliza o texto ao passar o mouse
            )
            
            # Layout do gráfico
            fig4.update_layout(
                title_x=0.3,  # Centraliza o título
                font=dict(size=14),
                xaxis_title="receita",  # Título do eixo X
                yaxis_title="Produção",  # Altera o título do eixo Y
                margin=dict(t=30)  # Aumenta a margem superior para dar mais espaço para os rótulos
            )

            col1, col2, col3 = st.columns(3)  

            with col1:
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.plotly_chart(fig1, use_container_width=True)
            with col3:  
                st.plotly_chart(fig2, use_container_width=True)
            
            col4, col5 = st.columns([1,2])  

            with col4:
                st.plotly_chart(fig3, use_container_width=True)
            with col5:
                st.plotly_chart(fig4, use_container_width=True)
                
            #Grafico de calor de produção por dias da semana
            # Extração de hora e dia da semana
            df_filtrado['hora'] = df['hora_fim'].dt.hour
            df_filtrado['dia_semana'] = df['hora_fim'].dt.weekday  # 0 = segunda-feira, 1 = terça-feira, ...
            
            # Agrupar os dados por hora e dia da semana para somar a produção
            df_week = df_filtrado.groupby(['dia_semana', 'hora']).agg({'pv_bat': 'sum'}).reset_index()
            
            # Obter valores mínimo e máximo de hora
            hora_min = df_week['hora'].min()
            hora_max = df_week['hora'].max()

            # Preencher os valores ausentes com zero para garantir que todas as combinações de hora e dia apareçam
            dias_semana = list(range(7))  # 0 = segunda-feira, ..., 6 = domingo
            horas_do_dia = list(range(hora_min, hora_max + 1))  # De hora_min até hora_max (incluindo o último valor)
            
            # Criar uma multi-index que contém todas as combinações possíveis de dia_semana e hora
            df_completo = pd.MultiIndex.from_product([dias_semana, horas_do_dia], names=['dia_semana', 'hora'])
            
            # Reindexar para garantir que todas as combinações de dia e hora apareçam, preenchendo com 0 caso faltem dados
            df_week_completo = df_week.set_index(['dia_semana', 'hora']).reindex(df_completo, fill_value=0).reset_index()
            
            # Criar o gráfico de heatmap usando Plotly
            fig6 = go.Figure(data=go.Heatmap(
                z=df_week_completo['pv_bat'],  # Valores de produção
                x=df_week_completo['dia_semana'],  # Dias da semana (0 = segunda-feira, ..., 6 = domingo)
                y=df_week_completo['hora'],  # Horas do dia (hora_min até hora_max)
                colorscale='Oranges',  # Escala de cores em tons de laranja
                hovertemplate='<b>Dia da Semana:</b> %{x}<br><b>Hora:</b> %{y}:00<br><b>Produção:</b> %{z:.2f} Ton<extra></extra>',  # Customizar o texto ao passar o mouse
                showscale=False  # Remover a barra lateral de graduação de cor
            ))
            
            # Ajuste do layout
            fig6.update_layout(
                xaxis=dict(tickmode='array', tickvals=list(range(7)), ticktext=["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]),  # Marcar os dias da semana
                yaxis=dict(tickmode='array', tickvals=list(range(hora_min, hora_max + 1)), ticktext=[f"{i}:00" for i in range(hora_min, hora_max + 1)]),  # Mostrar apenas as horas no intervalo
                title="Produção em Horas x Dias da Semana",
                title_x=0.37,  # Centraliza o título
                font=dict(size=14),
                xaxis_title="Dia da Semana",
                yaxis_title="Hora do Dia",
                plot_bgcolor='white',  # Fundo branco do gráfico
                paper_bgcolor='white',  # Fundo branco da área externa do gráfico
            )
            
            # Exibir o gráfico no Streamlit
            st.plotly_chart(fig6, use_container_width=True)
            
            #Grafico de consumo
            # Criar um DataFrame contendo os nomes dos produtos e a soma do consumo
            def criar_df_somatorio(df_filtrado, dosadores):
                # Lista para armazenar os dados agregados
                dados_agregados = []
                # print("Após a definição, dosadores:", dosadores)
                # Iterar sobre os dosadores válidos
                for idx, dosador in enumerate(dosadores, start=1):
                    # Definir os nomes das colunas relevantes
                    nome_col = f"nome_prod{str(idx).zfill(2)}"
                    pv_dos_col = f"pv_dos{str(idx).zfill(2)}"
            
                    # Verificar se ambas as colunas existem
                    if nome_col in df_filtrado.columns and pv_dos_col in df_filtrado.columns:
                        # Agrupar por produto e somar o consumo
                        df_agrupado = df_filtrado.groupby(nome_col).agg({pv_dos_col: "sum"}).reset_index()
                        df_agrupado.rename(columns={nome_col: "Produto", pv_dos_col: "Consumo"}, inplace=True)
            
                        # Adicionar os dados ao conjunto final
                        dados_agregados.append(df_agrupado)
            
                # Verificar se há dados para concatenar
                if not dados_agregados:
                    st.warning("Nenhum dosador válido foi encontrado no arquivo carregado.")
                    return pd.DataFrame(columns=["Produto", "Consumo"])  # Retornar DataFrame vazio
            
                # Concatenar todos os DataFrames em um único DataFrame
                df_resultado = pd.concat(dados_agregados, ignore_index=True)
            
                # Agrupar novamente para consolidar os valores de consumo para o mesmo produto
                df_resultado = df_resultado.groupby("Produto").agg({"Consumo": "sum"}).reset_index()
            
                return df_resultado
            
            df_somatorio = criar_df_somatorio(df_filtrado, dosadores)
            
            df_somatorio = df_somatorio.dropna()  # Remove todas as linhas com NaN em qualquer coluna
            df_somatorio = df_somatorio[df_somatorio['Consumo'] != 0]  # Filtra linhas onde Consumo é diferente de 0
            df_somatorio['Consumo'] = df_somatorio['Consumo'] / 1000
            df_somatorio = df_somatorio.sort_values(by="Consumo", ascending=True)
            
            # Mapeamento de cores para os produtos
            unique_produtos = df_somatorio["Produto"].unique()
            color_map1 = {produto: orange_scale[i % len(orange_scale)] for i, produto in enumerate(unique_produtos)}
            
            # Criação do gráfico de barras verticais
            fig5 = px.bar(
                df_somatorio,
                x="Produto",  # Eixo X será o nome do Produto
                y="Consumo",  # Eixo Y será o consumo
                title="Consumo x Produto",
                color="Produto",  # A cor será baseada no Produto
                color_discrete_map=color_map1  # Mapeamento de cores
            )
            
            # Adicionando rótulos com valores nas barras
            fig5.update_traces(
                texttemplate='%{y:.2f}',  # Exibe os valores com 2 casas decimais no topo das barras
                textposition='outside',  # Coloca os rótulos fora das barras
                hovertemplate='Receita: %{x}<br>Produção: %{y:.2f} Ton'  # Personaliza o texto ao passar o mouse
            )
            
            # Layout do gráfico
            fig5.update_layout(
                title_x=0.3,  # Centraliza o título
                font=dict(size=14),
                xaxis_title="Receita",  # Título do eixo X
                yaxis_title="Produção",  # Altera o título do eixo Y
                margin=dict(t=30)  # Aumenta a margem superior para dar mais espaço para os rótulos
            )
       
            df_somatorio = df_somatorio.sort_values(by="Consumo", ascending=True)
            # Adicionar a linha com a somatória total
            total_consumo = df_somatorio["Consumo"].sum()
            
            # Gerar o HTML da tabela estilizada
            html_tb_cons_prod = (
                df_somatorio.style
                .format({"Consumo": "{:.2f} L"})  # Formatação com 2 casas decimais
                .set_table_styles([            # Estilos gerais da tabela
                    {"selector": "thead th", "props": [("font-weight", "bold"), ("text-align", "center"), ("font-size", "13px")]},
                    {"selector": "tbody td", "props": [("text-align", "center"), ("font-size", "12px")]},  # Centralizar textos
                    {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]}  # Fundo alternado
                ])
                .hide(axis='index')   # Remover o índice
                .to_html()  # Converter para HTML
            )
           
            col1, col2 = st.columns([3, 1], gap="large")  # Ajustar proporções das colunas e espaço
            with col1:
                st.plotly_chart(fig5, use_container_width=True)
            with col2:
                st.markdown(f"""
                    <div style="
                        display: flex;
                        flex-direction: column;
                        justify-content: center;  /* Centraliza verticalmente */
                        align-items: flex-end;   /* Alinha à direita */
                        height: 100%;  /* Ocupa toda a altura disponível */
                        text-align: right;
                    ">
                        <!-- Inserir quebras de linha para espaço acima da tabela -->
                        <br><br>
                        {html_tb_cons_prod}
                """, unsafe_allow_html=True)
                # Exibir o consumo total em um markdown separado, garantindo a formatação
                st.markdown(f"""
                    <p style="text-align: center; font-weight: bold; font-size: 13px; margin-top: 20px;">
                        Consumo Total: {total_consumo:.2f} L
                    </p>
                """, unsafe_allow_html=True)
            
            
            # Agrupando os dados por lote e Receita
            df_agrupado = df_filtrado.groupby(["lote", "receita"]).agg(
                hora_inicio=("hora_ini", "min"),
                hora_final=("hora_fim", "max"),
                sementes_tratadas=("pv_bat", "sum"),
                num_bateladas=("lote", "size"),
                qtd_necessaria=("total_sp", "sum"),
                qtd_dosada=("total_consumo", "sum")
            ).reset_index()

            # Convertendo as unidades para toneladas (divisão por 1000)
            df_agrupado["sementes_tratadas"] = df_agrupado["sementes_tratadas"] / 1000
            df_agrupado["qtd_necessaria"] = df_agrupado["qtd_necessaria"] / 1000
            df_agrupado["qtd_dosada"] = df_agrupado["qtd_dosada"] / 1000

            # Calculando Variação de Dosagem (%)
            df_agrupado["variacao_dosagem"] = ((df_agrupado["qtd_dosada"] / df_agrupado["qtd_necessaria"]) - 1) * 100
            
            # Formatando os valores com 2 casas decimais
            df_agrupado["sementes_tratadas"] = df_agrupado["sementes_tratadas"].map("{:.2f}".format)
            df_agrupado["qtd_necessaria"] = df_agrupado["qtd_necessaria"].map("{:.2f}".format)
            df_agrupado["qtd_dosada"] = df_agrupado["qtd_dosada"].map("{:.2f}".format)
            df_agrupado["variacao_dosagem"] = df_agrupado["variacao_dosagem"].map("{:.3f}".format)

            # Formatando as colunas de hora
            df_agrupado["hora_inicio"] = pd.to_datetime(df_agrupado["hora_inicio"]).dt.strftime("%d-%m-%Y / %H:%M:%S")
            df_agrupado["hora_final"] = pd.to_datetime(df_agrupado["hora_final"]).dt.strftime("%H:%M:%S")

            # Reordenando as colunas
            df_agrupado = df_agrupado[[
                "hora_inicio", "hora_final", "lote", "receita",
                "sementes_tratadas", "num_bateladas",
                "qtd_necessaria", "qtd_dosada", "variacao_dosagem"
            ]]

            # Renomeando colunas para exibição
            df_agrupado.rename(columns={
                "hora_inicio": "Início",
                "hora_final": "Fim",
                "sementes_tratadas": "Qtd. Tratada",
                "num_bateladas": "Núm. Bateladas",
                "qtd_necessaria": "Qtd. Necessária",
                "qtd_dosada": "Qtd. Dosada",
                "variacao_dosagem": "Variação Dosagem"
            }, inplace=True)

            # Ordenando pela coluna Início
            df_agrupado.sort_values(by="Início", inplace=True)

            # Garantir que 'Variação Dosagem' seja numérico
            df_agrupado['Variação Dosagem'] = pd.to_numeric(df_agrupado['Variação Dosagem'], errors='coerce')

            # Criando o gráfico de linha
            plt.figure(figsize=(10, 2))
            
            # Plotando a linha de variação de dosagem
            plt.plot(df_agrupado['Início'], df_agrupado['Variação Dosagem'], color='darkorange', linewidth=2)
            
            # Adicionando círculos em cada amostragem
            plt.scatter(df_agrupado['Início'], df_agrupado['Variação Dosagem'], color='darkorange', zorder=5)

            # Adicionando linhas pivot
            plt.axhline(y=5, color='lightcoral', linestyle='--', linewidth=1)
            plt.axhline(y=-5, color='lightcoral', linestyle='--', linewidth=1)
            
            # Definindo limites dinâmicos do eixo Y
            min_dosagem = df_agrupado['Variação Dosagem'].min()
            max_dosagem = df_agrupado['Variação Dosagem'].max()
            
            # Ajustando o limite inferior e superior do eixo Y
            if min_dosagem < -5.5:
                y_min = min_dosagem - 3
            else:
                y_min = -5.5
            
            if max_dosagem > 5.5:
                y_max = max_dosagem + 3
            else:
                y_max = 5.5
            
            # Ajustando o limite do eixo Y com base nos valores calculados
            plt.ylim(y_min, y_max)
 
            # Ocultando os valores do eixo X e Y
            plt.xticks([])  # Remove os valores do eixo X
            plt.yticks([])  # Define as marcas do eixo Y entre -5 e 5
            
            # Adicionando uma linha central em 0
            plt.axhline(y=0, color='lightgrey', linewidth=1)
            
            # Exibindo o gráfico sem borda em volta
            plt.gca().spines['top'].set_visible(False)
            plt.gca().spines['right'].set_visible(False)
            plt.gca().spines['left'].set_visible(False)
            plt.gca().spines['bottom'].set_visible(False)
            
            
            # Exibindo o gráfico
            st.markdown("---")       
            st.markdown("""
                <p style="text-align: center; font-weight: bold; font-size: 16px; margin-top: 20px;">
                    Variação de Dosagem
                </p>
            """, unsafe_allow_html=True)
            plt.grid(True, axis='x', linestyle='--', alpha=0.6)
            plt.tight_layout()
            st.pyplot(plt)
             
        else:
            st.warning("As colunas 'Data' e/ou 'Hora' não foram encontradas no DataFrame.")
    else:
        st.warning("Por favor, carregue um arquivo primeiro.")