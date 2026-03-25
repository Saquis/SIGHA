// German Del Rio
// Desarrollador Version 1
// SIGHA - Sistema de Gestión de Horarios y Asignación

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './reportes.component.html'
})
export class ReportesComponent implements OnInit {
  periodos: any[] = [];
  periodoSeleccionado = '';
  error = '';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.cargarPeriodos();
  }

  cargarPeriodos() {
    this.http.get<any[]>(`${environment.apiUrl}/periodos/`).subscribe({
      next: (data) => this.periodos = data,
      error: () => this.error = 'Error al cargar periodos'
    });
  }

  descargarExcel() {
  this.http.get(`${environment.apiUrl}/reportes/excel`,
    { responseType: 'blob' }
  ).subscribe({
    next: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Planificacion_Academica_ITQ.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    },
    error: () => this.error = 'Error al descargar reporte'
  });
}

  descargarExcelDocente(docenteId: string) {
    this.http.get(`${environment.apiUrl}/reportes/excel/docente/${docenteId}`,
      { responseType: 'blob' }
    ).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `horario_docente_${docenteId}.xlsx`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: () => this.error = 'Error al descargar reporte docente'
    });
  }
}