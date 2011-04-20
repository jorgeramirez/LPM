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

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String, Date
from sqlalchemy.orm import relation, backref

from lpm.model import DeclarativeBase, DBSession

__all__ = ['Fase', 'Proyecto']

class Fase(DeclarativeBase):
    """
    Clase que define un Fase de Proyecto.
    """
    __tablename__ = 'tbl_fase'
    
    #{ Columnas
    id_fase = Column(Integer, autoincrement=True, primary_key=True)
    id_proyecto = Column(Integer, ForeignKey('tbl_proyecto.id_proyecto'))
    posicion = Column(Integer, nullable=False)
    nombre = Column(String(32), nullable=False)
    descripcion = Column(String(200), nullable=True)
    numero_items = Column(Integer, nullable=True)
    numero_lb = Column(Integer, nullable=True)
    estado = Column(String(20), nullable=True)
    
    #{ Relaciones
    items = relation('Item', backref='fase')
    #}


class Proyecto(DeclarativeBase):
    """
    Clase que define un Proyecto que será administrado por el sistema.
    """
    __tablename__ = 'tbl_proyecto'
    
    #{Columnas
    id_proyecto = Column(Integer, autoincrement=True, primary_key=True)
    nombre = Column(String(32), nullable=False)
    descripcion = Column(String(200), nullable=False)
    fecha_creacion = Column(Date, nullable=False)
    complejidad_total = Column(Integer, nullable=False)
    estado = Column(String(20), nullable=False)
    numero_fases = Column(Integer, nullable=False)
    
    #{ Relaciones
    fases = relation('Fase', backref="proyecto")
    #}





