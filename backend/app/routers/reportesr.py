# German Del Rio
# Desarrollador Version 1
# SIGHA - Sistema de Gestión de Horarios y Asignación
# routers/reportesr.py: Endpoints para descarga de reportes

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Usuario
from app.core.auth import obtener_usuario_actual
from app.services.excel_service import generar_reporte_excel

router = APIRouter(prefix="/reportes", tags=["Reportes"])

@router.get("/excel")
def descargar_excel_horarios(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(obtener_usuario_actual)
):
    # 1. Obtener el archivo Excel en memoria desde el servicio
    stream = generar_reporte_excel(db)
    
    # 2. Configurar las cabeceras para forzar la descarga con el nombre oficial
    headers = {
        "Content-Disposition": "attachment; filename=Planificacion_Academica_ITQ.xlsx"
    }
    
    # 3. Retornar el archivo binario al frontend
    return StreamingResponse(
        stream, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )