# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación
# routers/horariosr.py: Endpoints para generación y gestión de horarios

from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
from app.database import get_db
from app.models import Horario, Usuario, Modulo
from app.schemas import HorarioOut
from app.core.auth import obtener_usuario_actual
from app.services.horario_service import generar_propuesta_ia, validar_horario_itq

router = APIRouter(prefix="/horarios", tags=["Horarios"])


@router.get("/modulos")
def listar_modulos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    return db.query(Modulo).all()

# Endpoint para generar horarios usando IA de Groq

@router.post("/generar")
def generar_horarios_ia(
    modulo_id: str = Query(...),
    carrera_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    # 1. Solicitar propuesta a Groq
    try:
        propuesta_json = generar_propuesta_ia(db, modulo_id, carrera_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con la IA de Groq: {str(e)}")

    # 2. Pasar la propuesta por 'El Juez'
    errores = validar_horario_itq(propuesta_json, db)

    # 3. Flujo alterno: Hay choques o violaciones de reglas ITQ
    if errores:
        # No guardamos nada. Enviamos los errores y la propuesta al Frontend
        # para que el coordinador (Angular) haga el ajuste manual.
        return {
            "status": "requiere_ajuste",
            "mensaje": "Se generó la propuesta pero existen conflictos con las reglas del ITQ.",
            "errores": errores,
            "propuesta_sugerida": propuesta_json
        }

    # 4. Flujo feliz: La IA generó un horario perfecto sin choques
    nuevos_horarios = []
    for item in propuesta_json:
        nuevo_horario = Horario(
            modulo_id=UUID(modulo_id),
            docente_id=UUID(item['docente_id']),
            asignatura_id=UUID(item['asignatura_id']),
            carrera_id=UUID(carrera_id),
            paralelo=item.get('paralelo', 1),
            jornada=item['jornada'],
            dia=item['dia'],
            hora_inicio=item['hora_inicio'],
            hora_fin=item['hora_fin']
        )
        db.add(nuevo_horario)
        nuevos_horarios.append(nuevo_horario)

    db.commit()

    return {
        "status": "exito",
        "mensaje": "Horarios generados y guardados correctamente en la base de datos.",
        "total_registros": len(nuevos_horarios)
    }


@router.get("/", response_model=List[HorarioOut])
def listar_horarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    # Endpoint básico para que los docentes vean sus horarios
    if current_user.rol == "docente":
        return db.query(Horario).filter(Horario.docente_id == current_user.docente.id).all()

    # Coordinadores y administrativos ven todo
    return db.query(Horario).all()