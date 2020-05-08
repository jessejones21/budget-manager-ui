import PySimpleGUI as sg
from datetime import datetime
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

tab1_layout = [ [sg.T('Upload CSV:', font= ('Any', 13, 'bold'), pad= ((3,0),(10,0)))],
                 [sg.T('Table:'), 
                 sg.Combo(['expense', 'income'], key= 'tableName1'),
                 sg.T('File:'), 
                 sg.InputText(key='csvFile', size=(33, 1), do_not_clear=False), 
                 sg.FileBrowse(target='csvFile', size=(6, 1))],
          
                [sg.T('Add Expense:', font= ('Any', 13, 'bold'), pad=((3,0),(10,0)))],
                [sg.T('Amount:'), sg.InputText(size=(10,1), key='expAmount', do_not_clear=False), 
                 sg.T('Category:'), 
                 sg.Combo(['','Shopping', 'Groceries', 'Food & Drink', 'Travel', 'Personal', 'Bill'], key='expCat', default_value=''),
                 sg.T('Date:'), 
                 sg.CalendarButton('Calendar', button_color=('black', 'light gray'), key='expDate')],
                [sg.T('Description:'), 
                 sg.InputText(key='expDescription', do_not_clear=False)],

                [sg.T('Add Income:', font= ('Any', 13, 'bold'), pad= ((3,0),(10,0)))],
                [sg.T('Amount:'), 
                 sg.InputText(size=(10,1), key='incAmount', do_not_clear=False), 
                 sg.T('Date:'), 
                 sg.CalendarButton('Calendar', button_color=('black', 'light gray'), key='incDate')],
                [sg.T('Description:'), sg.InputText(key='incDescription', do_not_clear=False)], 
                [sg.B('Submit', pad= (5,(15,4)), size=(8, 1)), 
                 sg.B('Cancel', pad= (5,(15,4)), size=(8, 1))] 
              ]


tab2_layout = [[sg.T('Table:', pad= ((5,0),(10,0))), 
                sg.Combo(['expense', 'income'], key= 'tableName', pad= ((3,0),(10,0))), 
                sg.T('Month:', pad=((30,0),(10,0))), 
                sg.Combo(['','January', 'February', 'March', 
                          'April', 'May', 'June', 'July', 
                          'August', 'September', 'October',
                          'November', 'December'], key='month', pad= ((3,0),(10,0))),
                sg.T('Year:', pad=((30,0),(10,0))),
                sg.Combo(['', '2020', '2019', '2018', '2017', '2016',
                          '2015', '2014', '2013', '2012', '2011', 
                          '2010', '2009', '2008', '2007'], key='year', pad= ((3,0),(10,0)))],
                [sg.T('Category:', pad= ((5,0),(20,0))),
                sg.Combo(['Shopping', 'Groceries', 'Food & Drink', 
                          'Travel', 'Personal', 'Bill'], 
                          key='tableCat', pad= (0,(20,0)))],
                [sg.B('View Table', pad= (5,(15,4)), size=(9, 1)),
                sg.B('Summary', pad= (5,(15,4)), size=(8, 1)),
                sg.B('Close', pad= ((205,0),(15,4)), size=(8, 1))]
              ]


layout = [[sg.TabGroup([[sg.Tab('Upload', tab1_layout), sg.Tab('View', tab2_layout)]])]] 
                
window = sg.Window('Budget Manager', layout)

def init():
    # initialize database
    con = sqlite3.connect('budgetTrack.db')
    cur = con.cursor()
    createExpTable = '''
    CREATE TABLE IF NOT EXISTS expense (
        date TEXT,
        amount INTEGER,
        category TEXT,
        description TEXT)
    '''
    createIncTable = '''
    CREATE TABLE IF NOT EXISTS income (
        date TEXT,
        amount INTEGER,
        description TEXT)
    '''
    cur.execute(createExpTable)
    cur.execute(createIncTable)
    con.commit()
    con.close()


def viewTable(tableName, year, month='', category=''):
    #allows user to view entire database table or subset of table
    data = []
    con = sqlite3.connect('budgetTrack.db')
    cur = con.cursor()

    if category and month:
        selectAll = f'''
        SELECT * FROM '{tableName}' WHERE category = '{category}' AND date LIKE '{month}%{year}'
        '''
        header = f' - {category.upper()} - 0{month}/{year}'
        
    elif category:
        selectAll = f'''
        SELECT * FROM '{tableName}' WHERE category = '{category}' AND date LIKE '%{year}'
        '''
        header = f' - {category.upper()} - {year}'
        
    elif month:
        selectAll = f'''
        SELECT * FROM '{tableName}' WHERE date LIKE '{month}%{year}'
        '''
        header = f' - 0{month}/{year}'
        
    else: 
        selectAll = f"SELECT * FROM '{tableName}' WHERE date LIKE '%{year}'"
        header = f' - {year}'

    df = pd.read_sql_query(selectAll, con)
    df['amount'] = df['amount'].astype(str)
    data = df.values.tolist()
    headers = df.columns.values.tolist()

    tableLayout = [
              [sg.Table(values=data,
               headings=headers)]
            ]
    
    tableWindow = sg.Window(tableName.upper() + header, tableLayout)
    event, values = tableWindow.Read()

    
