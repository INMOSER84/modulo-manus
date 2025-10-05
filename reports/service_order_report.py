from odoo import models, api

class ServiceOrderReport(models.AbstractModel):
    _name = 'report.inmoser_service_order.service_order'
    _description = 'Service Order Report'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['service.order'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'service.order',
            'docs': docs,
            'data': data,
        }
