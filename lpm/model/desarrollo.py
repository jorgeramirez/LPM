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

from sqlalchemy import ForeignKey, Column, and_
from sqlalchemy.types import Integer, Unicode, Boolean, LargeBinary, DateTime
from sqlalchemy.orm import relation, synonym, backref

from lpm.model import *
from lpm.model.excepciones import *


__all__ = ['Item', 'PropiedadItem', 'RelacionPorItem',
           'Relacion', 'AtributosDeItems', 'ArchivosExternos',
            'ArchivosPorItem', 'HistorialItems', 'AtributosPorItem']


class Item(DeclarativeBase):
    """
    Clase que representa al Item en su versión
    actual
    """
    __tablename__ = 'tbl_item'
    
    #{ Columnas
    id_item = Column(Integer, autoincrement=True, primary_key=True)
    codigo = Column(Unicode(50), unique=True)
    numero = Column(Integer, nullable=False)
    numero_por_tipo = Column(Integer, nullable=False)
    id_tipo_item = Column(Integer,
                          ForeignKey('tbl_tipo_item.id_tipo_item',
                                      onupdate='CASCADE', ondelete='CASCADE'),
                          nullable=False)
    id_fase = Column(Integer, ForeignKey('tbl_fase.id_fase', 
                                         onupdate='CASCADE', ondelete='CASCADE'),
                     nullable=False)
    id_propiedad_item = Column(Integer)

    
    #template para codificacion
    tmpl_codigo = u"IT-{id_item}-TI-{id_tipo_item}"
    #{ Relaciones
    propiedad_item_versiones = relation('PropiedadItem')
    
    #}
    
    def aprobar(self): #jorge (falta probar)
        """
        Aprueba un ítem.
        
        Las transiciones de estado pueden ser:
            - Revisión-Desbloq al de Aprobado
            - Desaprobado al de Aprobado
        
        @raises CondicionAprobarError: No cumple las condiciones de 
            aprobación del ítem
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        fase = Fase.por_id(self.id_fase)
        anteriores_count = DBSession.query(Relacion).filter_by( \
            id_posterior=self.id_item).count()
        
        if fase.posicion > 1 and anteriores_count == 0:
            raise CondicionAprobarError( \
                u"El ítem debe tener al menos un antecesor o padre")
                        
        for rpi in p_item.relaciones:
            if rpi.relacion.id_anterior == self.id_item: 
                continue
            item_ant = Item.por_id(rpi.relacion.id_anterior)
            p_item_ant = PropiedadItem.por_id(item_ant.id_propiedad_item)
            iplb = ItemsPorLB.filter_by_id_item(p_item_ant.id_propiedad_item)
            lb = LB.por_id(iplb.id_lb)
            if lb.estado != u"Cerrada":
                raise CondicionAprobarError( \
                    "Todos los antecesores y padres " + 
                    "deben estar en una LB cerrada")
        
        if p_item.estado == u"Desaprobado":
            for rpi in p_item.relaciones:
                item_rel = rpi.relacion.obtener_otro_item(self.id_item)
                item_rel.revisar(self.id_item)
        
        p_item.estado = u"Aprobado"
        DBSession.add(p_item)

    def desaprobar(self): #carlos
        """
        Desaprueba un ítem, implica que cambia su estado de "Aprobado", 
            o de "Revisión-Desbloq” al de “Desaprobado".
        
        @raises DesAprobarItemError: el estado del L{Item} es distinto al 
            de "Aprobado" o "Revision-Desbloq"
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado == u"Aprobado" :
            p_item.estado = u"Desaprobado"
        elif p_item.estado == u"Revision-Desbloq":
            p_item.estado = u"Desaprobado"

            iplb = ItemsPorLB.filter_by_id_item(p_item.id_propiedad_item)
            lb = Lb.por_id(iplb.id_lb)
            lb.romper()
        else:
            raise DesAprobarItemError()
        DBSession.add(p_item)
    
    def bloquear(self): #jorge
        """
        Bloquea un ítem, lo que implica que el mismo no puede
        ser modificado.
        
        @raises BloquearItemError: el estado del L{Item} es distinto al 
            de aprobado
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado != u"Aprobado":
            raise BloquearItemError()
        p_item.estado = u"Bloqueado"
        DBSession.add(p_item)
            
    def desbloquear(self): #carlos
        """
        Desbloquea un ítem, implica que el mismo puede ser
        modificado.
        
        @raises DesBloquearItemError: el estado del L{Item} es distinto al 
            de "Bloqueado" o "Revision-Desbloq"
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado == u"Bloqueado":
            p_item.estado = u"Aprobado"
        elif p_item.estado == u"Revision-Bloq":
            p_item.estado = u"Revision-Desbloq"
        else:
            raise DesBloquearItemError()
        DBSession.add(p_item)
    
    def revisar(self, id_origen):#nahuelop
        """id_origen es el id de un Item desde el que se produjo el cambio """
        pass
    
    def eliminar(self): #jorge
        """
        Elimina un ítem
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        p_item.estado = u"Eliminado"
        DBSession.add(p_item)
    
    def revivir(self):
        """
        Revive un ítem, implica que el mismo reviva con el estado desbloqueado.
        
        @raises RevivirItemError: el estado del L{Item} es distinto al 
            de "Eliminado"
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado != u"Eliminado":
            raise RevivirItemError()
        p_item_revivido = PropiedadItem()
        p_item_revivido.version = p_item.version + 1
        p_item_revivido.complejidad = p_item.complejidad
        p_item_revivido.prioridad = p_item.prioridad
        p_item_revivido.atributos = list(p_item.atributos)
        p_item_revivido.archivos = list(p_item.archivos)
        p_item_revivido.estado = u"Desaprobado"
        self.propiedad_item_versiones.append(p_item_revivido)
        DBSession.add(p_item_revivido)
        DBSession.flush()
        self.id_propiedad_item = p_item_revivido.id_propiedad_item
    
    def modificar(self, id_usuario, dict): #jorge
        """ 
        Modifica los valores de la propiedad del ítem.
        
        Se le pasa un diccionario y con los nuevos valores y 
        se compara con los actuales para ver qué cambió, para 
        registrar dicho cambio en el historial.
        
        @param id_usuario: Identificador del usuario que realizo el cambio
        @type id_usuario: C{Integer}
        @param dict: Diccionario con los nuevos valores
        @type dict: C{dict}
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado in [u"Bloqueado", u"Eliminado", u"Revisión-Bloq"]:
            raise ModificarItemError()
        p_item_mod = PropiedadItem()
        p_item_mod.version = p_item.version + 1
        p_item_mod.estado = u"Desaprobado"
        for attr in ["prioridad", "complejidad"]:
            valor = getattr(p_item, attr)
            setattr(p_item_mod, attr, dict[attr])
            if valor != dict[attr]:
                hist_items = HistorialItems()
                hist_items.tipo_modificacion = u"Modificado " + attr
                hist_items.usuario = Usuario.por_id(id_usuario)
                hist_items.item = p_item_mod
                DBSession.add(hist_items)
        p_item_mod.incorporar_relaciones(p_item.relaciones)
        p_item_mod.incorporar_atributos(p_item.atributos)
        p_item_mod.incorporar_archivos(p_item.archivos)
        self.propiedad_item_versiones.append(p_item_mod)
        DBSession.add(p_item_mod)
        DBSession.flush()
        self.id_propiedad_item = p_item_mod.id_propiedad_item

    def _crear_propiedad_item(self): #jorge
        """ ayuda a modificar() """
        pass
    
    def revertir(self, version): #jorge, falta probar
        """
        Modifica el Ítem a una versión específica.
        
        Si la versión anterior careciese de atributos agregados a su
        tipo de ítem en versiones posteriores, dichos atributos se 
        establecerán a sus valores por defecto.
        
        En el conjunto de relaciones no se incluirán relaciones que 
        se tenían con ítems que al momento de la reversión están en 
        estado "Eliminado"
        
        @param version: la versión a la que se desea volver
        @type version: C{Integer}
        """
        p_item_actual = PropiedadItem.por_id(self.id_propiedad_item)
        p_item_version = PropiedadItem.por_id_version(self.id_item, version)
        p_item_nuevo = PropiedadItem()
        p_item_nuevo.version = p_item_actual.version + 1
        p_item_nuevo.estado = u"Desaprobado"
        p_item_nuevo.prioridad = p_item_version.prioridad
        p_item_nuevo.complejidad = p_item_version.complejidad
        p_item_nuevo.incorporar_archivos(p_item_version.archivos)
        if len(p_item_version.atributos) < len(p_item_actual.atributos):
            tipo_item = TipoItem.por_id(self.id_tipo_item)
            for attr_por_tipo in tipo_item.atributos:
                attr_por_item = AtributosPorItem()
                attr_de_item = p_item_version.obtener_atributo(attr_por_tipo)
                if not attr_de_item:
                    attr_de_item = AtributosDeItems()
                    attr_de_item.valor = attr_por_tipo.valor_por_defecto
                attr_por_item.atributo = attr_de_item
                p_item_nuevo.atributos.append(attr_por_item)
                DBSession.add_all([attr_de_item, attr_por_item])
        else:
            p_item_nuevo.incorporar_atributos(p_item_version.atributos)

        for rpi in p_item_version.relaciones:
            item_otro = rpi.relacion.obtener_otro_item( \
                        p_item_version.id_item_actual)
            p_item_otro = PropiedadItem.por_id(item_otro.id_propiedad_item)
            if p_item_otro.estado != u"Eliminado":
                rpi_nuevo = RelacionPorItem()
                rpi_nuevo.relacion = rpi.relacion
                p_item_nuevo.relaciones.append(rpi_nuevo)
                DBSession.add(rpi_nuevo)
        hist_items = HistorialItems()
        hist_items.tipo_modificacion = u"Reversión De: %d A: %d" % \
            (p_item_actual.version, p_item_version.version)
        hist_items.usuario = Usuario.por_id(id_usuario)
        hist_items.item = p_item_nuevo
        DBSession.add_all([p_item_nuevo, hist_items])
        DBSession.flush()
        self.id_propiedad_item = p_item_nuevo.id_propiedad_item

    def calcular_impacto(self):
        pass
    
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{Item}
        """
        return DBSession.query(cls).filter_by(id_item=id).one()    

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
                                                onupdate='CASCADE', 
                                                ondelete='CASCADE'))
    
    #{ Relaciones
    relaciones = relation('RelacionPorItem')
    archivos = relation('ArchivosPorItem')
    atributos = relation('AtributosPorItem')
    #}
    
    def modificar_atributo(self):
        pass
    
    def agregar_relacion(self, id_antecesor, tipo):#nahuel
        """
        Relaciona dos items
        @param id_antecesor: identificador del ítem con el que se quiere relacionar.
        @param tipo: tipo de relación.
        
        @raise RelacionError: Si se quiere relacionar con un ítem que no está en una LB
        """
        antecesor = Item.por_id(id_antecesor)
        p_item_ant = PropiedadItem.por_id(antecesor.id_propiedad_item)
        
        if (self.estado != u"Bloqueado"):
            raise RelacionError(u"El item con el que se relaciona debe estar en una LB")
        
        relacion = Relacion()
        relacion.id_anterior = antecesor.id_item
        relacion.id_posterior = self.id_item_actual
        
        
        relacion.tipo = tipo
        rel_por_item = RelacionPorItem()
        rel_por_item.relaciones.append(relacion)
        DBSession.add(relacion)
          
            
    def _detectar_bucle(self):   
        """ 
        funciona con el método dfs()
         retorna una lista con id_item_actual de los que forman el ciclo
         None si no se encontró ciclo
        """
        index = 0
        visitado = {}
        
        return PropiedadItem._dfs(self, visitado)
        
    @classmethod
    def _dfs(cls, nodo, visitado):
        """ realiza la búsqueda en profundidad para encontrar bucles """
        if (nodo.item_actual in visitado):
            if (self.item_actual == nodo.item_actual):
                return [nodo.item_actual]
        
        visitado.setdefault(nodo.item_actual, [True])
        
        for arco in Relacion.relaciones_como_anterior(nodo.id_propiedad_item):
            if (arco.tipo == Relacion.tipo_relaciones['p-h']):
                adyacente = ProiedadItem.por_id(Item.por_id(arco.id_anterior).id_item_actual)
                ciclo = PropiedadItem._dfs(adyacente, visitado)
                if (ciclo):
                    ciclo.append(adyacente.id_item_actual)
                
        visitado[nodo.item_actual] = [False]
        
        return None

    def eliminar_relacion(self):#nahuel
        pass
    
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{PropiedadItem}
        """
        return DBSession.query(cls).filter_by(id_propiedad_item=id).one()
    
    @classmethod
    def por_id_version(cls, id, version):
        """
        Método de clase que realiza las búsquedas por identificador de
        ítem y versión de un elemento.
        
        @param id: identificador del ítem actual.
        @type id: C{Integer}
        @param version: la versión que se desea recuperar
        @type version: C{Integer}
        @return: el elemento recuperado
        @rtype: L{PropiedadItem}
        """
        return DBSession.query(cls).filter(
            and_(PropiedadItem.id_item_actual == id, 
            PropiedadItem.version == version)).one()
    
    def obtener_atributo(self, attr_por_tipo):
        """
        Obtiene el atributo del ítem. Si el ítem posee entre sus 
        atríbutos correspondientes a su tipo, el atributo dado
        entonces retorna el valor de dicho atributo, caso contrario
        retorna None.
        
        @param attr_por_tipo: el atributo a verificar
        @type attr_por_tipo: L{AtributosPorTipoItem}
        @return: El valor del atributo recuperado
        @rtype: L{AtributoDeItem} o C{None}.
        """
        for attr_por_item in self.atributos:
            attr_de_item = attr_por_item.atributo
            if attr_de_item.id_atributos_por_tipo_item == \
               attr_por_tipo.id_atributos_por_tipo_item:
                return attr_de_item
        return None
    
    def incorporar_relaciones(self, relaciones):
        """
        Agrega las relaciones al objecto. Se utiliza cuando se crean
        nuevas versiones, de manera tal que la nueva versión continue
        teniendo las relaciones que la vieja versión posee.
        
        @param relaciones: lista de objetos L{RelacionPorItem}
        @type relaciones: C{list}
        """
        for rpi in relaciones:
            rpi_nuevo = RelacionPorItem()
            rpi_nuevo.relacion = rpi.relacion
            self.relaciones.append(rpi_nuevo)
            DBSession.add(rpi_nuevo)

    def incorporar_atributos(self, atributos):
        """
        Agrega los atributos al objecto. Se utiliza cuando se crean
        nuevas versiones, de manera tal que la nueva versión continue
        teniendo los atributos que la vieja versión posee.
        
        @param atributos: lista de objetos L{AtributosPorItem}
        @type atributos: C{list}
        """
        for api in atributos:
            attr_nuevo = AtributosPorItem()
            attr_nuevo.atributo = api.atributo
            self.atributos.append(attr_nuevo)
            DBSession.add(attr_nuevo)
        
    def incorporar_archivos(self, archivos):
        """
        Agrega los archivos externos al objecto. Se utiliza cuando 
        se crean nuevas versiones, de manera tal que la nueva versión 
        continue teniendo los archivos externos que la vieja versión 
        posee.
        
        @param archivos: lista de objetos L{ArchivosPorItem}
        @type archivos: C{list}
        """
        for api in archivos:
            archivo_nuevo = ArchivosPorItem()
            archivo_nuevo.archivo = api.archivo
            self.archivos.append(archivo_nuevo)
            DBSession.add(archivo_nuevo)    


class RelacionPorItem(DeclarativeBase):
    """
    Clase que asocia los ítems con sus relaciones
    """
    __tablename__ = 'tbl_relacion_por_item'
    
    #{Columnas
    id_relacion_por_item = Column(Integer, autoincrement=True, 
                                  primary_key=True)
    id_propiedad_item = Column(Integer, 
                               ForeignKey('tbl_propiedad_item.id_propiedad_item',
                                          onupdate='CASCADE', ondelete='CASCADE'))
    id_relacion = Column(Integer, ForeignKey('tbl_relacion.id_relacion',
                                             onupdate='CASCADE', ondelete='CASCADE'))
    revisar = Column(Boolean, nullable=False, default=False)
   
    #{ Relaciones
    relaciones = relation("Relacion")
    #}


class Relacion(DeclarativeBase):
    """
    Clase que define una relación entre ítems.
    """
    __tablename__ = 'tbl_relacion'
    
    #{ Columnas
    id_relacion = Column(Integer, autoincrement=True, primary_key=True)
    tipo = Column(Unicode(45), nullable=False)
    codigo = Column(Unicode(50), unique=True)
    id_anterior = Column(Integer, ForeignKey('tbl_item.id_item',
                                              onupdate='CASCADE', 
                                              ondelete='CASCADE'))
    id_posterior = Column(Integer, ForeignKey('tbl_item.id_item',
                                              onupdate='CASCADE', 
                                              ondelete='CASCADE'))
    
    tipo_relaciones = {'a-s': u"Antecesor-Sucesor", 'p-h' : u"Padre-Hijo"}
    #template para codificacion
    tmpl_codigo = u"REL-{id_relacion}-{tipo}-{id_anterior}-{id_posterior}"
    #{ Métodos de clase
    @classmethod
    def relaciones_como_posterior(cls, id_item):
        """
        Recupera las relaciones en las que el ítem esta como
        hijo o sucesor, dependiendo del tipo de relación
        de ítem dado.
        
        @param id: el identificador del ítem hijo o sucesor
        @type id: C{Integer}
        @return: las relaciones
        @rtype: L{Relacion}
        """
        return DBSession.query(cls).filter_by(id_posterior=id_item).all()

    @classmethod
    def relaciones_como_anterior(cls, id_item):
        """
        Recupera las relaciones en las que el ítem esta como
        padre o antecesor, dependiendo del tipo de relación
        de ítem dado.
        
        @param id: el identificador del ítem padre o antecesor
        @type id: C{Integer}
        @return: las relaciones
        @rtype: L{Relacion}
        """
        DBSession.query(cls).filter_by(id_anterior=id_item).all()
    
    #{ Métodos de Objeto
    def obtener_otro_item(self, id_item):
        """
        Obtiene el otro ítem que forma parte de la relación.
        
        @param id_item: identificador de uno de los extremos de la relación.
        @type id_item: C{Integer}
        @return: el otro extremo de la relación
        @rtype: L{Item}
        """
        if self.id_anterior != id_item:
            id_otro = self.id_anterior
        else:
            id_otro = self.id_posterior
        item_otro = Item.por_id(id_otro)
        return item_otro
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
        ForeignKey('tbl_atributos_por_tipo_item.id_atributos_por_tipo_item',
                   onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False)
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
        ForeignKey('tbl_propiedad_item.id_propiedad_item',
                   onupdate='CASCADE', ondelete='CASCADE'))
    id_atributos_de_items = Column(Integer,
        ForeignKey('tbl_atributos_de_items.id_atributos_de_items',
                    onupdate='CASCADE', ondelete='CASCADE'))

    #{ Relaciones
    atributo = relation("AtributosDeItems")
    #}
    
    def modificar_atributo(self, id, valor):
        pass


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
        ForeignKey('tbl_propiedad_item.id_propiedad_item',
                   onupdate='CASCADE', ondelete='CASCADE'))  #parte izquierda de la relación
    id_archivo_externo = Column(Integer,
        ForeignKey('tbl_archivos_externos.id_archivo_externo',
                   onupdate='CASCADE', ondelete='CASCADE')) #parte derecha de la relación
    
    #{ Relaciones
    archivo = relation("ArchivosExternos")
    #} 
    
    def agregar_archivo(self):
        pass


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
    id_usuario = Column(Integer, ForeignKey('tg_user.id_usuario',
                                            onupdate='CASCADE', 
                                            ondelete='CASCADE'))
    id_item = Column(Integer, 
        ForeignKey('tbl_propiedad_item.id_propiedad_item',
                    onupdate='CASCADE', ondelete='CASCADE'))
    
    #{ Relaciones
    usuario = relation("Usuario", backref="historial_item")
    item = relation("PropiedadItem", backref="historial_item")
    #}  
