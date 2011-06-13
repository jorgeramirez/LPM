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

from lpm.controllers.validaciones import UsuarioAddFormValidator, UsuarioEditFormValidator
from lpm.model import DBSession, Usuario, Rol, TipoItem, Proyecto, Fase
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.authorization import PoseePermiso, AlgunPermiso
from lpm.controllers.rol import (RolTable as RolRolTable,
                                     RolTableFiller as RolRolTableFiller)

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
        if PoseePermiso('modificar usuario').is_met(request.environ):
            value += '<div>' + \
                        '<a href="/usuarios/'+ str(obj.id_usuario) +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        if PoseePermiso('eliminar usuario').is_met(request.environ):
            value += '<div><form method="POST" action="' + str(obj.id_usuario) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                     '</form></div><br />'

        if PoseePermiso('asignar rol').is_met(request.environ):
            value += '<div>' + \
                        '<a href="/usuarios/roles/' + str(obj.id_usuario) + '" ' +\
                        'class="' + clase + '">Roles</a>' + \
                     '</div><br />'
        value += '</div>'
        return value

    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de usuario si se tiene un permiso 
        necesario. Caso contrario se muestra solo su usuario
        """
        if AlgunPermiso(patron="usuario").is_met(request.environ):
            return super(UsuarioTableFiller,
                         self)._do_get_provider_count_and_objs(**kw)
        username = request.credentials['repoze.what.userid']
        user = Usuario.by_user_name(username)
        return 1, [user]


#    def _do_get_provider_count_and_objs(self, **kw):
#        """
#        Se muestra la lista de usuario si se tiene un permiso 
#        necesario
#        """
#        count, filtrados = super(UsuarioTableFiller, self). \
#                                 _do_get_provider_count_and_objs(**kw)
#        if count == 0:
#            return count, filtrados
#        nombre_usuario = request.credentials['repoze.what.userid']
#        usuario = Usuario.by_user_name(nombre_usuario)
#        for r in usuario.roles:
#            for p in r.permisos:
#                if p.nombre_permiso.find("usuario") > 0:
#                    return count, filtrados
#
#        #si no tiene permisos necesarios lo unico que puede ver es su usuario
#        return 1, [usuario]

    
usuario_table_filler = UsuarioTableFiller(DBSession)


class UsuarioAddForm(AddRecordForm):
    __model__ = Usuario
    __omit_fields__ = ['id_usuario', 'creado', '_password', 'historial_lb', 'roles',
                       'historial_item']
    __require_fields__ = ['nombre_usuario', 'nombre', 'apellido', 'password',
                          'repita_password', 'email']
    __base_validator__ = UsuarioAddFormValidator
    __field_order__ = ['nombre_usuario', 'nombre', 'apellido', 'password',
                       'repita_password', 'email', 'nro_documento', 'telefono']
    __field_attrs__ = {}
    
    repita_password = PasswordField('repita_password')

#    from sprox.formbase import Field
#    roles_boton = Field(SubmitButton('roles'))
                             

usuario_add_form = UsuarioAddForm(DBSession)


class UsuarioEditForm(EditableForm):
    __model__ = Usuario
    __hide_fields__ = ['id_usuario']
    __omit_fields__ = ['nombre_usuario', 'creado', '_password', 'password',
                        'historial_lb', 'roles', 'historial_item']
    __require_fields__ = ['nombre', 'apellido', 'nuevo_password',
                          'repita_password', 'email']
    __base_validator__ = UsuarioEditFormValidator
    __field_order__ = ['nombre_usuario', 'nombre', 'apellido', 'nuevo_password',
                       'repita_password', 'email', 'nro_documento', 'telefono']
    __field_attrs__ = {
                       'nombre_usuario': { 'maxlength' : '32'},
                       'roles' : {'label_text' :'Roles'}
                       }

    nuevo_password = PasswordField('nuevo_password')
    repita_password = PasswordField('repita_nuevo_password')
    
usuario_edit_form = UsuarioEditForm(DBSession)        


class UsuarioEditFiller(EditFormFiller):
    __model__ = Usuario

usuario_edit_filler = UsuarioEditFiller(DBSession)


