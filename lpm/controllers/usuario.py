# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de usuarios.

@authors:
    - U{Carlos Bellino<mailto:carlosbellino@gmail.com>}
    - U{Nahuel Hernández<mailto:nahuel.11990@gmail.com>}
    - U{Jorge Ramírez<mailto:jorgeramirez1990@gmail.com>}

@since: 1.0
"""
from tgext.crud import CrudRestController
from tg.controllers import RestController
from tg.decorators import (paginate, expose, with_trailing_slash, 
                           without_trailing_slash)
from tg import redirect, request, require, flash, url, validate 

from lpm.model import DBSession, Usuario, Rol
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.authorization import PoseePermiso

from sprox.tablebase import TableBase
from sprox.fillerbase import TableFiller
#from sprox.dojo.tablebase import DojoTableBase as TableBase
#from sprox.dojo.fillerbase import DojoTableFiller as TableFiller
from sprox.fillerbase import EditFormFiller
#from sprox.formbase import AddRecordForm, EditableForm
from sprox.dojo.formbase import DojoAddRecordForm as AddRecordForm
from sprox.dojo.formbase import DojoEditableForm as EditableForm
from sprox.widgets import PropertySingleSelectField

from tw.forms.fields import PasswordField, TextField, InputField, SubmitButton

from repoze.what.predicates import not_anonymous

from formencode.validators import String, Email, NotEmpty

import transaction

from tg import tmpl_context, request

class UsuarioTable(TableBase):
    __model__ = Usuario
    __headers__ = {'nombre_usuario' : u'Nombre de Usuario', 'email' : u"E-mail",
                   'nombre' : u"Nombre", 'apellido' : u"Apellido", 'creado': u"Fecha Creación"
                  }
    __omit_fields__ = ['id_usuario', 'password', 'telefono', 'nro_documento', 
                       '_password', 'historial_lb', 'roles',
                       'historial_item']
    __default_column_width__ = '15em'
    __column_widths__ = {'email': "35em",
                         'creado': "35em",
                         '__actions__' : "50em"
                        }
#    __url__ = '/usuarios.json'
    
usuario_table = UsuarioTable(DBSession)


class UsuarioTableFiller(CustomTableFiller):
    __model__ = Usuario
    __omit_fields__ = ['password', 'telefono', 'nro_documento', 
                       '_password', 'historial_lb', 'roles',
                       'historial_item']

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'   
        if PoseePermiso('modificar usuario', 
                        id_usuario=obj.id_usuario).is_met(request.environ):
            value += '<div>' + \
                        '<a href="/usuarios/'+ str(obj.id_usuario) +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        if PoseePermiso('eliminar usuario',
                        id_usuario=obj.id_usuario).is_met(request.environ):
            value += '<div><form method="POST" action="' + str(obj.id_usuario) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                     '</form></div><br />'
#-------------------------------------------------------------- arreglar!
        if PoseePermiso('asignar rol',
                        id_usuario=obj.id_usuario).is_met(request.environ):
            value += '<div>' + \
                        '<a href="/usuarios/roles/' + str(obj.id_usuario) + '" ' +\
                        'class="' + clase + '">Roles</a>' + \
                     '</div><br />'
        value += '</div>'
        return value

    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de usuario si se tiene un permiso 
        necesario
        """
        count, filtrados = super(UsuarioTableFiller, self). \
                                 _do_get_provider_count_and_objs(**kw)
        if count == 0:
            return count, filtrados
        nombre_usuario = request.credentials['repoze.what.userid']
        usuario = Usuario.by_user_name(nombre_usuario)
        for r in usuario.roles:
            for p in r.permisos:
                if p.nombre_permiso.find("usuario") > 0:
                    return count, filtrados

        #si no tiene permisos necesarios lo unico que puede ver es su usuario
        return 1, [usuario]

    
usuario_table_filler = UsuarioTableFiller(DBSession)


class UsuarioAddForm(AddRecordForm):
    __model__ = Usuario
    __omit_fields__ = ['id_usuario', 'creado', '_password', 'historial_lb', 'roles',
                       'historial_item']
    __require_fields__ = ['nombre_usuario', 'nombre', 'apellido', 'password',
                          'repita_password', 'email']
    __check_if_unique__ = True
    __field_order__ = ['nombre_usuario', 'nombre', 'apellido', 'password',
                       'password2', 'email', 'nro_documento', 'telefono']
    __field_attrs__ = {
                       'nombre_usuario': { 'maxlength' : '32'},
#                       'roles' : {'label_text':'Roles',
#                                  'named_button' : True,
#                                  'attrs' : {'value' : 'Roles'}
#                                  }
                       }
    __add_fields__ = {'password2' : PasswordField('repita_password')}
    
    nombre_usuario = String(min=4)
    password = String(min=6, max=80)
    email = Email()

#    from sprox.formbase import Field
#    roles_boton = Field(SubmitButton('roles'))
                             

usuario_add_form = UsuarioAddForm(DBSession)


class UsuarioEditForm(EditableForm):
    __model__ = Usuario
    __hide_fields__ = ['id_usuario']
    __omit_fields__ = ['nombre_usuario', 'creado', '_password', 'password',
                        'historial_lb', 'roles', 'historial_item']
    __require_fields__ = ['nombre', 'apellido', 'password',
                          'repita_password', 'email']
    __check_if_unique__ = True
    __field_order__ = ['nombre_usuario', 'nombre', 'apellido', 'password1',
                       'password2', 'email', 'nro_documento', 'telefono']
    __field_attrs__ = {
                       'nombre_usuario': { 'maxlength' : '32'},
                       'roles' : {'label_text' :'Roles'}
                       }
    __add_fields__ = {'password1' : PasswordField('nuevo_password'),
                      'password2' : PasswordField('repita_nuevo_password'),
                      }

