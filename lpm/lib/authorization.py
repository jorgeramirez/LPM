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
from repoze.what.predicates import Predicate, is_anonymous
from lpm.model import Usuario

__all__ = ['Permisos', 'PoseePermiso', 'AlgunPermiso']


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
    u"consultar usuario": u"Permite consultar valores de atributos de usuarios",
    u"crear fase": u"Permite crear fases",
    u"modificar fase": u"Permite modificar valores de atributos de una fase",
    u"eliminar fase": u"Permite eliminar una fase",
    u"consultar fase": u"Permite consultar valores de atributos de fase"
}


class PoseePermiso(Predicate):
    """
    Clase que evalua si el usuario actual posee
    el permiso especificado
    """
    message = "El usuario debe poseer el permiso: %s"
    
    def __init__(self, nombre_permiso, **kw):
        """
        Método inicializador.
        
        @param nombre_permiso: el nombre del permiso a evaluar
        @type nombre_permiso: C{unicode}
        """
        
        self.nombre_permiso = unicode(nombre_permiso)
        self.valor_contexto = None
        self.contexto = u""
        for key in ["id_proyecto", "id_fase", "id_tipo_item"]:
            if kw.has_key(key):
                self.valor_contexto = int(kw[key])
                self.contexto = key
                del kw[key]
                break
        super(PoseePermiso, self).__init__(**kw)
        
    def evaluate(self, environ, credentials):
        if is_anonymous().is_met(environ):
            self.unmet()
        nombre_usuario = credentials['repoze.what.userid']
        usuario = Usuario.by_user_name(nombre_usuario)
        for r in usuario.roles:
            valor = getattr(r, self.contexto, None)
            if r.es_rol_sistema() or (valor and valor == self.valor_contexto):
                for p in r.permisos:
                    if p.nombre_permiso == self.nombre_permiso:
                        return
        self.unmet(self.message % self.nombre_permiso)


class AlgunPermiso(Predicate):
    """
    Evalua si el usuario tiene algún permiso para un
    contexto dado.
    """
    message = u"No tiene algun permiso para dicho contexto"
    def __init__(self, **kw):
        """
        Método inicializador
        
        @param kw: Parametros para inicializar
        @keyword patron: El patron para el nombre del permiso.
        """
        self.valor_contexto = None
        self.contexto = u""
        for key in ["id_proyecto", "id_fase", "id_tipo_item"]:
            if kw.has_key(key):
                self.valor_contexto = int(kw[key])
                self.contexto = key
                del kw[key]
                break
        self.patron = unicode(kw["patron"])
        del kw["patron"]
        super(AlgunPermiso, self).__init__(**kw)
    
    def evaluate(self, environ, credentials):
        if is_anonymous().is_met(environ) or not self.valor_contexto: 
            self.unmet()
        nombre_usuario = credentials["repoze.what.userid"]
        usuario = Usuario.by_user_name(nombre_usuario)
        for r in usuario.roles:
            valor = getattr(r, self.contexto, None)
            if r.es_rol_sistema() or (valor and valor == self.valor_contexto):
                for p in r.permisos:
                    if self.patron == u"item" and \
                       p.nombre_permiso.find("tipo item") > 0:
                        continue
                    if p.nombre_permiso.find(self.patron) > 0 and \
                       p.nombre_permiso.find(u"consultar") < 0:
                        return
        self.unmet(self.message)
    
