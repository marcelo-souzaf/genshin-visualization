import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.palettes import brewer
from bokeh.plotting import figure
from bokeh.transform import cumsum, factor_cmap

@st.cache
def get_data():
    # Dados obtidos por web scraping de páginas de dados abertos do jogo Genshin Impact
    data = pd.read_csv("data/genshin.csv", sep=";")
    data["Rarity"] = data["Rarity"].astype(str)

    # Obtém dados apenas dos níveis máximos de cada personagem
    return data[data["Level"] == "90/90"].drop(columns="Level").reset_index(drop=True)

def build_palette(column, labels):
    # Se está agrupando por elementos, usa suas cores
    if column == "Element":
        palette = element_colors
    else:
        size = len(labels)
        if size <= 8:
            if size == 2:
                colors = [brewer["Accent"][3][0], brewer["Accent"][3][2]]
            else:
                colors = brewer["Accent"][size]
        else:
            colors = brewer["RdYlBu"][size]
        palette = dict(zip(labels, colors))
    return palette

# @st.cache
def pie():
    data = data_leveled["Element"].value_counts().rename("counts").reset_index()
    data["angles"] = data["counts"] / data_leveled.shape[0] * 2 * np.pi
    data["colors"] = [element_colors[element] for element in data["index"]]

    fig = figure(height=300, toolbar_location=None, tools="hover",
                tooltips="@index: @counts", title="Distribuição de elementos")
    fig.wedge(x=0, y=1, radius=0.5, start_angle=cumsum("angles", include_zero=True),
            end_angle=cumsum("angles"), line_color="black", fill_color="colors", source=data)
    fig.grid.grid_line_color = None
    fig.axis.visible = False
    return fig

# @st.cache
def boxplot(data, log_scale=False):
    title = "Distribuição das estatísticas\nem base logarítmica"
    if log_scale:
        fig = figure(height=284, tools="", x_range=list(data.columns),
                    y_axis_type="log", toolbar_location=None, title=title)
    else:
        fig = figure(height=284, tools="", x_range=list(data.columns),
                    toolbar_location=None, title=title)
    
    for index, column in enumerate(data.columns):
        
        # Categorias ficam entre inteiros do eixo x
        x = index + 0.5
        q1 = data[column].quantile(q=0.25)
        q2 = data[column].quantile(q=0.5)
        q3 = data[column].quantile(q=0.75)

        inter_quartile_range = q3 - q1
        upper = q3 + 1.5 * inter_quartile_range
        lower = q1 - 1.5 * inter_quartile_range

        outliers = data[column][(data[column] > upper) | (data[column] < lower)].dropna()

        # linhas
        fig.segment(x0=x, y0=upper, x1=x, y1=q3, line_color="black")
        fig.segment(x0=x, y0=lower, x1=x, y1=q1, line_color="black")
        # Linhas no fim do intervalo interquartil somado a q3 ou subtraído de q1
        fig.rect(x=x, y=upper, width=0.2, height=0.01, line_color="black")
        fig.rect(x=x, y=lower, width=0.2, height=0.01, line_color="black")
        # Caixas (boxes)
        fig.vbar(x=x, width=0.7, top=q3, bottom=q2, fill_color="#F1D74E", line_color="black")
        fig.vbar(x=x, width=0.7, top=q2, bottom=q1, fill_color="#037A76", line_color="black")
        # Outliers como círculos
        fig.circle(x=[x] * outliers.shape[0], y=outliers, size=6, color="#F38630", fill_alpha=0.6)

    fig.xgrid.grid_line_color = None
    return fig

# @st.cache
def lines():
    index_after_release = 0
    release = datetime(2020, 9, 28)
    data = data_leveled["Release Date"].apply(datetime.fromisoformat).to_frame()
    for index, date in enumerate(data["Release Date"]):
        if date > release:
            index_after_release = index
            break
    data = data[index_after_release:]
    data["HP"] = data_leveled["HP"][index_after_release:]
    data["ATK"] = data_leveled["ATK"][index_after_release:]
    data["DEF"] = data_leveled["DEF"][index_after_release:]

    fig = figure(height=400, tools="", toolbar_location=None, x_axis_type="datetime", y_axis_type="log",
                title="Estatísticas base dos personagens ao longo do tempo pós-lançamento")

    fig.line(x="Release Date", y="HP", source=data, line_width=2, color=element_colors["Hydro"])
    fig.line(x="Release Date", y="ATK", source=data, line_width=2, color=element_colors["Pyro"])
    fig.line(x="Release Date", y="DEF", source=data, line_width=2, color=element_colors["Geo"])
    return fig