#tablas para la asignación/desasignación de roles
class RolTable(TableBase):
    __model__ = Rol
    __headers__ = {'nombre_rol' : u'Nombre de Rol',
                   'codigo' : u"Código", 'tipo' : u'Tipo',
                   'proyecto': u'Proyecto', 'fase': u"Fase", 
                   'tipo_item': u"Tipo de Ítem", 'check' : u'Check',
                  }
    __omit_fields__ = ['id_rol', 'permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion', 'creado']
    __default_column_width__ = '15em'
    
    __add_fields__ = {'proyecto':None, 'fase': None,
                      'tipo_item': None, 'check' : None}
    __xml_fields__ = ['Check']
    __column_widths__ = {'nombre_rol': "35em",
                         'codigo': "35em",
                         '__actions__' : "50em"
                        }
    __field_order__ = ["nombre_rol", "codigo", "tipo", "proyecto", "fase",
                       "tipo_item", "check"]

    
rol_user_table = RolTable(DBSession)

class RolTableFiller(TableFiller):
    __model__ = Rol
    __add_fields__ = {'proyecto':None, 'fase': None,
                      'tipo_item': None, 'check' : None}

    def check(self, obj, **kw):
        #id
        checkbox = '<input type="checkbox" class="checkbox_tabla" id="' + str(obj.id_rol) + '"/>'
        return checkbox
    
    def proyecto(self, obj, **kw):
        if obj.id_proyecto != 0:
            proy = Proyecto.por_id(obj.id_proyecto)
            return proy.nombre
        else:
            return u"---------"

    def fase(self, obj, **kw):
        if obj.id_fase != 0:
            fase = Fase.por_id(obj.id_fase)
            return fase.nombre
        else:
            return u"---------"
            
    def tipo_item(self, obj, **kw):
        if obj.id_tipo_item != 0:
            tipo_item = TipoItem.por_id(obj.id_tipo_item)
            return tipo_item.codigo
        else:
            return u"---------"
    
    def _do_get_provider_count_and_objs(self,
                                         usuario=None, asignados=True, **kw):
        if (not asignados):
            roles = Rol.roles_desasignados(usuario.id_usuario)
        elif (asignados):
            roles = usuario.roles
            
        return len(roles), roles

    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'   
        if PoseePermiso('modificar rol').is_met(request.environ):
            value += '<div>' + \
                        '<a href="/roles/'+ str(obj.id_rol) +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</div><br />'
        if PoseePermiso('eliminar rol').is_met(request.environ):
            value += '<div><form method="POST" action="/roles/' + str(obj.id_rol) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                     '</form></div><br />'
        value += '</div>'
        return value


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

    #para el form de busqueda
    columnas = dict(nombre_usuario="texto", nombre="texto", apellido="texto",
                    email="texto", nro_documento="texto")
 
    #{ Métodos
    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.usuario.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        puede_crear = PoseePermiso("crear usuario").is_met(request.environ)
        if request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            usuarios = self.table_filler.get_value(**kw)
        else:
            usuarios = []
            
        tmpl_context.widget = usuario_table
    
        return dict(lista_elementos=usuarios, page=self.title, titulo=self.title, 
                    modelo=self.model.__name__, columnas=self.columnas,
                    url_action="/usuarios/", puede_crear=puede_crear)

    @expose('lpm.templates.usuario.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar usuario"""
        '''
        pp = PoseePermiso('modificar usuario', id_usuario=args[0])
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/usuarios")
        '''
        
        puede_asignar_rol = PoseePermiso("asignar rol").is_met(request.environ)
        class mis_roles_tf(RolRolTableFiller):
            def __actions__(self, obj):
                """Links de acciones para un registro dado"""
                value = '<div>'
                clase = 'actions'   
                if PoseePermiso('modificar rol').is_met(request.environ):
                    value += '<div>' + \
                                '<a href="/roles/'+ str(obj.id_rol) + '/edit/" ' + \
                                'class="' + clase + '">Ver</a>' + \
                             '</div><br />'
                value += '</div>'           
                return value

            def _do_get_provider_count_and_objs(self, **kw):
                user = Usuario.por_id(int(kw["id_usuario"]))
                return len(user.roles), user.roles

        tmpl_context.widget = self.edit_form
        usuarios = self.table_filler.get_value(**kw)
        roles = mis_roles_tf(DBSession).get_value(id_usuario=args[0])
        tmpl_context.tabla_roles = RolRolTable(DBSession)
        user = Usuario.por_id(args[0])
        if (False): # si viene de /usuarios/perfil
            page = "Mi perfil"
        else:
            page = "Usuario {nombre}".format(nombre=user.nombre_usuario)
        
        return dict(super(UsuarioController, self).edit(*args, **kw), 
                    page=page, roles=roles, id=args[0], 
                    puede_asignar_rol=puede_asignar_rol)
        
    @expose()
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
        url = '/usuarios/' + str(id.id_usuario) + '/edit/'
        redirect(url)
          

    @expose('lpm.templates.usuario.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un usuario"""
#        pp = PoseePermiso('modificar usuario', id_usuario=args[0])
#        if not pp.is_met(request.environ):
#            flash(pp.message % pp.nombre_permiso, 'warning')
#            redirect("/usuarios")
        nav = dict(atras="/", adelante="/proyectos")
        return dict(super(UsuarioController, self).new(*args, **kw),
                     page='Nuevo Usuario', nav=nav)
 
    @validate(usuario_edit_form, error_handler=edit)
    @expose()
    def put(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        if "repita_nuevo_password" in kw:
            del kw["repita_nuevo_password"]
        if kw["nro_documento"]:
            kw["nro_documento"] = int(kw["nro_documento"])
        pp = PoseePermiso('modificar usuario')
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect(self.action)
        transaction.begin()
        usuario = Usuario.por_id(args[0])
        usuario.nombre = kw["nombre"]
        usuario.apellido = kw["apellido"]
        usuario.email = kw["email"]
        usuario.telefono = kw["telefono"]
        usuario.nro_documento = kw["nro_documento"]
        usuario.password = kw["nuevo_password"]
        transaction.commit()      
        redirect("../") 
    
    @validate(usuario_add_form, error_handler=new)
    @expose()
    def post(self, *args, **kw):
        if "sprox_id" in kw:
            del kw["sprox_id"]
        if "repita_password" in kw:
            del kw["repita_password"]
        if kw["nro_documento"]:
            kw["nro_documento"] = int(kw["nro_documento"])
        transaction.begin()
        usuario = Usuario(**kw)
        DBSession.add(usuario)
        transaction.commit()
        redirect("./")

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
                    page=page, id=args[0])

    @with_trailing_slash
    @paginate('lista_elementos', items_per_page=5)
    @expose('lpm.templates.usuario.get_all')
    @expose('json')
    def post_buscar(self, *args, **kw):
        puede_crear = PoseePermiso("crear usuario").is_met(request.environ)
        tmpl_context.widget = self.table
        buscar_table_filler = UsuarioTableFiller(DBSession)
        buscar_table_filler.filtros = kw
        usuarios = buscar_table_filler.get_value()
        return dict(lista_elementos=usuarios, page=self.title, titulo=self.title, 
                    modelo=self.model.__name__, columnas=self.columnas,
                    url_action="/usuarios/", puede_crear=puede_crear)
    
    @expose('lpm.templates.usuario.roles')
    def desasignar_roles(self, *args, **kw):
        """ Desasigna los roles seleccionados a un usuario """
        if kw:
            pks = []
            for k, pk in kw.items():
                pks.append(int(pk))
            transaction.begin()
            user = Usuario.por_id(int(args[0]))
            c = 0
            while c < len(user.roles):
                if user.roles[c].id_rol in pks:
                    del user.roles[c]
                else:
                    c += 1
            transaction.commit()
        return self.roles(*args)

    @expose('lpm.templates.usuario.roles')
    def asignar_roles(self, *args, **kw):
        """ Asigna los roles seleccionados a un usuario """
        if kw:
            pks = []
            for k, pk in kw.items():
                pks.append(int(pk))
            transaction.begin()
            user = Usuario.por_id(int(args[0]))
            roles = DBSession.query(Rol).filter(Rol.id_rol.in_(pks)).all()
            for r in roles:
                r.usuarios.append(user)
            transaction.commit()
        return self.roles(*args)
    #}
