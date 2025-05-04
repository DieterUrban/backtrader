import os

from datetime import timedelta

import pandas as pd

import backtrader as bt

import matplotlib.pyplot as plt

import seaborn as sns

#%%
 

# Globale Variablen

trade_log = []  # Liste für Trades

start_date = pd.Timestamp("2023-12-01")

end_date = pd.Timestamp("2024-12-30")

indicator_start_date = start_date - timedelta(days=200)

 

# Daten vorbereiten

if os.getlog() == 'urban':
    data_path = 
    out_path = 
else: 
    data_path = "C:\Users\Bernd\Desktop\Python"
    
    out_path = os.path.join("C:/Users/Bernd/","Desktop/Python/Ergebnisse/")
    
file_path = r"C:\Users\Bernd\Desktop\Python\CSV-Dateien\Ariva_Brent_Oil_20131231_20241230.csv"

df = pd.read_csv(file_path, delimiter=';', decimal=',')

df['Datum'] = pd.to_datetime(df['Datum'])

df.set_index('Datum', inplace=True)

df.sort_index(inplace=True)


#%%

# Spaltennamen anpassen

df.rename(columns={

    'Erster': 'Open',

    'Hoch': 'High',

    'Tief': 'Low',

    'Schlusskurs': 'Close',

    'Stuecke': 'Volume',

    'Volumen': 'OpenInterest'

}, inplace=True)

#%% 

# Konvertiere numerische Werte

numeric_columns = ['Open', 'High', 'Low', 'Close']

df[numeric_columns] = df[numeric_columns].apply(lambda x: x.astype(str).str.replace(',', '.').astype(float))

 

# Filtere Daten nach Backtestzeitraum

df = df[(df.index >= indicator_start_date) & (df.index <= end_date)]

 

# Fehlende Werte entfernen

print(f"Anzahl der Datenpunkte:{len(df)}")

print(df.head(60))

print(df.isnull().sum())

df.dropna(inplace=True)

 

# Backtrader-Datenfeed erstellen

data = bt.feeds.PandasData(dataname=df, fromdate=indicator_start_date, todate=end_date)

#%% 

class FixedSizer(bt.Sizer):

    params = (('stake', 5000),)

 

    def _getsizing(self, comminfo, cash, data, isbuy):

        if isbuy:

            return self.params.stake // data.close[0]

        return self.broker.getposition(data).size

 

class EMACrossoverStrategy(bt.Strategy):

    params = (('ema1_period', 10), ('ema2_period', 20), ('entry_exit_params', None))

 

    def __init__(self):

        self.ema1 = bt.indicators.EMA(self.data.close, period=self.params.ema1_period)

        self.ema2 = bt.indicators.EMA(self.data.close, period=self.params.ema2_period)

        self.entry_exit_params = self.params.entry_exit_params

        self.buy_price = None

        self.last_trade_date = None  # Cooldown-Variable hinzufügen

        self.strategy_name = "EMACrossover"

 

    def handle_entry_signal(self, signal_type):

        if signal_type == "LONG":

            self.buy()

            self.buy_price = self.data.close[0]

            self.last_trade_date = self.data.datetime.date(0)

            self.log_trade('LONG', 'BUY', 'EMA Crossover')

        elif signal_type == "SHORT":

            self.sell()

            self.buy_price = self.data.close[0]

            self.last_trade_date = self.data.datetime.date(0)

            self.log_trade('SHORT', 'SELL', 'EMA Crossover')

 

    def handle_exit_logic(self):

        if self.position:

            if self.position.size > 0:  # Long position

                if self.data.close[0] < self.ema2:

                    self.close()

                    self.log_trade('LONG', 'CLOSE', 'Exit Condition Met')

            elif self.position.size < 0:  # Short position

                if self.data.close[0] > self.ema2:

                    self.close()

                    self.log_trade('SHORT', 'CLOSE', 'Exit Condition Met')

 

    def next(self):

        if self.data.datetime.date(0) < start_date.date():

            return

 

        if self.last_trade_date is not None and self.data.datetime.date(0) == self.last_trade_date:

            return

 

        if not self.position and self.ema1 > self.ema2:

            self.handle_entry_signal(signal_type="LONG")

            print(f"Long-Signal generiert: {self.data.datetime.date(0)} zu {self.data.close[0]}")

 

        if not self.position and self.ema1 < self.ema2:

            self.handle_entry_signal(signal_type="SHORT")

            print(f"Short-Signal generiert: {self.data.datetime.date(0)} zu {self.data.close[0]}")

 

        elif self.position:

            self.handle_exit_logic()

 

    def reset_trade(self):

        self.buy_price = None

 

    def log_trade(self, direction, action, reason, pnl=0):

        trade_log.append({

            'Strategy': self.strategy_name,

            'Direction': direction,

            'Action': action,

            'Reason': reason,

            'EMA1_Period': self.params.ema1_period,

            'EMA2_Period': self.params.ema2_period,

            'Date': self.data.datetime.date(0),

            'Price': self.data.close[0],

            'PnL': pnl

        })

 

