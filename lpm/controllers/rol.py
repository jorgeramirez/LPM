# -*- coding: utf-8 -*-
"""
Módulo que define el controlador de roles.

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
from tg import redirect, request, require, flash, url

from lpm.model import DBSession, Usuario, Rol, Permiso, Proyecto, Fase, TipoItem
from lpm.lib.sproxcustom import CustomTableFiller
from lpm.lib.sproxcustom import WidgetSelectorDojo, MultipleSelectDojo
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

from tw.forms.fields import PasswordField, TextField, TextArea, Button

from repoze.what.predicates import not_anonymous

from tg import tmpl_context, request

class RolTable(TableBase):
    __model__ = Rol
    __headers__ = {'nombre_rol' : u'Nombre de Rol',
                   'codigo' : u"Código", 'creado': u"Fecha Creación",
                   'tipo' : u'Tipo'
                  }
    __omit_fields__ = ['id_rol', 'permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion']
    __default_column_width__ = '15em'
    __column_widths__ = {'nombre_rol': "35em",
                         'codigo': "35em",
                         '__actions__' : "50em"
                        }
#    __url__ = '/rols.json'
    
rol_table = RolTable(DBSession)


class RolTableFiller(CustomTableFiller):
    __model__ = Rol
    __omit_fields__ = ['permisos', 'usuarios',
                       'id_proyecto', 'id_fase', 'id_tipo_item',
                       'descripcion']
'''   
    def __actions__(self, obj):
        """Links de acciones para un registro dado"""
        value = '<div>'
        clase = 'actions'   
        if PoseePermiso('modificar rol', 
                        id_rol=obj.id_rol).is_met(request.environ):
            value += '<div>' + \
                        '<a href="'+ str(obj.id_rol) +'/edit" ' + \
                        'class="' + clase + '">Modificar</a>' + \
                     '</ div><br />'
        if PoseePermiso('eliminar rol',
                        id_rol=obj.id_rol).is_met(request.environ):
            value += '<div><form method="POST" action="' + str(obj.id_rol) + '" class="button-to">'+\
                     '<input type="hidden" name="_method" value="DELETE" />' +\
                     '<input onclick="return confirm(\'Está seguro?\');" value="Delete" type="submit" '+\
                     'style="background-color: transparent; float:left; border:0; color: #286571;'+\
                     'display: inline; margin: 0; padding: 0;" class="' + clase + '"/>'+\
                     '</ form></ div><br />'
#-------------------------------------------------------------- arreglar!
        if PoseePermiso('asignar rol',
                        id_rol=obj.id_rol).is_met(request.environ):
            value += '<div>' + \
                        '<a href="' + str(obj.id_rol) + '/roles/" ' +\
                        'class="' + clase + '">Roles</a>' + \
                     '</ div><br />'

    def _do_get_provider_count_and_objs(self, **kw):
        """
        Se muestra la lista de rol si se tiene un permiso 
        necesario
        """
        count, filtrados = super(RolTableFiller, self). \
                                 _do_get_provider_count_and_objs(**kw)
        if count == 0:
            return count, filtrados
        pks = []
        nombre_rol = request.credentials['repoze.what.userid']
        rol = Rol.by_user_name(nombre_rol)
        for r in rol.roles:
            for p in r.permisos:
                if p.nombre_permiso.find("rol") > 0:
                    return count, filtrados

        #si no tiene permisos necesarios lo unico que puede ver es su rol
        return 1, [rol]
'''
    
rol_table_filler = RolTableFiller(DBSession)

class CodProyectoField(PropertySingleSelectField):
    """Dropdown list para codigo de proyecto"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        proyectos = DBSession.query(Proyecto).all()
        for p in proyectos:
            options.append((p.id_proyecto, '%s (%s)' % (p.codigo, 
                    p.nombre)))
        d['options'] = options
        return d
    
