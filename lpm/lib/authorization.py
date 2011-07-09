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
from repoze.what.predicates import Predicate, is_anonymous, has_permission
from lpm.model import Usuario, Fase, TipoItem

__all__ = ['Permisos', 'PoseePermiso', 'AlgunPermiso']


# Diccionario que define los permisos del sistema
# clave: nombre del permiso
# valor: descripcion del permiso
Permisos = [
#usuario
    dict(nombre= u"crear usuario", descripcion= u"Permite crear usuarios", tipo= u"Sistema, Usuario"),
    dict(nombre= u"eliminar usuario", descripcion= u"Permite eliminar usuarios", tipo= u"Sistema, Usuario"),
    dict(nombre= u"modificar usuario", descripcion= u"Permite modificar valores de atributos de usuarios", tipo= u"Sistema, Usuario"),
    dict(nombre= u"consultar usuario", descripcion= u"Permite consultar valores de atributos de usuarios", tipo= u"Sistema, Usuario"),
#roles
    dict(nombre= u"crear rol", descripcion= u"Permite realizar la operación de crear un rol", tipo= u"Proyecto, Fase, Tipo Ítem, Rol"),
    dict(nombre= u"eliminar rol", descripcion= u"Permite realizar la operación de eliminar un rol", tipo= u"Proyecto, Fase, Tipo Ítem, Rol"),
    dict(nombre= u"modificar rol", descripcion= u"Permite modificar un rol", tipo= u"Proyecto, Fase, Tipo Ítem, Rol"),
    dict(nombre= u"asignar-desasignar rol", descripcion= u"Permite realizar la operación de asignar un rol", tipo= u"Proyecto, Fase, Tipo Ítem, Rol"),
    dict(nombre= u"consultar rol", descripcion= u"Permite consultar atributos de un rol", tipo= u"Proyecto, Fase, Tipo Ítem, Rol"),

    #dict(nombre= u"miembro", descripcion= u"Indica si es miembro", tipo= u"Proyecto, Fase, Tipo Ítem"),

#proyecto
    dict(nombre= u"consultar proyecto", descripcion= (u"Permite consultar valores de atributos de " +
                           u"proyecto"), tipo= u"Proyecto"),
    dict(nombre= u"modificar proyecto", descripcion= (u"Permite modificar valores de atributos de " +
                           u"proyecto"), tipo= u"Proyecto"),
    dict(nombre= u"iniciar proyecto", descripcion= (u"Permite realizar la operación de iniciar un " +
                         u"proyecto"), tipo= u"Proyecto"),
    dict(nombre= u"crear proyecto", descripcion= u"Permite crear proyectos", tipo= u"Sistema"),
    dict(nombre= u"eliminar proyecto", descripcion= u"Permite eliminar proyectos", tipo= u"Sistema"),

#fases
    dict(nombre= u"crear fase", descripcion= u"Permite crear fases", tipo= u"Proyecto"),
    dict(nombre= u"modificar fase", descripcion= u"Permite modificar valores de atributos de una fase", tipo= u"Proyecto, Fase"),
    dict(nombre= u"eliminar fase", descripcion= u"Permite eliminar una fase", tipo= u"Proyecto, Fase"),
    dict(nombre= u"consultar fase", descripcion= u"Permite consultar valores de atributos de fase", tipo= u"Proyecto, Fase"),
    
#tipo de item
    dict(nombre= u"crear tipo item" , descripcion= u"Permite la definición de un nuevo tipo de ítem", tipo= u"Proyecto, Fase"),
    dict(nombre= u"redefinir tipo item", descripcion= u"Permite agregar características al tipo de ítem", tipo= u"Proyecto, Fase, Tipo Ítem"),
    dict(nombre= u"consultar tipo item", descripcion= u"Permite consultar los atributos de " + 
                            u"un tipo de ítem", tipo= u"Proyecto, Fase, Tipo Ítem"),
                                
#item
    dict(nombre= u"crear item", descripcion= u"Permite crear ítems de un tipo dado", tipo= u"Proyecto, Fase, Tipo Ítem"),
    dict(nombre= u"modificar item", descripcion= u"Permite modificar valores de atributos del ítem", tipo= u"Proyecto, Fase, Tipo Ítem"),
    dict(nombre= u"consultar item", descripcion= u"Permite consultar valores de atributos de ítem", tipo= u"Proyecto, Fase, Tipo Ítem"),
    dict(nombre= u"aprobar-desaprobar item", descripcion= u"Permite realizar la operación de aprobar un ítem", tipo= u"Proyecto, Fase, Tipo Ítem"),
    dict(nombre= u"eliminar-revivir item", descripcion= u"Permite realizar la operación de eliminar un ítem", tipo= u"Proyecto, Fase, Tipo Ítem"),
    dict(nombre= u"calcular impacto", descripcion= u"Permite realizar la operación calcular impacto", tipo= u"Proyecto, Fase, Tipo Ítem"),
    
#lb
    dict(nombre= u"crear lb", descripcion= u"Permite crear una Línea Base", tipo= u"Proyecto, Fase"),
    dict(nombre= u"abrir-cerrar lb", descripcion= u"Permite realizar la operación de abrir o cerrar una línea base", tipo= u"Proyecto, Fase"),
    dict(nombre= u"consultar lb", descripcion= (u"Permite consultar la información almacenada en una " +
                      u"línea base"), tipo= u"Proyecto, Fase")
        
]

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
        self.id_proyecto = 0
        self.id_fase = 0
        self.id_tipo_item = 0
        self.id_usuario = 0
        
        if not kw.has_key('id_proyecto'):
            if kw.has_key('id_fase'):
                self.id_fase = int(kw['id_fase'])
                self.id_proyecto = Fase.por_id(self.id_fase).id_proyecto
                del kw['id_fase']
            if kw.has_key('id_tipo_item'):
                self.id_tipo_item = int(kw['id_tipo_item'])
                ti = TipoItem.por_id(self.id_tipo_item)
                self.id_fase = ti.id_fase
                self.id_proyecto = ti.id_proyecto
                del kw['id_tipo_item']
        else:
            self.id_proyecto = int(kw['id_proyecto'])
            del kw['id_proyecto']        

        if kw.has_key("id_usuario"):
            self.id_usuario = int(kw["id_usuario"])
            del kw["id_usuario"]
        
        super(PoseePermiso, self).__init__(**kw)
        
    def evaluate(self, environ, credentials):
        if is_anonymous().is_met(environ):
            self.unmet()
        nombre_usuario = credentials['repoze.what.userid']
        usuario = Usuario.by_user_name(nombre_usuario)

        if self.id_usuario:
            usuario = Usuario.por_id(self.id_usuario)
        
            
        if (self.id_tipo_item):
            #recuperar id  de fase y proyecto
            ti = TipoItem.por_id(self.id_tipo_item)
            if (not self.id_fase):
                self.id_fase = ti.id_fase
            if (not self.id_proyecto):
                self.id_proyecto = ti.id_proyecto
        
        elif (self.id_fase):
            fase = Fase.por_id(self.id_fase)
            if (not self.id_proyecto):
                self.id_proyecto = fase.id_proyecto
                    
                             
        for r in usuario.roles:
            tiene = False
            for p in r.permisos:
                if p.nombre_permiso == self.nombre_permiso:
                    tiene = True
                    
            if not tiene: 
                continue
            
            if r.es_rol_sistema():
                return
            
            if self.id_proyecto == r.id_proyecto:
                if r.tipo == u"Proyecto":
                    return
            
            if self.id_fase == r.id_fase:
                if r.tipo == u"Fase":
                    return
                
            ti = TipoItem.por_id(self.id_tipo_item)
            if ti and ti.es_o_es_hijo(r.id_tipo_item):
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
        @keyword tipo: El tipo de permiso (Rol, Usuario, Proyecto, Fase, Tipo Ítem).
        """
        self.id_proyecto = 0
        self.id_fase = 0
        self.id_tipo_item = 0
        self.id_usuario = 0
        
        self.tipo = unicode(kw["tipo"])
        del kw["tipo"]
        
        if (not kw.has_key('id_proyecto')):
            if (kw.has_key('id_fase')):
                self.id_fase = int(kw['id_fase'])
                self.id_proyecto = Fase.por_id(self.id_fase).id_proyecto
                del kw['id_fase']
            if (kw.has_key('id_tipo_item')):
                self.id_tipo_item = int(kw['id_tipo_item'])
                ti = TipoItem.por_id(self.id_tipo_item)
                self.id_fase = ti.id_fase
                self.id_proyecto = ti.id_proyecto
                del kw['id_tipo_item']
        else:
            self.id_proyecto = int(kw['id_proyecto'])
            del kw['id_proyecto']
        
        if kw.has_key("id_usuario"):
            self.id_usuario = int(kw["id_usuario"])
            del kw["id_usuario"]
        
            
        super(AlgunPermiso, self).__init__(**kw)
    
    def evaluate(self, environ, credentials):
        if is_anonymous().is_met(environ): 
            self.unmet()
        nombre_usuario = credentials["repoze.what.userid"]
        usuario = Usuario.by_user_name(nombre_usuario)
        
        if self.id_usuario:
            usuario = Usuario.por_id(self.id_usuario)
        
        if (self.id_tipo_item):
            #recuperar id  de fase y proyecto
            ti = TipoItem.por_id(self.id_tipo_item)
            if (not self.id_fase):
                self.id_fase = ti.id_fase
            if (not self.id_proyecto):
                self.id_proyecto = ti.id_proyecto
        
        elif (self.id_fase):
            fase = Fase.por_id(self.id_fase)
            if (not self.id_proyecto):
                self.id_proyecto = fase.id_proyecto
                    
        for r in usuario.roles:
            
            if (r.tipo.find(u"Sistema") == 0):
                
                for p in r.permisos:
                    if (p.tipo.find(self.tipo) >= 0):
                        return
                    
            if (r.tipo.find(u"Proyecto") == 0):
                if (self.tipo == "Proyecto" and self.id_proyecto == r.id_proyecto):
                    return
                
                elif (self.tipo == "Fase" or self.tipo == "Tipo"):
                    algun = False
                    for p in r.permisos:
                        if (p.tipo.find(self.tipo) >= 0):
                            algun = True
                            break
                        
                    if (algun and self.id_proyecto == r.id_proyecto):
                        return
                     
            elif (r.tipo.find(u"Fase") == 0):
                if (self.tipo == "Fase"):
                    if (self.id_fase == r.id_fase):
                        return
                    
                    elif (not self.id_fase):
                        fase = Fase.por_id(r.id_fase)
                        if (self.id_proyecto == fase.id_proyecto):
                            return
                    
                elif (self.tipo == "Tipo"):
                    algun = False
                    for p in r.permisos:
                        if (p.tipo.find(self.tipo) >= 0):
                            algun = True
                            break
                        
                    if (algun and self.id_fase == r.id_fase):
                        return
                      
            elif (r.tipo.find(u"Tipo") == 0):
                if (self.tipo == "Tipo"):
                    if (self.id_tipo_item and ti.es_o_es_hijo(r.id_tipo_item)):
                        return
                    
                    ti = TipoItem.por_id(r.id_tipo_item)
                            
                    if (ti.id_fase == self.id_fase or ti.id_proyecto == self.id_proyecto):
                        return
            '''
            algun = False
            for p in r.permisos:
                if p.nombre_permiso.find(u"consultar") < 0 and \
                   p.tipo.find(self.tipo) >= 0 and \
                   p.nombre_permiso != "miembro":
                    algun = True
                    break
            if not algun:
                continue
            
            if (self.id_fase + self.id_proyecto + self.id_tipo_item == 0):
                return
            
            if (r.es_rol_sistema()):
                return
            
            if (self.id_proyecto == r.id_proyecto):
                if (r.tipo == u"Proyecto"):
                    return
                
            if (self.id_fase == r.id_fase):
                if (r.tipo == u"Fase"):
                    return
                
            ti = TipoItem.por_id(self.id_tipo_item)
            if (ti and ti.es_o_es_hijo(r.id_tipo_item)):
                return
            '''
        self.unmet(self.message)





class Miembro(Predicate):
    """
    Evalua si el usuario tiene algún permiso para un
    contexto dado.
    """
    message = u"No tiene algun permiso para dicho contexto"
    def __init__(self, **kw):
        """
        Método inicializador
        
        @param kw: Parametros para inicializar
        @keyword tipo: El tipo de permiso (Rol, Usuario, Proyecto, Fase, Tipo Ítem).
        """
        self.id_proyecto = 0
        self.id_fase = 0
        self.id_tipo_item = 0
        self.id_usuario = 0
        
        
        if kw.has_key('id_proyecto'):
            self.id_proyecto = int(kw['id_proyecto'])
            del kw['id_proyecto']
            
        elif kw.has_key('id_fase'):
            self.id_fase = int(kw['id_fase'])
            del kw['id_fase']
            
        elif kw.has_key('id_tipo_item'):
            self.id_tipo_item = int(kw['id_tipo_item'])
            del kw['id_tipo_item']
        
        if kw.has_key("id_usuario"):
            self.id_usuario = int(kw["id_usuario"])
            del kw["id_usuario"]
        
            
        super(Miembro, self).__init__(**kw)
    
    def evaluate(self, environ, credentials):
        if is_anonymous().is_met(environ): 
            self.unmet()
        nombre_usuario = credentials["repoze.what.userid"]
        usuario = Usuario.by_user_name(nombre_usuario)
        
        if self.id_usuario:
            usuario = Usuario.por_id(self.id_usuario)
        
        for r in usuario.roles:
            for p in r.permisos:
                if p.nombre_permiso.find(u"miembro") >= 0:
                    if self.id_proyecto:
                        if r.tipo == "Proyecto" and \
                           r.id_proyecto == self.id_proyecto:
                            return
                    elif self.id_fase:
                        if r.tipo == "Fase" and \
                           r.id_fase == self.id_fase:
                            return
                    else:
                        if r.tipo.find("Tipo") >= 0:
                            ti = TipoItem.por_id(self.id_tipo_item)
                            if ti and ti.es_o_es_hijo(r.id_tipo_item):
                                return
                        #if (r.tipo.find("Tipo") >= 0 and \
                        #    self.id_tipo_item.es_o_es_hijo(r.id_tipo_item)):
                        #    r.id_tipo_item == self.id_tipo_item:
                        #    return
        self.unmet(self.message)


