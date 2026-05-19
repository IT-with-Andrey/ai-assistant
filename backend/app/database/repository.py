


from backend.app.database.models import Message, Summary , UserFact


def save_message(db , role: str , content: str):
    """
    Accepts a ready session db and saves one message to the database.
    it does not open or close the session - that's the caller's responsibility
      """
    # Create a Message object (id and timestamp will be set automatically)
    msg = Message(role=role, content=content)

    # Add the object to the session (in memory will be set automatically )
    db.add(msg)

    # Commit the changes to the database 
    db.commit()
    
    #  Don't Close the session - it will be closed by whoever created it (get_db)

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

def get_lastest_summary(db):
      """Returns the most recent resume or None."""
      return db.query(Summary).order_by(Summary.id.desc()).first()


def save_user_fact(db, key: str,value: str):
      """Stores one fact about the user."""

      fact = UserFact(key=key, value=value)
      db.add(fact)
      db.commit()

def get_all_user_facts(db):
      return db.query(UserFact).all()