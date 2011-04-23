# -*- coding: utf-8 -*-
"""
Módulo de prueba para lpm.model.administracion

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0 
"""
from nose.tools import eq_

from lpm import model
#from lpm.tests.models import ModelTest

import transaction
from lpm.model import *

p = Proyecto()
p.nombre = u"proyecto4"
DBSession.add(p)
DBSession.flush()
#p = DBSession.query(Proyecto).filter_by(id_proyecto=1).one()
p.crear_fase(dict(nombre=u'fase1', descripcion=u'nada'))
p.crear_fase(dict(nombre=u'fase2', descripcion=u'hola'))
p.crear_fase(dict(nombre=u'fase3', descripcion=u'lala'))
DBSession.flush()
p.eliminar_fase(8)
p.iniciar_proyecto()

DBSession.flush()
transaction.commit()
