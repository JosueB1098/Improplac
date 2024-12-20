"""Añadir relación entre Categoria y Producto

Revision ID: 2e8e50d6bc6c
Revises: 03c49e9f4198
Create Date: 2024-07-16 02:15:49.574535

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2e8e50d6bc6c'
down_revision = '03c49e9f4198'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.add_column(sa.Column('categoria_id', sa.Integer(), nullable=True))
        batch_op.drop_index('ix_producto_categoria')
        batch_op.create_foreign_key(None, 'categoria', ['categoria_id'], ['id'])
        batch_op.drop_column('imagen')
        batch_op.drop_column('categoria')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.add_column(sa.Column('categoria', sa.VARCHAR(length=64), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('imagen', postgresql.BYTEA(), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_index('ix_producto_categoria', ['categoria'], unique=False)
        batch_op.drop_column('categoria_id')

    # ### end Alembic commands ###
