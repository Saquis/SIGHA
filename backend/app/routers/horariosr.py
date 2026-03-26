# German Del Rio
# Desarrollador Version 1.1 (Corregido)
# SIGHA - Sistema de Gestión de Horarios y Asignación
# routers/horariosr.py: Endpoints para generación y gestión de horarios

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID, uuid4
from app.database import get_db
from app.models import Horario, Usuario, Modulo, Docente
from app.schemas import HorarioOut
from app.core.auth import obtener_usuario_actual
from app.services.horario_service import generar_propuesta_ia, validar_horario_itq

router = APIRouter(prefix="/horarios", tags=["Horarios"])

# --- Helpers de Seguridad ---
def verificar_rol_coordinador(current_user: Usuario):
    """Verifica si el usuario tiene permisos de administración"""
    roles_permitidos = ["coordinador", "administrador", "director"]
    if current_user.rol not in roles_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permisos para realizar esta acción"
        )
    return True

# --- Endpoints ---

@router.get("/modulos")
def listar_modulos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    """Lista todos los módulos disponibles"""
    return db.query(Modulo).all()

@router.post("/generar")
def generar_horarios_ia(
    modulo_id: str = Query(...),
    carrera_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    """
    Genera horarios usando IA. 
    Solo coordinadores pueden ejecutar esta acción.
    """
    # 1. Verificar permisos
    verificar_rol_coordinador(current_user)

    # 2. Validar que el módulo existe
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    # 3. Prevenir duplicados: Verificar si ya existen horarios para este módulo
    existentes = db.query(Horario).filter(Horario.modulo_id == modulo_id).count()
    if existentes > 0:
        raise HTTPException(
            status_code=409, 
            detail=f"El módulo ya tiene {existentes} horarios asignados. Elimínelos antes de generar nuevos."
        )

    # 4. Solicitar propuesta a Groq
    try:
        propuesta_json = generar_propuesta_ia(db, modulo_id, carrera_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con la IA de Groq: {str(e)}")

    if not propuesta_json:
        raise HTTPException(status_code=500, detail="La IA no generó ninguna propuesta válida")

    # 5. Validar reglas de negocio ('El Juez')
    errores = validar_horario_itq(propuesta_json, db)

    # 6. Flujo alterno: Hay choques o violaciones
    if errores:
        return {
            "status": "requiere_ajuste",
            "mensaje": "Se generó la propuesta pero existen conflictos con las reglas del ITQ.",
            "errores": errores[:10],  # Limitar a 10 errores para no saturar la respuesta
            "propuesta_sugerida": propuesta_json,
            "total_errores": len(errores)
        }

    # 7. Flujo feliz: Guardar en BD con transacción segura
    nuevos_horarios = []
    try:
        for item in propuesta_json:
            # Validación segura de UUIDs
            try:
                nuevo_horario = Horario(
                    id=uuid4(),  # Generar ID propio para el horario
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
            except ValueError as e:
                # Si un ID no es UUID válido, se registra el error pero no se rompe todo
                continue
        
        db.commit()
        
        # Refresh para obtener IDs generados
        for h in nuevos_horarios:
            db.refresh(h)

    except Exception as e:
        db.rollback()  # ⚠️ CRÍTICO: Deshacer cambios si falla algo
        raise HTTPException(status_code=500, detail=f"Error al guardar horarios: {str(e)}")

    return {
        "status": "exito",
        "mensaje": "Horarios generados y guardados correctamente.",
        "total_registros": len(nuevos_horarios),
        "horarios": [HorarioOut.from_orm(h) for h in nuevos_horarios]
    }

@router.get("/", response_model=List[HorarioOut])
def listar_horarios(
    modulo_id: str = Query(None, description="Filtrar por módulo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    """
    Lista horarios. 
    - Docentes: Solo ven los suyos.
    - Coordinadores: Ven todos o filtran por módulo.
    """
    query = db.query(Horario)

    # Filtro por módulo (opcional para coordinadores)
    if modulo_id:
        query = query.filter(Horario.modulo_id == modulo_id)

    # Restricción por rol
    if current_user.rol == "docente":
        # ⚠️ CORRECCIÓN: Verificar si existe el registro Docente antes de acceder
        registro_docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
        if not registro_docente:
            raise HTTPException(status_code=404, detail="Usuario docente no tiene perfil asociado")
        
        query = query.filter(Horario.docente_id == registro_docente.id)
    
    # Coordinadores ven todo (o lo filtrado por módulo)
    return query.all()

@router.delete("/{horario_id}")
def eliminar_horario(
    horario_id: str, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    """
    Elimina un horario específico. 
    ⚠️ Solo permitido para coordinadores y administradores.
    """
    # 1. Verificar permisos (Seguridad)
    verificar_rol_coordinador(current_user)

    # 2. Buscar horario
    try:
        horario_uuid = UUID(horario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de horario inválido")

    horario = db.query(Horario).filter(Horario.id == horario_uuid).first()
    if not horario:
        raise HTTPException(status_code=404, detail="Horario no encontrado")

    # 3. Eliminar
    try:
        db.delete(horario)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

    return {"mensaje": "Horario eliminado correctamente", "id": str(horario_id)}