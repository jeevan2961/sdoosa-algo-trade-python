import logging

from core.Controller import Controller
from models.Quote import Quote

from utils.Utils import Utils

class Quotes:
  @staticmethod
  def getQuote(tradingSymbol, isFnO = False):
    broker = Controller.getBrokerName()
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
    quote = None
    if broker == "zerodha":
      key = ('NFO:' + tradingSymbol) if isFnO == True else ('NSE:' + tradingSymbol)
      bQuoteResp = brokerHandle.quote(key) 
      bQuote = bQuoteResp[key]
      # convert broker quote to our system quote
      quote = Quote(tradingSymbol)
      quote.tradingSymbol = tradingSymbol
      quote.lastTradedPrice = bQuote['last_price']
      quote.lastTradedQuantity = bQuote['last_quantity']
      quote.avgTradedPrice = bQuote['average_price']
      quote.volume = bQuote['volume']
      quote.totalBuyQuantity = bQuote['buy_quantity']
      quote.totalSellQuantity = bQuote['sell_quantity']
      ohlc = bQuote['ohlc']
      quote.open = ohlc['open']
      quote.high = ohlc['high']
      quote.low = ohlc['low']
      quote.close = ohlc['close']
      quote.change = bQuote['net_change']
      quote.oiDayHigh = bQuote['oi_day_high']
      quote.oiDayLow = bQuote['oi_day_low']
      quote.lowerCiruitLimit = bQuote['lower_circuit_limit']
      quote.upperCircuitLimit = bQuote['upper_circuit_limit']
    elif broker=='icicidirect':
      if isFnO:
        values = Utils.icicidirectFnOsymbolToValues(tradingSymbol)
        bQuoteResp = brokerHandle.get_quotes(stock_code=values['stockcode'],
                      exchange_code="NFO",
                      expiry_date=values['ExpiryDate'],
                      product_type=values['Series'],
                      right=values['OptionType'],
                      strike_price=values['StrikePrice'])
        bQuote = bQuoteResp['Success'][0]
      else:
        bQuoteResp = brokerHandle.get_quotes(stock_code=tradingSymbol,
                    exchange_code="NSE")
        bQuoteResp_success = bQuoteResp['Success']
        if len(bQuoteResp_success)>1:
          for i in bQuoteResp_success:
            if i['exchange_code']=='NSE':
              bQuote = i
              break
        elif len(bQuoteResp_success)==1:
          bQuote = bQuoteResp_success[0]
      # convert broker quote to our system quote
      quote = Quote(tradingSymbol)
      quote.tradingSymbol = tradingSymbol
      quote.lastTradedPrice = bQuote['ltp']
      # quote.lastTradedQuantity = bQuote['last_quantity']
      # quote.avgTradedPrice = bQuote['average_price']
      quote.volume = bQuote['total_quantity_traded']
      # quote.totalBuyQuantity = bQuote['buy_quantity']
      # quote.totalSellQuantity = bQuote['sell_quantity']
      # ohlc = bQuote['ohlc']
      quote.open = bQuote['open']
      quote.high = bQuote['high']
      quote.low = bQuote['low']
      quote.close = bQuote['previous_close']
      quote.change = bQuote['ltp_percent_change']
      # quote.oiDayHigh = bQuote['oi_day_high']
      # quote.oiDayLow = bQuote['oi_day_low']
      quote.lowerCiruitLimit = bQuote['upper_circuit']
      quote.upperCircuitLimit = bQuote['lower_circuit']

    else:
      # The logic may be different for other brokers
      quote = None
    return quote

  @staticmethod
  def getCMP(tradingSymbol):
    quote = Quotes.getQuote(tradingSymbol)
    if quote:
      return quote.lastTradedPrice
    else:
      return 0