def viewStats(year, nameMonth='', month=''):
    #create pd dataframes from database tables
    con = sqlite3.connect('budgetTrack.db')
    exp = f"SELECT * FROM expense WHERE date LIKE '%{year}'"
    inc = f"SELECT * FROM income WHERE date LIKE '%{year}'"
    expdf = pd.read_sql_query(exp, con)
    incdf = pd.read_sql_query(inc, con)
    con.commit()
    con.close()

    
    if month:
        #aggregating data based on selected month and making calculations on the result 
        monthSpent = round(expdf.loc[expdf.date.str.startswith(f'{month}'), 'amount'].sum(), 2)
        monthIncome = round(incdf.loc[incdf.date.str.startswith(f'{month}'), 'amount'].sum(), 2)
        monthSaved =  round(monthIncome - monthSpent, 2)
        savingsPer = round((monthSaved / monthIncome) * 100, 2)
        if monthSaved < 0:
            monthSaved = 0
        if savingsPer < 0:
            savingsPer = 0
            
        #aggregating amount spent for each category during selected month
        g = expdf.loc[(expdf['category'] == 'Groceries') & (expdf.date.str.startswith(f'{month}')), 'amount'].sum() 
        t = expdf.loc[(expdf['category'] == 'Travel') & (expdf.date.str.startswith(f'{month}')), 'amount'].sum() 
        s = expdf.loc[(expdf['category'] == 'Shopping') & (expdf.date.str.startswith(f'{month}')), 'amount'].sum()
        f = expdf.loc[(expdf['category'] == 'Food & Drink') & (expdf.date.str.startswith(f'{month}')), 'amount'].sum()
        p = expdf.loc[(expdf['category'] == 'Personal') & (expdf.date.str.startswith(f'{month}')), 'amount'].sum()
        b = expdf.loc[(expdf['category'] == 'Bill') & (expdf.date.str.startswith(f'{month}')), 'amount'].sum()

        amounts = [g, t, s, f, p, b]
        labels = ['groceries', 'travel', 'shopping', 'food & drink', 'personal', 'bill']
 
        def draw_figure(canvas, loc=(0, 0)):
            #creating pie chart to show breakdown of amount spent on each category during selected month
            fig = plt.figure(figsize = (5.75,3.5))
            patches, text = plt.pie(amounts, startangle=90, colors=['yellow', 'purple', 'red', 'blue', 'orange', 'green'])
            legLabels = ['{0} - $ {1:1.2f}'.format(i,j) for i,j in zip(labels, amounts)]
            plt.legend(patches, legLabels, bbox_to_anchor=(-.625, 1.17), loc='upper left', fontsize=8)
            figure_canvas_agg = FigureCanvasTkAgg(fig, canvas)
            figure_canvas_agg.get_tk_widget().pack()
    
        #layout of summary stats window
        statsLayout = [ [sg.T(f'Summary for {nameMonth} {year}:', font= ('Any', 13, 'bold'))],
                        [sg.T(f' Income: ${monthIncome}')],
                        [sg.T(f' Expenses: ${monthSpent}')],
                        [sg.T(f' Savings: ${monthSaved}')],
                        [sg.T(f' Savings Percentage: {savingsPer}%')],
                        [sg.Canvas(size=(40, 25), key='canvas')]
                      ]

        statsWindow = sg.Window('Stats Summary', statsLayout, finalize=True)

        fig_canvas_agg = draw_figure(statsWindow['canvas'].TKCanvas)

        event, values = statsWindow.Read()


    if not month:
        #aggregating data for entire selected year and making calculations on the result
        totalSpent = round(expdf['amount'].sum(), 2)
        totalIncome = round(incdf['amount'].sum(), 2)
        totalSaved =  totalIncome - totalSpent
        savingsPer = round((totalSaved / totalIncome) * 100, 2)

        #aggregating amount spent for each category during selected year
        g = expdf.loc[(expdf['category'] == 'Groceries'), 'amount'].sum() 
        t = expdf.loc[(expdf['category'] == 'Travel'), 'amount'].sum() 
        s = expdf.loc[(expdf['category'] == 'Shopping'), 'amount'].sum()
        f = expdf.loc[(expdf['category'] == 'Food & Drink'), 'amount'].sum()
        p = expdf.loc[(expdf['category'] == 'Personal'), 'amount'].sum()
        b = expdf.loc[(expdf['category'] == 'Bill') & (expdf.date.str.startswith(f'{month}')), 'amount'].sum()

        amounts = [g, t, s, f, p, b]
        labels = ['groceries', 'travel', 'shopping', 'food & drink', 'personal', 'bill']

        def draw_figure(canvas, loc=(0, 0)):
            #creating pie chart to show breakdown of amount spent on each category during selected year
            fig = plt.figure(figsize = (5.75,3.5))
            patches, text = plt.pie(amounts, startangle=90, colors=['yellow', 'purple', 'red', 'blue', 'orange', 'green'])
            legLabels = ['{0} - $ {1:1.2f}'.format(i,j) for i,j in zip(labels, amounts)]
            plt.legend(patches, legLabels, bbox_to_anchor=(-.625, 1.17), loc='upper left', fontsize=8)
            figure_canvas_agg = FigureCanvasTkAgg(fig, canvas)
            figure_canvas_agg.get_tk_widget().pack()
        
        #layout of summary stats window
        statsLayout = [ [sg.T(f'Summary for {year}:', font= ('Any', 13, 'bold'))],
                        [sg.T(f'Income: ${totalIncome}')],
                        [sg.T(f'Expenses: ${totalSpent}')],
                        [sg.T(f'Savings: ${totalSaved}')],
                        [sg.T(f'Savings Percentage: {savingsPer}%')],
                        [sg.Canvas(size=(40, 25), key='canvas')]
                      ]

        statsWindow = sg.Window('Stats Summary', statsLayout, finalize=True)

        fig_canvas_agg = draw_figure(statsWindow['canvas'].TKCanvas)

        event, values = statsWindow.Read()

    
