
from datetime import date, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Path, status, Security
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth import create_access_token, create_refresh_token, get_email_form_refresh_token, get_current_user, Hash
from db import get_db
from models import Contact, User
from schema import ContactResponse, ContactSchema, UserModel


app = FastAPI()
hash_handler = Hash()
security = HTTPBearer()

@app.get("/")
def main_root():
    return {"message": "Hello, fastapi application!"}

@app.post("/contacts/", response_model=ContactResponse)
async def create_contact(body: ContactSchema, db: Session = Depends(get_db)):
    #new_contact = Contact(**contact.dict())
    contact = db.query(Contact).filter_by(email=body.email).first()
    if contact:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact already exists!")
    contact=Contact(fullname=body.fullname, phone_number=body.phone_number, email=body.email, birthday =body.birthday)
    # Создаем новый контакт
    # new_contact = Contact(**body.dict())
    db.add(contact)
    db.commit()
    return contact

@app.get("/contacts", response_model=list[ContactResponse])
#async def get_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
async def get_contacts(db: Session = Depends(get_db)):
    contacts = db.query(Contact).all()
    return contacts


@app.get("/contacts/id/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(contact_id: int = Path(ge=1), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter_by(id=contact_id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact

@app.get("/contacts/by_name/{contact_fullname}", response_model=ContactResponse)
async def get_contact_by_fullname(contact_fullname: str = Path(...), db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter(Contact.fullname.ilike(f"%{contact_fullname}%")).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact

@app.get("/contacts/by_email/{contact_email}", response_model=ContactResponse)
async def get_contact_by_email(contact_email: str = Path(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print("Searching for contact with name:", contact_email)
    contact = db.query(Contact).filter(Contact.email.ilike(f"%{contact_email}%")).first()
    print("Found contact:", contact)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact

@app.get("/contacts/by_birthday/{get_birthday}", response_model=list[ContactResponse])
async def get_upcoming_birthdays(db: Session = Depends(get_db)):
    current_date = date.today()
    future_date = current_date + timedelta(days=7)
    contacts = db.query(Contact).filter(current_date >= Contact.birthday, Contact.birthday <= future_date).all()
    print(contacts)
    return contacts

@app.get("/contacts/get_new_day/{new_date}", response_model=list[ContactResponse])
async def get_upcoming_birthdays_from_new_date(new_date: str = Path(..., description="Current date in format YYYY-MM-DD"),db: Session = Depends(get_db)):
    new_date_obj = datetime.strptime(new_date,"%Y-%m-%d").date()
    future_date = new_date_obj + timedelta(days=7)
    contacts = db.query(Contact).filter(Contact.birthday >= new_date_obj, Contact.birthday <= future_date).all()
    
    print(contacts)
    return contacts

@app.post("/contacts/", response_model=ContactSchema)
async def create_contact(body: ContactSchema, db: Session = Depends(get_db)):
    #new_contact = Contact(**contact.dict())
    contact = db.query(Contact).filter_by(email=body.email).first()
    if contact:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact already exists!")

    contact=Contact(fullname=body.fullname, phone_number=body.phone_number, email=body.email, birthday =body.birthday)
    # Создаем новый контакт
    # new_contact = Contact(**body.dict())
    db.add(contact)
    db.commit()
    return contact

@app.put("/contacts/update/{contact_id}", response_model=ContactResponse)
async def update_contact(body: ContactSchema, contact_id: int = Path(ge=1),db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter_by(id = contact_id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    
    contact.fullname = body.fullname
    contact.email = body.email
    contact.phone_number = body.phone_number
    contact.birthday = body.birthday

    db.commit()
    return contact


@app.delete("/contacts/{contact_id}", response_model=ContactResponse)
async def delete_contact(contact_id: int = Path(ge=1), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contact = db.query(Contact).filter_by(id = contact_id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Contact does not exist or you do not have permission to delete it.")
    db.delete(contact)
    db.commit()
    return contact


@app.post("/signup")
async def signup(body: UserModel, db: Session = Depends(get_db)):
    exist_user = db.query(User).filter(User.email == body.username).first()
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    new_user = User(email=body.username, password=hash_handler.get_password_hash(body.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"new_user": new_user.email}


@app.post("/login")
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not hash_handler.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate JWT
    access_token = await create_access_token(data={"sub": user.email})
    refresh_token = await create_refresh_token(data={"sub": user.email})
    user.refresh_token = refresh_token
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@app.get('/refresh_token')
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    email = await get_email_form_refresh_token(token)
    user = db.query(User).filter(User.email == email).first()
    if user.refresh_token != token:
        user.refresh_token = None
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await create_access_token(data={"sub": email})
    refresh_token = await create_refresh_token(data={"sub": email})
    user.refresh_token = refresh_token
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@app.get("/secret")
async def read_item(current_user: User = Depends(get_current_user)):
    return {"message": 'secret router', "owner": current_user.email}

# from fastapi import FastAPI, Request, HTTPException
# from fastapi.responses import JSONResponse
# from pydantic import ValidationError
# from starlette import status


# @app.exception_handler(HTTPException)
# def http_exception_handler(request: Request, exc: HTTPException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"message": exc.detail},
#     )

# @app.exception_handler(ValidationError)
# def validation_error_handler(request: Request, exc: ValidationError):
#     return JSONResponse(
#         status_code=status.HTTP_400_BAD_REQUEST,
#         content={"message": "Invalid input data"}
#     )

# @app.exception_handler(Exception)
# def unexpected_exception_handler(request: Request, exc: Exception):
#     return JSONResponse(
#         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         content={"message": "An unexpected error occurred"},
#     )

