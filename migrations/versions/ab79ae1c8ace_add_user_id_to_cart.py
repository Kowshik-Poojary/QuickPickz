"""Add user_id to cart

Revision ID: ab79ae1c8ace
Revises: e3402a090c6a
Create Date: 2025-03-30 22:41:11.079996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab79ae1c8ace'
down_revision = 'e3402a090c6a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('cart_item', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key(
            'fk_cart_item_user_id',  # 👈 give it a name
            'user',
            ['user_id'],
            ['id']
        )

def downgrade():
    with op.batch_alter_table('cart_item', schema=None) as batch_op:
        batch_op.drop_constraint('fk_cart_item_user_id', type_='foreignkey')  # 👈 use the same name
        batch_op.drop_column('user_id')


    # ### end Alembic commands ###
