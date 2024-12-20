"""cat

Revision ID: 82a6f2e12fac
Revises: 1deaeb5264cc
Create Date: 2024-05-20 23:49:14.241205

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82a6f2e12fac'
down_revision = '1deaeb5264cc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.drop_constraint('producto_categoriaId_fkey', type_='foreignkey')
        batch_op.drop_column('categoriaId')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.add_column(sa.Column('categoriaId', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.create_foreign_key('producto_categoriaId_fkey', 'categoria', ['categoriaId'], ['id'])

    # ### end Alembic commands ###
