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

from sqlalchemy import ForeignKey, Column, and_, or_
from sqlalchemy.types import Integer, Unicode, Boolean, LargeBinary, DateTime
from sqlalchemy.orm import relation, synonym, backref

from lpm.model import *
import lpm.model#Para elementos de administracion y gestconf
from lpm.model.excepciones import *

import transaction


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
    #tmpl_codigo = u"IT-{id_item}-TI-{id_tipo_item}"
    tmpl_codigo = u"{siglas}-{numero_por_tipo}/f-{pos}/p-{proy}"
    estados_posibles = {'d' : u"Desaprobado",
                        'a' : u"Aprobado",
                        'b' :  u"Bloqueado",
                        'e' : u"Eliminado",
                        'r-b' : u"Revisión-Bloq",
                        'r-d' : u"Revisión-Desbloq"
                        }
    #{ Relaciones
    propiedad_item_versiones = relation('PropiedadItem')
    
    #}

    @classmethod
    def generar_codigo(cls, item):
        """
        Genera el codigo para el elemento pasado como parametro
        """
        tipo = lpm.model.TipoItem.por_id(item.id_tipo_item)
        siglas = tipo.codigo.split("-")[0]
        fase = lpm.model.Fase.por_id(tipo.id_fase)
        return cls.tmpl_codigo.format(siglas=siglas,
                                      numero_por_tipo=item.numero_por_tipo,
                                      pos=fase.posicion,
                                      proy=tipo.id_proyecto)
    
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
        fase = lpm.model.Fase.por_id(self.id_fase)
        anteriores_count = DBSession.query(Relacion).filter_by( \
            id_posterior=self.id_item).count()
        
        if fase.posicion > 1 and anteriores_count == 0:
            raise CondicionAprobarError(u"El ítem debe tener al menos un antecesor o padre")
                        
        for rpi in p_item.relaciones:
            if rpi.relacion.id_anterior == self.id_item: 
                continue
            item_ant = Item.por_id(rpi.relacion.id_anterior)
            p_item_ant = PropiedadItem.por_id(item_ant.id_propiedad_item)
            iplb = lpm.model.ItemsPorLB.filter_by_id_item(p_item_ant.id_propiedad_item)
            lb = lpm.model.LB.por_id(iplb.id_lb)
            if lb.estado != u"Cerrada":
                raise CondicionAprobarError(u"Todos los antecesores y padres " + \
                                            "deben estar en una LB cerrada")
        
        if p_item.estado == u"Desaprobado":
            for rpi in p_item.relaciones:
                item_rel = rpi.relacion.obtener_otro_item(self.id_item)
                item_rel.marcar_para_revisar(self.id_item)
        
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

            iplb = lpm.model.ItemsPorLB.filter_by_id_item(p_item.id_propiedad_item)
            lb = lpm.model.Lb.por_id(iplb.id_lb)
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
        elif p_item.estado == u"Revisión-Bloq":
            p_item.estado = u"Revisión-Desbloq"
        else:
            raise DesBloquearItemError()
        DBSession.add(p_item)
    
    def marcar_para_revisar(self):#nahuelop
        """id_origen es el id de un Item desde el que se produjo el cambio """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        
        relaciones_por_item = DBSession.query(RelacionPorItem).\
                                        filter(RelacionPorItem.id_propiedad_item\
                                        == self.id_propiedad_item).all()
        for r in relaciones_por_item:
