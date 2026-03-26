# German Del Rio
# Desarrollador Version 1.1 (Corregido)
# SIGHA - Sistema de Gestión de Horarios y Asignación
# routers/horariosr.py: Endpoints para generación y gestión de horarios

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
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
    Restringido a coordinadores.
    """
    # 1. Verificar permisos
    verificar_rol_coordinador(current_user)

    # 2. Validar existencia del módulo
    modulo = db.query(Modulo).filter(Modulo.id == modulo_id).first()
    if not modulo:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    # 3. Prevenir duplicados en la generación
    existentes = db.query(Horario).filter(Horario.modulo_id == modulo_id).count()
    if existentes > 0:
        raise HTTPException(
            status_code=409, 
            detail=f"El módulo ya tiene {existentes} horarios asignados. Elimínelos antes de generar nuevos."
        )

    # 4. Solicitar propuesta a la IA
    try:
        propuesta_json = generar_propuesta_ia(db, modulo_id, carrera_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la conexión con la IA: {str(e)}")

    if not propuesta_json:
        raise HTTPException(status_code=500, detail="No se generó una propuesta válida")

    # 5. Validar reglas de negocio institucionales
    errores = validar_horario_itq(propuesta_json, db)

    # 6. Manejo de flujo con conflictos
    if errores:
        return {
            "status": "requiere_ajuste",
            "mensaje": "Propuesta generada con conflictos de reglas de negocio.",
            "errores": errores[:10],
            "propuesta_sugerida": propuesta_json,
            "total_errores": len(errores)
        }

    # 7. Guardado en base de datos con manejo de transacciones
    nuevos_horarios = []
    try:
        for item in propuesta_json:
            try:
                nuevo_horario = Horario(
                    id=uuid4(),
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
            except ValueError:
                # Omitir registros con UUIDs inválidos
                continue
        
        db.commit()
        
        for h in nuevos_horarios:
            db.refresh(h)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar los horarios: {str(e)}")

    return {
        "status": "exito",
        "mensaje": "Horarios generados y guardados correctamente.",
        "total_registros": len(nuevos_horarios),
        "horarios": [HorarioOut.from_orm(h) for h in nuevos_horarios]
    }

@router.post("/guardar_manual")
def guardar_horario_manual(
    modulo_id: str = Query(...),
    carrera_id: str = Query(...),
    horarios_editados: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    try:
        # 1. Verificación de seguridad
        verificar_rol_coordinador(current_user)

        if not horarios_editados:
            raise HTTPException(status_code=400, detail="La lista proporcionada está vacía.")

        # 2. ESCUDO 1: Proteger la validación
        try:
            errores = validar_horario_itq(horarios_editados, db)
        except Exception as val_error:
            raise HTTPException(status_code=500, detail=f"Error en validación ITQ: {str(val_error)}")
        
        if errores:
            raise HTTPException(
                status_code=409, 
                detail={
                    "mensaje": "Aún existen conflictos con las reglas.",
                    "errores": errores[:10]
                }
            )

        # 3. ESCUDO 2: Proteger la inserción
        nuevos_horarios = []
        for item in horarios_editados:
            # Usamos .get() para que si la IA olvidó un campo, no explote el programa
            nuevo_horario = Horario(
                id=uuid4(),
                modulo_id=UUID(str(item.get('modulo_id', modulo_id))),
                docente_id=UUID(str(item.get('docente_id'))),
                asignatura_id=UUID(str(item.get('asignatura_id'))),
                carrera_id=UUID(str(item.get('carrera_id', carrera_id))),
                paralelo=item.get('paralelo', 1),
                jornada=item.get('jornada', 'matutina'),
                dia=item.get('dia', 'Lunes'),
                hora_inicio=item.get('hora_inicio', '08:00'),
                hora_fin=item.get('hora_fin', '10:00')
            )
            db.add(nuevo_horario)
            nuevos_horarios.append(nuevo_horario)

        db.commit()

        for h in nuevos_horarios:
            db.refresh(h)

        return {
            "status": "exito", 
            "mensaje": "Planificación final guardada con éxito.",
            "total_registros": len(nuevos_horarios)
        }

    except HTTPException:
        db.rollback()
        raise # Si es un error controlado (400, 409), lo dejamos pasar normal
    except Exception as e:
        db.rollback()
        # ESCUDO FINAL: Atrapa cualquier error crítico y lo envía limpio a Angular
        raise HTTPException(status_code=500, detail=f"Error crítico en datos: {str(e)}")

    # 3. Guardado en base de datos
    nuevos_horarios = []
    try:
        for item in horarios_editados:
            try:
                nuevo_horario = Horario(
                    id=uuid4(),
                    modulo_id=UUID(str(item.get('modulo_id', modulo_id))),
                    docente_id=UUID(str(item['docente_id'])),
                    asignatura_id=UUID(str(item['asignatura_id'])),
                    carrera_id=UUID(str(item.get('carrera_id', carrera_id))),
                    paralelo=item.get('paralelo', 1),
                    jornada=item['jornada'],
                    dia=item['dia'],
                    hora_inicio=item['hora_inicio'],
                    hora_fin=item['hora_fin']
                )
                db.add(nuevo_horario)
                nuevos_horarios.append(nuevo_horario)
            except ValueError as e:
                 raise HTTPException(status_code=400, detail=f"Datos inválidos en el registro: {e}")

        db.commit()

        for h in nuevos_horarios:
            db.refresh(h)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al guardar la edición: {str(e)}")

    return {
        "status": "exito", 
        "mensaje": "Planificación final guardada con éxito.",
        "total_registros": len(nuevos_horarios),
        "horarios": [HorarioOut.from_orm(h) for h in nuevos_horarios]
    }

@router.get("/", response_model=List[HorarioOut])
def listar_horarios(
    modulo_id: str = Query(None, description="Filtro opcional por módulo"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    """
    Lista los horarios registrados. Aplica filtros según el rol del usuario.
    """
    query = db.query(Horario)

    if modulo_id:
        query = query.filter(Horario.modulo_id == modulo_id)

    if current_user.rol == "docente":
        # Validación de integridad referencial para el rol docente
        registro_docente = db.query(Docente).filter(Docente.usuario_id == current_user.id).first()
        if not registro_docente:
            raise HTTPException(status_code=404, detail="El usuario no tiene un perfil docente asociado.")
        
        query = query.filter(Horario.docente_id == registro_docente.id)
    
    return query.all()

@router.delete("/{horario_id}")
def eliminar_horario(
    horario_id: str, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    """
    Elimina un registro de horario específico.
    Restringido a coordinadores y administradores.
    """
    # 1. Verificación de seguridad
    verificar_rol_coordinador(current_user)

    # 2. Búsqueda y validación del registro
    try:
        horario_uuid = UUID(horario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="El formato del ID de horario es inválido.")

    horario = db.query(Horario).filter(Horario.id == horario_uuid).first()
    if not horario:
        raise HTTPException(status_code=404, detail="Registro de horario no encontrado.")

    # 3. Eliminación
    try:
        db.delete(horario)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al eliminar el registro: {str(e)}")

    return {"mensaje": "Registro eliminado correctamente", "id": str(horario_id)}