import logging

from ordermgmt.BaseOrderManager import BaseOrderManager
from ordermgmt.Order import Order

from models.ProductType import ProductType
from models.OrderType import OrderType
from models.Direction import Direction
from models.OrderStatus import OrderStatus

from utils.Utils import Utils
from datetime import datetime

class ICICIDirectOrderManager(BaseOrderManager):
  def __init__(self):
    super().__init__("icicidirect")

  def placeOrder(self, orderInputParams):
    logging.info('%s: Going to place order with params %s', self.broker, orderInputParams)
    brokerhandle = self.brokerHandle
    try:
      if orderInputParams.isFnO == False:
        orderId = brokerhandle.place_order(
          stock_code=orderInputParams.tradingSymbol,
          exchange_code="NSE",
          product="margin",
          action=self.convertToBrokerDirection(orderInputParams.direction),
          order_type=self.convertToBrokerOrderType(orderInputParams.orderType),
          stoploss="0",
          quantity=str(orderInputParams.qty),
          price=str(orderInputParams.price),
          validity="day"
          )
      else:
        values = Utils.icicidirectFnOsymbolToValues(orderInputParams.tradingSymbol)
        orderId = brokerhandle.place_order(
          stock_code=values['stockcode'],
          exchange_code="NFO",
          product=self.convertToBrokerProductType(orderInputParams.productType),
          action=self.convertToBrokerDirection(orderInputParams.direction),
          order_type=self.convertToBrokerOrderType(orderInputParams.orderType),
          stoploss=str(orderInputParams.triggerPrice),
          quantity=str(orderInputParams.qty),
          price=str(orderInputParams.price),
          validity="day",
          validity_date=Utils.icicidirectTimeFormat(datetime.today().replace(hour=16, minute=0,second=0,microsecond=0)),
          disclosed_quantity="0",
          expiry_date=values['ExpiryDate'],
          right=values['OptionType'],
          strike_price=str(values['StrikePrice']),
          user_remark="Test"
          )

      logging.info('%s: Order placed successfully, orderId = %s', self.broker, orderId)
      order = Order(orderInputParams)
      order.orderId = orderId
      order.orderPlaceTimestamp = Utils.getEpoch()
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order placement failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def modifyOrder(self, order, orderModifyParams):
    logging.info('%s: Going to modify order with params %s', self.broker, orderModifyParams)
    brokerhandle = self.brokerHandle
    try:
      orderId = brokerhandle.modify_order(
        order_id=order.orderId,
        exchange_code=order.exchange,
        order_type=orderModifyParams.newOrderType,
        stoploss=str(orderModifyParams.newTriggerPrice) if orderModifyParams.newTriggerPrice > 0 else "0",
        quantity=str(orderModifyParams.newQty) if orderModifyParams.newQty > 0 else str(order.qty),
        price=str(orderModifyParams.newPrice) if orderModifyParams.newPrice > 0 else str(order.price),
        validity="day",
        disclosed_quantity="0",
        validity_date=Utils.icicidirectTimeFormat(datetime.today().replace(hour=16, minute=0,second=0,microsecond=0))
        )

      logging.info('%s Order modified successfully for orderId = %s', self.broker, orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order modify failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def modifyOrderToMarket(self, order):
    logging.info('%s: Going to modify order with params %s', self.broker)
    brokerhandle = self.brokerHandle
    try:
      orderId = brokerhandle.modify_order(
        order_id=order.orderId,
        exchange_code=order.exchange,
        order_type="market",
        stoploss="0",
        quantity=order.qty,
        price="0",
        validity="day",
        disclosed_quantity="0",
        validity_date=Utils.icicidirectTimeFormat(datetime.today().replace(hour=16, minute=0,second=0,microsecond=0))
        )

      logging.info('%s Order modified successfully to MARKET for orderId = %s', self.broker, orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order modify to market failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def cancelOrder(self, order):
    logging.info('%s Going to cancel order %s', self.broker, order.orderId)
    brokerhandle = self.brokerHandle
    try:
      orderId = brokerhandle.cancel_order(
        exchange_code=order.exchange,
        order_id=order.orderId)

      logging.info('%s Order cancelled successfully, orderId = %s', self.broker, orderId)
      order.lastOrderUpdateTimestamp = Utils.getEpoch()
      return order
    except Exception as e:
      logging.info('%s Order cancel failed: %s', self.broker, str(e))
      raise Exception(str(e))

  def fetchAndUpdateAllOrderDetails(self, orders):
    logging.info('%s Going to fetch order book', self.broker)
    icicidirect = self.brokerHandle
    orderBook = None
    try:
      from_datetime = datetime.today().replace(hour=0, minute=0,second=0,microsecond=0).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
      to_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
      orderBook_nse = (icicidirect.get_order_list(exchange_code='NSE',from_date=from_datetime, to_date=to_datetime))['Success']
      orderBook_nfo = (icicidirect.get_order_list(exchange_code='NFO',from_date=from_datetime, to_date=to_datetime))['Success']
      orderBook = (orderBook_nse + orderBook_nfo) if (orderBook_nse and orderBook_nfo)!= None else \
       orderBook_nse if orderBook_nse!=None else orderBook_nfo if orderBook_nfo!=None else []
    except Exception as e:
      logging.error('%s Failed to fetch order book', self.broker)
      return

    logging.info('%s Order book length = %d', self.broker, len(orderBook))
    numOrdersUpdated = 0
    for bOrder in orderBook:
      foundOrder = None
      for order in orders:
        if order.orderId == bOrder['order_id']:
          foundOrder = order
          break
      
      if foundOrder != None:
        logging.info('Found order for orderId %s', foundOrder.orderId)
        foundOrder.qty = int(bOrder['quantity'])
        foundOrder.cancelledQty = int(bOrder['cancelled_quantity'])
        foundOrder.pendingQty = int(bOrder['pending_quantity'])
        foundOrder.filledQty = foundOrder.qty - (foundOrder.cancelledQty + foundOrder.pendingQty)
        foundOrder.orderStatus = bOrder['status']
        if foundOrder.orderStatus == OrderStatus.CANCELLED and foundOrder.filledQty > 0:
          # Consider this case as completed in our system as we cancel the order with pending qty when strategy stop timestamp reaches
          foundOrder.orderStatus = OrderStatus.COMPLETED
        foundOrder.price = float(bOrder['price'])
        foundOrder.triggerPrice = float(bOrder['SLTP_price'])  ## SLTP_price
        foundOrder.averagePrice = float(bOrder['average_price'])
        logging.info('%s Updated order %s', self.broker, foundOrder)
        numOrdersUpdated += 1

    logging.info('%s: %d orders updated with broker order details', self.broker, numOrdersUpdated)

  def convertToBrokerProductType(self, productType):
    # brokerhandle = self.brokerHandle
    # if productType == ProductType.MARGIN:
    #   return "margin"
    # elif productType == ProductType.FUTURES:
    #   return brokerhandle.PRODUCT_NRML
    # elif productType == ProductType.CNC:
    #   return "cash"
    return productType

    # "futures", "options", "futureplus", "optionplus", "cash", "eatm", "margin"

  def convertToBrokerOrderType(self, orderType):
    brokerhandle = self.brokerHandle
    if orderType == OrderType.LIMIT:
      return "limit"
    elif orderType == OrderType.MARKET:
      return "market"
    elif orderType == OrderType.SL_MARKET:
      return "stoploss"
    elif orderType == OrderType.SL_LIMIT:
      return "stoploss"
    return None

  def convertToBrokerDirection(self, direction):
    brokerhandle = self.brokerHandle
    if direction == Direction.LONG:
      return "buy"
    elif direction == Direction.SHORT:
      return "sell"
    return None
