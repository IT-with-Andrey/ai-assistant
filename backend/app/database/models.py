




from sqlalchemy import Column , Integer , String , Text , DateTime 
# import datetime and timezone to work whis time in python 
from datetime import datetime , timezone
# Column — this is the foundation. Each table field will be created using it.
# Integer — column type for whole numbers (identifier).
# String — type for short strings (e.g., role)
# Text — type for long texts (the content of a message can be large).
# DateTime — type for date and time (timestamp)

from backend.app.database.connection import Base
# We import our base class from the connention module

class Message(Base):           # Inherit from Base - this makes the class a database table model
    __tablename__ = 'messages' # is requierd - it sets the actual table name in the database 
                                # and then the table named message will be created 

    id = Column(Integer , primary_key=True , index=True)    # index=True created an index to spped up searches on this filed 

    role = Column(String , nullable=False)                   

    content = Column(Text , nullable=False)                    # content = the message text (can be long) also required

    timestamp = Column( DateTime(timezone=True) , default=lambda: datetime.now(timezone.utc))

                                                                # Datetime(timezone=True) means we store time with timezone info.
                                                                # default=lanbda : datetime.now(timezone.utc) - function that automatically
                                                                # sets the current UTC time when a new record is created , unless we provide a 
                                                                # value manually 
                                                                #  The lamdba is needed so that the function now() is called exactly at the moment
                                                                # the record is created , not when the model is first defined, only then application
                                                                # starts . Without lambda every message would get the same timestamp the lambda forces
                                                                # now() to be called each time a new message is added  

class Summary(Base):
    __tablename__ = 'summaries'
    id = Column(Integer, primary_key=True , index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True) , default=lambda: datetime.now(timezone.utc))