class AdvancedEMACrossoverStrategy(EMACrossoverStrategy):

    params = (('ema3_period', 50), ('entry_exit_params', None))

 

    def __init__(self):

        super().__init__()

        self.ema3 = bt.indicators.EMA(self.data.close, period=self.params.ema3_period)

        self.strategy_name = "AdvancedEMACrossover"

 

    def handle_entry_signal(self, signal_type):

        if signal_type == "LONG":

            self.buy()

            self.buy_price = self.data.close[0]

            self.last_trade_date = self.data.datetime.date(0)

            self.log_trade('LONG', 'BUY', 'EMA Crossover with Trend Filter')

        elif signal_type == "SHORT":

            self.sell()

            self.buy_price = self.data.close[0]

            self.last_trade_date = self.data.datetime.date(0)

            self.log_trade('SHORT', 'SELL', 'EMA Crossover with Trend Filter')

 

    def handle_exit_logic(self):

        if self.position:

            if self.position.size > 0:  # Long position

                if self.data.close[0] < self.ema2 or self.data.close[0] < self.ema3:

                    self.close()

                    self.log_trade('LONG', 'CLOSE', 'Exit Condition Met')

            elif self.position.size < 0:  # Short position

                if self.data.close[0] > self.ema2 or self.data.close[0] > self.ema3:

                    self.close()

                    self.log_trade('SHORT', 'CLOSE', 'Exit Condition Met')

 

    def next(self):

        if self.data.datetime.date(0) < start_date.date():

            return

 

        if self.last_trade_date is not None and self.data.datetime.date(0) == self.last_trade_date:

            return

 

        if not self.position and self.ema1 > self.ema2 and self.data.close[0] > self.ema3[0]:

            self.handle_entry_signal(signal_type="LONG")

            print(f"Long-Signal mit Trendfilter generiert: {self.data.datetime.date(0)} zu {self.data.close[0]}")

 

        elif not self.position and self.ema1 < self.ema2 and self.data.close[0] < self.ema3[0]:

            self.handle_entry_signal(signal_type="SHORT")

            print(f"Short-Signal mit Trendfilter generiert: {self.data.datetime.date(0)} zu {self.data.close[0]}")

 

        elif self.position:

            self.handle_exit_logic()

 

class ThreeEMACrossoverStrategy(bt.Strategy):

    params = (('ema1_period', 5), ('ema2_period', 20), ('ema3_period', 50), ('entry_exit_params', None))

 

    def __init__(self):

        self.ema1 = bt.indicators.EMA(self.data.close, period=self.params.ema1_period)

        self.ema2 = bt.indicators.EMA(self.data.close, period=self.params.ema2_period)

        self.ema3 = bt.indicators.EMA(self.data.close, period=self.params.ema3_period)

        self.strategy_name = "ThreeEMACrossover"

        self.last_trade_date = None  # Cooldown-Variable hinzufügen

 

    def handle_entry_signal(self, signal_type):

        if signal_type == "LONG":

            self.buy()

            self.buy_price = self.data.close[0]

            self.last_trade_date = self.data.datetime.date(0)

            self.log_trade('LONG', 'BUY', '3 EMA Crossover')

        elif signal_type == "SHORT":

            self.sell()

            self.buy_price = self.data.close[0]

            self.last_trade_date = self.data.datetime.date(0)

            self.log_trade('SHORT', 'SELL', '3 EMA Crossover')

 

    def handle_exit_logic(self):

        if self.position:

            if self.position.size > 0:  # Long position

                if self.data.close[0] < self.ema2 or self.data.close[0] < self.ema3:

                    self.close()

                    self.log_trade('LONG', 'CLOSE', 'Exit Condition Met')

            elif self.position.size < 0:  # Short position

                if self.data.close[0] > self.ema2 or self.data.close[0] > self.ema3:

                    self.close()

                    self.log_trade('SHORT', 'CLOSE', 'Exit Condition Met')

 

    def next(self):

        if self.data.datetime.date(0) < start_date.date():

            return

 

        if self.last_trade_date is not None and self.data.datetime.date(0) == self.last_trade_date:

            return

 

        if not self.position and self.ema1 > self.ema2 > self.ema3:

            self.handle_entry_signal(signal_type="LONG")

            print(f"Long-Signal generiert: {self.data.datetime.date(0)} zu {self.data.close[0]}")

 

        elif not self.position and self.ema1 < self.ema2 < self.ema3:

            self.handle_entry_signal(signal_type="SHORT")

            print(f"Short-Signal generiert: {self.data.datetime.date(0)} zu {self.data.close[0]}")

 

        elif self.position:

            self.handle_exit_logic()

 

    def log_trade(self, direction, action, reason, pnl=0):

        trade_log.append({

            'Strategy': self.strategy_name,

            'Direction': direction,

            'Action': action,

            'Reason': reason,

            'EMA1_Period': self.params.ema1_period,

            'EMA2_Period': self.params.ema2_period,

            'EMA3_Period': self.params.ema3_period,

            'Date': self.data.datetime.date(0),

            'Price': self.data.close[0],

            'PnL': pnl

        })

 

