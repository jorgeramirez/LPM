# -*- coding: utf-8 -*-
"""
Módulo de prueba para lpm.model.administracion

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0 
"""
from nose.tools import eq_, raises

from lpm.model import DBSession
from lpm.model.desarrollo import *
from lpm.model.administracion import *
from lpm.model.gestconf import *
from lpm.model.excepciones import *

from lpm.tests.models import ModelTest
from sqlalchemy.orm.exc import NoResultFound

class TestProyecto(ModelTest):
    """Unidad de prueba para el modelo ``Proyecto``"""
    klass = Proyecto
    attrs = dict(
        nombre = u"proyecto",
        descripcion = u"proyecto de prueba"
    )
    
    def test_obj_creacion(self):
        """El constructor debe setear los datos correctamente"""
        assert self.obj.nombre == u"proyecto" and \
            self.obj.descripcion == u"proyecto de prueba"
    
    def test_crear_fase(self):
        """Debe poder agregarse fases a un proyecto recién creado"""
        self.obj.crear_fase(dict(nombre=u'fase1', descripcion=u'nada'))
        assert self.obj.fases[0].nombre == u"fase1"
    
    def test_no_crear_fase(self):
        """No se puede agregar fases una vez iniciado el proyecto"""
        self.obj.estado = u"Iniciado"
        self.obj.crear_fase(dict(nombre=u'fase1', descripcion=u'nada'))
        eq_(len(self.obj.fases), 0)
    
    @raises(NoResultFound)
    def test_eliminar_fase(self):
        """Debe poder eliminarse fases de un proyecto ``No Iniciado``"""
        self.obj.crear_fase(dict(nombre=u'fase1', descripcion=u'nada'))
        query = DBSession.query(Fase).filter_by(nombre=u"fase1")
        f = query.one()
        DBSession.flush()
        self.obj.eliminar_fase(f.id_fase)
        query.one()
    
    def test_iniciar_proyecto(self):
        """
            ``iniciar_proyecto`` debe setear correctamente 
            el estadodel proyecto
        """
        self.obj.iniciar_proyecto()
        eq_(self.obj.estado, u"Iniciado")
