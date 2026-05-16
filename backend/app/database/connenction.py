
from sqlalchemy import create_engine
#declarative_base — функция, возвращающая базовый класс. От него мы будем наследовать все наши модели (таблицы). 
# Так SQLAlchemy «видит» наши классы как таблицы.
from sqlalchemy.orm import sessionmaker , declarative_base
# sessionmaker — фабрика для создания сессий. 
# Сессия — это временное пространство, где ты выполняешь запросы и изменения в БД.
DATABASE_URL = 'sqlite:///./assistant.db'


engine = create_engine(
    DATABASE_URL , 
    connect_args={'check_same_thread': False}  # нужно только для SQLite так как о умолчанию SQLite 
                                               #запрещает использовать одно соединение из разных потоков (падает с ошибкой)
)

# создаём фабрику сессий
SessionLocal = sessionmaker(
            
        autocommit=False,
        autoflush=False,
        bind=engine
)


# базовый класс для всех моделей
Base = declarative_base()


# функция для получения сессии (будем использовать в API)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

