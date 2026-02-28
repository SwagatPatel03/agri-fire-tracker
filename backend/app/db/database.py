from sqlalchemy import create_engine # To create a connection pool to our database
from app.core.config import settings
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# engine manages the main connection
engine = create_engine(settings.DATABASE_URL)

# Temporary workspace to create a workspace or session
# For ex - Will be used when the servers needs to save new satellite fire coordinate
# It will open a temp isolated "workspace", execute the queries and safely close it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

"""The Base class is very important. In the next step, when we define 
what a "Fire" or a "District" looks like in our database, our Python classes
 will inherit from this Base so SQLAlchemy knows
 they are mapped to database tables. """
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        """ The yield keyword makes this function a generator. 
        It pauses execution here, gives the database connection to the
        route handler, and only closes the connection when the handler is done."""
        yield db
    finally:
        db.close()