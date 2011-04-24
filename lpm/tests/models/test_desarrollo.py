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

from lpm.model import DBSession
from lpm.model.desarrollo import *
from lpm.model.administracion import *
from lpm.model.gestconf import *
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
        p.crear_fase(dict(nombre=u"fase1", descripcion=u"fase uno"))
        DBSession.flush()
        tipo_item = TipoItem()
        tipo_item.codigo = u"cu"
        tipo_item.id_proyecto = p.id_proyecto
        DBSession.add(tipo_item)
        DBSession.flush()
        dep["id_fase"] = p.fases[0].id_fase
        dep["numero"] = 0
        dep["numero_por_tipo"] = 0
        dep["id_tipo_item"] = tipo_item.id_tipo_item
        return dep
    
    def test_crear_item(self):
        """``crear_item`` funciona"""
        fase = Fase.por_id(self.obj.id_fase)
        item = fase.crear_item(self.obj.id_tipo_item)
        
        
