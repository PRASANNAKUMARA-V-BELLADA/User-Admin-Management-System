from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, LargeBinary, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import BIGINT

Base = declarative_base()

class Elements(Base):
    __tablename__ = 'LoginMadu'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role=Column(String,index=True)
    password = Column(String,index=True)

class Emps(Base):
    __tablename__ = 'fileEmployee'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    pno=Column(String,index=True)
    filename = Column(String,index=True)
    filecontent= Column(LargeBinary)


from sqlalchemy import create_engine
from sqlalchemy.orm import session, sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://senscio:Agile2022#@192.168.2.12/test"  # Replace with your credentials

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
from sqlalchemy.orm import Session

# Dependency to get the database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from fastapi import FastAPI,UploadFile,File,Form, Request,Depends
from sqlalchemy import func
from pydantic import BaseModel, EmailStr
from fastapi.responses import StreamingResponse,JSONResponse,FileResponse
from io import BytesIO
from typing import Optional
from fastapi.templating import Jinja2Templates
templates=Jinja2Templates(directory="Templates")

app=FastAPI()

#Making Python and HTML Connection Using FastAPI
@app.get("/")
def connect_templates(request:Request):
    return templates.TemplateResponse("Login.html",{"request":request})

@app.get("/user-hogu/{id}")
def connect_templates(request:Request,id:int):
    return templates.TemplateResponse("user.html",{"request":request,"id":id})

@app.get("/admin-hogu/{id}")
def connect_templates(request:Request,id:int):
    return templates.TemplateResponse("admin.html",{"request":request,"id":id})

@app.get("/complete-madu/{id}")
def complete_profile(request:Request,id:int):
     return templates.TemplateResponse("UserProfile.html",{"request":request,"id":id})

#Now This is pydantic model for data validation
class Item(BaseModel):
    id:Optional[int]=None
    name:Optional[str]=None
    role:Optional[str]=None
    password:Optional[str]=None
    class Config:
        arbitrary_types_allowed = True
        orm_mode = True


#Now Creating Endpoints
@app.post('/register')
def insert_data(item:Item,db:Session=Depends(get_db)):
    fetch=db.query(Elements).filter(func.lower(Elements.role)=='admin').first()
    if fetch and item.role.lower()=='admin':
       return JSONResponse(content={"status": "error", "message": "There Is Already Admin Present"}, status_code=500)
    if item.role.lower()=='user' or item.role.lower()=='admin': 
        db_emt=Elements(name=item.name,role=item.role.lower(),password=item.password)
    else:
        return JSONResponse(content={"status": "error", "message": "Role should be either User Or Admin"}, status_code=500)
       
    db.add(db_emt)
    db.commit()
    db.refresh(db_emt)
    return {"message":"You Registered Successfully"}

@app.post('/login')
def get_User(item:Item,db:Session=Depends(get_db)):
    fetch=db.query(Elements).filter(func.lower(Elements.name)==(item.name).lower()).first()
    if fetch is None:
        return JSONResponse(content={"status": "error", "message": "There Is No User Found"}, status_code=500)
    print(fetch.name,"+++++++++")
    if (fetch.role).lower()!='user' and (fetch.role).lower()!='admin':
        return JSONResponse(content={"status": "error", "message": "Role should be either User Or Admin"}, status_code=500)
    if (fetch.password).lower()==(item.password).lower():
        print((fetch.id),"+++++++++")
        if (fetch.role).lower()=='user':
            return {"Message":"user","id":fetch.id}
        elif (fetch.role).lower()=='admin': 
            return {"Message":"admin","id":fetch.id}
    else:
        return JSONResponse(content={"status": "error", "message": "Your Password Is Not Matching"}, status_code=404)

