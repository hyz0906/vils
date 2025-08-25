-- Database initialization script for VILS
-- This script sets up the initial database configuration

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
        CREATE TYPE task_status AS ENUM ('active', 'paused', 'completed', 'failed');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'build_status') THEN
        CREATE TYPE build_status AS ENUM ('pending', 'running', 'success', 'failed', 'cancelled');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feedback_type') THEN
        CREATE TYPE feedback_type AS ENUM ('working', 'broken', 'inconclusive');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'repository_type') THEN
        CREATE TYPE repository_type AS ENUM ('gerrit', 'repo', 'codehub', 'github', 'gitlab');
    END IF;
END
$$;

-- Create indexes for better performance (will be created with tables via Alembic)
-- This is just a placeholder for initial setup