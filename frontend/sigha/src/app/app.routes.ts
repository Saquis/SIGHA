// German Del Rio
// Desarrollador Version 1
// SIGHA - Sistema de Gestión de Horarios y Asignación

import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', loadComponent: () => import('./modules/auth/login.component').then(m => m.LoginComponent) },
  { path: 'docentes', canActivate: [authGuard], loadComponent: () => import('./modules/docentes/docentes.component').then(m => m.DocentesComponent) },
  { path: 'horarios', canActivate: [authGuard], loadComponent: () => import('./modules/horarios/horarios.component').then(m => m.HorariosComponent) },
  { path: 'reportes', canActivate: [authGuard], loadComponent: () => import('./modules/reportes/reportes.component').then(m => m.ReportesComponent) },
  { path: 'configuracion', canActivate: [authGuard], loadComponent: () => import('./modules/configuracion/configuracion.component').then(m => m.ConfiguracionComponent) },
  { path: '**', redirectTo: 'login' }, 
  { 
    path: 'mis-horarios', 
    canActivate: [authGuard], 
    loadComponent: () => import('./modules/mis-horarios/mis-horarios.component').then(m => m.MisHorariosComponent) 
  },
];