@app.post('/uploadFile/{id}')
async def emp_file(id:int,email:str=Form(...),pno:str=Form(...),file:UploadFile=File(...),db:Session=Depends(get_db)):
     try:
        check=db.query(Emps).filter(Emps.id==id).first()
        if check:
             print(check.email,check,"===========================")
             return JSONResponse(content={"status": "error", "Message": "You Already Completed Your Profile"}, status_code=404)
        file_content=await file.read()
        file_name=file.filename
        emp=Emps(id=id,email=email,pno=pno,filename=file_name,filecontent=file_content)
        print("#########",emp)
        db.add(emp)
        db.commit()
        db.refresh(emp)
        return {"Message":"Employee Data Uploaded SuccessFully"}
     except Exception as e:
         return JSONResponse(content={"status": "error", "Message": f"File Upload Failed: {str(e)}"}, status_code=500)

@app.get('/user/forgot-password')
def forgot_password_page(request:Request):
    return templates.TemplateResponse("forgot.html",{"request":request})

@app.get('/admin/forgot-password')
def forgot_password_page(request:Request):
    return templates.TemplateResponse("forgot.html",{"request":request})

@app.get('/Update-Admin')
def update_admin(request:Request):
    return templates.TemplateResponse("AdminUpdate.html",{"request":request})

@app.get('/register-madu')
def register_madu(request:Request):
    return templates.TemplateResponse("register.html",{"request":request})

@app.get('/View-emp/{id}')
def register_madu(request:Request,id:int):
    return templates.TemplateResponse("View_emp_info.html",{"request":request,"id":id})

@app.get('/Update-Emp/{id}/{role}/{email}/{pno}/{filename}')
def updEmp_madu(request:Request,id:int,role:str,email:str,pno:int,filename:str):
    return templates.TemplateResponse("UpdateEmp.html",{"request":request,"id":id,"role":role,"email":email,"pno":pno,"filename":filename})

@app.get('/getAll')
def view_all(db:Session=Depends(get_db)):
    data=db.query(Emps,Elements).join(Elements,Elements.id==Emps.id).filter(func.lower(Elements.role)!='admin').all()
    print("-------------------",data)
    if data is None:
        return JSONResponse(content={"status": "error", "message": "There Is No User Found"}, status_code=500)
    lst=[]
    for emp,element in data:
        dc={
            "id":element.id,
            "name":element.name,
            "role":element.role,
             "email":emp.email,
            "pno":emp.pno,
            "filename":emp.filename
            }
        lst.append(dc)
    print(lst)
    return {"Message":lst}

@app.get('/getAdmin')
def get_admin(db:Session=Depends(get_db)):
    data=db.query(Elements).filter(func.lower(Elements.role)=='admin').first()
    print(data)
    if not data:
        return JSONResponse(content={"status": "error", "message": "There Is No Admin Found"}, status_code=500)
    return {"name":data.name,"id":data.id}

@app.get('/getUser/{id}')
def get_user(id:int,db:Session=Depends(get_db)):
    data=db.query(Elements).filter(Elements.id==id).first()
    if not data:
        return JSONResponse(content={"status": "error", "message": "There Is No User Found"}, status_code=500)
    return {"name":data.name}


@app.get('/get-emp/{id}')
def view_all(id:int,db:Session=Depends(get_db)):
    data=db.query(Emps,Elements).join(Elements,Elements.id==Emps.id).filter(Elements.id==id).first()
    print("-------------------",data)
    if not data:
        return JSONResponse(content={"status": "error", "message": "You Not Completed Your Profile"}, status_code=404)
    lst=[]
    print("*******",data)
    for emp,element in data:
        dc={
            "id":element.id,
            "name":element.name,
            "role":element.role,
            "email":emp.email,
            "pno":emp.pno,
            "filename":emp.filename
            }
        lst.append(dc)
    print(lst)
    return {"Message":lst}

@app.get('/res/{id}')
def download_file(id:int,db:Session=Depends(get_db)):
    data=db.query(Emps).filter(Emps.id==id).first()
    print(data.filename)
    if not data:
        return JSONResponse(content={"status": "error", "message": "There Is No User Found"}, status_code=500)
    return StreamingResponse(BytesIO(data.filecontent), media_type="application/pdf",headers={"Content-Disposition": f"inline; filename=hosafile.pdf"})

