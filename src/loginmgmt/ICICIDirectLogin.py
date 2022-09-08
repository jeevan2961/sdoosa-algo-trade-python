import logging
import urllib
from kiteconnect import KiteConnect
from breeze_connect import BreezeConnect

from config.Config import getSystemConfig
from loginmgmt.BaseLogin import BaseLogin

class ICICIDirectLogin(BaseLogin):
  def __init__(self, brokerAppDetails):
    BaseLogin.__init__(self, brokerAppDetails)

  def login(self, args):
    logging.info('==> ICICIDirectLogin .args => %s', args);
    systemConfig = getSystemConfig()
    brokerHandle = BreezeConnect(api_key=self.brokerAppDetails.appKey)
    redirectUrl = None
    if 'API_Session' in args:
      requestToken = args['API_Session']
      logging.info('ICICI API_session_token = %s', requestToken)
      # session = brokerHandle.generate_session(requestToken, api_secret=self.brokerAppDetails.appSecret)
      brokerHandle.generate_session(api_secret=self.brokerAppDetails.appSecret, session_token=requestToken)

      # accessToken = session['access_token']
      # accessToken = accessToken
      accessToken = requestToken
      logging.info('ICICI accessToken = %s', accessToken)
      # brokerHandle.set_access_token(accessToken)
      
      logging.info('Zerodha Login successful. accessToken = %s', accessToken)

      # set broker handle and access token to the instance
      self.setBrokerHandle(brokerHandle)
      self.setAccessToken(accessToken)

      # redirect to home page with query param loggedIn=true
      homeUrl = systemConfig['homeUrl'] + '?loggedIn=true'
      logging.info('ICICIdirect Redirecting to home page %s', homeUrl)
      redirectUrl = homeUrl
    else:
      loginUrl = "https://api.icicidirect.com/apiuser/login?api_key="+urllib.parse.quote_plus(self.brokerAppDetails.appKey)
      # brokerHandle.login_url()
      logging.info('Redirecting to ICICIDirect login url = %s', loginUrl)
      redirectUrl = loginUrl

    return redirectUrl

