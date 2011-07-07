# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de usuarios miembros
y no miembros de un tipo de ítem.

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tg.controllers import RestController
from tg.decorators import (paginate, expose, with_trailing_slash, 
                           without_trailing_slash)
from tg import redirect, request, require, flash, url, validate 

from lpm.model import DBSession, Usuario, Proyecto, Rol, Fase, TipoItem
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.authorization import PoseePermiso, AlgunPermiso, Miembro
from lpm.lib.util import UrlParser
from lpm.controllers.usuario import UsuarioEditForm, UsuarioEditFiller
from lpm.controllers.miembros_tipo_item import (miembros_tipo_table)

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
from sprox.fillerbase import EditFormFiller
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from repoze.what.predicates import not_anonymous

from sqlalchemy import and_

import transaction

from tg import tmpl_context, request



class NoMiembrosTipoTableFiller(CustomTableFiller):
    __model__ = Usuario
    __omit_fields__ = ['password', 'telefono', 'nro_documento', 
                       '_password', 'historial_lb', 'roles',
                       'historial_item', 'creado']
    __add_fields__ = {'check' : None}

    def check(self, obj, **kw):
        #id
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_usuario) + '"/>'
        return checkbox

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        clase = 'actions'
        value = "<div>"
        value += '<div>' + \
                    '<a href="./'  + str(obj.id_usuario) + '/" ' + \
                    'class="' + clase + '">Ver</a>' + \
                 '</div><br />'
                 
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        if PoseePermiso("asignar-desasignar rol", 
                        id_tipo_item=id_tipo_item).is_met(request.environ):
            value += '<div>' + \
                        '<a href="./incorporar/' + \
                        str(obj.id_usuario) + '" ' + \
                        'class="' + clase + '">Incorporar</a>' + \
                     '</div><br />'

        value += '</div>'
        
        return value
        
    def _do_get_provider_count_and_objs(self, id_tipo_item=None, **kw):
        """
        Se muestra la lista de usuario si se tiene un permiso 
        necesario. Caso contrario se muestra solo su usuario
        """
        count, lista = super(NoMiembrosTipoTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        
        filtrados = []
        tipo = TipoItem.por_id(id_tipo_item)
        for u in lista:
            if Miembro(id_proyecto=tipo.id_proyecto,
                       id_usuario=u.id_usuario).is_met(request.environ) and \
                       not Miembro(id_tipo_item=id_tipo_item,
                                   id_usuario=u.id_usuario).is_met(request.environ):
                filtrados.append(u)
        return len(filtrados), filtrados

no_miembros_tipo_table_filler = NoMiembrosTipoTableFiller(DBSession)


class NoMiembrosTipoController(RestController):
    table = miembros_tipo_table
    table_filler = no_miembros_tipo_table_filler
    action = "./"
    
    #para el form de busqueda
    opciones = dict(nombre_usuario="Nombre de Usuario", 
                    nombre="Nombre", 
                    apellido="Apellido",
                    email="Email")
                    
    columnas = dict(nombre_usuario="texto", 
                    nombre="texto", 
                    apellido="texto",
                    email="texto")


    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.no_miembros_get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """

        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        tipo = TipoItem.por_id(id_tipo_item)
        titulo = "Lista de Usuarios"

        puede_incorporar = PoseePermiso("asignar-desasignar rol", 
                                        id_tipo_item=id_tipo_item).is_met(request.environ)

        if request.response_type == 'application/json':
            return self.table_filler.get_value(id_tipo_item=id_tipo_item,**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            nomiembros = self.table_filler.get_value(id_tipo_item=id_tipo_item,**kw)
        else:
            nomiembros = []
            
        tmpl_context.widget = self.table
        atras = "../"
        return dict(lista_elementos=nomiembros, 
                    page=titulo, 
                    titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action=self.action, 
                    atras=atras,
                    puede_incorporar=puede_incorporar)

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.miembros.no_miembros_get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        tipo = TipoItem.por_id(id_tipo_item)
        titulo = "Lista de Usuarios"

        puede_incorporar = PoseePermiso("asignar-desasignar rol", 
                                        id_tipo_item=id_tipo_item).is_met(request.environ)
        tmpl_context.widget = miembros_tipo_table
        buscar_table_filler = NoMiembrosTipoTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value(id_tipo_item=id_tipo_item,**kw)
        atras = "../"
        return dict(lista_elementos=usuarios, 
                    page=titulo, titulo=titulo, 
                    columnas=self.columnas,
                    opciones=self.opciones,
                    url_action="../", 
                    atras=atras,
                    puede_incorporar=puede_incorporar)
    
    @expose("lpm.templates.miembros.get_one")
    def get_one(self, *args, **kw):
        """
        Muestras los datos de un usuario miembro de la fase.
        """
        tmpl_context.widget = UsuarioEditForm(DBSession)
        filler = UsuarioEditFiller(DBSession)
        value = filler.get_value(values={'id_usuario': int(args[0])})
        page = u"Usuario %s" % value["nombre_usuario"]
        atras = "../"
        return dict(value=value, page=page, atras=atras)
        
    @expose()
    def incorporar_seleccionados(self, *args, **kw):
        """ 
        Incorporar al proyecto a los usuarios que fueron seleccionados.
        """
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        
        #recuperamos el rol miembro de tipo de item
        rol = DBSession.query(Rol) \
                       .filter(and_(Rol.id_tipo_item == id_tipo_item,
                               Rol.nombre_rol == u"Miembro de Tipo Item")).first()
        if kw:
            pks = []
            for k, pk in kw.items():
                if not k.isalnum():
                    continue
                pks.append(int(pk))

            transaction.begin()
            usuarios = DBSession.query(Usuario) \
                                .filter(Usuario.id_usuario.in_(pks)).all()
            for u in usuarios:
                u.roles.append(rol)

            transaction.commit()

        flash("Usuarios incorporados correctamente")
        return "../"
    
    
    @expose()
    def incorporar(self, *args, **kw):
        id_tipo_item = UrlParser.parse_id(request.url, "tipositems")
        id_usuario = int(args[0])

        #recuperamos el rol miembro de tipo de item
        rol = DBSession.query(Rol) \
                       .filter(and_(Rol.id_tipo_item == id_tipo_item,
                               Rol.nombre_rol == u"Miembro de Tipo Item")).first()
        transaction.begin()
        usuario = Usuario.por_id(id_usuario)
        usuario.roles.append(rol)

        transaction.commit()

        flash("Usuario incorporado correctamente")
        redirect("../")