@app.put('/updateEmp/{id}')
async def update_emp(id:int,email:str=Form(...),pno:str=Form(...),filename:str=Form(...),file:UploadFile=File(None),db:Session=Depends(get_db)):
    data=db.query(Emps).filter(Emps.id==id).first()
    if not data:
        return JSONResponse(content={"status": "error", "message": "There Is No User Found"}, status_code=404)
    if email:
        data.email=email
    if pno:
        data.pno=pno
    if filename:
        data.filename=filename
    if file:
        filecontent=await file.read()
        if not filename:
            data.filename=file.filename
        data.filecontent=filecontent
    try:
        db.commit()
        return {"Message":"Successfully Updated Employees"}
    except Exception as e:
        db.rollback()  # Rollback in case of error
        return JSONResponse(content={"status": "error", "message": f"Error updating employee: {str(e)}"}, status_code=500)

@app.delete('/delete/{id}')
def delete_emp(id:int,db:Session=Depends(get_db)):
    data=db.query(Elements).filter(Elements.id==id).first()
    if data.role.lower()=='admin':
        db.delete(data)
        print(")))))))) admin deleted")
        db.commit()
        return {"Message":"Successfully Deleted Admin"}
    dataUser=db.query(Emps,Elements).join(Elements,Elements.id==Emps.id).filter(Emps.id==id).first()
    if not dataUser or not data:
        return JSONResponse(content={"status": "error", "message": "There Is No User Found"}, status_code=404)
    print("***********",data)
    emp,element=dataUser
    db.delete(emp)
    print(")))))))) emp deleted")
    db.delete(element)
    print(")))))))) element deleted")
    db.commit()
    return {"Message":"Successfully Deleted Employee"}

    

        

@app.put('/changePassword')
def update_password(key:str,item:Item,db:Session=Depends(get_db)):
    update=db.query(Elements).filter(func.lower(Elements.name)==(item.name).lower()).first()
    if update is None:
        return JSONResponse(content={"status": "error", "message": "There Is No User Found"}, status_code=500)
    update.password=item.password
    db.commit()
    return {"Message":"Password Changed Successful"}
    
    

# @app.delete('/delete/{name}')
# def delete_user(name:str,db:Session=Depends(get_db)):
#     user=db.query(Elements).filter(func.lower(Elements.name)==name.lower()).first()
#     if user is None:
#         return JSONResponse(content={"status": "error", "message": "There Is No User Found"}, status_code=500)
#     db.delete(user)
#     db.commit()
#     return {"Message":"User Deleted SuccessFully"}



#------------------------- This Is Handling Put and Delete Request Without JavaScript----------------------------------
@app.get('/new')
def get_this(request:Request):
    return templates.TemplateResponse("PutDelete.html",{"request":request})

@app.post('/put')
def updating_employee(request:Request,id:int=Form(...),password:str=Form(...),db:Session=Depends(get_db)):
    fetch=db.query(Elements).filter(Elements.id==id).first()
    if not fetch:
        return templates.TemplateResponse("PutDelete.html",{"request":request,"message":f'User with id:{id} not exists'})
    fetch.password=password
    db.commit()
    return templates.TemplateResponse("PutDelete.html",{"request":request,"message":f'User with name:{fetch.name} Updated Password Successfully'})

@app.post('/delete')
def delete_employee(request:Request,id:int=Form(...),db:Session=Depends(get_db)):
    fetch=db.query(Elements).filter(Elements.id==id).first()
    if not fetch:
        return templates.TemplateResponse("PutDelete.html",{"request":request,"message":f'User with id:{id} not exists'})
    db.delete(fetch)
    db.commit()
    return templates.TemplateResponse("PutDelete.html",{"request":request,"message":f'User name:{fetch.name} Deleted Successfully'})
