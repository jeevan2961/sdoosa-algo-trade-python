import logging
import json

from kiteconnect import KiteTicker
from breeze_connect import BreezeConnect

from ticker.BaseTicker import BaseTicker
from instruments.Instruments import Instruments
from models.TickData import TickData
from core.Controller import Controller

class ICICIDirectTicker(BaseTicker):
  def __init__(self):
    super().__init__("icicidirect")

  def startTicker(self):
    brokerAppDetails = self.brokerLogin.getBrokerAppDetails()
    accessToken = self.brokerLogin.getAccessToken()
    if accessToken == None:
      logging.error('BreezeConnect startTicker: Cannot start ticker as accessToken is empty')
      return
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle() 
    # ticker = KiteTicker(brokerAppDetails.appKey, accessToken)
    ticker = brokerHandle
    # ticker = brokerHandle.ws_connect()
    ticker.connect = self.on_connect
    ticker.on_close = self.on_close
    ticker.on_error = self.on_error
    ticker.on_reconnect = self.on_reconnect
    ticker.on_noreconnect = self.on_noreconnect
    ticker.on_ticks = self.on_ticks
    ticker.on_order_update = self.on_order_update

    logging.info('BreezeConnect: Going to connect..')
    self.ticker = ticker
    self.ticker.ws_connect()

  def stopTicker(self):
    logging.info('BreezeConnect: stopping..')
    self.ticker.close(1000, "Manual close")

  def registerSymbols(self, symbols):
    tokens = []
    for symbol in symbols:
      isd = Instruments.getInstrumentDataBySymbol(symbol)
      token = isd['instrument_token']
      logging.info('BreezeConnect registerSymbol: %s token = %s', symbol, token)
      tokens.append(token)

    logging.info('BreezeConnect Subscribing tokens %s', tokens)
    self.ticker.subscribe_feeds(tokens)

  def unregisterSymbols(self, symbols):
    tokens = []
    for symbol in symbols:
      isd = Instruments.getInstrumentDataBySymbol(symbol)
      token = isd['instrument_token']
      logging.info('BreezeConnect unregisterSymbols: %s token = %s', symbol, token)
      tokens.append(token)

    logging.info('BreezeConnect Unsubscribing tokens %s', tokens)
    self.ticker.unsubscribe_feeds(tokens)

  def on_ticks(self, brokerTicks):
    # convert broker specific Ticks to our system specific Ticks (models.TickData) and pass to super class function
    ticks = []
    print(brokerTicks)
    bTick = brokerTicks
    # for bTick in brokerTicks:
    # print(bTick)
    isd = Instruments.getInstrumentDataByToken(bTick['symbol'])
    tradingSymbol = isd['tradingsymbol']
    tick = TickData(tradingSymbol)
    tick.lastTradedPrice = bTick['last']
    tick.lastTradedQuantity = bTick['ltq']
    tick.avgTradedPrice = bTick['avgPrice']
    # tick.volume = bTick['ttv']
    # tick.totalBuyQuantity = bTick['buy_quantity']
    # tick.totalSellQuantity = bTick['sell_quantity']
    tick.open = bTick['open']
    tick.high = bTick['high']
    tick.low = bTick['low']
    tick.close = bTick['close']
    tick.change = bTick['change']
    ticks.append(tick)
      
    self.onNewTicks(ticks)

  def on_connect(self, ws, response):
    self.onConnect()

  def on_close(self, ws, code, reason):
    self.onDisconnect(code, reason)

  def on_error(self, ws, code, reason):
    self.onError(code, reason)

  def on_reconnect(self, ws, attemptsCount):
    self.onReconnect(attemptsCount)

  def on_noreconnect(self, ws):
    self.onMaxReconnectsAttempt()

  def on_order_update(self, ws, data):
    self.onOrderUpdate(data)