class CodFaseField(PropertySingleSelectField):
    """Dropdown list para codigo de proyecto"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        fases = DBSession.query(Fase).all()
        for f in fases:
            options.append((f.id_fase, '%s (%s)' % (f.codigo, 
                    f.nombre)))
        d['options'] = options
        return d

class CodTipoItemField(PropertySingleSelectField):
    """Dropdown list para codigo de proyecto"""
    def _my_update_params(self, d, nullable=False):
        options = []
        options.append((0, "----------"))
        tipos = DBSession.query(TipoItem).all()
        for t in tipos:
            options.append((t.id_tipo_item, '%s' % t.codigo))
        d['options'] = options
        return d

class TiposRolesField(PropertySingleSelectField):
    """Dropdown list para codigo de proyecto"""
    def _my_update_params(self, d, nullable=False):
        options = [u'Plantilla', u'Sistema', u'Proyecto',
                   u'Fase', u'Tipo de Ítem']
        d['options'] = options
        return d
    
#para mejorar el multiple selector hecho en dojo
class PermisosMultipleSelect(MultipleSelectDojo):
    def _my_update_params(self, d, nullable=False):
        options = []
        permisos = DBSession.query(Permiso).all()
        for p in permisos:
            options.append((p.id_permiso, '%s' % p.nombre_permiso))
        d['options'] = options
        return d

class SelectorPermisos(WidgetSelectorDojo):
    default_multiple_select_field_widget_type = PermisosMultipleSelect
       
class RolAddForm(AddRecordForm):
    __model__ = Rol
    __omit_fields__ = ['id_rol', 'usuarios',
                       'codigo', 'creado']
    __require_fields__ = ['nombre_rol', 'tipo', 'permisos']
    __check_if_unique__ = True
    __field_order__ = ['nombre_rol', 'tipo', 'descripcion',
                        'id_proyecto', 'id_fase', 'id_tipo_item',
                        'permisos']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre_rol': { 'maxlength' : '32'}
                       
                       }
#no sé si esto sirve de algo
    __dropdown_field_names__ = {'id_proyecto' : 'codigo',
                                'id_fase' : 'codigo',
                                'id_tipo_item' : 'codigo',
                                'tipo' : 'tipo'
                                }
    
    __widget_selector_type__ = SelectorPermisos
    
    id_proyecto = CodProyectoField
    id_fase = CodFaseField
    id_tipo_item = CodTipoItemField
    descripcion = TextArea                         
    tipo = TiposRolesField
    
    
rol_add_form = RolAddForm(DBSession)


class RolEditForm(EditableForm):
    __model__ = Rol
    __hide_fields__ = ['id_rol']
    __omit_fields__ = [ 'usuarios',
                       'codigo', 'creado']
    __require_fields__ = ['nombre_rol', 'tipo', 'permisos']
    __check_if_unique__ = True
    __field_order__ = ['nombre_rol', 'tipo', 'descripcion',
                        'id_proyecto', 'id_fase', 'id_tipo_item',
                        'permisos']
    __field_attrs__ = {'descripcion' : {'row': '1'},
                       'nombre_rol': { 'maxlength' : '32'}
                       
                       }
#no sé si esto sirve de algo
    __dropdown_field_names__ = {'id_proyecto' : 'codigo',
                                'id_fase' : 'codigo',
                                'id_tipo_item' : 'codigo',
                                'tipo' : 'tipo'
                                }
    
    __widget_selector_type__ = SelectorPermisos
    
    id_proyecto = CodProyectoField
    id_fase = CodFaseField
    id_tipo_item = CodTipoItemField
    descripcion = TextArea                         
    tipo = TiposRolesField

rol_edit_form = RolEditForm(DBSession)        


class RolEditFiller(EditFormFiller):
    __model__ = Rol

rol_edit_filler = RolEditFiller(DBSession)


class RolController(CrudRestController):
    """Controlador de roles"""
    #{ Variables
    title = u"Administrar Roles"
    #{ Plantillas

    # No permitir rols anonimos (?)
    allow_only = not_anonymous(u"El rol debe haber iniciado sesión")
    
    #{ Modificadores
    model = Rol
    table = rol_table
    table_filler = rol_table_filler
    new_form = rol_add_form
    edit_form = rol_edit_form
    edit_filler = rol_edit_filler

 
    #{ Métodos
    #@with_trailing_slash
    @paginate('lista_elementos', items_per_page=7)
    @expose('lpm.templates.rol.get_all')
    @expose('json')
    def get_all(self, *args, **kw):
        """ 
        Retorna todos los registros
        Retorna una página HTML si no se especifica JSON
        """
        if request.response_type == 'application/json':
            return self.table_filler.get_value(**kw)
        if not getattr(self.table.__class__, '__retrieves_own_value__', False):
            rols = self.table_filler.get_value(**kw)
        else:
            rols = []
            
        tmpl_context.widget = rol_table
        return dict(lista_elementos=rols, page=self.title, titulo=self.title, 
                    modelo=self.model.__name__)


    @expose('lpm.templates.rol.edit')
    def edit(self, *args, **kw):
        """Despliega una pagina para modificar rol"""
        '''
        pp = PoseePermiso('modificar rol', id_rol=args[0])
        if not pp.is_met(request.environ):
            flash(pp.message % pp.nombre_permiso, 'warning')
            redirect("/rols")
        '''   
        roles = self.table_filler.get_value(**kw)
        tmpl_context.tabla_roles = rol_table
        rol = Rol.por_id(args[0])
        page = "Rol {nombre}".format(nombre=rol.nombre_rol)
        return dict(super(RolController, self).edit(*args, **kw), 
                    page=page, roles=roles)
        
 
    @expose('lpm.templates.rol.new')
    def new(self, *args, **kw):
        """Despliega una pagina para crear un rol"""
#        pp = PoseePermiso('modificar rol', id_rol=args[0])
#        if not pp.is_met(request.environ):
#            flash(pp.message % pp.nombre_permiso, 'warning')
#            redirect("/rols")
        return dict(super(RolController, self).new(*args, **kw), page='Nuevo Rol')
    #}

