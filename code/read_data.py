#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  4 18:07:25 2025

@author: urban
"""

#%% Daten einlesen

import os
import pandas as pd
import backtrader as bt

#%%

if os.getlogin() == 'urban':
    base_path = os.getcwd().split('code')[0]
    data_path = os.path.join(base_path,'data')
    out_path = os.path.join(base_path,'results')
else: 
    base_path = r"C:\Users\Bernd\Desktop\Python"
    data_path = os.path.join(base_path,"CSV-Dateien")
    out_path = os.path.join(base_path,"Ergebnisse")

    
def read_data(name="wkn_COM062_historic.csv", fromdate='1900-01-01', todate=pd.Timestamp.today() ):
    
    #file_path = os.path.join(data_path,"Ariva_Brent_Oil_20131231_20241230.csv"
    file_path = os.path.join(data_path,name )
    
    df = pd.read_csv(file_path, delimiter=';', decimal=',')
    
    df['Datum'] = pd.to_datetime(df['Datum'])
    
    df.set_index('Datum', inplace=True)
    
    df.sort_index(inplace=True)
    
    # Spaltennamen anpassen
    df.rename(columns={
        'Erster': 'Open',
        'Hoch': 'High',
        'Tief': 'Low',
        'Schlusskurs': 'Close',
        'Stuecke': 'Volume',
        'Volumen': 'OpenInterest'
    }, inplace=True)


    # Konvertiere numerische Werte
    
    numeric_columns = ['Open', 'High', 'Low', 'Close']
    df[numeric_columns] = df[numeric_columns].apply(lambda x: x.astype(str).str.replace(',', '.').astype(float))
        
    # Filtere Daten nach Backtestzeitraum    
    df = df[(df.index >= pd.Timestamp(fromdate)) & (df.index <= pd.Timestamp(todate))]
    
    # Fehlende Werte entfernen
    
    print(f"Anzahl der Datenpunkte:{len(df)}")
    #print(df.head(60))
    #print(df.isnull().sum())
    
    # spalten ohne daten entfernen
    df.dropna(axis=1, how='all', inplace=True)
    
    # add dummy Volume as this is mandatory for plots
    if not 'Volume' in df.columns:
        df['Volume'] = 100.
    
    # zeilen ganz ohne entries entfernen
    df.dropna(axis=0,how='all',inplace=True)
    
    # zeilen mit einem Fehlwerte entfernen
    df.dropna(axis=0,how='any',inplace=True)
    # optional: fehlende werte ergänzen durch vorhandenen in close bzw. open
    
    # Backtrader-Datenfeed erstellen
    
    data = bt.feeds.PandasData(dataname=df, fromdate=fromdate, todate=todate)
    
    return df, data
    