#            relacion = Relacion.por_id(r.id_relacion)
#            
#            if (relacion.id_anterior == self.id_item):
#                otro = Item.por_id(relacion.id_anterior)
#            else:
#                otro = Item.por_id(relacion.id_posterior)
            
            otro = r.relacion.obtener_otro_item(self.id_item)
            p_otro = PropiedadItem.por_id(otro.id_item)
               
            if (otro.revisar()):#solo si se cambio el estado de revisar se pone como para revisar la relacion
                rpi_otro = DBSession.query(RelacionPorItem).\
                                            filter(and_(RelacionPorItem.id_propiedad_item\
                                            == otro.id_propiedad_item,\
                                            RelacionPorItem.id_relacion == r.id_relacion))\
                                            .first()
                rpi_otro.revisar = True
    
    def revisar(self):
        """ Cambia el estado de bloqueado a Rev-bloqueado y de aprobado a 
        rev-desbloqueado
        @return: True si se marcó para revisión"""
        
        p_item = PropieadadItem.por_id(self.id_propiedad_item)
        if (p_item.estado == u"Bloqueado"):
            p_item.estado = u"Revisión-Bloq"
            return True
        elif (p_item.estado == u"Aprobado"):
            p_item.estado = u"Revisión-Desbloq"
            return True
        
        return False
            
    def eliminar(self): #jorge
        """
        Elimina un ítem
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado in [u"Bloqueado", u"Eliminado", u"Revisión-Bloq"]:
            raise EliminarItemError()
        p_item.estado = u"Eliminado"
    
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
        p_item_revivido.incorporar_atributos(p_item.atributos)
        p_item_revivido.incorporar_archivos(p_item.archivos)
        p_item_revivido.estado = u"Desaprobado"
        self.propiedad_item_versiones.append(p_item_revivido)
        DBSession.add(p_item_revivido)
        DBSession.flush()
        self.id_propiedad_item = p_item_revivido.id_propiedad_item
    
    def modificar(self, usuario, **kw): #jorge
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
            setattr(p_item_mod, attr, kw[attr])
            if valor != kw[attr]:
                hist_items = HistorialItems()
                hist_items.tipo_modificacion = u"Modificado " + attr
                hist_items.usuario = usuario
                hist_items.item = p_item
                DBSession.add(hist_items)
        p_item_mod.incorporar_relaciones(p_item.relaciones)
        p_item_mod.incorporar_atributos(p_item.atributos)
        p_item_mod.incorporar_archivos(p_item.archivos)
        self.propiedad_item_versiones.append(p_item_mod)
        DBSession.add(p_item_mod)
        DBSession.flush()
        self.id_propiedad_item = p_item_mod.id_propiedad_item

        
    def revertir(self, id_version, usuario): #jorge, falta probar
        """
        Modifica el Ítem a una versión específica.
        
        Si la versión anterior careciese de atributos agregados a su
        tipo de ítem en versiones posteriores, dichos atributos se 
        establecerán a sus valores por defecto.
        
        En el conjunto de relaciones no se incluirán relaciones que 
        se tenían con ítems que al momento de la reversión están en 
        estado "Eliminado"
        
        @param id_version: identificador de la versión a la que se desea volver
        @type id_version: C{Integer}
        """
        p_item_actual = PropiedadItem.por_id(self.id_propiedad_item)
        p_item_version = PropiedadItem.por_id(id_version)
        p_item_nuevo = PropiedadItem()
        p_item_nuevo.version = p_item_actual.version + 1
        p_item_nuevo.estado = u"Desaprobado"
        p_item_nuevo.prioridad = p_item_version.prioridad
        p_item_nuevo.complejidad = p_item_version.complejidad
        p_item_nuevo.incorporar_archivos(p_item_version.archivos)
        if len(p_item_version.atributos) < len(p_item_actual.atributos):
            tipo_item = lpm.model.TipoItem.por_id(self.id_tipo_item)
            for attr_por_tipo in tipo_item.atributos:
                attr_por_item = AtributosPorItem()
                attr_de_item = p_item_version.obtener_atributo(attr_por_tipo)
                if not attr_de_item:
                    attr_de_item = AtributosDeItems()
                    attr_de_item.id_atributos_por_tipo_item = attr_por_tipo. \
                                                  id_atributos_por_tipo_item
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
        hist_items.usuario = usuario
        hist_items.item = p_item_actual
        self.propiedad_item_versiones.append(p_item_nuevo)
        DBSession.add_all([p_item_nuevo, hist_items])
        DBSession.flush()
        self.id_propiedad_item = p_item_nuevo.id_propiedad_item

    def calcular_impacto(self):
        pass
    
    def crear_siguiente_propiedad_item(self):
        """Crea y asigna al item una nueva propiedad en la que se deben realizar
        las modificaciones antes de guardar en el historial
        @return: la nueva propiedad item creada """
        
        p_item_viejo = PropiedadItem.por_id(self.id_propiedad_item)
        p_item_nuevo = PropiedadItem()
        p_item_nuevo.version = p_item_viejo.version + 1
        p_item_nuevo.estado = p_item_viejo.estado
        p_item_nuevo.id_item_actual = self.id_item
        p_item_nuevo.incorporar_archivos(p_item_viejo.archivos)
        p_item_nuevo.incorporar_atributos(p_item_viejo.atributos)
        p_item_nuevo.incorporar_relaciones(p_item_viejo.relaciones)
        self.id_propiedad_item = p_item_nuevo.id_propiedad_item
        DBSession.add(p_item_nuevo)
        
        return p_item_nuevo
    
    def guardar_historial(self, operacion, usuario):
        """ utilizado para guardar la propiedad de item actual en el historial
        @param operacion : operación que se registra en la nueva entrada del
        historial
        @param usuario : usuario que realizó el cambio
        """
        hist_items = HistorialItems()
        hist_items.tipo_modificacion = operacion
        hist_items.usuario = usuario
        hist_items.item = self.id_propiedad_item
        
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
    
    def adjuntar_archivo(self, nombre_archivo, archivo, usuario):
        """
        Adjunta un archivo al item
        
        @param nombre_archivo: nombre del archivo.
        @param archivo: el contenido del archivo.
        @param usuario: el usuario que adjunta el archivo.
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado in [u"Bloqueado", u"Eliminado", u"Revisión-Bloq"]:
            raise AdjuntarArchivoError()
        p_item_mod = PropiedadItem()
        p_item_mod.version = p_item.version + 1
        p_item_mod.estado = u"Desaprobado" #?
        p_item_mod.complejidad = p_item.complejidad
        p_item_mod.prioridad = p_item.prioridad
        p_item_mod.incorporar_relaciones(p_item.relaciones)
        p_item_mod.incorporar_atributos(p_item.atributos)
        p_item_mod.incorporar_archivos(p_item.archivos)
        new_file = ArchivosExternos(nombre_archivo=unicode(nombre_archivo), 
                                    archivo=archivo)
        api = ArchivosPorItem()
        api.archivo = new_file
        p_item_mod.archivos.append(api)
        self.propiedad_item_versiones.append(p_item_mod)
        hist_items = HistorialItems()
        hist_items.tipo_modificacion = u"Adjuntar Archivo"
        hist_items.usuario = usuario
        hist_items.item = p_item
        DBSession.add_all([new_file, hist_items, api, p_item_mod])
        DBSession.flush()
        self.id_propiedad_item = p_item_mod.id_propiedad_item
        
    def eliminar_archivo_adjunto(self, id_archivo, usuario):
        """
        Elimina un el archivo adjunto indicado como parámetro:
        
        @id_archivo: identificador del archivo a eliminar
        @type id_archivo: C{int}
        @usuario: el usuario que realiza la operación.
        @type usuario: L{Usuario}
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado in [u"Bloqueado", u"Eliminado", u"Revisión-Bloq"]:
            raise EliminarArchivoAdjuntoError()
        p_item_mod = PropiedadItem()
        p_item_mod.version = p_item.version + 1
        p_item_mod.estado = u"Desaprobado" #?
        p_item_mod.complejidad = p_item.complejidad
        p_item_mod.prioridad = p_item.prioridad
        p_item_mod.incorporar_relaciones(p_item.relaciones)
        p_item_mod.incorporar_atributos(p_item.atributos)
        p_item_mod.incorporar_archivos(p_item.archivos, id_ignorado=id_archivo)
        self.propiedad_item_versiones.append(p_item_mod)
        hist_items = HistorialItems()
        hist_items.tipo_modificacion = u"Archivo Adjunto Eliminado"
        hist_items.usuario = usuario
        hist_items.item = p_item
        DBSession.add_all([hist_items, p_item_mod])
        DBSession.flush()
        self.id_propiedad_item = p_item_mod.id_propiedad_item
        

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
    
    def modificar_atributo(self, usuario, id_atributo, valor):
        """
        Modifica un atributo de la propiedad del item. Este atributo
        corresponde a uno de los atributos introducidos por el tipo de ítem.
        """
        if self.estado in [u"Bloqueado", u"Eliminado", u"Revisión-Bloq"]:
            raise ModificarItemError()
        p_item_mod = PropiedadItem()
        p_item_mod.version = self.version + 1
        p_item_mod.estado = u"Desaprobado"
        p_item_mod.complejidad = self.complejidad
        p_item_mod.prioridad = self.prioridad
        p_item_mod.incorporar_relaciones(self.relaciones)
        p_item_mod.incorporar_archivos(self.archivos)
        p_item_mod.incorporar_atributos(self.atributos, 
                                        id_ignorado=id_atributo)
        api = AtributosPorItem.por_id(id_atributo)
        attr_de_item = AtributosDeItems()
        attr_de_item.id_atributos_por_tipo_item = api.atributo.id_atributos_por_tipo_item
        attr_de_item.valor = valor
        api_mod = AtributosPorItem()
        api_mod.atributo = attr_de_item
        p_item_mod.atributos.append(api_mod)
        hist_items = HistorialItems()
        hist_items.tipo_modificacion = u"Mod. Atributo Especifico"
        hist_items.usuario = usuario
        hist_items.item = self
        item = Item.por_id(self.id_item_actual)
        item.propiedad_item_versiones.append(p_item_mod)
        DBSession.add_all([p_item_mod, hist_items, attr_de_item, api_mod])
        DBSession.flush()
        item.id_propiedad_item = p_item_mod.id_propiedad_item

    
    def agregar_relaciones(self, ids, tipo):#nahuel
        """
        Relaciona el ítem actual y crea una nueva versión
        @param ids: IDs de ítems con los que se quiere relacionar.
        @param tipo: indica el tipo de relacion(p-h o a-s)
        @raise RelacionError: Si se quiere relacionar con un ítem que no está en una LB
        @return: un string conteniendo los códigos de los ítems con los que no se puedo relacionar
        por formaciones de ciclos, cadena vacía en caso de que todos se relacionen.
        """
        retorno = ""
        
        item = Item.por_id(self.id_item_actual)
        p_item_nuevo = item._crear_propiedad_item()
        
        for i in ids:
            if (i):
                i = int(i)
            else:
                continue
            
            antecesor = Item.por_id(i)
            p_item_ant = PropiedadItem.por_id(antecesor.id_propiedad_item)
            
            if (tipo == 'a-s' and self.estado != u"Bloqueado"):
                raise RelacionError(u"El item con el que se relaciona debe estar en una LB")
            
            relacion = Relacion()
            relacion.id_anterior = antecesor.id_item
            relacion.id_posterior = self.id_item_actual
            
            relacion.tipo = Relacion.tipo_relaciones[tipo]
            relacion.set_codigo()
            rel_por_item = RelacionPorItem()
            #rel_por_item.relaciones.append(relacion)
            rel_por_item.relacion = relacion
            DBSession.add(relacion)
            DBSession.flush()
            
            if (tipo == 'p-h' and \
                not PropiedadItem._detectar_bucle(self)):
                #raise RelacionError(u"Se formó un bucle con la realcion nueva")
                DBSession.delete(relacion)
                DBSession.flush()
                retorno =+ antecesor.codigo + " "
                continue
                      
            p_item_nuevo.relaciones.append(rel_por_item)
            p_item_ant.relaciones.append(rel_por_item)
            DBSession.add(rel_por_item)
            #no hace falta agregar p_item_ant verdad?
        
        return retorno  
    
    @classmethod        
    def _detectar_bucle(cls, item_prop):   
        """ 
        funciona con el método dfs()
         retorna una lista con id_item_actual de los que forman el ciclo
         None si no se encontró ciclo
        """
        inicio = item_prop.id_item_actual
        visitado = {}
        
        return cls._dfs(inicio, item_prop, visitado)
        
    @classmethod
    def _dfs(cls, inicio, nodo, visitado):
        """ realiza la búsqueda en profundidad para encontrar bucles """
        if (nodo.item_actual in visitado):
            if (inicio == nodo.item_actual):
                return [nodo.item_actual]
        
        visitado.setdefault(nodo.item_actual, [True])
        
        for arco in Relacion.relaciones_como_anterior(nodo.id_propiedad_item):
            if (arco.tipo == Relacion.tipo_relaciones['p-h']):
                adyacente = ProiedadItem.por_id(Item.por_id(arco.id_anterior).id_item_actual)
                ciclo = PropiedadItem._dfs(inicio, adyacente, visitado)
                if (ciclo):
                    ciclo.append(adyacente.id_item_actual)
                
        visitado[nodo.item_actual] = [False]
        
        return None

    def eliminar_relaciones(self, ids):#nahuel
        """
        Elimina relaciones en la lista de IDs
        @param ids: IDs de las relaciones que se quieren eliminar.
        """
        
        item = Item.por_id(self.id_item_actual)
        p_item_nuevo = item._crear_propiedad_item()
        
        for i in ids:
            if (i):
                i = int(i)
            else:
                continue
                
            relacion = Relacion.por_id(i)
#            if (relacion.id_anterior == self.id_item_actual):
#                otro = Item.por_id(relacion.id_posterior)
#            else:
#                otro = Item.por_id(relacion.id_anterior)
            otro = relacion.obtener_otro_item()
                
#            p_item_otro = PropiedadItem.por_id(otro.id_propiedad_item)
#            
#            relaciones_otro = p_item_otro.relaciones
#            relaciones_este = self.relaciones
    
            DBSession.query(RelacionPorItem).filter(and_(or_(RelacionPorItem.id_propiedad_item\
                                                        == otro.id_propiedad_item,\
                                                        RelacionPorItem.id_propiedad_item\
                                                        == p_item_nuevo.id_propiedad_item),\
                                                        RelacionPorItem.id_relacion == i)).\
                                                        all().delete()

            
            relacion.tipo = Relacion.tipo_relaciones[tipo]
            relacion.set_codigo()
            rel_por_item = RelacionPorItem()
            #rel_por_item.relaciones.append(relacion)
            rel_por_item.relacion = relacion
            DBSession.add(relacion)
            DBSession.flush()
            
            if (tipo == 'p-h' and \
                not PropiedadItem._detectar_bucle(self)):
                #raise RelacionError(u"Se formó un bucle con la realcion nueva")
                DBSession.delete(relacion)
                DBSession.flush()
                retorno =+ antecesor.codigo + " "
                continue
                
            
            p_item_nuevo.relaciones.append(rel_por_item)
            p_item_ant.relaciones.append(rel_por_item)
            DBSession.add(rel_por_item)
            #no hace falta agregar p_item_ant verdad?
        
        return retorno  

        
    
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

    def incorporar_atributos(self, atributos, id_ignorado=None):
        """
        Agrega los atributos al objecto. Se utiliza cuando se crean
        nuevas versiones, de manera tal que la nueva versión continue
        teniendo los atributos que la vieja versión posee.
        
        @param atributos: lista de objetos L{AtributosPorItem}
        @type atributos: C{list}
        @param id_ignorado: identificador del atributo a ignorar.
        """
        for api in atributos:
            if api.id_atributos_por_item == id_ignorado:
                continue
            attr_nuevo = AtributosPorItem()
            attr_nuevo.atributo = api.atributo
            self.atributos.append(attr_nuevo)
            DBSession.add(attr_nuevo)
        
    def incorporar_archivos(self, archivos, id_ignorado=None):
        """
        Agrega los archivos externos al objecto. Se utiliza cuando 
        se crean nuevas versiones, de manera tal que la nueva versión 
        continue teniendo los archivos externos que la vieja versión 
        posee.
        
        @param archivos: lista de objetos L{ArchivosPorItem}
        @type archivos: C{list}
        @id_ignorado: el identificador del archivo a ignorar
        @type id_ignorado: C{int}
        """
        for api in archivos:
            if api.archivo.id_archivo_externo == id_ignorado:
                continue        
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
    
    # Segun la pagina de SqlAlchemy
    #Many to one places a foreign key in the parent table referencing the 
    #child. The mapping setup is identical to one-to-many, however SQLAlchemy 
    #creates the relationship as a scalar attribute on the parent object 
    #referencing a single instance of the child object.
    
    #relaciones = relation("Relacion")
    relacion = relation("Relacion")
    
    #Métodos de clase
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{PropiedadItem}
        """
        return DBSession.query(cls).filter_by(id_relacion_por_item=id).first()
    
    @classmethod
    def por_id_relacion(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{PropiedadItem}
        """
        return DBSession.query(cls).filter_by(id_relacion=id).first()
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
    tmpl_codigo = u"rel-{id_relacion}-{tipo}-{id_anterior}-{id_posterior}"
    
    #{ Métodos de clase

    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{PropiedadItem}
        """
        return DBSession.query(cls).filter_by(id_relacion=id).first()
    
    @classmethod
    def generar_codigo(cls, rel):
        """
        Genera el código para el elemento pasado como parametro
        """
        if (rel.tipo == tipo_relaciones['a-s']):
            t = "as"
        else:
            t = "ph"
            
        return cls.tmpl_codigo.format(id_relacion=rel.id_relacion,
                                      tipo=t,
                                      id_anterior=rel.id_anterior,
                                      id_posterior=rel.id_posterior)

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
    
    def set_codigo(self):
        """ 
        Establece el código de la relación.
        """
        self.codigo = Relacion.generar_codigo(self)
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
        #Implementacion Parcial
        api = lpm.model.AtributosPorTipoItem.por_id(self.id_atributos_por_tipo_item)
        if api.tipo == u"Numérico":
            return int(self._valor)
        elif api.tipo == u"Fecha":
            return self._valor
        else:
            return self._valor
    
    def _set_valor(self, valor):
        """ dependiendo del tipo del valor, verifica que sea válido,
         si no lanza una excepción (?) """
        #Implementacion parcial
        api = lpm.model.AtributosPorTipoItem.por_id(self.id_atributos_por_tipo_item)
        if api.tipo == u"Numérico":
            try:
                self._valor = int(valor)
            except:
                #excepcion?
                return
        elif api.tipo == u"Fecha":
            self._valor = valor
        else:
            self._valor = valor
    
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
        
    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{AtributosPorItem}
        """
        return DBSession.query(cls).filter_by(id_atributos_por_item=id).one()



class ArchivosExternos(DeclarativeBase):
    """
    Clase que representa un archivo externo que puede ser adjuntado a un
    L{Item}
    """
    __tablename__ = 'tbl_archivos_externos'
    
    #{ Columnas
    id_archivo_externo = Column(Integer, autoincrement=True, primary_key=True)
    archivo = Column(LargeBinary, nullable=False)
    nombre_archivo = Column(Unicode(50), nullable=False)

    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{ArchivosExternos}
        """
        return DBSession.query(cls).filter_by(id_archivo_externo=id).one()
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

    #{ Métodos
    def agregar_archivo(self):
        pass

    @classmethod
    def por_id(cls, id):
        """
        Método de clase que realiza las búsquedas por identificador.
        
        @param id: identificador del elemento a recuperar
        @type id: C{Integer}
        @return: el elemento recuperado
        @rtype: L{ArchivosExternos}
        """
        return DBSession.query(cls).filter_by(id_archivo_externo=id).one()
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
