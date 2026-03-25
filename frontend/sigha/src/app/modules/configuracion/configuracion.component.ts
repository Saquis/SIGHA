// German Del Rio
// Desarrollador Version 1
// SIGHA - Sistema de Gestión de Horarios y Asignación

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
    selector: 'app-configuracion',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './configuracion.component.html'
})
export class ConfiguracionComponent implements OnInit {
    carreras: any[] = [];
    periodos: any[] = [];
    asignaturas: any[] = [];

    nuevaCarrera = { nombre: '', codigo: '' };
    nuevoPeriodo = { nombre: '', fecha_inicio: '', fecha_fin: '', numero_paralelos: 2 };
    nuevaAsignatura = { carrera_id: '', nombre: '', nivel: 1, horas_semanales: 2 };

    error = '';
    mensaje = '';

    constructor(private http: HttpClient) { }

    ngOnInit() {
        this.cargarCarreras();
        this.cargarPeriodos();
        this.cargarAsignaturas();
    }

    cargarCarreras() {
        this.http.get<any[]>(`${environment.apiUrl}/academic/carreras`).subscribe({
            next: (data) => this.carreras = data,
            error: () => this.error = 'Error al cargar carreras'
        });
    }

    cargarPeriodos() {
        this.http.get<any[]>(`${environment.apiUrl}/periodos/`).subscribe({
            next: (data) => this.periodos = data,
            error: () => this.error = 'Error al cargar periodos'
        });
    }

    cargarAsignaturas() {
        this.http.get<any[]>(`${environment.apiUrl}/academic/asignaturas`).subscribe({
            next: (data) => this.asignaturas = data,
            error: () => this.error = 'Error al cargar asignaturas'
        });
    }

    crearCarrera() {
        if (!this.nuevaCarrera.nombre || !this.nuevaCarrera.codigo) {
            this.error = 'Complete todos los campos';
            return;
        }
        this.http.post(`${environment.apiUrl}/academic/carreras`, this.nuevaCarrera).subscribe({
            next: () => {
                this.cargarCarreras();
                this.nuevaCarrera = { nombre: '', codigo: '' };
                this.mensaje = 'Carrera creada correctamente';
                this.error = '';
            },
            error: () => this.error = 'Error al crear carrera'
        });
    }

    crearPeriodo() {
        if (!this.nuevoPeriodo.nombre || !this.nuevoPeriodo.fecha_inicio || !this.nuevoPeriodo.fecha_fin) {
            this.error = 'Complete todos los campos';
            return;
        }
        this.http.post(`${environment.apiUrl}/periodos/`, this.nuevoPeriodo).subscribe({
            next: () => {
                this.cargarPeriodos();
                this.nuevoPeriodo = { nombre: '', fecha_inicio: '', fecha_fin: '', numero_paralelos: 2 };
                this.mensaje = 'Periodo creado correctamente';
            },
            error: () => this.error = 'Error al crear periodo'
        });
    }

    crearAsignatura() {
        if (!this.nuevaAsignatura.carrera_id || !this.nuevaAsignatura.nombre) {
            this.error = 'Complete todos los campos';
            return;
        }
        this.http.post(`${environment.apiUrl}/academic/asignaturas`, this.nuevaAsignatura).subscribe({
            next: () => {
                this.cargarAsignaturas();
                this.nuevaAsignatura = { carrera_id: '', nombre: '', nivel: 1, horas_semanales: 2 };
                this.mensaje = 'Asignatura creada correctamente';
            },
            error: () => this.error = 'Error al crear asignatura'
        });
    }
}