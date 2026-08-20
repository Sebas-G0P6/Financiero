{
    "name": "Fenalco Recaudos",
    "version": "18.0.1.0.0",
    "category": "Accounting",
    "summary": "",
    "icon": "/fenalco_cuadre_cajas/static/description/icon.png",
    "author": "Fenalco Valle",
    "license": "LGPL-3",
    "depends": ["base", "account", "base_external_dbsource"],
    "data": [
        "security/fenalco_cuadre_cajas_security.xml",
        "security/ir.model.access.csv",
        "views/fenalco_reportes_views.xml",
        "views/account_journal_views.xml",
        "data/account_journal_recaudo_nacional.xml",
    ],
    "installable": True,
    "application": False,
}