def static_draw(container, column, stats):
    metric1, metric2, metric3, metric4 = container.container().columns(4)
    metric1.metric("Número de personagens jogáveis", len(data_leveled), delta=2)
    metric2.metric("Número de regiões disponíveis", 4, delta=1)
    metric3.metric("Meu tempo livre pra jogar", "15 min", delta=-105)
    metric4.metric('"Idade" do jogo',
        f"{(datetime.today().date() - datetime(2020, 9, 28).date()).days} dias", delta=1)

    fig = lines()
    curdoc().add_root(fig)
    container.bokeh_chart(fig, use_container_width=True)

    container.text("""Fonte: <https://genshin-impact.fandom.com/wiki/Category:Characters_by_Release_Date>.
    Número de personagens exclui protagonistas e personagens promocionais.""")

    fig = pie()
    curdoc().add_root(fig)
    column.bokeh_chart(fig, use_container_width=True)

    fig = boxplot(data_leveled[stats[:-1]], log_scale=True)
    curdoc().add_root(fig)
    column.bokeh_chart(fig, use_container_width=True)

def draw():
    container = everything.container()
    container.markdown("## Dados de personagens do jogo Genshin Impact")
    numerical_stats = ["ATK", "DEF", "HP", "Quantidade"]
    groups = ["Rarity", "Weapon", "Element", "Sex", "Region", "Ascension Stat"]

    col1, col2, col3 = container.columns(3)
    args = [col1.selectbox("Agrupar por:", groups, key="selection_0", index=2),
            col2.selectbox("Agrupar por:", groups, key="selection_1", index=4),
            col3.selectbox("Valor:", numerical_stats, key="selection_2", index=3)]

    if args[0] == args[1]:
        if args[2] == "Quantidade":
            grouped = data_leveled[[args[1], "ATK"]].groupby(args[1]).agg("count").reset_index()
        else:
            grouped = data_leveled[args[1:]].groupby(args[1]).agg("mean").reset_index()
        labels = grouped[args[1]].unique()
        palette = build_palette(args[1], labels)

        fig = figure(width=1000, height=600, toolbar_location="right",
                    tools="pan, crosshair, wheel_zoom, box_select, reset", x_range=FactorRange(*labels))

        factors = grouped.iloc[:, 0].unique()
        source = ColumnDataSource(dict(x=factors, top=grouped.iloc[:, 1]))
        fig.vbar(x="x", top="top", source=source, width=0.6, line_color="black", fill_color=
                factor_cmap("x", palette=[palette[f] for f in factors], factors=factors, end=3))
    else:
        # Agrupa e obtém a média conforme o terceiro argumento
        if args[2] == "Quantidade":
            args[2] = "ATK"
            grouped = data_leveled[args].groupby(args[:2]).agg("count")
        else:
            grouped = data_leveled[args].groupby(args[:2]).agg("mean")
        # Obtém todos os pares dos primeiros dois argumentos, ou seja,
        # todas as combinações categóricas do eixo x
        pairs = list(grouped.index)
        grouped.reset_index(inplace=True)
        labels = grouped.iloc[:, 0].unique()
        palette = build_palette(args[0], labels)

        fig = figure(width=1000, height=600, toolbar_location="right",
                    tools="pan, crosshair, wheel_zoom, box_select, reset", x_range=FactorRange(*pairs))

        # Para cada label presente na segunda coluna do agrupamento,
        # cria barras para cada label presente na primeira coluna
        # usando a média dos valores da terceira coluna
        for group in grouped.iloc[:, 1].unique():
            factors = [pair for pair in pairs if pair[1] == group]
            source = ColumnDataSource(dict(x=factors, top=grouped.iloc[:, 2][grouped.iloc[:, 1] == group]))
            fig.vbar(x="x", top="top", source=source, width=0.8, line_color="black", fill_color=
                    factor_cmap("x", palette=[palette[f[0]] for f in factors], factors=factors, end=3))

    fig.x_range.range_padding = 0.1
    fig.xgrid.grid_line_color = None
    fig.xaxis.major_label_orientation = 1
    fig.y_range.start = 0

    curdoc().add_root(fig)
    col1, col2 = container.columns([4, 1])
    col1.bokeh_chart(fig, use_container_width=True)

    static_draw(container, col2, numerical_stats)   

# Define informações sobre a página e o contâiner principal
if "started" not in st.session_state or not st.session_state["started"]:
    st.set_page_config(page_title="Dashboard - Genshin Impact", layout="wide")
    st.session_state["started"] = True
    curdoc().theme = "dark_minimal"

everything = st.empty()
data_leveled = get_data()

element_colors = {"Anemo": "#71C2A7", "Cryo": "#A3D6E3", "Dendro": "#9BC926",
                "Electro": "#B38CC1", "Geo": "#F2B722", "Hydro": "#5FC1F1", "Pyro": "#EA7938"}


# Atualiza o gráfico para as opções selecionadas pelo usuário
draw()
