# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación
# routers/docentesr.py: Endpoints para gestión de docentes

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models import Docente, Usuario
from app.schemas import DocenteCreate, DocenteOut
from app.core.auth import obtener_usuario_actual

router = APIRouter(prefix="/docentes", tags=["Docentes"])

@router.get("/", response_model=List[DocenteOut])
def listar_docentes(db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return db.query(Docente).all()

@router.post("/", response_model=DocenteOut)
def crear_docente(docente: DocenteCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    # Verificar si el usuario ya es docente
    existe = db.query(Docente).filter(Docente.usuario_id == docente.usuario_id).first()
    if existe:
        raise HTTPException(status_code=400, detail="El usuario ya está registrado como docente")
    
    nuevo_docente = Docente(
        usuario_id=docente.usuario_id,
        tipo=docente.tipo,
        horas_acumuladas=0
    )
    db.add(nuevo_docente)
    db.commit()
    db.refresh(nuevo_docente)
    return nuevo_docente

@router.get("/{docente_id}", response_model=DocenteOut)
def obtener_docente(docente_id: UUID, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(status_code=404, detail="Docente no encontrado")
    return docente