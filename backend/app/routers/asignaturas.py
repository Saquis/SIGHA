# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación
# routers/asignaturas.py: Endpoints para gestión de materias y carreras

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models import Asignatura, Carrera, Usuario
from app.schemas import AsignaturaCreate, AsignaturaOut, CarreraCreate, CarreraOut
from app.core.auth import obtener_usuario_actual

router = APIRouter(prefix="/academic", tags=["Académico"])

# --- Endpoints para Carreras ---
@router.post("/carreras", response_model=CarreraOut)
def crear_carrera(carrera: CarreraCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    existe = db.query(Carrera).filter(Carrera.codigo == carrera.codigo).first()
    if existe:
        raise HTTPException(status_code=400, detail="El código de carrera ya existe")
    
    nueva_carrera = Carrera(nombre=carrera.nombre, codigo=carrera.codigo)
    db.add(nueva_carrera)
    db.commit()
    db.refresh(nueva_carrera)
    return nueva_carrera

@router.get("/carreras", response_model=List[CarreraOut])
def listar_carreras(db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return db.query(Carrera).all()

# --- Endpoints para Asignaturas ---
@router.post("/asignaturas", response_model=AsignaturaOut)
def crear_asignatura(asignatura: AsignaturaCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    # Validar que la carrera exista
    carrera = db.query(Carrera).filter(Carrera.id == asignatura.carrera_id).first()
    if not carrera:
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    
    nueva_materia = Asignatura(
        carrera_id=asignatura.carrera_id,
        nombre=asignatura.nombre,
        nivel=asignatura.nivel,
        horas_semanales=asignatura.horas_semanales
    )
    db.add(nueva_materia)
    db.commit()
    db.refresh(nueva_materia)
    return nueva_materia

@router.get("/asignaturas", response_model=List[AsignaturaOut])
def listar_asignaturas(db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return db.query(Asignatura).all()