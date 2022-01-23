from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

sql_database_url="mysql://root:zeehan@localhost:3306/mybookstore"

engine=create_engine(sql_database_url)

sessionLocal=sessionmaker(autocommit=False,bind=engine)

Base=declarative_base()
