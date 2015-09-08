import sys, os, random
from PyQt4 import QtGui, QtCore

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.animation as animation

import urllib.request, urllib.error, urllib.parse
import time
import datetime
import numpy as np
from pylab import *
import pylab
from matplotlib.finance import candlestick_ohlc
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import pandas as pd
import pandas.io.data as web
from datetime import datetime

matplotlib.rcParams.update({'font.size': 9})
matplotlib.rc('axes',edgecolor='#5998ff')


stock = "AAPL"
interval = "15Min"
#candleWidth = 0.008

liveUpdate = False
forceUpdate = False

indicatorRSI = False
RSIperiod = 50
rsiMovingAveragePeriod = []

thirtyLine = False
fiftyLine = False
seventyLine = False

indicatorMACD = False

chartLoad = True

mainAxes = None

darkColor = "#183A54"
lightColor = "#00A3E0"

EMAs = []
SMAs = []

MA1 = 10
MA2 = 50
"""
calculating RSI
price and period variables (default  = 14)
"""
def rsiFunc(prices, n=14):
    deltas = np.diff(prices)
    seed = deltas[:n+1]
    up = seed[seed>=0].sum()/n
    down = -seed[seed<0].sum()/n
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:n] = 100. - 100./(1.+ rs)
    for i in range(n, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up =(up*(n - 1)+upval)/n
        down = (down*(n-1)+downval)/n
        rs = up/down
        rsi[i] = 100. - 100./(1. + rs)
    return rsi
"""
calculating moving average
"""

def movingaverage(values,window):
    weigths = np.repeat(1.0, window)/window
    smas = np.convolve(values, weigths, 'valid')
    return smas # as a numpy array

"""
calculating exponential moving average
"""
def ExpMovingAverage(values, window):
    weights = np.exp(np.linspace(-1., 0., window))
    weights /= weights.sum()
    a =  np.convolve(values, weights, mode='full')[:len(values)]
    a[:window] = a[window]
    return a


def computeMACD(x, slow=26, fast=12):
    """
    compute the MACD (Moving Average Convergence/Divergence) using a fast and slow exponential moving avg'
    return value is emaslow, emafast, macd which are len(x) arrays
    """
    emaslow = ExpMovingAverage(x, slow)
    emafast = ExpMovingAverage(x, fast)
    return emaslow, emafast, emafast - emaslow

"""
changing the interval of the graph
"""
def change_Interval(self, value):
    global interval
    interval = value

"""
function to decode read data
"""
def bytedate2num(fmt):
    def converter(b):
        return mdates.strpdate2num(fmt)(b.decode('ascii'))
    return converter


"""
main graph function

"""
    
class mainGraphCanvas(FigureCanvas):
   
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure((width, height), dpi=dpi, facecolor = '#07000d')
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        if liveUpdate == True:
            ani = animation.FuncAnimation(self.fig, self.plot, interval=2000)
        else:
            self.plot(self.fig)
            
        if indicatorRSI == True:
            self.fig.subplots_adjust(left=.05, bottom=.0, right=.95, top=.95, wspace=.20, hspace=.0)
        else:
            self.fig.subplots_adjust(left=.05, bottom=.15, right=.95, top=.95, wspace=.20, hspace=.0)

    """
    plot function, read the data from yahoo, draws the graph
    """
    def plot(self, fig):
        global indicatorRSI
        global mainAxes
        
        self.fig.clf()

        self.axes0 = self.fig.add_subplot(111, axisbg='#07000d')
        self.axes0.hold(False)
            
        self.axes0.clear()

        mainAxes = self.axes0
        global MA1
        global MA2

        try:
            date_converter = bytedate2num('%Y%m%d')
            print('Currently Pulling',stock)
            urlToVisit = 'http://chartapi.finance.yahoo.com/instrument/1.0/'+stock+'/chartdata;type=quote;range=1y/csv'
            stockFile =[]
            try:
                sourceCode = urllib.request.urlopen(urlToVisit).read().decode()
                splitSource = sourceCode.split('\n')
                for eachLine in splitSource:
                    splitLine = eachLine.split(',')
                    if len(splitLine)==6:
                        if 'values' not in eachLine:
                            if 'labels' not in eachLine:
                                stockFile.append(eachLine)
            except Exception as e:
                print(str(e), 'failed to organize pulled data.')
        except Exception as e:
            print(str(e), 'failed to pull pricing data')

        try:
            date, closep, highp, lowp, openp, volume = np.loadtxt(stockFile,delimiter=',', unpack=True,
                                                                  converters ={0:date_converter})
            x = 0
            y = len(date)
            newAr = []
            
            while x < y:
                appendLine = date[x],openp[x],highp[x],lowp[x],closep[x],volume[x]
                newAr.append(appendLine)
                x+=1


            Av1 = movingaverage(closep, MA1)
            Av2 = movingaverage(closep, MA2)

            SP = len(date[MA2-1:])

            Label1 = str(MA1) + ' SMA'
            Label2 = str(MA2) + ' SMA'

            self.axes0.hold(True)

            MALine1, = self.axes0.plot(date[-SP:], Av1[-SP:], '#e1edf9', label=Label1, linewidth=1.5)
            MALine2, = self.axes0.plot(date[-SP:], Av2[-SP:], '#4ee6fd', label=Label2, linewidth=1.5)
            self.axes0.legend([MALine1, MALine2], ['Moving Average 1', 'Moving Average 2'], title='Ticker Symbol: ' + stock, loc=2)
            
            candlestick_ohlc(self.axes0, newAr[-SP:], width=.4, colorup='#53c156', colordown='#ff1717')
            
            self.axes0.grid(True, color='w')
            self.axes0.xaxis.set_major_locator(mticker.MaxNLocator(10))
            self.axes0.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            self.axes0.xaxis.label.set_color("w")
            self.axes0.yaxis.label.set_color("w")
            self.axes0.tick_params(axis='y', colors='w')
            self.axes0.tick_params(axis='x', colors='w')
            #self.axes0.set_xlabel('Date')
            #self.axes0.set_ylabel('Price')
            if indicatorRSI == True:
                plt.setp(self.axes0.get_xticklabels(), visible=False)
                ytick = self.axes0.yaxis.get_major_ticks()
                ytick[-1].label1.set_visible(False)
                ytick[0].label1.set_visible(False)
            else:
                for label in self.axes0.xaxis.get_ticklabels():
                    label.set_rotation(45)

            self.draw()
            
        except Exception as e:
            print('failed main loop', str(e))
"""
RSI graph function
"""
class rsiGraphCanvas(FigureCanvas):
   
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure((width, height), dpi=dpi, facecolor = '#07000d')
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        if liveUpdate == True:
            ani = animation.FuncAnimation(self.fig, self.plot, interval=2000)
        else:
            self.plot(self.fig)
            
        if indicatorRSI == True:
            self.fig.subplots_adjust(left=.05, bottom=.15, right=.95, top= 1, wspace=.20, hspace=.0)
        else:
            self.fig.subplots_adjust(left=.05, bottom=.15, right=.95, top=.95, wspace=.20, hspace=.0)
            
    """
    plot function, read the data from yahoo, draws the RSI graph
    """
    def plot(self, fig):

        self.fig.clf()

        self.axes1 = self.fig.add_subplot(111, sharex = mainAxes, axisbg='#07000d')
        self.axes1.hold(False)
            
        self.axes1.clear()

        global MA1
        global MA2

        global thirtyLine
        global fiftyLine
        global seventyLine

        try:
            date_converter = bytedate2num('%Y%m%d')
            print('Currently Pulling',stock)
            urlToVisit = 'http://chartapi.finance.yahoo.com/instrument/1.0/'+stock+'/chartdata;type=quote;range=1y/csv'
            stockFile =[]
            try:
                sourceCode = urllib.request.urlopen(urlToVisit).read().decode()
                splitSource = sourceCode.split('\n')
                for eachLine in splitSource:
                    splitLine = eachLine.split(',')
                    if len(splitLine)==6:
                        if 'values' not in eachLine:
                            if 'labels' not in eachLine:
                                stockFile.append(eachLine)
            except Exception as e:
                print(str(e), 'failed to organize pulled data.')
        except Exception as e:
            print(str(e), 'failed to pull pricing data')

        try:
            date, closep, highp, lowp, openp, volume = np.loadtxt(stockFile,delimiter=',', unpack=True,
                                                                  converters ={0:date_converter})
            x = 0
            y = len(date)
            newAr = []
            
            while x < y:
                appendLine = date[x],openp[x],highp[x],lowp[x],closep[x],volume[x]
                newAr.append(appendLine)
                x+=1


            Av1 = movingaverage(closep, MA1)
            Av2 = movingaverage(closep, MA2)

            SP = len(date[MA2-1:])

            Label1 = str(MA1) + ' SMA'
            Label2 = str(MA2) + ' SMA'

            self.axes1.hold(True)
            global RSIperiod
            global rsiMovingAveragePeriod
            self.axes1.clear()
            self.axes1.hold(True)
            rsiCol = '#c1f9f7'
            posCol = '#386d13'
            negCol = '#8f2020'
            rsi = rsiFunc(closep, RSIperiod)
            rsiMAArray = []
            for rsiMAPeriod in rsiMovingAveragePeriod:
                rsiMA = movingaverage(rsi, rsiMAPeriod)
                rsiMAArray.append(rsiMA)
                self.axes1.plot(date[-SP:], rsiMA[-SP:], linewidth=1.5)
                    
                
            if thirtyLine == True:
                self.axes1.axhline(30, color = posCol)
            if fiftyLine == True:
                self.axes1.axhline(50)
            if seventyLine == True:
                self.axes1.axhline(70, color = negCol)

            self.axes1.plot(date[-SP:],rsi[-SP:], rsiCol, linewidth = 1.5)
                #self.axes1.fill_between(date[-SP:],rsi[-SP:],70,where=(rsi[-SP:]>= 70), facecolor = negCol, edgecolor = negCol)
                #self.axes1.fill_between(date[-SP:],rsi[-SP:],30,where=(rsi[-SP:]<= 30), facecolor = posCol, edgecolor = posCol)
            #self.axes1.set_yticks([30,70])
            self.axes1.yaxis.label.set_color("w")
            self.axes1.xaxis.set_major_locator(mticker.MaxNLocator(10))
            self.axes1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            self.axes1.tick_params(axis='x', colors='w')
            self.axes1.tick_params(axis='y', colors='w')
            self.axes1.text(0.015, 0.95, 'RSI (14)', va = 'top', color = 'w', transform = self.axes1.transAxes)
                #plt.gca().yaxis.set_major_locator(mticker.MaxNLocator(prune='lower'))
                #plt.ylabel('RSI')
                
            #maLeg = plt.legend(loc=9, ncol=2, prop={'size':7},fancybox=True, borderaxespad=0.)
            #maLeg.get_frame().set_alpha(0.4)
            #textEd = pylab.gca().get_legend().get_texts()
            #pylab.setp(textEd[0:5], color = 'w')
            
            #plt.setp(self.axes1.get_xticklabels(), visible=False)
            ytick = self.axes1.yaxis.get_major_ticks()
            ytick[-1].label1.set_visible(False)
            ytick[0].label1.set_visible(False)
            
            for label in self.axes1.xaxis.get_ticklabels():
                label.set_rotation(45)
                
            self.draw()
            
        except Exception as e:
            print('failed main loop', str(e))

"""
main class, initializing all variables, set the window and layout
"""
class Window(QtGui.QMainWindow):

    def __init__ (self):
        super(Window, self).__init__()
        self.setGeometry(50,50,1280,720)
        self.setWindowTitle("Stock Analysis App")
        self.setWindowIcon(QtGui.QIcon('stocksIcon.ico'))

        self.quitAction = QtGui.QAction("Exit Program", self)
        self.quitAction.triggered.connect(self.close_application)
        
        self.mainMenu = self.menuBar()
        self.fileMenu = self.mainMenu.addMenu('&File')
        self.fileMenu.addAction(self.quitAction)
        
        self.rsiSettingMenu = self.mainMenu.addMenu('&RSI Settings')
        
        self.rsiPeriod = QtGui.QAction("Period", self)
        self.rsiPeriod.triggered.connect(self.rsiPeriodSetting)
        self.rsiSettingMenu.addAction(self.rsiPeriod)
        
        self.movingAverageIndicator = self.rsiSettingMenu.addMenu("&Moving Average Indicators")

        self.addMovingAverage = QtGui.QAction("Add Moving Average", self)
        self.removeMovingAverage = QtGui.QAction("Remove Moving Average", self)
        
        self.addMovingAverage.triggered.connect(self.rsiAddMovingAverage)
        self.movingAverageIndicator.addAction(self.addMovingAverage)
        
        self.removeMovingAverage.triggered.connect(self.rsiRemoveMovingAverage)
        self.movingAverageIndicator.addAction(self.removeMovingAverage)

        #self.rsiMovingAverage = QtGui.QAction("Moving Average Indicators", self)
        #self.rsiMovingAverage.triggered.connect(self.rsiAddMovingAverage)
        #self.rsiSettingMenu.addAction(self.rsiMovingAverage)

        self.rsiLineIndicator = self.rsiSettingMenu.addMenu("&Add 30-50-70 Line")
        #self.rsiLineIndicator.triggered.connect(self.rsiLineSetting)
        self.thirtyLine = QtGui.QAction("Toggle 30 Line", self)
        self.fiftyLine = QtGui.QAction("Toggle 50 Line", self)
        self.seventyLine = QtGui.QAction("Toggle 70 Line", self)
        self.thirtyLine.triggered.connect(self.addThirtyLine)
        self.rsiLineIndicator.addAction(self.thirtyLine)
        self.fiftyLine.triggered.connect(self.addFiftyLine)
        self.rsiLineIndicator.addAction(self.fiftyLine)
        self.seventyLine.triggered.connect(self.addSeventyLine)
        self.rsiLineIndicator.addAction(self.seventyLine)

        
        self.macdSettingMenu = self.mainMenu.addMenu('&MACD Settings')
        self.macdPeriod = QtGui.QAction("EMA", self)
        #macdPeriod.triggered.connect(self.close_application)
        self.macdSettingMenu.addAction(self.macdPeriod)
        #settingMenu = mainMenu.addMenu('&Settings')
        #settingMenu = mainMenu.addMenu('&Settings')


        self.main_widget = QtGui.QWidget(self)
        
        self.mainHBox = QtGui.QHBoxLayout(self.main_widget)
        #self.side_widget = QtGui.QWidget(self)
        self.search = QtGui.QLineEdit(self.main_widget)
        self.search.setText("Stocks to search")
        #search.move(30,50)
        self.search.setFixedWidth(300)
        
        self.searchBtn = QtGui.QPushButton("Search")
        self.searchBtn.setMaximumWidth(300)
        self.searchBtn.clicked[bool].connect(self.searchBtn_clicked)
        
        self.leftVBox = QtGui.QVBoxLayout(self.main_widget)


        self.leftVBox.addWidget(self.search)
        self.leftVBox.addWidget(self.searchBtn)

        self.leftHBoxInterval = QtGui.QHBoxLayout(self.main_widget)
        
        self.intervalLabel = QtGui.QLabel("TimeFrame:", self.main_widget)
        
        self.timeFrame = QtGui.QComboBox(self.main_widget)
        #self.timeFrame.addItem("1 Minute")
        #self.timeFrame.addItem("5 Minutes")
        #self.timeFrame.addItem("15 Minutes")
        #self.timeFrame.addItem("30 Minutes")
        #self.timeFrame.addItem("Hourly")
        #self.timeFrame.addItem("2 Hour")
        self.timeFrame.addItem("Daily")
        self.timeFrame.addItem("3 Days")
        self.timeFrame.addItem("Weekly")
        self.timeFrame.addItem("Monthly")
        self.timeFrame.activated[str].connect(self.onActivated) 

        self.leftHBoxInterval.addWidget(self.intervalLabel)
        self.leftHBoxInterval.addWidget(self.timeFrame)
        self.leftVBox.addLayout(self.leftHBoxInterval)

        #self.leftHBoxIndicator = QtGui.QHBoxLayout(self.main_widget)
        self.indicatorLabel = QtGui.QLabel("Add Indicator:", self.main_widget)
        self.rsi = QtGui.QCheckBox('RSI', self.main_widget)
        #self.rsi.toggle()
        self.rsi.stateChanged.connect(self.selectRSI)
        self.macd = QtGui.QCheckBox('MACD', self.main_widget)
        #macd.toggle()
        self.macd.stateChanged.connect(self.selectMACD)

        self.leftVBox.addWidget(self.indicatorLabel)
        self.leftVBox.addWidget(self.rsi)
        self.leftVBox.addWidget(self.macd)
        self.leftVBox.addStretch(1)



        self.candlestick = mainGraphCanvas(self.main_widget)
        #self.rsiGraph = rsiGraphCanvas(self.main_widget)
        self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
        self.stockLabel = QtGui.QLabel(stock, self.main_widget)
        
        self.graphVBox = QtGui.QVBoxLayout(self.main_widget)
        self.graphVBox.addWidget(self.stockLabel)
        #self.graphVBox.addWidget(self.candlestick)
        #self.graphVBox.addWidget(self.toolbar)
        
        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter1.addWidget(self.candlestick)
        #self.splitter1.addWidget(self.rsiGraph)
        self.splitter1.addWidget(self.toolbar)
        self.graphVBox.addWidget(self.splitter1)
        
        self.mainHBox.addLayout(self.leftVBox)
        self.mainHBox.addLayout(self.graphVBox)
        
        self.main_widget.setFocus()
        #self.side_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        #search = self.searchInput()

        #self.fig = plt.figure()
        #graph = FigureCanvas(self.fig)

        #vbox = QtGui.QVBoxLayout()
        #hbox = QtGui.QHBoxLayout()

        #self.ani = FuncAnimation(graph.figure, self.animate, interval=2000)
        #self.rsiGraph.hide()
        self.show()

    """
    runs when the search Button is clicked
    """
    def searchBtn_clicked(self):
        global stock
        stock = self.search.text().upper()
        self.search.clear()
        self.stockLabel.setText(stock)
        print(stock)
        self.candlestick.setParent(None)
        self.toolbar.setParent(None)
        self.splitter1.setParent(None)
            
        self.candlestick = mainGraphCanvas(self.main_widget)
        self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter1.addWidget(self.candlestick)

        self.splitter1.addWidget(self.toolbar)
        self.graphVBox.addWidget(self.splitter1)
        if indicatorRSI == True:
            self.rsiGraph = rsiGraphCanvas(self.main_widget)
            self.splitter1.addWidget(self.rsiGraph)


        self.rsi.show()
        
    """
    runs when one of the intervals is clicked
    """      
    def onActivated(self, text):
        global interval
        if text == "Daily":
            interval = "1d"
        if text == "3 Days":
            interval = "3d"
        if text == "Weekly":
            interval = "7d"
        if text == "Monthly":
            interval = "1m"
        interval = text

    """
    functions that updates a change in RSI graph
    """
    def selectRSI(self):
        global indicatorRSI
        
        if(indicatorRSI == True):
            indicatorRSI = False
            self.rsiGraph.hide()

        else:
            indicatorRSI = True
            self.candlestick.setParent(None)
            self.toolbar.setParent(None)
            self.splitter1.setParent(None)
            
            self.candlestick = mainGraphCanvas(self.main_widget)
            self.rsiGraph = rsiGraphCanvas(self.main_widget)
            self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
            self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
            self.splitter1.addWidget(self.candlestick)
            self.splitter1.addWidget(self.rsiGraph)
            self.splitter1.addWidget(self.toolbar)
            self.graphVBox.addWidget(self.splitter1)
            self.rsi.show()

    """
    functions that updates a change in MACD graph
    """
    def selectMACD(self):
        global indicatorMACD
        if(indicatorMACD == True):
            indicatorMACD = False
        else:
            indicatorMACD = True

    """
    functions that updates a change in RSI period
    """
    def rsiPeriodSetting(self):
        global RSIperiod
        period, ok = QtGui.QInputDialog.getText(self, 'Change Period', 'Current Period', QtGui.QLineEdit.Normal,
                                       str(RSIperiod))
        
        if ok:
            RSIperiod = int(period)

    """
    functions that adds moving average in RSI graph
    """
    def rsiAddMovingAverage(self):
        self.rsiMovingAverageWindow = rsiMovingAverageSetting(self)
        self.rsiMovingAverageWindow.exec_()
        self.rsiGraph.setParent(None)
        self.candlestick.setParent(None)
        self.toolbar.setParent(None)
        self.splitter1.setParent(None)
        
        self.candlestick = mainGraphCanvas(self.main_widget)
        self.rsiGraph = rsiGraphCanvas(self.main_widget)
        self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter1.addWidget(self.candlestick)
        self.splitter1.addWidget(self.rsiGraph)
        self.splitter1.addWidget(self.toolbar)
        self.graphVBox.addWidget(self.splitter1)
        self.rsi.show()

    """
    functions that removes all moving average in RSI graph
    """
    def rsiRemoveMovingAverage(self):
        global rsiMovingAveragePeriod
        rsiMovingAveragePeriod = None

        self.rsiGraph.setParent(None)
        self.candlestick.setParent(None)
        self.toolbar.setParent(None)
        self.splitter1.setParent(None)
        
        self.candlestick = mainGraphCanvas(self.main_widget)
        self.rsiGraph = rsiGraphCanvas(self.main_widget)
        self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.splitter1.addWidget(self.candlestick)
        self.splitter1.addWidget(self.rsiGraph)
        self.splitter1.addWidget(self.toolbar)
        self.graphVBox.addWidget(self.splitter1)
        self.rsi.show()

    """
    functions that adds thirty percent line in RSI graph
    """
    def addThirtyLine(self):
        global thirtyLine
        if(thirtyLine == True):
            thirtyLine = False
            self.rsiGraph.setParent(None)
            self.candlestick.setParent(None)
            self.toolbar.setParent(None)
            self.splitter1.setParent(None)
            
            self.candlestick = mainGraphCanvas(self.main_widget)
            self.rsiGraph = rsiGraphCanvas(self.main_widget)
            self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
            self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
            self.splitter1.addWidget(self.candlestick)
            self.splitter1.addWidget(self.rsiGraph)
            self.splitter1.addWidget(self.toolbar)
            self.graphVBox.addWidget(self.splitter1)
            self.rsi.show()
        else:
            thirtyLine = True
            self.rsiGraph.setParent(None)
            self.candlestick.setParent(None)
            self.toolbar.setParent(None)
            self.splitter1.setParent(None)
            
            self.candlestick = mainGraphCanvas(self.main_widget)
            self.rsiGraph = rsiGraphCanvas(self.main_widget)
            self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
            self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
            self.splitter1.addWidget(self.candlestick)
            self.splitter1.addWidget(self.rsiGraph)
            self.splitter1.addWidget(self.toolbar)
            self.graphVBox.addWidget(self.splitter1)
            self.rsi.show()

    """
    functions that adds fifty percent line in RSI graph
    """         
    def addFiftyLine(self):
        global fiftyLine
        if(fiftyLine == True):
            fiftyLine = False
            self.rsiGraph.setParent(None)
            self.candlestick.setParent(None)
            self.toolbar.setParent(None)
            self.splitter1.setParent(None)
            
            self.candlestick = mainGraphCanvas(self.main_widget)
            self.rsiGraph = rsiGraphCanvas(self.main_widget)
            self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
            self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
            self.splitter1.addWidget(self.candlestick)
            self.splitter1.addWidget(self.rsiGraph)
            self.splitter1.addWidget(self.toolbar)
            self.graphVBox.addWidget(self.splitter1)
            self.rsi.show()
        else:
            fiftyLine = True
            self.rsiGraph.setParent(None)
            self.candlestick.setParent(None)
            self.toolbar.setParent(None)
            self.splitter1.setParent(None)
            
            self.candlestick = mainGraphCanvas(self.main_widget)
            self.rsiGraph = rsiGraphCanvas(self.main_widget)
            self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
            self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
            self.splitter1.addWidget(self.candlestick)
            self.splitter1.addWidget(self.rsiGraph)
            self.splitter1.addWidget(self.toolbar)
            self.graphVBox.addWidget(self.splitter1)
            self.rsi.show()

    """
    functions that adds seventy percent line in RSI graph
    """        
    def addSeventyLine(self):
        global seventyLine
        if(seventyLine == True):
            seventyLine = False
            self.rsiGraph.setParent(None)
            self.candlestick.setParent(None)
            self.toolbar.setParent(None)
            self.splitter1.setParent(None)
            
            self.candlestick = mainGraphCanvas(self.main_widget)
            self.rsiGraph = rsiGraphCanvas(self.main_widget)
            self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
            self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
            self.splitter1.addWidget(self.candlestick)
            self.splitter1.addWidget(self.rsiGraph)
            self.splitter1.addWidget(self.toolbar)
            self.graphVBox.addWidget(self.splitter1)
            self.rsi.show()
        else:
            seventyLine = True        
            self.rsiGraph.setParent(None)
            self.candlestick.setParent(None)
            self.toolbar.setParent(None)
            self.splitter1.setParent(None)
            
            self.candlestick = mainGraphCanvas(self.main_widget)
            self.rsiGraph = rsiGraphCanvas(self.main_widget)
            self.toolbar = NavigationToolbar(self.candlestick, self.main_widget)
            self.splitter1 = QtGui.QSplitter(QtCore.Qt.Vertical)
            self.splitter1.addWidget(self.candlestick)
            self.splitter1.addWidget(self.rsiGraph)
            self.splitter1.addWidget(self.toolbar)
            self.graphVBox.addWidget(self.splitter1)
            self.rsi.show()

    """
    functions for search box
    """
    def searchInput(self):
        search = QtGui.QLineEdit(self)
        search.move(30,50)

    """
    quit
    """
    def close_application(self):
            sys.exit()

"""
functions for GUI that updates RSI moving averages
"""  
class rsiMovingAverageSetting(QtGui.QDialog):
    
    def __init__(self, parent=None):
        super(rsiMovingAverageSetting, self).__init__(parent)
        
        self.setGeometry(50,50,210,300)
        self.setWindowTitle("RSI Moving Average Settings")
        
        self.addButton = QtGui.QPushButton("Add Moving Average")
        self.addButton.clicked[bool].connect(self.addPeriodButtonClicked)
        self.cancelButton = QtGui.QPushButton("Cancel")
        self.cancelButton.clicked[bool].connect(self.okButtonClicked)
        #self.cancelButton = QtGui.QPushButton("Cancel")

        
        #self.textBrowser = QtGui.QTextBrowser(self)
        #self.textBrowser.append("This is a QTextBrowser!")
        self.main_widget = QtGui.QWidget(self)
        
        global RSIperiod
        rsiPeriod = QtGui.QInputDialog(self.main_widget)
        
        #rsiPeriod.setTextValue(str(RSIperiod))
        rsiPeriodVBox = QtGui.QVBoxLayout(self.main_widget)
        Label = QtGui.QLabel("Current Indicators:", self.main_widget)
        rsiPeriodVBox.addWidget(Label)
        
        for each in rsiMovingAveragePeriod:
            rsiPeriodVBox.addWidget(QtGui.QLabel ("Moving Average " + str(each), self.main_widget))
            
        self.addPeriod = QtGui.QLineEdit(self.main_widget)
        self.addPeriod.setText("Period to add")
        

        hbox = QtGui.QHBoxLayout(self.main_widget)


        rsiPeriodVBox.addWidget(self.addPeriod, 1)
        #rsiPeriodVBox.addStretch(1)
        hbox.addWidget(self.addButton)
        #rsiPeriodVBox.addWidget(self.cancelButton)
        hbox.addWidget(self.cancelButton)

        rsiPeriodVBox.addLayout(hbox)

    """
    function that adds the period of a moving average
    """
    def addPeriodButtonClicked(self):
        global rsiMovingAveragePeriod
        rsiMovingAveragePeriod.append(int(self.addPeriod.text()))
        #self.addPeriod.clear()
        self.close()
    """
    close the mini window
    """
    def okButtonClicked(self):
        self.close()

"""
main function running the application
"""
def run():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    GUI.show()
    sys.exit(app.exec_())

run()