usuario_edit_form = UsuarioEditForm(DBSession)        


class UsuarioEditFiller(EditFormFiller):
    __model__ = Usuario

usuario_edit_filler = UsuarioEditFiller(DBSession)


#tablas para la asignación/desasignación de roles
class RolTable(TableBase):
    __model__ = Rol
    __headers__ = {'nombre_rol' : u'Nombre de Rol',
                   'codigo' : u"Código", 'tipo' : u'Tipo',
                   'check' : u'Check'
                  }
    __omit_fields__ = ['id_rol', 'permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion']
    __default_column_width__ = '15em'
    
    __add_fields__ = {'check' : None}
    __xml_fields__ = ['Check']
    __column_widths__ = {'nombre_rol': "35em",
                         'codigo': "35em",
                         '__actions__' : "50em"
                        }

    
rol_user_table = RolTable(DBSession)

class RolTableFiller(TableFiller):
    __model__ = Rol
    __add_fields__ = {'check' : None}

    def check(self, obj, **kw):
        #id o name???
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_rol) + '"/>'
        return checkbox
    
    def _do_get_provider_count_and_objs(self,
                                         usuario=None, asignados=True, **kw):
        if (not asignados):
            roles = Rol.roles_desasignados(usuario.id_usuario)
        elif (asignados):
            roles = usuario.roles
            
        return len(roles), roles

roles_usuario_filler = RolTableFiller(DBSession)


class UsuarioController(CrudRestController):
    """Controlador de usuarios"""
    #{ Variables
    title = u"Administrar usuarios"
    #{ Plantillas

    # No permitir usuarios anonimos (?)
    allow_only = not_anonymous(u"El usuario debe haber iniciado sesión")
    
    #{ Modificadores
    model = Usuario
    table = usuario_table
    table_filler = usuario_table_filler
    new_form = usuario_add_form
    edit_form = usuario_edit_form
    edit_filler = usuario_edit_filler

 
    #{ Métodos
    #@with_trailing_slash
    @paginate('lista_elementos', items_per_page=7)
    @expose('lpm.templates.usuario.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        if request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            usuarios = self.table_filler.get_value(**kw)
        else:
            usuarios = []
            
        tmpl_context.widget = usuario_table
        return dict(lista_elementos=usuarios, page=self.title, titulo=self.title, 
                    modelo=self.model.__name__)

    '''            
    @without_trailing_slash
    @paginate('lista_elementos', items_per_page=7)
    @expose('lpm.templates.get_all')
    @expose('json')
    def buscar(self, *args, **kw):
        pp = PoseePermiso('consultar usuario')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/usuarios")
        buscar_table_filler = UsuarioTableFiller(DBSession)
        if kw.has_key('filtro'):
            buscar_table_filler.filtro = kw['filtro']
        usuarios = buscar_table_filler.get_value()
        tmpl_context.widget = self.table
        retorno = self.retorno_base()
        retorno["lista_elementos"] = usuarios
        return retorno
''' 
    @expose('lpm.templates.usuario.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar usuario"""
        '''
        pp = PoseePermiso('modificar usuario', id_usuario=args[0])
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/usuarios")
        '''   
        usuarios = self.table_filler.get_value(**kw)
        tmpl_context.tabla_usuarios = usuario_table
        user = Usuario.por_id(args[0])
        page = "Usuario {nombre}".format(nombre=user.nombre_usuario)
        return dict(super(UsuarioController, self).edit(*args, **kw), 
                    page=page, usuarios=usuarios, id=args[0])
        
    @expose('lpm.templates.usuario.perfil')
    def perfil(self, *args, **kw):
        """ Despliega una pagina para modificar el perfil del usuario que 
        inició sesión """
        '''
        pp = PoseePermiso('modificar usuario', id_usuario=args[0])
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/usuarios")
        '''
        user = request.identity['repoze.who.userid']
        id = Usuario.by_user_name(user)
        ret = self.edit(id.id_usuario,*args, **kw)
        ret["page"] = "Mi perfil"
        return ret    

    @expose('lpm.templates.usuario.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un usuario"""
#        pp = PoseePermiso('modificar usuario', id_usuario=args[0])
#        if not pp.is_met(request.environ):
#            flash(pp.message % pp.nombre_permiso, 'warning')
#            redirect("/usuarios")
        return dict(super(UsuarioController, self).new(*args, **kw), page='Nuevo Usuario')
 
    #@validate(proyecto_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        """update"""
        if "sprox_id" in kw:
            del kw["sprox_id"]
        print kw
        #redirect("../") 
    
    @validate(usuario_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        if "repita_password" in kw:
            del kw["repita_password"]
        transaction.begin()
        if kw["nro_documento"]:
            kw["nro_documento"] = int(kw["nro_documento"])
        usuario = Usuario(**kw)
        DBSession.add(usuario)
        transaction.commit()
        redirect("./")
    #}

    @expose('lpm.templates.usuario.roles')
    def roles(self, *args, **kw):
        """ Asignar y desasignar Roles """

        tmpl_context.tabla_asignados = rol_user_table
        tmpl_context.tabla_desasignados = rol_user_table
        user = Usuario.por_id(args[0])
        page = "Roles de Usuario {nombre}".format(nombre=user.nombre_usuario)
        asignados = roles_usuario_filler.get_value(usuario=user,
                                                          asignados=True, **kw)
        desasignados = roles_usuario_filler.get_value(usuario=user,
                                                       asignados=False, **kw)
        return dict(asignados=asignados, desasignados=desasignados,
                    page=page)
