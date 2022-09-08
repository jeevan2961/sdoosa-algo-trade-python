import logging
from flask.views import MethodView
from flask import request, redirect

from core.Controller import Controller 

class BrokerLoginAPI(MethodView):
  def get(self):
    redirectUrl = Controller.handleBrokerLogin(request.args)
    return redirect(redirectUrl, code=302)
  
  def post(self):
    print(request)
    redirectUrl = Controller.handleBrokerLogin(request.form)
    return redirect(redirectUrl, code=302)