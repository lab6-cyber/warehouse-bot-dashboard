import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import database as db

# Инициализация приложения
app = Dash(__name__)
app.title = 'Складской дашборд'


def load_data():
    """Загрузка данных из базы"""
    orders = db.get_all_orders()
    if orders:
        df = pd.DataFrame(orders, columns=['id', 'user', 'product', 'quantity', 'status', 'date'])
        return df
    else:
        return pd.DataFrame()


# Макет дашборда
app.layout = html.Div([
    html.H1('Дашборд складских операций', style={'textAlign': 'center'}),
    html.P('Статистика заявок и остатков', style={'textAlign': 'center'}),

    html.Div([
        html.H3('Статистика заявок по статусам'),
        dcc.Graph(id='orders-chart')
    ], style={'margin': '20px'}),

    html.Div([
        html.H3('Список заявок'),
        html.Div(id='orders-table')
    ], style={'margin': '20px'}),

    dcc.Interval(
        id='interval-component',
        interval=30 * 1000,
        n_intervals=0
    )
])


@app.callback(
    Output('orders-chart', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_chart(n):
    """Обновление графика"""
    df = load_data()
    if df.empty:
        return px.bar(title='Нет данных')

    status_counts = df['status'].value_counts().reset_index()
    status_counts.columns = ['status', 'count']

    fig = px.bar(status_counts, x='status', y='count',
                 title='Распределение заявок по статусам',
                 labels={'status': 'Статус', 'count': 'Количество'},
                 color='status')
    return fig


@app.callback(
    Output('orders-table', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_table(n):
    """Обновление таблицы"""
    df = load_data()
    if df.empty:
        return html.Div('Нет данных для отображения')

    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[{'name': i, 'id': i} for i in df.columns],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'},
        style_data={'backgroundColor': 'white'},
        filter_action='native',
        sort_action='native'
    )
    return table


def run_dashboard():
    """Запуск дашборда"""
    print(f"Дашборд запущен по адресу: http://127.0.0.1:8050")
    app.run(debug=True, port=8050)


if __name__ == '__main__':
    run_dashboard()