def logExp(date, amount, category, description=''):
    # logs expense in the expense table in database
    data = (date, amount, category, description)
    con = sqlite3.connect('budgetTrack.db')
    cur = con.cursor()
    insert = 'INSERT INTO expense VALUES(?, ?, ?, ?)'
    cur.execute(insert, data)
    con.commit()
    con.close()

def logInc(date, amount, description=''):
    # logs income in the income table in database
    data = (date, amount, description)
    con = sqlite3.connect('budgetTrack.db')
    cur = con.cursor()
    insert = 'INSERT INTO income VALUES(?, ?, ?)'
    cur.execute(insert, data)
    con.commit()
    con.close()
    
def log_csv(file, tableName):
    # log csv file in the database - must input entire file path
    con = sqlite3.connect('budgetTrack.db')
    cur = con.cursor()
    read_file = pd.read_csv(file)
    read_file.to_sql(f'{tableName}', con, if_exists='append', index=False)
    con.commit()
    con.close()
    
while True:
    event, values = window.Read()
    
    if event in ('Close', 'Cancel', None):
        break
        
    if event == 'Submit':
        #uploading data into the data base
        try:
            init()
            if values['csvFile']:
                log_csv(values['csvFile'], values['tableName1'])
                item = 'CSV File'
            if values['expAmount']:
                expdate = values['expDate'].strftime('%#m/%d/%Y')
                logExp(expdate, values['expAmount'], values['expCat'], values['expDescription'])
                item = 'Expense'
            if values['incAmount']:
                incdate = values['incDate'].strftime('%#m/%d/%Y')
                logInc(incdate, values['incAmount'], values['incDescription'])
                item = 'Income'
            window['expCat']('')
            sg.popup(f'{item} Upload Complete')
        except:
            sg.popup('Upload Error: Please try again')
        
            
    if event == 'View Table':
        #viewing entire database tables or subset of tables based on selected year, month, category
        table = values['tableName']
        month = values['month']
        year = values['year']
        category = values['tableCat']
        
        calDict = {'January':1, 'February':2, 'March':3, 
                          'April':4, 'May':5, 'June':6, 'July':7, 
                          'August':8, 'September':9, 'October':10,
                          'November':11, 'December':12}
        try:
            if category and month:
                viewTable(table, month=calDict[month], category=category, year=year)        
            elif month:
                viewTable(table, month=calDict[month], year=year)
            elif category:
                viewTable(table, year=year, category=category)
            else:
                viewTable(table, year)
        except:
            sg.popup('Error: Please try again')
            
    if event == 'Summary':
        #viewing summary stats window for entire tables or subsets of the tables
        month = values['month']
        year = values['year']
        
        calDict = {'January':1, 'February':2, 'March':3, 
                          'April':4, 'May':5, 'June':6, 'July':7, 
                          'August':8, 'September':9, 'October':10,
                          'November':11, 'December':12}
        try: 
            if month:
                viewStats(year=year, nameMonth=month, month=calDict[month])

            if not month:
                viewStats(year=year)
        except:
            sg.popup('No data for the requested period', title='Request Error')
window.close()

