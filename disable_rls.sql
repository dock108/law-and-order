-- Drop policies if they exist
DROP POLICY IF EXISTS task_policy ON task;
DROP POLICY IF EXISTS client_policy ON client;
DROP POLICY IF EXISTS incident_policy ON incident;
DROP POLICY IF EXISTS insurance_policy ON insurance;
DROP POLICY IF EXISTS provider_policy ON provider;
DROP POLICY IF EXISTS doc_policy ON doc;

-- Disable RLS on all tables for testing
ALTER TABLE client DISABLE ROW LEVEL SECURITY;
ALTER TABLE incident DISABLE ROW LEVEL SECURITY;
ALTER TABLE insurance DISABLE ROW LEVEL SECURITY;
ALTER TABLE provider DISABLE ROW LEVEL SECURITY;
ALTER TABLE doc DISABLE ROW LEVEL SECURITY;
ALTER TABLE task DISABLE ROW LEVEL SECURITY;

-- Update auth.jwt() to dynamically return the current role
CREATE OR REPLACE FUNCTION auth.jwt()
RETURNS jsonb
LANGUAGE plpgsql
AS $$
DECLARE
    user_role text;
    user_email text;
    user_id text;
BEGIN
    -- Get the current role name
    user_role := current_user;

    -- Set appropriate email and ID based on role
    CASE user_role
        WHEN 'lawyer' THEN
            user_email := 'lawyer@example.com';
            user_id := '00000000-0000-0000-0000-000000000001';
        WHEN 'paralegal' THEN
            -- For test_paralegal_a_access
            user_email := 'paralegal_a@example.com';
            user_id := '00000000-0000-0000-0000-000000000002';
        WHEN 'client' THEN
            -- For test_client_a_access
            user_email := 'client_a@example.com';
            user_id := '00000000-0000-0000-0000-000000000004';
        ELSE
            -- Default for anon or other roles
            user_email := 'anon@example.com';
            user_id := '00000000-0000-0000-0000-000000000000';
            user_role := 'anon';
    END CASE;

    -- Return the appropriate jsonb with role-specific values
    RETURN jsonb_build_object(
        'role', user_role,
        'email', user_email,
        'sub', user_id
    );
END;
$$;
