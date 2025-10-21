"""Initial migration - create tables"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])
    
    # Invoice number sequence table
    op.create_table(
        'invoice_number_sequence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('prefix', sa.String(10), nullable=False),
        sa.Column('current_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('prefix'),
    )
    
    # Invoices table
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False),
        sa.Column('issue_date', sa.DateTime(), nullable=False),
        sa.Column('delivery_date_start', sa.DateTime()),
        sa.Column('delivery_date_end', sa.DateTime()),
        
        # Seller
        sa.Column('seller_name', sa.String(255), nullable=False),
        sa.Column('seller_street', sa.String(255), nullable=False),
        sa.Column('seller_zip', sa.String(20), nullable=False),
        sa.Column('seller_city', sa.String(100), nullable=False),
        sa.Column('seller_country', sa.String(2), nullable=False),
        sa.Column('seller_tax_id', sa.String(50), nullable=False),
        sa.Column('seller_email', sa.String(255)),
        sa.Column('seller_phone', sa.String(50)),
        
        # Buyer
        sa.Column('buyer_name', sa.String(255), nullable=False),
        sa.Column('buyer_street', sa.String(255), nullable=False),
        sa.Column('buyer_zip', sa.String(20), nullable=False),
        sa.Column('buyer_city', sa.String(100), nullable=False),
        sa.Column('buyer_country', sa.String(2), nullable=False),
        sa.Column('buyer_tax_id', sa.String(50)),
        sa.Column('buyer_email', sa.String(255)),
        sa.Column('buyer_phone', sa.String(50)),
        
        # Totals
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('net_total', sa.Float(), nullable=False),
        sa.Column('tax_total', sa.Float(), nullable=False),
        sa.Column('gross_total', sa.Float(), nullable=False),
        
        # Tax
        sa.Column('tax_exempt', sa.Boolean(), default=False),
        sa.Column('tax_exempt_reason', sa.String(255)),
        
        # Notes
        sa.Column('notes', sa.Text()),
        sa.Column('payment_terms', sa.String(255)),
        
        # Files
        sa.Column('zugferd_xml_path', sa.String(500)),
        sa.Column('pdfa3_path', sa.String(500), nullable=False),
        sa.Column('pdf_hash', sa.String(64), nullable=False),
        sa.Column('tsa_token', sa.JSON()),
        sa.Column('signature_info', sa.JSON()),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_immutable', sa.Boolean(), default=False),
        
        # Audit
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_number'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
    )
    op.create_index('ix_invoices_invoice_number', 'invoices', ['invoice_number'])
    op.create_index('idx_invoice_date', 'invoices', ['issue_date'])
    op.create_index('idx_invoice_status', 'invoices', ['status'])
    
    # Invoice line items table
    op.create_table(
        'invoice_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('invoice_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(20), nullable=False),
        sa.Column('unit_price', sa.Float(), nullable=False),
        sa.Column('line_net', sa.Float(), nullable=False),
        sa.Column('tax_rate', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Float(), nullable=False),
        sa.Column('line_gross', sa.Float(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('invoice_id', 'position', name='uq_invoice_position'),
    )
    
    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer()),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('details', sa.JSON()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_timestamp', 'audit_logs', ['timestamp'])


def downgrade():
    op.drop_table('audit_logs')
    op.drop_table('invoice_line_items')
    op.drop_table('invoices')
    op.drop_table('invoice_number_sequence')
    op.drop_table('users')
