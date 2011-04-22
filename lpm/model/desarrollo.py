# -*- coding: utf-8 -*-

"""
Este módulo contiene las clases del modelo referentes
al B{Módulo de Desarrollo}

Ejemplo de utilización de L{PropiedadItem}, L{RelacionPorItem} y L{Relacion}::
    pi = PropiedadItem()
    rpi = RelacionPorItem()
    rpi.relacion = Relacion()
    pi.relaciones.append(rpi)

Iterar sobre los objetos Relacion via RelacionPorItem::
    for rpi in pi.relaciones:
        print rpi.revisar
        print rpi.relacion

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
import os
from datetime import datetime

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Unicode, Boolean, LargeBinary, DateTime
from sqlalchemy.orm import relation, synonym, backref

from lpm.model import DeclarativeBase, DBSession


__all__ = ['Item', 'PropiedadItem', 'TipoItem', 'AtributosPorTipoItem',
           'RelacionPorItem', 'Relacion', 'AtributosDeItems',
           'ArchivosExternos', 'ArchivosPorItem', 'HistorialItems',
           'AtributosPorItem']


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
    id_tipo_item = Column(Integer,
                          ForeignKey('tbl_tipo_item.id_tipo_item'),
                          nullable=False)
    id_fase = Column(Integer, ForeignKey('tbl_fase.id_fase', ondelete="CASCADE"),
                     nullable=False)
    id_propiedad_item = Column(Integer, 
                               ForeignKey('tbl_propiedad_item.id_propiedad_item'),
                               nullable=False,)
    

    #{ Relaciones
    propiedad_item_versiones = relation('PropiedadItem')
    
    #}
    
    def aprobar(self):
        pass
    

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
    estado = Column(Unicode(20), nullable=False)
    id_item_actual = Column(Integer, ForeignKey('tbl_item.id_item',
                            ondelete = "CASCADE"))
    
    #{ Relaciones
    relaciones = relation('RelacionPorItem')
    archivos = relation('ArchivosPorItem')
    atributos = relation('AtributosPorItem')
    #}
    
    

class TipoItem(DeclarativeBase):
    """
    Clase que define las características
    de un tipo de ítem.
    """
    __tablename__ = 'tbl_tipo_item'
    
    #{ Columnas
    id_tipo_item = Column(Integer, autoincrement=True, primary_key=True)
    codigo = Column(Unicode(32), nullable=False)
    descripcion = Column(Unicode(200), nullable=True)
    id_proyecto = Column(Integer, ForeignKey('tbl_proyecto.id_proyecto',
                         ondelete="CASCADE"), nullable=True)
    id_padre = Column(Integer, ForeignKey('tbl_tipo_item.id_tipo_item'))
    
    #{ Relaciones
    
    #tipo_hijo = relation('TipoItem', backref=backref('tipo_padre', remote_side=id_tipo_item))
    atributos = relation('AtributosPorTipoItem')
    items = relation('Item')
    #}


class AtributosPorTipoItem(DeclarativeBase):
    """
    Clase que define que atributos posee un determinado
    tipo de ítem.
    """
    __tablename__ = 'tbl_atributos_por_tipo_item'
    
    #{ Columnas
    id_atributos_por_tipo_item = Column(Integer, autoincrement=True, 
                                        primary_key=True)
    nombre = Column(Unicode(32), nullable=False)
    tipo = Column(Unicode(32), nullable=False)
    valor_por_defecto = Column(Unicode(32), nullable=True)
    id_tipo_item = Column(Integer, ForeignKey('tbl_tipo_item.id_tipo_item'))
    #}


class RelacionPorItem(DeclarativeBase):
    """
    Clase que asocia los ítems con sus relaciones
    """
    __tablename__ = 'tbl_relacion_por_item'
    
    #{Columnas
    id_relacion_por_item = Column(Integer, autoincrement=True, 
                                  primary_key=True)
    revisar = Column(Boolean, nullable=False, default=False)
    id_propiedad_item = Column(Integer, 
                               ForeignKey('tbl_propiedad_item.id_propiedad_item',
                               ondelete="CASCADE"))
    id_relacion = Column(Integer, ForeignKey('tbl_relacion.id_relacion',
                         ondelete="CASCADE"))
    
   
    #{ Relaciones
    relacion = relation("Relacion")

    #}


class Relacion(DeclarativeBase):
    """
    Clase que define una relación entre ítems.
    """
    __tablename__ = 'tbl_relacion'
    
    #{ Columnas
    id_relacion = Column(Integer, autoincrement=True, primary_key=True)
    tipo = Column(Unicode(45), nullable=False)
    id_anterior = Column(Integer, ForeignKey('tbl_item.id_item'))
    id_posterior = Column(Integer, ForeignKey('tbl_item.id_item'))
    #}

    

class AtributosDeItems(DeclarativeBase):
    """
    Clase que define el valor para un atributo del item. Dicho atributo
    forma parte del conjunto de atributos del L{TipoItem}.
    """
    __tablename__ = 'tbl_atributos_de_items'
    
    #{ Columnas
    id_atributos_de_items = Column(Integer, 
                                   autoincrement=True, primary_key=True)
    id_atributos_por_tipo_item = Column(Integer,
        ForeignKey('tbl_atributos_por_tipo_item.id_atributos_por_tipo_item'),
        nullable=False,)
    _valor = Column(Unicode(200), nullable=False)
    
    def _get_valor(self):
        """ dependiendo del tipo retorna un valor"""
        pass
    
    def _set_valor(self, valor):
        """ dependiendo del tipo del valor, verifica que sea válido,
         si no lanza una excepción (?) """
        pass
    
    valor = synonym('_valor', descriptor=property(_get_valor, _set_valor))
    
    #}


class AtributosPorItem(DeclarativeBase):
    """
    Clase que asocia un ítem con sus atributos
    """
    __tablename__ = 'tbl_atributos_por_item'
    
    #{ Columnas
    id_atributos_por_item = Column(Integer, autoincrement=True, 
                                   primary_key=True)
    id_propiedad_item = Column(Integer,
        ForeignKey('tbl_propiedad_item.id_propiedad_item'))
    id_atributos_de_items = Column(Integer,
        ForeignKey('tbl_atributos_de_items.id_atributos_de_items'))

    #{ Relaciones
    atributos = relation("AtributosDeItems")
    #}


class ArchivosExternos(DeclarativeBase):
    """
    Clase que representa un archivo externo que puede ser adjuntado a un
    L{Item}
    """
    __tablename__ = 'tbl_archivos_externos'
    
    #{ Columnas
    id_archivo_externo = Column(Integer, autoincrement=True, primary_key=True)
    archivo = Column(LargeBinary(2048), nullable=False)
    nombre_archivo = Column(Unicode(50), nullable=False)
    #}


class ArchivosPorItem(DeclarativeBase):
    """
    Clase que asocia un ítem con sus archivos externos
    """
    __tablename__ = 'tbl_archivos_por_item'
    
    #{ Columnas
    id_archivos_por_item = Column(Integer, autoincrement=True, primary_key=True)
    id_propiedad_item = Column(Integer, 
        ForeignKey('tbl_propiedad_item.id_propiedad_item'))  #parte izquierda de la relación
    id_archivo_externo = Column(Integer,
        ForeignKey('tbl_archivos_externos.id_archivo_externo')) #parte derecha de la relación
    
    #{ Relaciones
    archivos = relation("ArchivosExternos")
    #} 


class HistorialItems(DeclarativeBase):
    """
    Clase que define un historial de modificaciones
    hechas sobre los ítems.
    """
    __tablename__ = 'tbl_historial_item'
    
    #{ Columnas
    id_historial_items = Column(Integer, autoincrement=True, primary_key=True)
    tipo_modificacion = Column(Unicode(45), nullable=False)
    fecha_modificacion = Column(DateTime, nullable=False, default=datetime.now)
    id_usuario = Column(Integer, ForeignKey('tg_user.user_id'))
    id_item = Column(Integer, 
        ForeignKey('tbl_propiedad_item.id_propiedad_item'))
    
    #{ Relaciones
    usuario = relation("Usuario", backref="regs_historial_items")
    #}
   
    
    
    
