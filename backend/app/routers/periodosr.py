# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import PeriodoAcademico, Modulo, Usuario
from app.schemas import PeriodoCreate, PeriodoOut
from app.core.auth import obtener_usuario_actual

router = APIRouter(prefix="/periodos", tags=["Periodos"])

@router.get("/", response_model=List[PeriodoOut])
def listar_periodos(db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    return db.query(PeriodoAcademico).all()

@router.post("/", response_model=PeriodoOut)
def crear_periodo(periodo: PeriodoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(obtener_usuario_actual)):
    existe = db.query(PeriodoAcademico).filter(PeriodoAcademico.nombre == periodo.nombre).first()
    if existe:
        raise HTTPException(status_code=400, detail="El periodo ya existe")
    
    nuevo_periodo = PeriodoAcademico(
        nombre=periodo.nombre,
        fecha_inicio=periodo.fecha_inicio,
        fecha_fin=periodo.fecha_fin,
        numero_paralelos=periodo.numero_paralelos
    )
    db.add(nuevo_periodo)
    db.commit()
    db.refresh(nuevo_periodo)

    # Crear automáticamente los 3 módulos del periodo
    from datetime import timedelta
    duracion = (periodo.fecha_fin - periodo.fecha_inicio).days // 3

    for i in range(1, 4):
        inicio_mod = periodo.fecha_inicio + timedelta(days=duracion * (i - 1))
        fin_mod = periodo.fecha_inicio + timedelta(days=duracion * i)
        modulo = Modulo(
            periodo_id=nuevo_periodo.id,
            numero=i,
            fecha_inicio=inicio_mod,
            fecha_fin=fin_mod
        )
        db.add(modulo)

    db.commit()
    return nuevo_periodo