from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class Manuscript(models.Model):
    _name = 'manus.manuscript'
    _description = 'Manuscrito Antiguo'
    _order = 'date_desc desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campos básicos (sin elementos deprecados)
    name = fields.Char(string="Título", required=True, tracking=True)
    date_desc = fields.Date(string="Fecha de Descripción", tracking=True)
    author = fields.Char(string="Autor/Atribución", tracking=True)
    description = fields.Html(
        string="Descripción", 
        sanitize=True, 
        strip_style=True,  # Seguridad mejorada
        tracking=True
    )
    
    # Archivos (usando fields.Image en lugar de Binary)
    image = fields.Image(
        string="Imagen Portada", 
        max_width=1024, 
        max_height=1024,
        help="Imagen optimizada automáticamente"
    )
    
    # Archivos PDF (Binary con validaciones)
    file = fields.Binary(
        string="Archivo PDF", 
        attachment=True,
        help="Máximo 20MB"
    )
    file_name = fields.Char(string="Nombre del Archivo")
    file_size = fields.Integer(
        string="Tamaño", 
        compute='_compute_file_size',
        help="Tamaño en bytes"
    )
    
    # Clasificación
    tag_ids = fields.Many2many(
        'manus.tag', 
        string='Etiquetas',
        help="Etiquetas de clasificación"
    )
    category_id = fields.Many2one(
        'manus.category', 
        string="Categoría",
        help="Categoría principal"
    )
    
    # Control de acceso (sin usar cr/uid)
    user_id = fields.Many2one(
        'res.users', 
        string="Responsable", 
        default=lambda self: self.env.user
    )
    department_id = fields.Many2one(
        'hr.department', 
        string="Departamento"
    )
    
    # Estados (flujo de trabajo)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('review', 'En Revisión'),
        ('validated', 'Validado'),
        ('archived', 'Archivado')
    ], default='draft', tracking=True, required=True)

    # Métodos sin api.multi (deprecado)
    @api.depends('file')
    def _compute_file_size(self):
        for record in self:
            record.file_size = len(record.file) if record.file else 0

    @api.constrains('date_desc')
    def _check_date_desc(self):
        for record in self:
            if record.date_desc and record.date_desc > fields.Date.today():
                raise ValidationError(_("La fecha no puede ser futura"))

    @api.constrains('file')
    def _check_file_size(self):
        max_size = 20 * 1024 * 1024  # 20MB
        for record in self:
            if record.file and record.file_size > max_size:
                raise ValidationError(_("El archivo no puede exceder 20MB"))

    # Acciones de estado (sin elementos deprecados)
    def action_submit_review(self):
        self.write({'state': 'review'})
        self.message_post(body=_("Enviado a revisión"))

    def action_validate(self):
        self.write({'state': 'validated'})
        self.message_post(body=_("Manuscrito validado"))

    def action_archive(self):
        self.write({'state': 'archived'})
        self.message_post(body=_("Manuscrito archivado"))

class Tag(models.Model):
    _name = 'manus.tag'
    _description = 'Etiqueta de Clasificación'
    
    name = fields.Char(required=True, translate=True)
    color = fields.Integer(string="Color")
    active = fields.Boolean(default=True)

class Category(models.Model):
    _name = 'manus.category'
    _description = 'Categoría de Manuscrito'
    
    name = fields.Char(required=True, translate=True)
    parent_id = fields.Many2one('manus.category', string="Categoría Padre")
    child_ids = fields.One2many('manus.category', 'parent_id', string="Subcategorías")
