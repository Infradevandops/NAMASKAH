"""Add enhanced conversation and message models

Revision ID: 003_enhanced_conversations
Revises: 002_user_management_v1_1
Create Date: 2024-01-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_enhanced_conversations'
down_revision = '002_user_management_v1_1'
branch_labels = None
depends_on = None

def upgrade():
    # Create conversation_participants association table
    op.create_table('conversation_participants',
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('last_read_at', sa.DateTime(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('conversation_id', 'user_id')
    )
    
    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('is_group', sa.Boolean(), nullable=True),
        sa.Column('external_number', sa.String(length=20), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ARCHIVED', 'DELETED', 'BLOCKED', name='conversationstatus'), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=True),
        sa.Column('is_muted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for conversations
    op.create_index('idx_conversation_created_by', 'conversations', ['created_by'], unique=False)
    op.create_index('idx_conversation_external_number', 'conversations', ['external_number'], unique=False)
    op.create_index('idx_conversation_last_message', 'conversations', ['last_message_at'], unique=False)
    op.create_index('idx_conversation_status', 'conversations', ['status'], unique=False)
    
    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=False),
        sa.Column('sender_id', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.Enum('CHAT', 'SMS_OUTBOUND', 'SMS_INBOUND', 'SYSTEM', 'INTERNAL', name='messagetype'), nullable=True),
        sa.Column('external_message_id', sa.String(length=255), nullable=True),
        sa.Column('from_number', sa.String(length=20), nullable=True),
        sa.Column('to_number', sa.String(length=20), nullable=True),
        sa.Column('is_delivered', sa.Boolean(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('delivery_status', sa.String(length=50), nullable=True),
        sa.Column('is_edited', sa.Boolean(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for messages
    op.create_index('idx_message_conversation', 'messages', ['conversation_id'], unique=False)
    op.create_index('idx_message_created_at', 'messages', ['created_at'], unique=False)
    op.create_index('idx_message_delivery_status', 'messages', ['is_delivered', 'is_read'], unique=False)
    op.create_index('idx_message_sender', 'messages', ['sender_id'], unique=False)
    op.create_index('idx_message_type', 'messages', ['message_type'], unique=False)

def downgrade():
    # Drop indexes
    op.drop_index('idx_message_type', table_name='messages')
    op.drop_index('idx_message_sender', table_name='messages')
    op.drop_index('idx_message_delivery_status', table_name='messages')
    op.drop_index('idx_message_created_at', table_name='messages')
    op.drop_index('idx_message_conversation', table_name='messages')
    
    # Drop messages table
    op.drop_table('messages')
    
    # Drop conversation indexes
    op.drop_index('idx_conversation_status', table_name='conversations')
    op.drop_index('idx_conversation_last_message', table_name='conversations')
    op.drop_index('idx_conversation_external_number', table_name='conversations')
    op.drop_index('idx_conversation_created_by', table_name='conversations')
    
    # Drop conversations table
    op.drop_table('conversations')
    
    # Drop association table
    op.drop_table('conversation_participants')
    
    # Drop enums (PostgreSQL only)
    # Note: SQLite doesn't have native enums, so this is only for PostgreSQL
    try:
        op.execute("DROP TYPE IF EXISTS conversationstatus")
        op.execute("DROP TYPE IF EXISTS messagetype")
    except:
        pass  # Ignore errors for SQLite