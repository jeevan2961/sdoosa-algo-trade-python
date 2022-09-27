
class OrderStatus:
  OPEN = "OPEN"
  COMPLETE = "COMPLETE"
  OPEN_PENDING = "OPEN PENDING"
  VALIDATION_PENDING = "VALIDATION PENDING"
  PUT_ORDER_REQ_RECEIVED = "PUT ORDER REQ RECEIVED"
  TRIGGER_PENDING = "TRIGGER PENDING"
  REJECTED = "REJECTED"
  CANCELLED = "CANCELLED"
  

  # R – Requested, Request taken by ICICI direct system.
  # Q – Queued, Request sent to Exchange.
  # O – Request is open at Exchange.
  # P – Request is partly filled at Exchange.
  # E – Request is executed at Exchange.
  # J – Request is rejected by exchange/ICICI direct system.
  # X – Request expired by exchange/ICICI direct system
  # C – Cancelled.