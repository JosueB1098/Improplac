"""Agregado campo en_oferta al modelo Producto

Revision ID: c84cbfaa89c3
Revises: ff1f239b611f
Create Date: 2024-12-02 20:13:01.187514

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c84cbfaa89c3'
down_revision = 'ff1f239b611f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.add_column(sa.Column('en_oferta', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('producto', schema=None) as batch_op:
        batch_op.drop_column('en_oferta')

    # ### end Alembic commands ###