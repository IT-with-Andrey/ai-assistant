


from backend.app.database.models import Message, Summary , UserFact
from backend.app.core.logging_utils import log_execution_time

def save_message(db, role: str, content: str):
    msg = Message(role=role, content=content)
    db.add(msg)
    db.commit()
    return msg   # ← добавить

def  get_last_messages(db,limit: int=10):
    
        """
        Accepts a session db and returns the last limit message 
        in order from oldest to newest (chronologcal order)
        Query: all message , sort by id descending (newest first),
        take limit items , then reverse the list [::-1]
        so that the final order is: oldest -> newest . 
        """
    
        message =    (

        db.query(Message)
        .order_by(Message.id.desc())
        .limit(limit)
        .all()[::-1]
    )
        return message
    

def save_summary(db , content :str):
      """ Saves a new resume to the database  """
      summary = Summary(content=content)
      db.add(summary)
      db.commit()
      return summary
def get_lastest_summary(db):
      """Returns the most recent resume or None."""
      return db.query(Summary).order_by(Summary.id.desc()).first()

@log_execution_time
def save_user_fact(db, key: str,value: str):
      
      """Stores one fact about the user."""

      fact = UserFact(key=key, value=value)
      db.add(fact)
      db.commit()
      return fact
def get_all_user_facts(db):
      return db.query(UserFact).all()