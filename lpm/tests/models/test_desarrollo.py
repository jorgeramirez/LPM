# -*- coding: utf-8 -*-
"""
Módulo de prueba para lpm.model.desarrollo

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0 
"""
from nose.tools import eq_

from lpm.model import *
from lpm.model.excepciones import *

from lpm.tests.models import ModelTest


class TestItem(ModelTest):
    """Unidad de prueba para el modelo ``Item``"""
    klass = Item
    
    #sobreescribimos el método en ModelTest
    def do_get_dependencies(self):
        dep = {}
        p = Proyecto(nombre=u"proyecto1", descripcion=u"Proyecto Uno")
        DBSession.add(p)
        DBSession.flush()
        p.crear_fase(nombre=u"fase1", descripcion=u"fase uno", posicion=1)
        DBSession.flush()
        tipo_item = TipoItem()
        tipo_item.codigo = u"cu"
        tipo_item.id_proyecto = p.id_proyecto
        tipo_item.nombre = u"Caso de Uso"
        p_item = PropiedadItem()
        p_item.version = 1
        p_item.complejidad = 5
        p_item.prioridad = 5
        p_item.estado = u"Aprobado"
        DBSession.add(p_item)
        DBSession.add(tipo_item)
        DBSession.flush()
        dep["id_fase"] = p.fases[0].id_fase
        dep["numero"] = 0
        dep["numero_por_tipo"] = 0
        dep["id_tipo_item"] = tipo_item.id_tipo_item
        dep["id_propiedad_item"] = p_item.id_propiedad_item
        dep["propiedad_item_versiones"] = [p_item]
        return dep
    
    def test_aprobar_item(self):
        """Aprobar ítem funciona correctamente"""
        
        pass
    
    def test_desaprobar_item(self):
        """Desaprobar ítem funciona correctamente"""
        
        pass
    
    def test_bloquear_item(self):
        """Bloquear Item funciona correctamente"""
        usuario = Usuario(nombre_usuario = u'usertest' , email=u"test@x.org")
        DBSession.add(usuario)
        DBSession.flush()
        self.obj.bloquear(usuario=usuario)
        eq_(self.obj.propiedad_item_versiones[0].estado, u"Bloqueado")
    
    def test_desbloquear_item(self):
        """Desbloquear Item funciona correctamente"""
        usuario = Usuario(nombre_usuario = u'usertest' , email=u"test@x.org")
        DBSession.add(usuario)
        DBSession.flush()
        self.obj.propiedad_item_versiones[0].estado = u"Bloqueado"
        self.obj.desbloquear(usuario=usuario)
        assert self.obj.propiedad_item_versiones[0].estado == u"Aprobado" or \
            self.obj.propiedad_item_versiones[0].estado == u"Revision-Desbloq"
    
    def test_eliminar_item(self):
        """Eliminar ítem funciona correctamente"""
        usuario = Usuario(nombre_usuario = u'usertest' , email=u"test@x.org")
        DBSession.add(usuario)
        DBSession.flush()
        self.obj.eliminar(usuario=usuario)
        eq_(self.obj.propiedad_item_versiones[0].estado, u"Eliminado")
    
    def test_modificar_item(self):
        """Modificar Item funciona correctamente"""
        u = Usuario()
        u.nombre_usuario = u'admin'
        u.nombre = u'Administrador'
        u.apellido = u'Del Sistema'
        u.email = u'manager@somedomain.com'
        u.password = u'administrador'
        DBSession.add(u)
        DBSession.flush()
        self.obj.modificar(u, complejidad=8, prioridad=10, descripcion=u'test',
                            observaciones=u'test')
        p_item = PropiedadItem.por_id(self.obj.id_propiedad_item)
        eq_(p_item.complejidad, 8)

    def test_revivir_item(self):
        """Revivir item funciona correctamente"""
        p_item = self.obj.propiedad_item_versiones[0]
        DBSession.add(p_item)
        DBSession.flush()
        usuario = Usuario(nombre_usuario = u'usertest' , email=u"test@x.org")
        DBSession.add(usuario)
        DBSession.flush()
        self.obj.eliminar(usuario=usuario)
        eq_(self.obj.propiedad_item_versiones[0].estado, u"Eliminado")
    
    def test_revertir_item(self):
        """Revertir Item funciona correctamente"""
        pass
