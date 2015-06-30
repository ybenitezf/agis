#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *
from applications.agis.modules.db import estudiante
from applications.agis.modules.db import tipos_ensennanza
from applications.agis.modules.db import escuela_media
from applications.agis.modules.tools import requerido
from applications.agis.modules.db import unidad_organica
from applications.agis.modules.db import discapacidad
from applications.agis.modules.db import regimen
from applications.agis.modules.db import regimen_uo
from applications.agis.modules.db import ano_academico
from applications.agis.modules.db import escuela
from applications.agis.modules import tools

CANDIDATURA_DOCUMENTOS_VALUES = {
    '1':'Certificado original',
    '2':'Cópia de documento',
    '3':'Documento de trabajo',
    '4':'Documento Militar',
    '5':'Internado',
}
def candidatura_documentos_represent(valores, fila):
    res = ""
    for i in valores:
        if res == "":
            res += CANDIDATURA_DOCUMENTOS_VALUES[ i ]
        else:
            res += ", " + CANDIDATURA_DOCUMENTOS_VALUES[ i ]
    return res

CANDIDATURA_ESTADO = {
    '1':'Inscrito con deudas',
    '2':'Inscrito',
    '3':'Inscrito no admitido',
    '4':'Inscrito admitido',
}
def candidatura_estado_represent(valor, fila):
    T = current.T
    if valor:
        return T( CANDIDATURA_ESTADO[ valor ] )
    else:
        return ''

def obtener_manejo( ano_academico_id=None,estado='1' ):
    db = current.db
    if not ano_academico_id:
        ano_academico_id = ( ano_academico.buscar_actual() ).id
    query = ( (db.persona.id == db.estudiante.persona_id) & (db.candidatura.estudiante_id == db.estudiante.id) &
        (db.candidatura.estado_candidatura == estado) & (db.candidatura.ano_academico_id == ano_academico_id)
    )
    db.candidatura.id.readable = False
    db.persona.id.readable = False
    manejo = SQLFORM.grid(query=query,
        fields=[db.persona.nombre_completo,
                db.candidatura.estado_candidatura,
                db.candidatura.id,
                db.persona.id],
        orderby=[db.persona.nombre_completo],
        details=False,
        csv=False,
        searchable=False,
        editable=False,
        create=False,
        showbuttontext=False,
        maxtextlength=100,
        formstyle='bootstrap',
    )
    return manejo

def candidatura_format(registro):
    db = current.db
    definir_tabla()
    est = db.estudiante[registro.estudiante_id]
    return estudiante.estudiante_format(est)

def definir_tabla():
    db = current.db
    T = current.T
    estudiante.definir_tabla()
    tipos_ensennanza.definir_tabla()
    escuela_media.definir_tabla()
    unidad_organica.definir_tabla()
    discapacidad.definir_tabla()
    regimen.definir_tabla()
    regimen_uo.definir_tabla()
    ano_academico.definir_tabla()
    if not hasattr( db,'candidatura' ):
        db.define_table( 'candidatura',
            Field( 'estudiante_id','reference estudiante' ),
            # laborales
            Field( 'es_trabajador','boolean' ),
            Field( 'profesion','string',length=30 ),
            Field( 'nombre_trabajo','string',length=30 ),
            # procedencia
            Field( 'habilitacion','string',length=5 ),
            Field( 'tipo_escuela_media_id','reference tipo_escuela_media' ),
            Field( 'escuela_media_id','reference escuela_media' ),
            Field( 'carrera_procedencia','string',length=20 ),
            Field( 'ano_graduacion','string',length=4 ),
            # institucional
            Field( 'unidad_organica_id', 'reference unidad_organica' ),
            Field( 'discapacidades', 'list:reference discapacidad' ),
            Field( 'documentos', 'list:string' ),
            Field( 'regimen_unidad_organica_id', 'reference regimen_unidad_organica' ),
            Field( 'ano_academico_id','reference ano_academico' ),
            Field( 'estado_candidatura','string',length=1,default='1' ),
            format=candidatura_format,
            )
        db.candidatura.estado_candidatura.writable = False
        db.candidatura.estado_candidatura.label = T('Estado')
        db.candidatura.estado_candidatura.represent = candidatura_estado_represent
        db.candidatura.estado_candidatura.requires = IS_IN_SET( CANDIDATURA_ESTADO,zero=None )
        db.candidatura.estudiante_id.label = T( 'Estudiante' )
        db.candidatura.estudiante_id.required = True
        db.candidatura.habilitacion.required = True
        db.candidatura.habilitacion.widget = SQLFORM.widgets.autocomplete(
            current.request,db.candidatura.habilitacion,limitby=(0,10),min_length=1
        )
        db.candidatura.tipo_escuela_media_id.label = T( 'Tipo de enseñanza media' )
        db.candidatura.tipo_escuela_media_id.required = True
        db.candidatura.tipo_escuela_media_id.requires = IS_IN_DB( db,'tipo_escuela_media.id','%(nombre)s',zero=None )
        db.candidatura.escuela_media_id.label = T( 'Escuela de procedencia' )
        db.candidatura.carrera_procedencia.label = T( 'Carrera de procedencia' )
        db.candidatura.carrera_procedencia.required = True
        db.candidatura.carrera_procedencia.requires = IS_NOT_EMPTY( T('Información requerido') )
        db.candidatura.carrera_procedencia.widget = SQLFORM.widgets.autocomplete(
            current.request,db.candidatura.habilitacion,limitby=(0,10),min_length=3
        )
        db.candidatura.ano_graduacion.label = T( 'Año de conclusión' )
        db.candidatura.ano_graduacion.requires = [ IS_INT_IN_RANGE(1900, 2300,
            error_message=T( 'Año incorrecto, debe estar entre 1900 y 2300' )
            )]
        db.candidatura.ano_graduacion.requires.extend( requerido )
        db.candidatura.ano_graduacion.comment = T( 'En el formato AAAA' )
        db.candidatura.unidad_organica_id.required = True
        db.candidatura.unidad_organica_id.requires = IS_IN_DB( db,
            'unidad_organica.id',"%(nombre)s",zero=None
            )
        db.candidatura.discapacidades.required = False
        db.candidatura.discapacidades.notnull = False
        db.candidatura.discapacidades.label = T( 'Necesita educación especial' )
        db.candidatura.documentos.requires = IS_IN_SET( CANDIDATURA_DOCUMENTOS_VALUES,multiple=True )
        db.candidatura.documentos.represent = candidatura_documentos_represent
        db.candidatura.documentos.label = T( 'label' )
        db.candidatura.unidad_organica_id.label = T( 'Unidad organica' )
        db.candidatura.regimen_unidad_organica_id.label = T( 'Régimen' )
        db.candidatura.ano_academico_id.label = T( 'Año académico' )
        db.candidatura.ano_academico_id.default = ano_academico.buscar_actual().id
        db.candidatura.ano_academico_id.requires = IS_IN_DB( db,'ano_academico.id',"%(nombre)s",zero=None )
        db.candidatura.habilitacion.requires = requerido
        db.commit()