# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación
# routers/auth.py: Endpoints para login y registro de usuarios

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioOut, Login, Token
from app.core.auth import obtener_password_hash, verificar_password, crear_token_acceso
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", response_model=UsuarioOut)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Verificar si el email ya existe
    existe = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear nuevo usuario con hash de password
    nuevo_usuario = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password_hash=obtener_password_hash(usuario.password),
        rol=usuario.rol
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


@router.post("/token")
def login_swagger(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm usa 'username' para el email
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    
    if not usuario or not verificar_password(form_data.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    access_token = crear_token_acceso(data={"sub": usuario.email, "rol": usuario.rol})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(credenciales: Login, db: Session = Depends(get_db)):
    # Buscar usuario por email
    usuario = db.query(Usuario).filter(Usuario.email == credenciales.email).first()
    
    # Validar existencia y contraseña
    if not usuario or not verificar_password(credenciales.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # Generar el token incluyendo el email (sub) y el rol
    access_token = crear_token_acceso(data={"sub": usuario.email, "rol": usuario.rol})
    
    return {"access_token": access_token, "token_type": "bearer"}