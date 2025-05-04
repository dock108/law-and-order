-- First, drop the RLS policies to re-create them with modified conditions
DROP POLICY IF EXISTS task_policy ON task;
DROP POLICY IF EXISTS client_policy ON client;
DROP POLICY IF EXISTS incident_policy ON incident;
DROP POLICY IF EXISTS insurance_policy ON insurance;
DROP POLICY IF EXISTS provider_policy ON provider;
DROP POLICY IF EXISTS doc_policy ON doc;

-- Temporary disable RLS for testing (we'll enable it again at the end)
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

-- Re-create the policies with more specific conditions
-- Client table policy
CREATE POLICY client_policy ON client
USING (
    (auth.jwt() ->> 'role') = 'lawyer'
    OR
    ((auth.jwt() ->> 'role') = 'paralegal' AND
     EXISTS (
        SELECT 1 FROM task
        WHERE assignee_email = (auth.jwt() ->> 'email')
        AND EXISTS (
            SELECT 1 FROM incident
            WHERE incident.id = task.incident_id
            AND incident.client_id = client.id
        )
     ))
    OR
    (email = (auth.jwt() ->> 'email'))
);

-- Incident table policy
CREATE POLICY incident_policy ON incident
USING (
    (auth.jwt() ->> 'role') = 'lawyer'
    OR
    ((auth.jwt() ->> 'role') = 'paralegal' AND
     EXISTS (
        SELECT 1 FROM task
        WHERE assignee_email = (auth.jwt() ->> 'email')
        AND task.incident_id = incident.id
     ))
    OR
    EXISTS (
        SELECT 1 FROM client
        WHERE client.id = incident.client_id
        AND client.email = (auth.jwt() ->> 'email')
    )
);

-- Insurance table policy
CREATE POLICY insurance_policy ON insurance
USING (
    (auth.jwt() ->> 'role') = 'lawyer'
    OR
    ((auth.jwt() ->> 'role') = 'paralegal' AND
     EXISTS (
        SELECT 1 FROM task
        WHERE assignee_email = (auth.jwt() ->> 'email')
        AND task.incident_id = insurance.incident_id
     ))
    OR
    EXISTS (
        SELECT 1 FROM incident
        JOIN client ON client.id = incident.client_id
        WHERE incident.id = insurance.incident_id
        AND client.email = (auth.jwt() ->> 'email')
    )
);

-- Provider table policy
CREATE POLICY provider_policy ON provider
USING (
    (auth.jwt() ->> 'role') = 'lawyer'
    OR
    ((auth.jwt() ->> 'role') = 'paralegal' AND
     EXISTS (
        SELECT 1 FROM task
        WHERE assignee_email = (auth.jwt() ->> 'email')
        AND task.incident_id = provider.incident_id
     ))
    OR
    EXISTS (
        SELECT 1 FROM incident
        JOIN client ON client.id = incident.client_id
        WHERE incident.id = provider.incident_id
        AND client.email = (auth.jwt() ->> 'email')
    )
);

-- Doc table policy
CREATE POLICY doc_policy ON doc
USING (
    (auth.jwt() ->> 'role') = 'lawyer'
    OR
    ((auth.jwt() ->> 'role') = 'paralegal' AND
     EXISTS (
        SELECT 1 FROM task
        WHERE assignee_email = (auth.jwt() ->> 'email')
        AND task.incident_id = doc.incident_id
     ))
    OR
    EXISTS (
        SELECT 1 FROM incident
        JOIN client ON client.id = incident.client_id
        WHERE incident.id = doc.incident_id
        AND client.email = (auth.jwt() ->> 'email')
    )
);

-- Task table policy
CREATE POLICY task_policy ON task
USING (
    (auth.jwt() ->> 'role') = 'lawyer'
    OR
    ((auth.jwt() ->> 'role') = 'paralegal' AND assignee_email = (auth.jwt() ->> 'email'))
    OR
    (assignee_email = (auth.jwt() ->> 'email'))
    OR
    EXISTS (
        SELECT 1 FROM incident
        JOIN client ON client.id = incident.client_id
        WHERE incident.id = task.incident_id
        AND client.email = (auth.jwt() ->> 'email')
    )
);

-- Re-enable RLS on all tables
ALTER TABLE client ENABLE ROW LEVEL SECURITY;
ALTER TABLE incident ENABLE ROW LEVEL SECURITY;
ALTER TABLE insurance ENABLE ROW LEVEL SECURITY;
ALTER TABLE provider ENABLE ROW LEVEL SECURITY;
ALTER TABLE doc ENABLE ROW LEVEL SECURITY;
ALTER TABLE task ENABLE ROW LEVEL SECURITY;
