from odoo import fields, models


class AccountJournal(models.Model):
    """Campo mínimo requerido por fv_generar_consolidado_caja para relacionar
    el código de forma de pago que trae Oracle (ID_FORMA_PAGO) con un diario
    contable de Odoo. Puerto recortado de add_fields_account_journal en
    fenalco_recaudo_pagos/models/fenalco_inherit_productos_model.py (ahí trae
    muchos más campos usados por la interfaz contable UnoE, fuera de alcance
    de este reporte).
    """

    _inherit = 'account.journal'

    _fv_FORMAS_PAGOS = [
        ("1", "EFECTIVO"),
        ("2", "CHEQUE"),
        ("15", "TARJETA DEBITO"),
        ("16", "TARJETA CREDITO"),
        ("44", "CHEQUE_VIRTUAL"),
        ("20", "CONCILIATORIO"),
        ("19", "TRANSFERIDO"),
        ("22", "PLAZA EFECTIVO"),
        ("21", "RECONSIGNACION"),
        ("24", "TU_COMPRA"),
        ("25", "B_BOG_CORFI_EFE"),
        ("26", "BANCO_OCCIDENTE"),
        ("27", "B_BOG_FCO_EFE_0025"),
        ("29", "B_BOG_EFE_4557"),
        ("30", "B_BOG_EFE_9717"),
        ("32", "COMPENSACIÓN COLPATRIA"),
        ("43", "COMPENSACION COLPATRIA DINERS"),
        ("23", "PLAZA CHEQUE"),
        ("28", "B_BOG_FIDUCOLPATRIA_EFE"),
        ("31", "B_BOG_FCO_EFE_LIQ_4557"),
        ("33", "PAGOS CON ID BOG_EFE_2033"),
        ("34", "B_BOG_FCO_TAR_LIQ_4557"),
        ("35", "B_BOG_FIDUCOLPATRIA_TAR"),
        ("41", "B_DAVIVIENDA_AHORROS_3341"),
        ("40", "PAGOS CON ID BOG_TAR_2033"),
        ("42", "B_DAVIVIENDA_AHORROS_8427"),
        ("45", "B_COLPATRIA_AHORROS_4049"),
        ("46", "B_COLPATRIA_AHORROS_3654"),
    ]
    _fv_forma_pago_id = fields.Selection(_fv_FORMAS_PAGOS, "Relacionado Metodo de Pago (Recaudo Nacional)")
