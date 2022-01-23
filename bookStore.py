import email
from http.client import FOUND
from operator import gt
from typing import Optional
from webbrowser import get
from fastapi import FastAPI,Query,Depends,Path,HTTPException, status
from sqlalchemy import Column,String,Integer,Float,Boolean,ForeignKey
from pydantic import BaseModel, errors
from sqlalchemy.orm import Session, query, session
from sqlalchemy import create_engine
from sqlalchemy.sql.schema import MetaData
from sqlalchemy import update
from sqlalchemy.orm import relationship
from fastapi.encoders import jsonable_encoder
from book_Database import engine,Base,sessionLocal
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt

# model
class BookStore(Base):
    __tablename__="mybookstore"
    id=Column(Integer,primary_key=True,index=True,autoincrement=True)
    name=Column(String(255),index=True)
    author=Column(String(225))
    rating=Column(Float)
    description=Column(String(225))
    user=relationship("User",back_populates="owner")

class User(Base):
    __tablename__="users"
    id = Column(Integer,primary_key=True,autoincrement=True)
    email = Column(String(225), unique=True, index=True)
    password = Column(String(6))
    is_active= Column(Boolean,default=True)
    owner_id = Column(Integer,ForeignKey('mybookstore.id'))
    owner=relationship("BookStore",back_populates="user")


# #schema
class UserSchema(BaseModel):
    email: str
    password: str
    is_active:bool
    owner_id:int
    
    
    class Config():
        orm_mode = True
# schema
class BookStoreSchema(BaseModel):
    name:str
    author:str
    rating:float
    description:str

    class config():
        orm_mode=True

class LoginSchema(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email:Optional[str] =None

app=FastAPI()

Base.metadata.create_all(bind=engine)



def get_bookdb():
    db=sessionLocal()
    try:
        yield db
    finally:
        db.close()  
        

@app.put("/update-book/{id}",tags=['Update-Books'])
def updateBook(id:int,book:BookStoreSchema,db:Session=Depends(get_bookdb)):
    newDict={}
    if(book.name!="string"):
        newDict.update({"name":book.name})

    if(book.author!="string"):
        newDict.update({"author":book.author})
    
    if(book.rating!=0):
        newDict.update({"rating":book.rating})

    if(book.description!="string"):
        newDict.update({"description":book.description})

    if(bool(newDict)):
        db.query(BookStore).filter(BookStore.id==id).update(newDict)
        db.commit()
        return {"data":"updated succesfully !!!"}
    else:
        return {"data":"not updated succesfully !!!"}      

@app.delete("/delete-book/{id}",tags=['Delete-Books'])
def delete_student(id: int, db: Session = Depends(get_bookdb)):
    bookstore = db.query(BookStore).get(id)
    db.delete(bookstore)
    db.commit()
    return bookstore 

@app.post("/create-book",tags=['Create-Books'])
def create_Book(book:BookStoreSchema,db:Session=Depends(get_bookdb)):
        bookstore = BookStore( name=book.name,author=book.author,rating=book.rating  ,description=book.description)
        if bookstore.rating > 5:
            raise  HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Rating Should be less then 6")
        db.add(bookstore)
        db.commit()
        return bookstore



@app.get("/books/{id}",tags=['Get-Books'])
def getbook_by_id(id:int,db:Session=Depends(get_bookdb)):
    bookstore = db.query(BookStore).get(id)
    return bookstore


@app.post("/create-user",tags=['create-user'])
def create_User(user:UserSchema,db:Session=Depends(get_bookdb)):

        user = User( email=user.email,password=user.password,is_active=user.is_active,owner_id=user.owner_id)
        
        db.add(user)
        db.commit()
        return user

@app.get("/users",tags=['Get-user'])
def getuser(db:Session=Depends(get_bookdb)):
    return db.query(User).all() 

@app.delete("/delete-user/{id}",tags=['Delete-user'])
def delete_user(id: int, db: Session = Depends(get_bookdb)):
    user = db.query(User).get(id)
    db.delete(user)
    db.commit()
    return user


@app.put("/update-user/{id}",tags=['Update-user'])
def updateBook(id:int,user:UserSchema,db:Session=Depends(get_bookdb)):
    newDict={}
    if(user.email!="string"):
        newDict.update({"email":user.email})

    if(user.password!="string"):
        newDict.update({"password":user.password})
    
    if(user.is_active!=0):
        newDict.update({"is_active":user.is_active})

    
    if(bool(newDict)):
        db.query(User).filter(User.id==id).update(newDict)
        db.commit()
        return {"data":"updated succesfully !!!"}
    else:
        return {"data":"not updated succesfully !!!"}


@app.post('/login',tags=['Authentication'])
def login(request:OAuth2PasswordRequestForm = Depends(),db:Session=Depends(get_bookdb)):
    user=db.query(User).filter(User.email == request.username ).first()
    password=db.query(User).filter(User.password == request.password ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="invalid credentials")
    if not password :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Incorrect Password")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}




SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token:str,credentials_exception):
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token : str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},)
    
    
    return verify_token(token,credentials_exception)

@app.get("/Book/me/", response_model=BookStoreSchema,tags=['Authentication'])
def read_book_me(db:Session=Depends(get_current_user),get_current_user: BookStoreSchema = Depends(get_current_user)):
    return db.query(BookStoreSchema).all() 
