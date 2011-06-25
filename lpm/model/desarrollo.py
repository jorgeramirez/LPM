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

import thread
import threading

__all__ = ['Item', 'PropiedadItem', 'RelacionPorItem',
           'Relacion', 'AtributosDeItems', 'ArchivosExternos',
            'ArchivosPorItem', 'HistorialItems', 'AtributosPorItem']

class HiloContador(threading.Thread):
    def __init__(self, p_item, lock_v, lock_h, lock_s, v, suma):
        self.p_item = p_item
        self.lock_v = lock_v
        self.lock_s = lock_s
        self.lock_h = lock_h
        self.visitados = v
        self.suma = suma
        self.lh = []
                
        threading.Thread.__init__(self)
        
    def run(self):
        
        for ri in self.p_item.relaciones:
            relacion = Relacion.por_id(ri.id_relacion)
            otro = relacion.obtener_otro_item(self.p_item.id_item_actual)
            p_otro = PropiedadItem.por_id(otro.id_propiedad_item)
            
            self.lock_v.acquire()
            if (not self.visitados.has_key(p_otro.id_item_actual)):
                self.visitados.setdefault(p_otro.id_item_actual, [])
                self.lock_v.release()
                
                self.lock_s.acquire()
                self.suma[0] += p_otro.complejidad
                #print 'suma: ', self.suma
                self.lock_s.release()
                
                fase = lpm.model.Fase.por_id(otro.id_fase)                
                identacion = " " * fase.posicion
                fila = identacion + otro.codigo + " " + str(p_otro.complejidad)
                self.lock_v.acquire()
                self.visitados[p_otro.id_item_actual].append(fila)
                #self.visitados[p_otro.id_item_actual].setdefault('codigo', otro.codigo)
                #self.visitados[p_otro.id_item_actual].setdefault('compl', p_otro.complejidad)
                #self.visitados[p_otro.id_item_actual].setdefault('papa', p_item.id_item_actual)
                self.lock_v.release()
                
                hilo = HiloContador(p_otro, self.lock_v, self.lock_h, self.lock_s, self.visitados, self.suma)
                #self.lock_h.acquire()
                self.lh.append(hilo)
                hilo.start()
                #self.lock_h.release()

            else:
                self.lock_v.release()
        
        for h in self.lh:
            h.join()
                          
                            
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
    
    def aprobar(self, usuario): #jorge (falta probar)
        """
        Aprueba un ítem.
        
        Las transiciones de estado pueden ser:
            - Revisión-Desbloq al de Aprobado
            - Desaprobado al de Aprobado
        
        @param usuario: el usuario que realiza la operación
        @type usuario: L{Usuario}
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
        op = u"Aprobación"
        HistorialItems.registrar(usuario, p_item, op)
        DBSession.add(p_item)

    def desaprobar(self, usuario): #carlos
        """
        Desaprueba un ítem, implica que cambia su estado de "Aprobado", 
            o de "Revisión-Desbloq” al de “Desaprobado".
        
        @param usuario: el usuario que realiza la operación
        @type usuario: L{Usuario}        
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
        op = u"Desaprobación"
        HistorialItems.registrar(usuario, p_item, op)
        DBSession.add(p_item)
    
    def bloquear(self, usuario): #jorge
        """
        Bloquea un ítem, lo que implica que el mismo no puede
        ser modificado.
        
        @param usuario: el usuario que realiza la operación
        @type usuario: L{Usuario}
        @raises BloquearItemError: el estado del L{Item} es distinto al 
            de aprobado
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado != u"Aprobado":
            raise BloquearItemError()
        p_item.estado = u"Bloqueado"
        op = u"Bloqueo"
        HistorialItems.registrar(usuario, p_item, op)
        DBSession.add(p_item)
            
    def desbloquear(self, usuario): #carlos
        """
        Desbloquea un ítem, implica que el mismo puede ser
        modificado.
        
        @param usuario: el usuario que realiza la operación
        @type usuario: L{Usuario}
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
        op = u"Desbloqueo"
        HistorialItems.registrar(usuario, p_item, op)        
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
            

    def eliminar(self, usuario): #jorge

        """
        Elimina un ítem
        
        @param usuario: el usuario que registra la operacion.
        @type usuario: L{Usuario}
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        if p_item.estado in [u"Bloqueado", u"Eliminado", u"Revisión-Bloq"]:
            raise EliminarItemError()
        p_item.estado = u"Eliminado"
        op = u"Eliminación"
        proy = DBSession.query(lpm.model.Proyecto) \
                        .join(lpm.model.Fase) \
                        .filter(lpm.model.Fase.id_fase == self.id_fase).one()
        proy.complejidad_total -= p_item.complejidad
        HistorialItems.registrar(usuario, p_item, op)
    
    def esta_relacionado(self, id_item):
        """ 
        Verifica si este ítem está relacionado con el item de id_item
        
        @param id_item: id del item con el que se quiere comprobar la relación
        @param tipo: tipo de relacion que se quiere comprobar
        @return: True si está relacionado con id_item
        """
              
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        
        for r in p_item.relaciones:
            relacion = Relacion.por_id(r.id_relacion)
            if (relacion.id_anterior == id_item or\
                relacion.id_posterior == id_item ):
                return True
            
        return False

            
        
    def revivir(self, usuario):
        """
        Revive un ítem, implica que el mismo reviva con el estado desbloqueado.
        
        @param usuario: el usuario que realiza la operación
        @type usuario: L{Usuario}
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
        p_item_revivido.observaciones = p_item.observaciones
        p_item_revivido.descripcion = p_item.descripcion
        p_item_revivido.incorporar_atributos(p_item.atributos)
        p_item_revivido.incorporar_archivos(p_item.archivos)
        p_item_revivido.estado = u"Desaprobado"
        self.propiedad_item_versiones.append(p_item_revivido)
        DBSession.add(p_item_revivido)
        op = u"Revivir"
        HistorialItems.registrar(usuario, p_item_revivido, op)
        DBSession.flush()
        self.id_propiedad_item = p_item_revivido.id_propiedad_item
        proy = DBSession.query(lpm.model.Proyecto) \
                        .join(lpm.model.Fase) \
                        .filter(lpm.model.Fase.id_fase == self.id_fase).one()
        proy.complejidad_total += p_item.complejidad
    
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

        ch = False   #verifica si cambio algo.
        for k in ["complejidad", "prioridad", "descripcion", "observaciones"]:
            val = getattr(p_item, k)
            if val and kw[k] != val:
                ch = True
                break
        if not ch:
            raise ModificarItemError(u"No se realizaron cambios")

        p_item_mod = PropiedadItem()
        p_item_mod.version = p_item.version + 1
        p_item_mod.estado = u"Desaprobado"
        for attr in ["prioridad", "complejidad", "descripcion", "observaciones"]:
            valor = getattr(p_item, attr)
            setattr(p_item_mod, attr, kw[attr])
            if valor != kw[attr]:
                op = u"Modificación Atributo General"
                HistorialItems.registrar(usuario, p_item_mod, op)
        p_item_mod.incorporar_relaciones(p_item.relaciones)
        p_item_mod.incorporar_atributos(p_item.atributos)
        p_item_mod.incorporar_archivos(p_item.archivos)
        self.propiedad_item_versiones.append(p_item_mod)
        DBSession.add(p_item_mod)
        DBSession.flush()
        self.id_propiedad_item = p_item_mod.id_propiedad_item
        
        if p_item.complejidad != p_item_mod.complejidad:
            proy = DBSession.query(lpm.model.Proyecto) \
                        .join(lpm.model.Fase) \
                        .filter(lpm.model.Fase.id_fase == self.id_fase).one()
            c1 = p_item.complejidad
            c2 = p_item_mod.complejidad
            diff  = abs(c1 - c2)
            if c1 > c2:
                proy.complejidad_total -= diff
            else:
                proy.complejidad_total += diff

        
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
        @param usuario: el usuario que realiza la operación
        @type usuario: L{Usuario}
        """
        p_item_actual = PropiedadItem.por_id(self.id_propiedad_item)
        p_item_version = PropiedadItem.por_id(id_version)
        p_item_nuevo = PropiedadItem()
        p_item_nuevo.version = p_item_actual.version + 1
        p_item_nuevo.estado = u"Desaprobado"
        p_item_nuevo.prioridad = p_item_version.prioridad
        p_item_nuevo.complejidad = p_item_version.complejidad
        p_item_nuevo.observaciones = p_item_version.observaciones
        p_item_nuevo.descripcion = p_item_version.descripcion
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

        op = u"Reversión De: %d A: %d" % (p_item_actual.version, 
                                          p_item_version.version)
        HistorialItems.registrar(usuario, p_item_nuevo, op)
        self.propiedad_item_versiones.append(p_item_nuevo)
        DBSession.add(p_item_nuevo)
        DBSession.flush()
        self.id_propiedad_item = p_item_nuevo.id_propiedad_item
        
        if p_item_actual.complejidad != p_item_version.complejidad:
            proy = DBSession.query(lpm.model.Proyecto) \
                        .join(lpm.model.Fase) \
                        .filter(lpm.model.Fase.id_fase == self.id_fase).one()
            c1 = p_item_actual.complejidad
            c2 = p_item_version.complejidad
            diff  = abs(c1 - c2)
            if c1 > c2:
                proy.complejidad_total -= diff
            else:
                proy.complejidad_total += diff

    def calcular_impacto(self):
        """ Calcula el impacto de cambiar un item
        @return: lista de strings con las lineas representando un grafo
        """
        p_item = PropiedadItem.por_id(self.id_propiedad_item)
        lock_visitados = threading.Lock()
        lock_sumatoria = threading.Lock()
        lock_hilos = threading.Lock()
        visitados = {}
        lista_hilos = []
        sumatoria = [0]
        
        hilo = HiloContador(p_item, lock_visitados, lock_hilos, lock_sumatoria, visitados, sumatoria)
        
        hilo.start()
        hilo.join()
        
        """
        i = 0
        while (True):
            lock_hilos.acquire()
            if (len(lista_hilos) > i):
                
                if (not lista_hilos[i].is_alive()):
                    lista_hilos.pop(i)
                    lock_hilos.release()
                else:   
                    lock_hilos.release()
                    lista_hilos[i].join()
            else:
                lock_hilos.release()
            
            i += 1
            lock_hilos.acquire()
            if (len(lista_hilos) < i):
                lock_hilos.release()
                i = 0
            elif (len(lista_hilos) == 0):
                lock_hilos.release()
                break  
        """
        return sumatoria, visitados


        
#    def _sumar(self, v, sum, lh):
#        
#        for ri in self.p_item.relaciones:
#            relacion = Relacion.por_id(ri.id_relacion)
#            otro = relacion.obtener_otro_item(self.p_item.id_item_actual)
#            p_otro = PropiedadItem.por_id(otro.id_propiedad_item)
#            
#            self.lock_v.acquire()
#            if (not self.visitados.has_key(p_otro.id_item_actual)):
#                self.visitados.setdefault(p_otro.id_item_actual, True)
#                self.lock_v.release()
#                
#                self.lock_s.acquire()
#                self.sum += p_otro.complejidad
#                self.lock_s.release()
#                
#                hilo = HilosContador(self.p_otro, self.lock_v, self.lock_h, self.lock_s, self.visitados, self.sum, self.lh)
#                self.lock_hilos.adquire()
#                self.li.append(hilo)
#                self.lock_hilos.release()
#                hilo.star()
#                
#            else:
#                self.lock_v.release()            
            
    def crear_siguiente_propiedad_item(self):
        """Crea y asigna al item una nueva propiedad en la que se deben realizar
        las modificaciones antes de guardar en el historial
        @return: la nueva propiedad item creada """
        
        p_item_viejo = PropiedadItem.por_id(self.id_propiedad_item)
        p_item_nuevo = PropiedadItem()
        p_item_nuevo.version = p_item_viejo.version + 1
        p_item_nuevo.estado = p_item_viejo.estado
        p_item_nuevo.complejidad = p_item_viejo.complejidad
        p_item_nuevo.prioridad = p_item_viejo.prioridad
        p_item_nuevo.descripcion = p_item_viejo.descripcion
        p_item_nuevo.observaciones = p_item_viejo.observaciones
        p_item_nuevo.id_item_actual = self.id_item
        p_item_nuevo.incorporar_archivos(p_item_viejo.archivos)
        p_item_nuevo.incorporar_atributos(p_item_viejo.atributos)
        p_item_nuevo.incorporar_relaciones(p_item_viejo.relaciones)
        DBSession.add(p_item_nuevo)
        DBSession.flush()
        self.id_propiedad_item = p_item_nuevo.id_propiedad_item
        DBSession.flush()
        
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
        hist_items.id_item = self.id_propiedad_item
        DBSession.add(hist_items)
        
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
        p_item_mod.observaciones = p_item.observaciones
        p_item_mod.descripcion = p_item.descripcion
        p_item_mod.incorporar_relaciones(p_item.relaciones)
        p_item_mod.incorporar_atributos(p_item.atributos)
        p_item_mod.incorporar_archivos(p_item.archivos)
        new_file = ArchivosExternos(nombre_archivo=unicode(nombre_archivo), 
                                    archivo=archivo)
        api = ArchivosPorItem()
        api.archivo = new_file
        p_item_mod.archivos.append(api)
        self.propiedad_item_versiones.append(p_item_mod)
        op = u"Nuevo Adjunto"
        HistorialItems.registrar(usuario, p_item_mod, op)
        DBSession.add_all([new_file, api, p_item_mod])
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
        p_item_mod.observaciones = p_item.observaciones
        p_item_mod.descripcion = p_item.descripcion
        p_item_mod.incorporar_relaciones(p_item.relaciones)
        p_item_mod.incorporar_atributos(p_item.atributos)
        p_item_mod.incorporar_archivos(p_item.archivos, id_ignorado=id_archivo)
        self.propiedad_item_versiones.append(p_item_mod)
        op = u"Eliminación de Archivo Adjunto"
        HistorialItems.registrar(usuario, p_item_mod, op)        
        DBSession.add(p_item_mod)
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
    descripcion = Column(Unicode(200), nullable=True, default=u"DESC")
    observaciones = Column(Unicode(200), nullable=True, default=u"OBS")
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

        api = AtributosPorItem.por_id(id_atributo)

        if api.atributo.valor == valor:
            raise ModificarItemError(u"No se realizaron cambios")

        p_item_mod = PropiedadItem()
        p_item_mod.version = self.version + 1
        p_item_mod.estado = u"Desaprobado"
        p_item_mod.complejidad = self.complejidad
        p_item_mod.prioridad = self.prioridad
        p_item_mod.observaciones = self.observaciones
        p_item_mod.descripcion = self.descripcion
        p_item_mod.incorporar_relaciones(self.relaciones)
        p_item_mod.incorporar_archivos(self.archivos)
        p_item_mod.incorporar_atributos(self.atributos, 
                                        id_ignorado=id_atributo)
        attr_de_item = AtributosDeItems()
        attr_de_item.id_atributos_por_tipo_item = api.atributo.id_atributos_por_tipo_item
        attr_de_item.valor = valor
        api_mod = AtributosPorItem()
        api_mod.atributo = attr_de_item
        p_item_mod.atributos.append(api_mod)
        attr_por_ti = lpm.model.AtributosPorTipoItem. \
                        por_id(api.atributo.id_atributos_por_tipo_item)
        op = u"Mod. Atributo Específico: %s" % attr_por_ti.nombre
        HistorialItems.registrar(usuario, p_item_mod, op)
        item = Item.por_id(self.id_item_actual)
        item.propiedad_item_versiones.append(p_item_mod)
        DBSession.add_all([p_item_mod, attr_de_item, api_mod])
        DBSession.flush()
        item.id_propiedad_item = p_item_mod.id_propiedad_item
    
    def tiene_relacion(self, relacion):
        """Verifica si este propiedad item itene la relacion
        @param relacion: relacion a verificar
        @return: True si tiene esa relacion
        """
        for r in self.relaciones:
            if (r.relacion.id_anterior == relacion.id_anterior and\
                r.relacion.id_posterior == relacion.id_posterior):
                return True
            
        return False
    
    def agregar_relaciones(self, ids, tipo):#nahuel
        """
        Relaciona el ítem actual y crea una nueva versión
        @param ids: IDs de ítems con los que se quiere relacionar.
        @param tipo: indica el tipo de relacion(p-h o a-s)
        @raise RelacionError: Si se quiere relacionar con un ítem que no está en una LB
        @return: un string conteniendo los códigos de los ítems con los que no se puedo relacionar
        por formaciones de ciclos, cadena vacía en caso de que todos se relacionen.
        """
        retorno = u""
        creado = False
        
        item = Item.por_id(self.id_item_actual)
        p_item_nuevo = item.crear_siguiente_propiedad_item()
        
        for i in ids:
            if (i):
                i = int(i)
            else:
                continue
            print "i:", i
            
            antecesor = Item.por_id(i)
            p_item_ant = PropiedadItem.por_id(antecesor.id_propiedad_item)
            
            if (tipo == 'a-s' and p_item_ant.estado != u"Bloqueado"):
                raise RelacionError(u"El item con el que se relaciona debe estar en una LB")
            
            relacion = Relacion()
            relacion.id_anterior = antecesor.id_item
            relacion.id_posterior = item.id_item
            
            relacion.tipo = Relacion.tipo_relaciones[tipo]
            
            if (p_item_nuevo.tiene_relacion(relacion)):#repetido
                continue
            
            rel_por_item1 = RelacionPorItem()
            rel_por_item2 = RelacionPorItem()
            #rel_por_item.relaciones.append(relacion)
            rel_por_item1.relacion = relacion
            rel_por_item2.relacion = relacion
            DBSession.add(relacion)
            DBSession.flush()
            relacion.set_codigo()
            
            if (tipo == 'p-h' and \
                PropiedadItem._detectar_bucle(p_item_nuevo)):
                #raise RelacionError(u"Se formó un bucle con la realcion nueva")
                DBSession.delete(relacion)
                DBSession.flush()
                retorno += (u"  :  " + antecesor.codigo)
                continue
            elif (not creado):
                creado = True
                          
            p_item_nuevo.relaciones.append(rel_por_item1)
            p_item_ant.relaciones.append(rel_por_item2)
            DBSession.add_all([rel_por_item1, rel_por_item2])
            #no hace falta agregar p_item_ant verdad?
        
        if (not creado):
            item.id_propiedad_item = self.id_propiedad_item
            DBSession.delete(p_item_nuevo)
            
        return retorno, creado  
    
    @classmethod        
    def _detectar_bucle(cls, item_prop):   
        """ 
        Funciona con el método dfs()
        @param item_prop: propiedad de item en al cual se quiere buscar un ciclo
        @return: retorna una lista con id_item_actual de los que forman el ciclo
                 None si no se encontró ciclo
        """
        inicio = item_prop.id_item_actual
        visitado = {}
        
        return cls._dfs(inicio, item_prop, visitado)
        
    @classmethod
    def _dfs(cls, inicio, nodo, visitado):
        """ Realiza la búsqueda en profundidad para encontrar bucles """
        if (visitado.has_key(nodo.id_item_actual) and visitado[nodo.id_item_actual]):
            if (inicio == nodo.id_item_actual):
                return nodo.id_item_actual
        
        visitado.setdefault(nodo.id_item_actual, True)
        
        #TODO mejorar el query de la función relaciones_como_anterior
        r_anterior = Relacion.relaciones_como_anterior(nodo.id_item_actual)
        print r_anterior
        if (r_anterior):
            
            for arco in r_anterior:
                if (arco.tipo == Relacion.tipo_relaciones['p-h']):
                    adyacente = PropiedadItem.por_id(Item.por_id(arco.id_anterior).id_propiedad_item)
                    ciclo = PropiedadItem._dfs(inicio, adyacente, visitado)
                    if (ciclo):
                        ciclo.append(adyacente.id_item_actual)
                
        visitado[nodo.id_item_actual] = False
        
        return None

    def eliminar_relaciones(self, ids):#nahuel
        """
        Elimina relaciones en la lista de IDs
        @param ids: IDs de las relaciones que se quieren eliminar.
        """
        
        item = Item.por_id(self.id_item_actual)
        p_item_nuevo = item.crear_siguiente_propiedad_item()
        
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
            otro = relacion.obtener_otro_item(item.id_item)
                
#            p_item_otro = PropiedadItem.por_id(otro.id_propiedad_item)
#            
#            relaciones_otro = p_item_otro.relaciones
#            relaciones_este = self.relaciones
    
            DBSession.query(RelacionPorItem).filter(and_(or_(RelacionPorItem.id_propiedad_item\
                                                        == otro.id_propiedad_item,\
                                                        RelacionPorItem.id_propiedad_item\
                                                        == p_item_nuevo.id_propiedad_item),\
                                                        RelacionPorItem.id_relacion == i))\
                                                        .delete()


        
    
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
        if (rel.tipo == cls.tipo_relaciones['a-s']):
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
        item = Item.por_id(id_item)
        
        return DBSession.query(cls).filter(cls.id_posterior == id_item)\
                                           .filter(item.id_propiedad_item == RelacionPorItem.id_propiedad_item)\
                                           .filter(cls.id_relacion == RelacionPorItem.id_relacion).all()

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
        item = Item.por_id(id_item)
        
        return DBSession.query(cls).filter(cls.id_anterior == id_item)\
                                           .filter(item.id_propiedad_item == RelacionPorItem.id_propiedad_item)\
                                           .filter(cls.id_relacion == RelacionPorItem.id_relacion).all()
    
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
    tipo_modificacion = Column(Unicode(100), nullable=False)
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

    #{ Métodos
    @classmethod
    def registrar(cls, usuario=None, p_item_mod=None, op=None):
        """
        Registra una nueva entrada en el historial de items.
        
        @param usuario: el usuario que realiza los cambios.
        @type usuario: L{Usuario}
        @param p_item_mod: el ítem con los cambios.
        @type p_item_mod: L{PropiedadItem}
        """
        hist_items = HistorialItems()
        hist_items.tipo_modificacion = unicode(op)
        hist_items.usuario = usuario
        hist_items.item = p_item_mod
        DBSession.add(hist_items)
    #}  
