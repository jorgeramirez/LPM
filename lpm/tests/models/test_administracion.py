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

from lpm.model import *
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
        self.obj.crear_fase(nombre=u'fase1', descripcion=u'nada', posicion=1)
        assert self.obj.fases[0].nombre == u"fase1"
    
    def test_no_crear_fase(self):
        """No se puede agregar fases una vez iniciado el proyecto"""
        self.obj.estado = u"Iniciado"
        self.obj.crear_fase(nombre=u'fase1', descripcion=u'nada', posicion=1)
        eq_(len(self.obj.fases), 0)
    
    @raises(NoResultFound)
    def test_eliminar_fase(self):
        """Debe poder eliminarse fases de un proyecto ``No Iniciado``"""
        self.obj.crear_fase(nombre=u'fase1', descripcion=u'nada', posicion=1)
        query = DBSession.query(Fase).filter_by(nombre=u"fase1")
        f = query.one()
        DBSession.flush()
        self.obj.eliminar_fase(f.id_fase)
        query.one()
    
    def test_iniciar_proyecto(self):
        """ 
        iniciar_proyecto funciona correctamente proyecto
        """
        self.obj.estado = u"Iniciado"
        self.obj.iniciar_proyecto()
        eq_(self.obj.estado, u"Iniciado")
    

class TestFase(ModelTest):
    """Unidad de prueba para el modelo ``Proyecto``"""
    klass = Fase
    
    #sobreescribimos el método en ModelTest
    def do_get_dependencies(self):
        dep = {}
        p = Proyecto(nombre=u"proyecto1", descripcion=u"Proyecto Uno")
        DBSession.add(p)
        DBSession.flush()
        p.crear_fase(posicion=1, nombre=u'fase1', descripcion=u"fase 1")
        p.iniciar_proyecto()
        return dep
    
    def test_crear_item(self):
        """crear_item funciona correctamente"""
        fase = DBSession.query(Fase).one()
        id_tipo = fase.tipos_de_item[0].id_tipo_item
        usuario = Usuario(nombre_usuario = u'usertest' , email=u"test@x.org")
        DBSession.add(usuario)
        DBSession.flush()
        fase.crear_item(id_tipo, prioridad=5, usuario=usuario ,descripcion = 'test', observaciones='test' , complejidad=5)
        item = DBSession.query(Item).one()
        assert item.propiedad_item_versiones[0].prioridad == 5
    
    def test_cambiar_estado_fase(self):
        """cambiar_estado de la fase funciona correctamente"""
        fase = DBSession.query(Fase).one()
        fase.cambiar_estado()
    
    def test_crear_lb(self):
        """crear_lb funciona correctamente"""
        fase = DBSession.query(Fase).one()
        num_lb = fase.numero_lb
        fase.crear_lb()
        DBSession.flush()
        assert num_lb < fase.numero_lb
    
    def test_query_obj(self):
        """Model objects can be queried"""
        fase = DBSession.query(Fase).one()
        
    def setUp(self):
        """Prepare model test fixture."""
        self.do_get_dependencies()

    def tearDown(self):
        """Finish model test fixture."""
        DBSession.rollback()
