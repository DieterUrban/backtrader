"""
Strategie Definitionen

https://www.backtrader.com/docu/signal_strategy/signal_strategy/#first-run-long-and-short

"""

import os
from datetime import timedelta
import pandas as pd
import backtrader as bt

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
        self.strategy_name = "EMACrossover"
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        self.ema1 = bt.indicators.EMA(self.data.close, period=self.params.ema1_period)
        self.ema2 = bt.indicators.EMA(self.data.close, period=self.params.ema2_period)
        
        self.buysig = self.ema1 > self.ema2
        self.sellsig = self.ema1 < self.ema2
        
        self.entry_exit_params = self.params.entry_exit_params
        self.buy_price = None
        self.last_trade_date = None  # Cooldown-Variable hinzufügen

    def handle_entry_signal(self, signal_type):
        if signal_type == "LONG":
            self.buy()
            self.buy_price = self.data.close[0]
            self.last_trade_date = self.data.datetime.date(0)
            self.log('LONG', 'BUY', self.strategy_name)
        elif signal_type == "SHORT":
            self.sell()
            self.buy_price = self.data.close[0]
            self.last_trade_date = self.data.datetime.date(0)
            self.log('SHORT', 'SELL', self.strategy_name)

    def handle_exit_logic(self):
        if self.position:
            if self.position.size > 0:  # Long position
                if self.data.close[0] < self.ema2:
                    self.close()
                    self.log('LONG', 'CLOSE', 'Exit Condition Met')
            elif self.position.size < 0:  # Short position
                if self.data.close[0] > self.ema2:
                    self.close()
                    self.log('SHORT', 'CLOSE', 'Exit Condition Met')

    def next(self):
       # Simply log the closing price of the series from the reference
       # self.log('Close, %.2f' % self.dataclose[0])
       print('.',end='')

       # Check if an order is pending ... if yes, we cannot send a 2nd one
       if self.order:
           self.log('pending order')
           return
    
       # Check if we are in the market
       if not self.position:
           # Not yet ... we MIGHT BUY if ...
           if self.buysig:
                       # BUY, BUY, BUY!!! (with default parameters)
                       self.log('BUY CREATE, %.2f' % self.dataclose[0])

                       # Keep track of the created order to avoid a 2nd order
                       self.order = self.buy()
       else:
           # Already in the market ... we might sell
           if self.sellsig:
               # SELL, SELL, SELL!!! (with all possible default parameters)
               self.log('SELL CREATE, %.2f' % self.dataclose[0])

               # Keep track of the created order to avoid a 2nd order
               self.order = self.sell()


    def __mettel_next(self):
        pass
        """
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
        """

    def reset_trade(self):
        self.buy_price = None

    if False:
        pass
        """
        def log(self, direction, action, reason, pnl=0):
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
        """
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

#%%


################################################################
# To Be Done

"""
 

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

"""

 
