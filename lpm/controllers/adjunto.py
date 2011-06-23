# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de archivos adjuntos
a un ítem.

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tgext.crud import CrudRestController
from tg.decorators import (paginate, expose, with_trailing_slash,
                           without_trailing_slash)
from tg import redirect, request, validate, flash, response
from tg.controllers import CUSTOM_CONTENT_TYPE

from lpm.model import (DBSession, ArchivosExternos, ArchivosPorItem, 
                      Item, TipoItem, Usuario, PropiedadItem)
from lpm.model.excepciones import *
from lpm.lib.sproxcustom import (CustomTableFiller,
                                 CustomPropertySingleSelectField)
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.lib.util import UrlParser

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller, EditFormFiller
from sprox.fillerbase import EditFormFiller
from sprox.formbase import AddRecordForm, EditableForm

from tw.forms.fields import FileField

from repoze.what.predicates import not_anonymous

import pylons
from pylons import tmpl_context

import transaction


class AdjuntoTable(TableBase):
    __model__ = ArchivosExternos
    __headers__ = {'nombre_archivo': u'Nombre del Archivo'}
    __omit_fields__ = ['id_archivo_externo', 'archivo']
    __default_column_width__ = '35em'
    __column_widths__ = { '__actions__': "50em"}
    
adjunto_table = AdjuntoTable(DBSession)


class AdjuntoTableFiller(CustomTableFiller):
    __model__ = ArchivosExternos
    __omit_fields__ = ['id_archivo_externo', 'archivo']
    
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""

        value = '<div>'
        clase = 'actions_fase'
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)
        p_item = PropiedadItem.por_id(item.id_propiedad_item)
        id = str(obj.id_archivo_externo)
        #if PoseePermiso('modificar item', 
        #                id_fase=item.id_fase).is_met(request.environ):
        if PoseePermiso('modificar item', 
                        id_tipo_item=item.id_tipo_item).is_met(request.environ):
            value += '<div>' + \
                        '<a href="./descargar/' + id + '" ' +  \
                        'class="' + clase + '">Descargar</a>' + \
                     '</div><br />'
            if not UrlParser.parse_nombre(request.url, "versiones") and \
                   p_item.estado not in [u"Eliminado", u"Bloqueado", 
                                       u"Revisión-Bloq"]:
                #No se puede eliminar desde el controlador de versiones.
                value += '<div><form method="POST" action="' + id + '" class="button-to">'+\
                         '<input type="hidden" name="_method" value="DELETE" />' +\
                         '<input onclick="return confirm(\'¿Está seguro?\');" value="Eliminar" type="submit" '+\
                         'style="background-color: transparent; float:left; border:0; color: #286571; display: inline;'+\
                         'margin: 0; padding: 0;' + clase + '"/>'+\
                         '</form></div><br />'

        value += '</div>'
        return value
    
    def _do_get_provider_count_and_objs(self, id_version=None, **kw):
        """
        Recupera los archivos adjuntos de la versión de ítem en cuestión.
        """
        count, lista = super(AdjuntoTableFiller, self).\
                            _do_get_provider_count_and_objs(**kw)
        filtrados = []                    
        if id_version:
            p_item = PropiedadItem.por_id(id_version)
            #p_item.archivos contiene una lista de objetos ArchivosPorItem
            for api in p_item.archivos:
                if api.archivo in lista:
                    filtrados.append(api.archivo)
        return len(filtrados), filtrados


adjunto_table_filler = AdjuntoTableFiller(DBSession)


class AdjuntoAddForm(AddRecordForm):
    __model__ = ArchivosExternos
    __omit_fields__ = ['id_archivo_externo', 'nombre_archivo']
    archivo = FileField("archivo", label_text="Archivo")

adjunto_add_form = AdjuntoAddForm(DBSession)


