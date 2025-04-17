from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, create_engine
from passlib.hash import bcrypt

# Define explicitly SQL database to store explicitly users (easy sqlite setup here explicitly)
Base = declarative_base()
engine = create_engine('sqlite:///users.db', echo=False, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()

# Explicit user model clearly defined:
class User(Base):
    __tablename__ = 'users'
    email = Column(String, primary_key=True, index=True)
    username = Column(String)
    password_hash = Column(String)

Base.metadata.create_all(engine)

# Explicit functions clearly defined:
def add_user(email, username, password):
    hashed_pw = bcrypt.hash(password)
    user = User(email=email, username=username, password_hash=hashed_pw)
    session.add(user)
    session.commit()

def authenticate_user(email, password):
    user = session.query(User).filter_by(email=email).first()
    if user and bcrypt.verify(password, user.password_hash):
        return True, user.username
    return False, None