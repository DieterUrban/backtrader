#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  4 18:04:53 2025

@author: urban

demo from backtrader quickstart

"""

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt


# Import the backtrader platform
import backtrader as bt

from IPython.display import Image

from read_data import read_data, get_path

from mettel_strategies import EMACrossoverStrategy


# Set the path to save the image
base_path, data_path, out_path = get_path()

img_path = os.path.join(base_path,"results/plots")


#%%

# Create a Stratey
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

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

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                    # current close less than previous close

                    if self.dataclose[-1] < self.dataclose[-2]:
                        # previous close less than the previous close

                        self.log('BUY CREATE, %.2f' % self.dataclose[0])
                        # Keep track of the created order to avoid a 2nd order
                        self.order = self.buy()

        else:
            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):

                self.log('SELL CREATE, %.2f' % self.dataclose[0])
                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


class BuyAndHold(bt.Strategy):

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

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

        
    def nextstart(self):
        # self.log('Close, %.2f' % self.dataclose[0])
        # simply BUY @ first data (with default parameters)
        self.log('BUY CREATE, %.2f' % self.dataclose[0])
        self.order = self.buy()


#%%

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    # cerebro.addstrategy(TestStrategy)
    cerebro.addstrategy(EMACrossoverStrategy)


    if True:
        fromdate = pd.Timestamp("2013-12-01")
        todate = pd.Timestamp("2024-12-30")
        indicator_start_date = todate - timedelta(days=200)
        indicator_start_date = fromdate

        # df, data = read_data(name='wkn_COM062_historic.csv')
        df, data = read_data(name='wkn_COM062_historic.csv', fromdate=indicator_start_date, todate=todate)
        
    else:

        # Datas are in a subfolder of the samples. Need to find where the script is
        # because it could have been called from anywhere
        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        datapath = os.path.join(modpath, 'data/orcl-1995-2014.txt')
    
        # Create a Data Feed
        data = bt.feeds.YahooFinanceCSVData(
            dataname=datapath,
            # Do not pass values before this date
            fromdate=datetime.datetime(2000, 1, 1),
            # Do not pass values before this date
            todate=datetime.datetime(2020, 12, 31),
            # Do not pass values after this date
            reverse=False)


    # Add the Data Feed to Cerebro
    cerebro.adddata(data)
    
    # add analysis
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='Sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='TradeAnalyzer')

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.001)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    strats = cerebro.run()
    strat = strats[0]

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # print analysis
    print(strat.analyzers.Sharpe.get_analysis())
    print(strat.analyzers.DrawDown.get_analysis())
    # print(strat.analyzers.TradeAnalyzer.get_analysis())
        

    fig = cerebro.plot(style="candlestick")[0][0]
    fig.savefig(os.path.join(img_path,"EMACrossoverStrategy.png"))
    Image(filename=os.path.join(img_path,"EMACrossoverStrategy.png"))

#%% compare buy & hold

    cerebro_bh = bt.Cerebro()
    cerebro_bh.addstrategy(BuyAndHold)
    cerebro_bh.adddata(data)
    cerebro_bh.addanalyzer(bt.analyzers.SharpeRatio, _name='Sharpe')
    cerebro_bh.addanalyzer(bt.analyzers.DrawDown, _name='DrawDown')
    cerebro_bh.addanalyzer(bt.analyzers.TradeAnalyzer, _name='TradeAnalyzer')
    cerebro_bh.broker.setcash(100000.0)
    cerebro_bh.broker.setcommission(commission=0.001)
    strats = cerebro_bh.run()
    strat = strats[0]
    print('Buy & Hold Portfolio Value: %.2f' % cerebro_bh.broker.getvalue())
    print(strat.analyzers.Sharpe.get_analysis())
    print(strat.analyzers.DrawDown.get_analysis())
    print(strat.analyzers.TradeAnalyzer.get_analysis())

    fig = cerebro_bh.plot(style="candlestick")[0][0]
    fig.savefig(os.path.join(img_path,"Buy&Hold.png"))
    Image(filename=os.path.join(img_path,"Buy&Hold.png"))


#%%

