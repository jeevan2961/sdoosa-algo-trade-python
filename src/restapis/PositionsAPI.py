from flask.views import MethodView
import json
import logging
from core.Controller import Controller

class PositionsAPI(MethodView):
  def get(self):
    brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
    if Controller.brokerName=='icicidirect':
      positions = brokerHandle.get_portfolio_positions()
    else:
      positions = brokerHandle.positions()
    logging.info('User positions => %s', positions)
    return json.dumps(positions)
  