# -*- coding: utf-8 -*-
"""
Módulo de prueba para lpm.model.gestconf

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

class TestLb(ModelTest):
    """Unidad de prueba para el modelo ``LB``"""
    klass = LB
    attrs = {"numero" : 1}
    
    def do_get_dependencies(self):
        return {}
        
    def test_agregar_item(self):
        """agregar_item funciona correctamente"""
        pass 
    
