"""Initial migration with enhanced user models

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('subscription_plan', sa.String(), nullable=True),
        sa.Column('subscription_expires', sa.DateTime(), nullable=True),
        sa.Column('monthly_sms_limit', sa.Integer(), nullable=True),
        sa.Column('monthly_sms_used', sa.Integer(), nullable=True),
        sa.Column('monthly_voice_minutes_limit', sa.Integer(), nullable=True),
        sa.Column('monthly_voice_minutes_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('api_calls_today', sa.Integer(), nullable=True),
        sa.Column('api_rate_limit', sa.Integer(), nullable=True),
        sa.Column('email_verification_token', sa.String(), nullable=True),
        sa.Column('email_verification_expires', sa.DateTime(), nullable=True),
        sa.Column('password_reset_token', sa.String(), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_active', 'users', ['is_active'], unique=False)
    op.create_index('idx_user_email', 'users', ['email'], unique=False)
    op.create_index('idx_user_username', 'users', ['username'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('refresh_token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_session_refresh_token', 'sessions', ['refresh_token'], unique=False)
    op.create_index('idx_session_user_active', 'sessions', ['user_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_sessions_refresh_token'), 'sessions', ['refresh_token'], unique=True)

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=True),
        sa.Column('requests_today', sa.Integer(), nullable=True),
        sa.Column('last_request_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_apikey_hash', 'api_keys', ['key_hash'], unique=False)
    op.create_index('idx_apikey_user_active', 'api_keys', ['user_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)

    # Create phone_numbers table
    op.create_table('phone_numbers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=False),
        sa.Column('country_code', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('owner_id', sa.String(), nullable=True),
        sa.Column('monthly_cost', sa.String(), nullable=True),
        sa.Column('sms_cost_per_message', sa.String(), nullable=True),
        sa.Column('voice_cost_per_minute', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('purchased_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('total_sms_sent', sa.Integer(), nullable=True),
        sa.Column('total_sms_received', sa.Integer(), nullable=True),
        sa.Column('total_voice_minutes', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_phone_numbers_phone_number'), 'phone_numbers', ['phone_number'], unique=True)

    # Create conversations table
    op.create_table('conversations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('is_group', sa.Boolean(), nullable=True),
        sa.Column('external_number', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create conversation_participants table
    op.create_table('conversation_participants',
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('conversation_id', sa.String(), nullable=True),
        sa.Column('sender_id', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=True),
        sa.Column('external_message_id', sa.String(), nullable=True),
        sa.Column('from_number', sa.String(), nullable=True),
        sa.Column('to_number', sa.String(), nullable=True),
        sa.Column('is_delivered', sa.Boolean(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('delivery_status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create verification_requests table
    op.create_table('verification_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('textverified_id', sa.String(), nullable=True),
        sa.Column('service_name', sa.String(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('verification_code', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_verification_status', 'verification_requests', ['status'], unique=False)
    op.create_index('idx_verification_textverified_id', 'verification_requests', ['textverified_id'], unique=False)
    op.create_index('idx_verification_user', 'verification_requests', ['user_id'], unique=False)
    op.create_index(op.f('ix_verification_requests_textverified_id'), 'verification_requests', ['textverified_id'], unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_verification_requests_textverified_id'), table_name='verification_requests')
    op.drop_index('idx_verification_user', table_name='verification_requests')
    op.drop_index('idx_verification_textverified_id', table_name='verification_requests')
    op.drop_index('idx_verification_status', table_name='verification_requests')
    op.drop_table('verification_requests')
    op.drop_table('messages')
    op.drop_table('conversation_participants')
    op.drop_table('conversations')
    op.drop_index(op.f('ix_phone_numbers_phone_number'), table_name='phone_numbers')
    op.drop_table('phone_numbers')
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_index('idx_apikey_user_active', table_name='api_keys')
    op.drop_index('idx_apikey_hash', table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index(op.f('ix_sessions_refresh_token'), table_name='sessions')
    op.drop_index('idx_session_user_active', table_name='sessions')
    op.drop_index('idx_session_refresh_token', table_name='sessions')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index('idx_user_username', table_name='users')
    op.drop_index('idx_user_email', table_name='users')
    op.drop_index('idx_user_active', table_name='users')
    op.drop_table('users')