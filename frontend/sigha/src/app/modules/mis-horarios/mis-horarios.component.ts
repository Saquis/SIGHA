// German Del Rio
// Desarrollador Version 1
// SIGHA - Sistema de Gestión de Horarios y Asignación

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-mis-horarios',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './mis-horarios.component.html'
})
export class MisHorariosComponent implements OnInit {
  horarios: any[] = [];
  error = '';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<any[]>(`${environment.apiUrl}/horarios/`).subscribe({
      next: (data) => this.horarios = data,
      error: () => this.error = 'Error al cargar horarios'
    });
  }
}