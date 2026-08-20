from odoo import api, fields, models


class FenalcoReportesInterfazConsolidado(models.Model):
    _name = 'fenalco.reportes.interfaz.consolidado'
    _description = 'fenalco.reportes.interfaz.consolidado'

    _fv_ESTADOS = [
        ("cancelado_parcial", "Cancelado Parcial"),
        ("cancelado", "Anulado"),
        ("pendiente", "Pendiente"),
        ("invalido", "Invalido"),
        ("no_aplico_pagado", "No Aplico Pagado"),
        ("aplico_pagado", "Aplico Pagado"),
        ("recaudado", "Pago Recaudado"),
        ("recaudado_externo", "Pago Recaudado Externo"),
    ]

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id, index=1)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id.id, required=True)

    _id = fields.Char(tracking=True, required=False, string='Id', help='')
    _fv_account_journal = fields.Many2one('account.journal', string='Metodo de Pago', tracking=True)
    _no_recibo_prefijo = fields.Char(store=True, string='No Recibo', tracking=True, compute="_compute_prefijo", readonly=True, force_save='1')
    _no_recibo = fields.Char(tracking=True, required=False, string='No Recibo', help='')
    _no_liquidacion = fields.Char(tracking=True, required=False, string='No Liquidacion', help='')
    _no_secuencia_tucompra = fields.Char(tracking=True, required=False, string='Secuencia Tucompra', help='')
    _fecha_pago = fields.Char(tracking=True, required=False, string='Fecha de Pago', help='')

    _fecha_pago_aplicado = fields.Datetime(string='Fecha de Pago Aplicado', tracking=True, required=False, help='')

    _comprobante = fields.Char(tracking=True, required=False, string='Comprobante', help='')
    _valor = fields.Integer(tracking=True, required=False, string='Valor', help='')
    _codigo_barras_open = fields.Char(tracking=True, required=False, string='Codigo Barras', help='')
    _paz_salvo_open = fields.Char(tracking=True, required=False, string='Paz Salvo', help='')
    _cajero = fields.Char(tracking=True, required=False, string='Cajero', help='')
    _hora = fields.Char(tracking=True, required=False, string='Hora', help='')
    _cedula_deudor = fields.Char(tracking=True, required=False, string='Cedula Deudor', help='')

    _validado = fields.Boolean("Validado", tracking=True)

    _relacion_informe = fields.Many2one('fenalco.reportes.interfaz.unoe', readonly=True, string='Informe')

    _fv_estado = fields.Selection(
        _fv_ESTADOS,
        "Estado",
        required=False,
        readonly=True,
        force_save='1',
        tracking=True,
    )

    _fv_estado_externo = fields.Selection(
        [("aprobado", "Aprobado"), ("anulado", "Anulado")],
        "Estado Externo",
        required=False,
        readonly=True,
        force_save='1',
        tracking=True,
    )

    _origen = fields.Selection(
        [("cobranzas", "Pagos de Cobranzas"), ("caja", "Pagos de Caja"), ("pago_manual_open", "Pagos Manuales Open"), ("caja_tranzaxis", "Recaudo Tranzaxis")],
        "Origen Pago",
        required=False,
        readonly=True,
        force_save='1',
        tracking=True,
    )
    _grupo_producto = fields.Selection(
        [("aval", "Aval (As400)"), ("open", "Open"), ("tranzaxis", "Tranzaxis")],
        "Grupo Productos",
        required=False,
        readonly=True,
        force_save='1',
        tracking=True,
    )

    _number_related_info = fields.Integer(tracking=True, required=False, string='Numero Relacion', help='')

    @api.depends('_no_recibo', '_origen')
    def _compute_prefijo(self):
        for rec in self:
            _prefijo = ''
            if rec._origen == 'cobranzas':
                _prefijo = 'RF-'
            elif rec._origen == 'caja':
                _prefijo = 'RCW-'
            rec._no_recibo_prefijo = _prefijo + rec._no_recibo
