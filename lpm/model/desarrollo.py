# -*- coding: utf-8 -*-

"""
Este módulo contiene las clases del modelo referentes
al B{Módulo de Desarrollo}

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com}

@since: 1.0
"""

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, String
from sqlalchemy.orm import relation

from lpm.model import DeclarativeBase, DBSession


__all__ = ['Item', 'PropiedadItem', 'TipoItem', 'AtributosPorTipoItem']


class Item(DeclarativeBase):
    """
    Clase que representa al Item en su versión
    actual
    """
    __tablename__ = 'tbl_item'
    
    #{ Columnas
    id_item = Column(Integer, autoincrement=True, primary_key=True)
    numero = Column(Integer, nullable=False)
    numero_por_tipo = Column(Integer, nullable=False)
    id_tipo_item = Column(Integer, ForeignKey('tbl_tipo_item.id_tipo_item'))
    id_fase = Column(Integer, ForeignKey('tbl_fase.id_fase'))
    
    #{ Relaciones
    propiedad_item = relation('PropiedadItem', backref='item_actual')
    #}


class PropiedadItem(DeclarativeBase):
    """
    Clase que contiene los atributos básicos de 
    un L{Item}
    """
    __tablename__ = 'tbl_propiedad_item'
    
    #{ Columnas
    id_propiedad_item = Column(Integer, autoincrement=True, primary_key=True)
    version = Column(Integer, nullable=False)
    complejidad = Column(Integer, nullable=False)
    prioridad = Column(Integer, nullable=False)
    estado = Column(String(20), nullable=False)
    id_item_actual = Column(Integer, ForeignKey('tbl_item.id_item'))
    #}


class TipoItem(DeclarativeBase):
    """
    Clase que define las características
    de un tipo de ítem.
    """
    __tablename__ = 'tbl_tipo_item'
    
    #{ Columnas
    id_tipo_item = Column(Integer, autoincrement=True, primary_key=True)
    codigo = Column(String(32), nullable=False)
    descripcion = Column(String(200), nullable=True)
    id_proyecto = Column(Integer, ForeignKey('tbl_proyecto.id_proyecto'))
    id_padre = Column(Integer, ForeignKey('tbl_tipo_item.id_tipo_item'))
    
    #{ Relaciones
    tipo_hijo = relation('TipoItem', backref=backref('tipo_padre', 
                                                     remote_side=id_tipo_item))
    atributos = relation('AtributosPorTipoItem', backref='tipo_item')
    #}


class AtributosPorTipoItem(DeclarativeBase):
    """
    Clase que define que atributos posee un determinado
    tipo de ítem.
    """
    
    #{ Columnas
    id_atributos_por_tipo_item = Column(Integer, autoincrement=True, 
                                        primary_key=True)
    nombre = Column(String(32), nullable=False)
    tipo = Column(String(32), nullable=False)
    valor_por_defecto = Column(String(32), nullable=True)
    id_tipo_item = Column(Integer, ForeignKey('tbl_tipo_item.id_tipo_item'))
    #}
   
