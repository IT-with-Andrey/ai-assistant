



from sqlalchemy import Column , Integer , String , Text , DateTime 

from datetime import datetime , timezone
#Column — это фундамент. Каждое поле таблицы мы будем создавать как
#Integer — тип колонки для целых чисел (идентификатор).
#String — тип для коротких строк (например, role)
#ext — тип для длинных текстов (content сообщения может быть большим).
#DateTime — тип для даты и времени (timestamp)

from backend.app.database.connenction import Base


class Message(Base):
    __tablename__ = 'messages' # Специальный атрибут __tablename__ задаёт имя таблицы в базе данных.

    id = Column(Integer , primary_key=True , index=True)

    role = Column(String , nullable=False)

    content = Column(Text , nullable=False)

    timestamp = Column( DateTime(timezone=True) , default=lambda: datetime.now(timezone.utc))
