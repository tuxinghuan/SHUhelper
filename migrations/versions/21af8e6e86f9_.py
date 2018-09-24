"""empty message

Revision ID: 21af8e6e86f9
Revises: 56fe87ab3bb1
Create Date: 2018-05-08 13:30:15.844474

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '21af8e6e86f9'
down_revision = '56fe87ab3bb1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('room_booking',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('room_id', sa.Integer(), nullable=True),
    sa.Column('create_time', sa.DateTime(), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('end_time', sa.DateTime(), nullable=True),
    sa.Column('remark', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['room_id'], ['room.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('room_order')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('room_order',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('room_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(precision=6), autoincrement=False, nullable=True),
    sa.Column('remark', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('date', postgresql.TIMESTAMP(precision=6), autoincrement=False, nullable=True),
    sa.Column('end_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('start_time', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['room_id'], ['room.id'], name='order_room_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='order_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='order_pkey')
    )
    op.drop_table('room_booking')
    # ### end Alembic commands ###