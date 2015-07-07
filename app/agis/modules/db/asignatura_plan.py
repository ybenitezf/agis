#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gluon import *
from applications.agis.modules.db import plan_curricular
from applications.agis.modules.db import asignatura
from applications.agis.modules.db import nivel_academico
from applications.agis.modules import tools

def obtener_manejo( plan_id ):
    db=current.db
    definir_tabla()
    db.asignatura_plan.id.readable=False
    db.asignatura_plan.plan_curricular_id.writable=False
    db.asignatura_plan.plan_curricular_id.readable=False
    db.asignatura_plan.plan_curricular_id.default=plan_id
    query=( (db.asignatura_plan.id > 0) & (db.asignatura_plan.plan_curricular_id == plan_id) )
    return tools.manejo_simple( query,buscar=True,
        campos=[db.asignatura_plan.nivel_academico_id,db.asignatura_plan.asignatura_id]
        )

def definir_tabla():
    db=current.db
    T=current.T
    plan_curricular.definir_tabla()
    asignatura.definir_tabla()
    nivel_academico.definir_tabla()
    if not hasattr( db,'asignatura_plan' ):
        db.define_table( 'asignatura_plan',
            Field( 'plan_curricular_id','reference plan_curricular' ),
            Field( 'asignatura_id','reference asignatura' ),
            Field( 'nivel_academico_id','reference nivel_academico' ),
            format="",
            )
        db.asignatura_plan.plan_curricular_id.label=T( 'Plan curricular' )
        db.asignatura_plan.asignatura_id.label=T( 'Asignatura' )
        db.asignatura_plan.nivel_academico_id.label=T( 'Nivel académico' )
        db.commit()