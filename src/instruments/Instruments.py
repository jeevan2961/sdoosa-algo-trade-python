import os
import logging
import json
import urllib
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
from io import StringIO
import pandas as pd

from config.Config import getServerConfig, getTimestampsData, saveTimestampsData
from core.Controller import Controller
from utils.Utils import Utils

class Instruments:
  instrumentsList = None
  symbolToInstrumentMap = None
  tokenToInstrumentMap = None
  icici_nse_instruments = None
  # icici_nfo_instruments = None

  @staticmethod
  def shouldFetchFromServer():
    timestamps = getTimestampsData()
    if 'instrumentsLastSavedAt' not in timestamps:
      return True
    lastSavedTimestamp = timestamps['instrumentsLastSavedAt']
    nowEpoch = Utils.getEpoch()
    if nowEpoch - lastSavedTimestamp >= 24 * 60* 60:
      logging.info("Instruments: shouldFetchFromServer() returning True as its been 24 hours since last fetch.")
      return True
    return False

  @staticmethod
  def updateLastSavedTimestamp():
    timestamps = getTimestampsData()
    timestamps['instrumentsLastSavedAt'] = Utils.getEpoch()
    saveTimestampsData(timestamps)

  @staticmethod
  def loadInstruments():
    serverConfig = getServerConfig()
    if Controller.brokerName=='icicidirect':
      file_name='instruments_icici.json'
    else:
      file_name='instruments.json'
    instrumentsFilepath = os.path.join(serverConfig['deployDir'], file_name)
    if os.path.exists(instrumentsFilepath) == False:
      logging.warn('Instruments: instrumentsFilepath %s does not exist', instrumentsFilepath)
      return [] # returns empty list

    isdFile = open(instrumentsFilepath, 'r')
    instruments = json.loads(isdFile.read())
    logging.info('Instruments: loaded %d instruments from file %s', len(instruments), instrumentsFilepath)
    return instruments

  @staticmethod
  def saveInstruments(instruments = []):
    serverConfig = getServerConfig()
    if Controller.brokerName=='icicidirect':
      file_name='instruments_icici.json'
    else:
      file_name='instruments.json'
    instrumentsFilepath = os.path.join(serverConfig['deployDir'], file_name)
    with open(instrumentsFilepath, 'w') as isdFile:
      json.dump(instruments, isdFile, indent=2, default=str)
    logging.info('Instruments: Saved %d instruments to file %s', len(instruments), instrumentsFilepath)
    # Update last save timestamp
    Instruments.updateLastSavedTimestamp()

  @staticmethod
  def downloadICICIDirectInstruments():
    download_link = "https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip"
    resp = urlopen(download_link)
    zipfile = ZipFile(BytesIO(resp.read()))
    # zipfile.namelist()
    # Reading zip files for NSE and FNO
    NSEinstruments = zipfile.read('NSEScripMaster.txt')
    FONSEinstruments = zipfile.read('FONSEScripMaster.txt')
    df = pd.read_csv(StringIO(str(NSEinstruments, 'utf-8')))
    df_nfo = pd.read_csv(StringIO(str(FONSEinstruments, 'utf-8')))
    # Removing quotes from the headers for nse data
    headers = df.columns
    headers_no_quotes = []
    for header in headers:
        headers_no_quotes.append(header.strip(' \"'))
    df.columns = headers_no_quotes
    ## Removing quotes from headers from FNO data
    headers_nfo = df_nfo.columns
    headers_no_quotes_nfo = []
    for header in headers_nfo:
        headers_no_quotes_nfo.append(header.strip(' \"'))
    df_nfo.columns = headers_no_quotes_nfo

    ## saving dataframes
    # df_nse = df.rename(columns={'SymbolName': 'tradingsymbol', 'Token': 'instrument_token'})
    # Instruments.icici_nse_instruments = df_nse

    ## adding symbolname columns
    df['SymbolName']= df['ShortName']
    df_nfo['SymbolName'] = df_nfo['ShortName'].map(str) +"#"+df_nfo['Series'].map(str) \
      +'#'+df_nfo['ExpiryDate'].map(str) +'#'+df_nfo['StrikePrice'].map(str) \
      +'#'+df_nfo['OptionType'].map(str) 
    instrumentsList = df.append(df_nfo)
    instrumentsList = instrumentsList.rename(columns={'SymbolName': 'tradingsymbol', 'Token': 'instrument_token'})
    instrumentsList['instrument_token'] = '4.1!' + instrumentsList['instrument_token'].astype(str)
    instrumentsList = instrumentsList.to_dict('records')
    
    # ## saving as jsons files
    # df_json = df.to_dict()
    # df_nfo_json = df_nfo.to_dict()
    # out = {'df_nse': df_json,
    #       'df_nfo': df_nfo_json
    #       }
    return instrumentsList


  @staticmethod
  def fetchInstrumentsFromServer():
    instrumentsList = []
    try:
      if Controller.brokerName=='icicidirect':
        instrumentsList = Instruments.downloadICICIDirectInstruments()
        logging.info('Fetched %d instruments from server.', len(instrumentsList))
      else:
        brokerHandle = Controller.getBrokerLogin().getBrokerHandle()
        logging.info('Going to fetch instruments from server...')
        instrumentsList = brokerHandle.instruments('NSE')
        instrumentsListFnO = brokerHandle.instruments('NFO')
        # Add FnO instrument list to the main list
        instrumentsList.extend(instrumentsListFnO)
        logging.info('Fetched %d instruments from server.', len(instrumentsList))
    except Exception as e:
      logging.exception("Exception while fetching instruments from server")
    return instrumentsList

  @staticmethod
  def fetchInstruments():
    if Instruments.instrumentsList:
      return Instruments.instrumentsList

    instrumentsList = Instruments.loadInstruments()
    if len(instrumentsList) == 0 or Instruments.shouldFetchFromServer() == True:
      instrumentsList = Instruments.fetchInstrumentsFromServer()
      # Save instruments to file locally
      if len(instrumentsList) > 0:
        Instruments.saveInstruments(instrumentsList)

    if len(instrumentsList) == 0:
      print("Could not fetch/load instruments data. Hence exiting the app.")
      logging.error("Could not fetch/load instruments data. Hence exiting the app.");
      exit(-2)
    if Controller.brokerName=='icicidirect':
      df = pd.DataFrame(instrumentsList)
      df_nse = df[~df['Series'].isin(['FUTURE','OPTION'])]
      Instruments.icici_nse_instruments = df_nse
       
    Instruments.symbolToInstrumentMap = {}
    Instruments.tokenToInstrumentMap = {}
    for isd in instrumentsList:
      tradingSymbol = isd['tradingsymbol']
      instrumentToken = isd['instrument_token']
      # logging.info('%s = %d', tradingSymbol, instrumentToken)
      Instruments.symbolToInstrumentMap[tradingSymbol] = isd
      Instruments.tokenToInstrumentMap[instrumentToken] = isd
    
    logging.info('Fetching instruments done. Instruments count = %d', len(instrumentsList))
    Instruments.instrumentsList = instrumentsList # assign the list to static variable
    return instrumentsList

  @staticmethod
  def getInstrumentDataBySymbol(tradingSymbol):
    return Instruments.symbolToInstrumentMap[tradingSymbol]

  @staticmethod
  def getInstrumentDataByToken(instrumentToken):
    return Instruments.tokenToInstrumentMap[instrumentToken]

  @staticmethod
  def getStockCodeFromExchangeCode(ExchangeCode):
    return Instruments.icici_nse_instruments[Instruments.icici_nse_instruments['ExchangeCode']==ExchangeCode].iloc[0]['tradingsymbol']
    