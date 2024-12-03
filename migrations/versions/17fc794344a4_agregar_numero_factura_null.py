"""agregar numero factura null 

Revision ID: 17fc794344a4
Revises: 96df25e775b9
Create Date: 2024-07-29 13:03:28.662702

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17fc794344a4'
down_revision = '96df25e775b9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('factura', schema=None) as batch_op:
        batch_op.create_unique_constraint(None, ['numero_pedido'])

    with op.batch_alter_table('factura_producto', schema=None) as batch_op:
        batch_op.alter_column('factura_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('producto_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('factura_producto', schema=None) as batch_op:
        batch_op.alter_column('producto_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('factura_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    with op.batch_alter_table('factura', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')

    # ### end Alembic commands ###