class AdjuntoController(CrudRestController):
    """Controlador de Adjuntos"""

    #{ Variables
    title = u"Archivos Adjuntos del Ítem"
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{plantillas
    tmp_action = "./"

    #{ Modificadores
    model = ArchivosExternos
    table = adjunto_table
    table_filler = adjunto_table_filler     
    new_form = adjunto_add_form
    
    opciones = dict(nombre_archivo= u'Nombre del Archivo')
    columnas = dict(nombre_archivo='texto')
    
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.adjunto.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        puede_crear = False
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        titulo = self.title
        archivos = {}
        if id_version:
            #desde controller de versiones
            p_item = PropiedadItem.por_id(id_version)
            titulo = u"Archivos Adjuntos de Versión: %d" % p_item.version
            archivos = self.table_filler. \
                        get_value(id_version=p_item.id_propiedad_item, **kw)
        elif id_item:
            #desde controller de items
            item = Item.por_id(id_item)
            #puede_crear = PoseePermiso("crear item", 
            #                    id_fase=item.id_fase).is_met(request.environ)
            puede_crear = PoseePermiso("modificar item", 
                                id_tipo_item=item.id_tipo_item).is_met(request.environ)
            titulo = u"Archivos Adjuntos de Ítem: %s" % item.codigo
            archivos = self.table_filler. \
                        get_value(id_version=item.id_propiedad_item, **kw)
        
        tmpl_context.widget = self.table
        return dict(lista_elementos=archivos, 
                    page=titulo,
                    titulo=titulo, 
                    modelo=self.model.__name__, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.tmp_action,
                    puede_crear=puede_crear,
                    atras="../../"
                    )
    
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.adjunto.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        """
        Controlador que recibe los parámetros de búsqueda para 
        devolver el resultado esperado.
        """
        id_item = UrlParser.parse_id(request.url, "items")
        id_version = UrlParser.parse_id(request.url, "versiones")
        titulo = self.title
        archivos = {}
        puede_crear = False
        buscar_table_filler = AdjuntoTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        if id_version:
            #desde controller de versiones
            p_item = PropiedadItem.por_id(id_version)
            titulo = u"Archivos Adjuntos de Versión: %d" % p_item.version
            archivos = buscar_table_filler. \
                        get_value(id_version=p_item.id_propiedad_item)
        elif id_item:
            #desde controller de items.
            item = Item.por_id(id_item)
            #puede_crear = PoseePermiso("crear item", 
            #                    id_fase=item.id_fase).is_met(request.environ)            
            puede_crear = PoseePermiso("modificar item", 
                                id_tipo_item=item.id_tipo_item).is_met(request.environ)            
            titulo = u"Archivos Adjuntos de Ítem: %s" % item.codigo
            archivos = buscar_table_filler. \
                        get_value(id_version=item.id_propiedad_item)
        
        tmpl_context.widget = self.table
        return dict(lista_elementos=archivos, 
                    page=titulo, 
                    titulo=titulo, 
                    modelo=self.model.__name__,
                    columnas=self.columnas,
                    url_action='../',
                    puede_crear=puede_crear,
                    opciones=self.opciones,
                    atras='../'
                    )
    
    @expose()
    def get_one(self, *args, **kw):
        pass

    @expose()
    def edit(self, *args, **kw):
        pass
        
    @expose()
    def put(self, *args, **kw):
        pass
        
    @without_trailing_slash
    @expose('lpm.templates.adjunto.new')
    def new(self, *args, **kw):
        """Display a page to show a new record."""
        tmpl_context.widget = self.new_form
        return dict(value=kw,
                    page=u"Adjuntar Archivo", 
                    atras='./')
    
    @expose()
    def post_delete(self, id_archivo):
        """Elimina un archivo externo"""
        
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        try:
            item.eliminar_archivo_adjunto(int(id_archivo), user)
        except EliminarArchivoAdjuntoError, err:
            flash(unicode(err), 'warning')
        redirect("./")
        
    @expose()
    def post(self, archivo=None, **kw):
        id_item = UrlParser.parse_id(request.url, "items")
        item = Item.por_id(id_item)
        user = Usuario.by_user_name(request.credentials["repoze.what.userid"])
        contenido = archivo.value #archivo.file.read()
        try:
            item.adjuntar_archivo(archivo.filename, contenido, user)
        except AdjuntarArchivoError, err:
            flash(unicode(err), 'warning')
        redirect("./")

    @expose(content_type=CUSTOM_CONTENT_TYPE)
    def descargar(self, *args, **kw):
        id_archivo = int(args[0])
        ae = ArchivosExternos.por_id(id_archivo)
        response.headers["Content-Type"] = "application/octet-stream"
        disp = 'attachment; filename="' + ae.nombre_archivo + '"'
        response.headers["Content-Disposition"] = disp
        return ae.archivo
    #}
