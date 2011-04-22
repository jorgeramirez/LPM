# -*- coding: utf-8 -*-

"""
Este módulo contiene las clases del modelo referentes
al B{Módulo de Administración}

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
import os
from datetime import datetime

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, DateTime
from sqlalchemy.orm import relation, backref

from lpm.model import DeclarativeBase, DBSession, desarrollo, gestconf
from lpm.model.desarrollo import *
from lpm.model.gestconf import *

__all__ = ['Fase', 'Proyecto']

class Fase(DeclarativeBase):
    """
    Clase que define un Fase de Proyecto.
    """
    __tablename__ = 'tbl_fase'
    
    #{ Columnas
    id_fase = Column(Integer, autoincrement=True, primary_key=True)
    id_proyecto = Column(Integer, ForeignKey('tbl_proyecto.id_proyecto', ondelete="CASCADE"))
    posicion = Column(Integer, unique=True, nullable=False)
    nombre = Column(Unicode(32), nullable=False)
    descripcion = Column(Unicode(200), nullable=True)
    numero_items = Column(Integer, nullable=False, default=0)
    numero_lb = Column(Integer, nullable=False, default=0)
    estado = Column(Unicode(20), nullable=True, default="Inicial")
    
    #{ Relaciones
    items = relation('Item')
    lbs = relation('LB')
    #}


class Proyecto(DeclarativeBase):
    """
    Clase que define un Proyecto que será administrado por el sistema.
    """
    __tablename__ = 'tbl_proyecto'
    
    #{Columnas
    id_proyecto = Column(Integer, autoincrement=True, primary_key=True)
    nombre = Column(Unicode(32), nullable=False)
    descripcion = Column(Unicode(200), nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    complejidad_total = Column(Integer, nullable=False, default=0)
    estado = Column(Unicode(20), nullable=False, default="No Iniciado")
    numero_fases = Column(Integer, nullable=False, default=0)
    
    #{ Relaciones
    fases = relation('Fase')
    #}
    
    def iniciar_proyecto(self):
        pass
    """creo que esto debería estar acá, no sé"""   
    def crear_fase(self):
        pass
    
    def eliminar_fase(self):
        pass





