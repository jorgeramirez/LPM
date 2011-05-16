# -*- coding: utf-8 -*-
"""
Módulo que contiene clases y objetos que guardan relacion
con los módulos de autorización y autenticación

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""

__all__ = ['Permisos']

# Diccionario que define los permisos del sistema
# clave: nombre del permiso
# valor: descripcion del permiso
Permisos = {
    u"crear tipo item" : u"Permite la definición de un nuevo tipo de ítem",
    u"redefinir tipo item": u"Permite agregar características al tipo de ítem",
    u"crear item": u"Permite crear ítems de un tipo dado",
    u"modificar item": u"Permite modificar valores de atributos del ítem",
    u"agregar relacion": u"Permite relacionar un ítem con otro",
    u"eliminar relacion": u"Permite eliminar la relación entre dos ítems",
    u"consultar item": u"Permite consultar valores de atributos de ítem",
    u"aprobar item": u"Permite realizar la operación de aprobar un ítem",
    u"desaprobar item": u"Permite realizar la operación de desaprobar un ítem",
    u"eliminar item": u"Permite realizar la operación de eliminar un ítem",
    u"revivir item": u"Permite realizar la operación de revivir un ítem",
    u"calcular impacto": u"Permite realizar la operación calcular impacto",
    u"consultar tipo item": u"Permite consultar los atributos de " + 
                             u"un tipo de ítem",
    u"crear lb": u"Permite crear una Línea Base",
    u"abrir lb": u"Permite realizar la operación de abrir una línea base",
    u"cerrar lb": u"Permite realizar la operación de cerrar una línea base",
    u"consultar lb": u"Permite consultar la información almacenada en una " +
                      u"línea base",
    u"crear rol": u"Permite realizar la operación de crear un rol",
    u"eliminar rol": u"Permite realizar la operación de eliminar un rol",
    u"asignar rol": u"Permite realizar la operación de asignar un rol",
    u"desasignar rol": u"Permite realizar la operación de desasignar un rol",
    u"asignar permiso": u"Permite asignar permisos a roles",
    u"desasignar permiso": u"Permite desasignar permisos a roles",
    u"consultar rol": u"Permite consultar atributos de un rol",
    u"consultar proyecto": u"Permite consultar valores de atributos de " +
                           u"proyecto",
    u"modificar proyecto": u"Permite modificar valores de atributos de " +
                           u"proyecto",
    u"administrar proyecto": u"Permite administrar componentes de proyecto",
    u"iniciar proyecto": u"Permite realizar la operación de iniciar un " +
                         u"proyecto",
    u"crear proyecto": u"Permite crear proyectos",
    u"eliminar proyecto": u"Permite eliminar proyectos",
    u"crear usuario": u"Permite crear usuarios",
    u"eliminar usuario": u"Permite eliminar usuarios",
    u"modificar usuario": u"Permite modificar valores de atributos de usuarios",
    u"consultar usuario": u"Permite consultar valores de atributos de usuarios"
}
