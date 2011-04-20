# -*- coding: utf-8 -*-

"""
Este módulo contiene las clases del modelo referentes
al B{Módulo de Gestión de Configuración}

Ejemplo de utilización de L{ItemsPorLB}, L{LB} y L{PropiedadItem}::

    lb = LB()
    iplb = ItemsPorLB()
    iplb.propiedad_item = PropiedadItem()
    lb.items.append(iplb)

Iterar sobre los objetos PropiedadItem via ItemsPorLB::

    for iplb in lb.items:
        print iplb.propiedad_item

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

__all__ = ['LB', 'HistorialLB', 'ItemsPorLB']

class LB(DeclarativeBase):
    """
    Clase que define un Linea Base.
    """
    __tablename__ = 'tbl_lb'
    
    #{ Columnas
    id_lb = Column(Integer, autoincrement=True, primary_key=True)
    numero = Column(Integer, nullable=False)
    estado = Column(String(20), nullable=True)
    
    #{ Relaciones
    regs_historial_lb = relation("HistorialLB", backref="lb")
    propiedad_items = relation("ItemsPorLB", backref='lb')
    #}


class HistorialLB(DeclarativeBase):
    """
    Clase que define un historial de modificaciones
    hechas sobre los las Líneas Bases.
    """
    __tablename__ = 'tbl_historial_lb'
    
    #{ Columnas
    id_historial_lb = Column(Integer, autoincrement=True, primary_key=True)
    tipo_operacion = Column(String(45), nullable=False)
    fecha_modificacion = Column(Date, nullable=False)
    id_usuario = Column(Integer, ForeignKey('tg_user.user_id'))
    id_lb = Column(Integer, ForeignKey('tbl_lb.id_lb'))
    #}

    
class ItemsPorLB(DeclarativeBase):
    """
    Clase que define el conjunto de ítems que forman parte
    de una línea base
    """
    __tablename__ = 'tbl_items_por_lb'
    
    #{ Columnas
    id_item_por_lb = Column(Integer, autoincrement=True, primary_key=True)
    id_item = Column(Integer, 
        ForeignKey('tbl_propiedad_item.id_propiedad_item'))
    id_lb = Column(Integer, ForeignKey('tbl_lb.id_lb'))
    
    #{ Relaciones
    propiedad_item = relation('PropiedadItem', backref='item_lb_assocs')
    #}
    



    



