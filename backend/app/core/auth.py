# German Del Rio

# Desarrollador Version 1

# SIGHA - Sistema de Gestión de Horarios y Asignación

# auth.py: Gestión de autenticación y seguridad JWT desde .env



from datetime import datetime, timedelta

from jose import JWTError, jwt

from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

import os

from app.database import get_db

from app.models import Usuario 

from fastapi.security import OAuth2PasswordRequestForm



# Carga de constantes desde el entorno

SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = os.getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))


#   Configuración de PassLib para hashing de contraseñas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")



# Funciones de autenticación

def verificar_password(plain_password, hashed_password): #   Verifica la contraseña ingresada con la almacenada en la base de datos

    return pwd_context.verify(plain_password, hashed_password)



def obtener_password_hash(password):

    return pwd_context.hash(password)



def crear_token_acceso(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def obtener_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    exc = HTTPException(

        status_code=status.HTTP_401_UNAUTHORIZED,

        detail="Token inválido o expirado",

        headers={"WWW-Authenticate": "Bearer"},

    )

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email: str = payload.get("sub")

        if email is None:

            raise exc

    except JWTError:

        raise exc

        

    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    if not usuario:

        raise exc

    return usuario