class EntryLogic:

    def __init__(self, params=None):

        self.params = params or {

            'threshold_percent': 0.25  # Schwellenwert für Überschreitungen (0.25% standard)

        }

        self.high_since_signal = None  # Tracking für Höchststand nach Signal

        self.signal_date = None  # Tracking für Signaldatum

 

    def handle_long_entry(self, data):

        if data.datetime.date(0) == self.signal_date:

            return  # Kein erneuter Kauf am selben Tag

 

        next_day_open = data.open[1]

        signal_high = data.high[0]

 

        # Regel 1: Kauf am nächsten Handelstag zum Eröffnungskurs

        if next_day_open:

            return next_day_open

 

        # Regel 2: Kauf, wenn Kurs am nächsten Tag das Hoch des Signals um x% überschreitet

        if data.high[1] > signal_high * (1 + self.params['threshold_percent'] / 100):

            return data.high[1]

 

        # Regel 3: Kauf nach Rücksetzer und neuem Hoch, wenn EMA-Kreuzung weiterhin aktiv ist

        if self.high_since_signal is not None and data.high[0] > self.high_since_signal * (1 + self.params['threshold_percent'] / 100):

            if self.ema1 > self.ema2:  # Überprüfen, ob die EMA-Kreuzung weiterhin aktiv ist

                return data.high[0]

 

    def track_signal(self, data):

        self.high_since_signal = data.high[0]  # Setze neuen Höchststand

        self.signal_date = data.datetime.date(0)  # Setze Signaldatum

 

    def reset(self):

        self.high_since_signal = None

        self.signal_date = None

 

class ExitLogic:

    def __init__(self, params=None):

        self.params = params or {

            'threshold_percent': 0.25,  # Schwellenwert für Unterschreitungen (0.25%)

            'take_profit': 300  # Fester Take-Profit (kann später angepasst werden)

        }

 

    def handle_long_exit(self, data, entry_price, position_size):

        next_day_open = data.open[1]

        signal_low = data.low[0]

        take_profit_price = entry_price + (self.params['take_profit'] / position_size)

 

        # Regel 1: Verkauf am nächsten Handelstag zum Eröffnungskurs

        if next_day_open:

            return next_day_open

 

        # Regel 2: Verkauf, wenn Kurs am nächsten Tag das Tief des Signals um x% unterschreitet

        if data.low[1] < signal_low * (1 - self.params['threshold_percent'] / 100):

            return data.low[1]

 

        # Regel 3: Verkauf bei Take-Profit

        if data.close[0] >= take_profit_price:

            return data.close[0]

        return None  # Kein Verkauf, wenn keine Regel erfüllt

#%% 

# Cerebro-Instanz

cerebro = bt.Cerebro()

cerebro.adddata(data)

cerebro.addsizer(FixedSizer, stake=5000)

 

# Gemeinsame Parameter für Entry und Exit

entry_exit_params = [

    {'threshold_percent': tp, 'take_profit': tp_value}

    for tp in [0.5, 1.0, 2.0]  # Schwellenwerte in % zur Optimierung

    for tp_value in [300, 500, 1000]  # Verschiedene Take-Profit-Werte

]

 

# Optimierung der Strategien mit Wiederverwendung

cerebro.optstrategy(

    EMACrossoverStrategy,

    ema1_period=range(5, 10, 5),

    ema2_period=range(10, 20, 5),

    entry_exit_params=entry_exit_params

)


#%% 

cerebro.optstrategy(

    AdvancedEMACrossoverStrategy,

    ema1_period=range(5, 10, 5),

    ema2_period=range(10, 20, 5),

    ema3_period=range(20, 30, 5),

    entry_exit_params=entry_exit_params

)

 

cerebro.optstrategy(

    ThreeEMACrossoverStrategy,

    ema1_period=range(5, 10, 5),

    ema2_period=range(10, 20, 5),

    ema3_period=range(20, 30, 10),

    entry_exit_params=entry_exit_params

)

#%%
 

# Broker-Einstellungen

cerebro.broker.set_cash(10000)

cerebro.broker.setcommission(commission=0.005)

 

# Analyse-Werkzeuge

cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', annualize=True)

cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

 

# Backtest ausführen

results = cerebro.run(maxcpus=1)  # maxcpus=1 für Single-Core-Ausführung

 

# Ergebnisse speichern und auswerten

strategy_results = []

 

for stratlist in results:  # results enthält Listen von Strategien

    for strat in stratlist:  # Iteriere durch die einzelnen Strategien

        drawdown = strat.analyzers.drawdown.get_analysis()

        sharpe = strat.analyzers.sharpe.get_analysis()

        trades = strat.analyzers.trades.get_analysis()

 

        # Strategieparameter sammeln

        params = {param: getattr(strat.params, param) for param in strat.params._getkeys()}

 

        result = {

            'Strategy Name': strat.strategy_name if hasattr(strat, 'strategy_name') else 'Unknown',

            **params,  # Strategieparameter einfügen

            'Final Value': round(cerebro.broker.getvalue(), 2),  # Kontostand runden

            'Drawdown (%)': round(drawdown['max']['drawdown'], 2) if 'max' in drawdown and 'drawdown' in drawdown['max'] else None,

            'Sharpe Ratio': round(sharpe['sharperatio'], 2) if 'sharperatio' in sharpe else None,

            'Total Trades': trades['total']['total'] if 'total' in trades else None,

            'Won Trades': trades['won']['total'] if 'won' in trades else None,

            'Lost Trades': trades['lost']['total'] if 'lost' in trades else None,

        }

        strategy_results.append(result)

 

# DataFrame erstellen und als CSV speichern

results_df = pd.DataFrame(strategy_results)

results_df.to_csv("C:/Users/Bernd/Desktop/Python/Ergebnisse/strategy_results.csv", index=False)

 

print("Strategie-Ergebnisse gespeichert in 'strategy_results.csv'")

 

# Ergebnisse speichern

trade_log_df = pd.DataFrame(trade_log)

trade_log_df.to_csv("C:/Users/Bernd/Desktop/Python/Ergebnisse/trade_log.csv", index=False)

 

print("Backtest abgeschlossen. Ergebnisse gespeichert.")

 

# Sortiere Strategien nach Sharpe-Ratio (oder einem anderen Kriterium)

top_strategies = results_df.sort_values(by='Sharpe Ratio', ascending=False).head(5)

 

print("Top 5 Strategien:")

print(top_strategies)

 

# Equity-Kurven oder Metriken der Top 3 Strategien auswählen

top_3_strategies = top_strategies.head(3)

 

# Balkendiagramm der besten Strategien

plt.figure(figsize=(10, 6))

sns.barplot(

    x=top_strategies['Sharpe Ratio'],

    y=top_strategies['Strategy Name'],

    palette="viridis"

)

plt.title("Top 5 Strategien basierend auf Sharpe-Ratio")

plt.xlabel("Sharpe Ratio")

plt.ylabel("Strategien")

plt.show()

 

# Pseudo-Daten für Equity-Kurven

equity_data = {

    "Datum": pd.date_range(start="2024-01-01", end="2024-12-30", freq="D"),

    "Strategie 1": [10000 + i * 10 for i in range(365)],

    "Strategie 2": [10000 + i * 15 for i in range(365)],

    "Strategie 3": [10000 + i * 12 for i in range(365)],

}

 

 
