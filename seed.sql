-- Seed data for testing RLS policies
-- Adjust UUIDs and details as necessary for your test environment

-- Ensure the test users exist in auth.users
-- Note: These users are created by the 0001 migration's helper function if run.
-- This script assumes those users might exist or ensures they do.
-- Using fixed UUIDs for predictability in tests.

INSERT INTO auth.users (id, email, role, created_at) VALUES
('00000000-0000-0000-0000-000000000001', 'lawyer@example.com', 'lawyer', now())
ON CONFLICT (id) DO NOTHING;

-- Use the existing paralegal@example.com as paralegal_a for simplicity if desired,
-- or create distinct ones. Let's create distinct ones for clarity.
INSERT INTO auth.users (id, email, role, created_at) VALUES
('00000000-0000-0000-0000-000000000002', 'paralegal_a@example.com', 'paralegal', now())
ON CONFLICT (id) DO NOTHING;

INSERT INTO auth.users (id, email, role, created_at) VALUES
('00000000-0000-0000-0000-000000000003', 'paralegal_b@example.com', 'paralegal', now())
ON CONFLICT (id) DO NOTHING;

-- Client user for testing client access
INSERT INTO auth.users (id, email, role, created_at) VALUES
('00000000-0000-0000-0000-000000000004', 'client_a@example.com', 'client', now())
ON CONFLICT (id) DO NOTHING;

-- Client associated with client_a@example.com
INSERT INTO client (id, full_name, email, created_at) VALUES
(1, 'Client A', 'client_a@example.com', now())
ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email, full_name = EXCLUDED.full_name;

-- Client associated with no specific user in auth.users (for general lawyer/paralegal access testing)
INSERT INTO client (id, full_name, email, created_at) VALUES
(2, 'Client B', 'client_b@example.com', now())
ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email, full_name = EXCLUDED.full_name;

-- Incident for Client A
INSERT INTO incident (id, client_id, date, location, created_at) VALUES
(101, 1, '2024-01-15', 'Location A', now())
ON CONFLICT (id) DO UPDATE SET client_id = EXCLUDED.client_id, date = EXCLUDED.date;

-- Incident for Client B
INSERT INTO incident (id, client_id, date, location, created_at) VALUES
(102, 2, '2024-02-20', 'Location B', now())
ON CONFLICT (id) DO UPDATE SET client_id = EXCLUDED.client_id, date = EXCLUDED.date;

-- Task for Incident 101 (Client A), assigned to paralegal_a
INSERT INTO task (id, incident_id, type, status, assignee_email, created_at) VALUES
(1001, 101, 'Task Type A1', 'pending', 'paralegal_a@example.com', now())
ON CONFLICT (id) DO UPDATE SET incident_id = EXCLUDED.incident_id, assignee_email = EXCLUDED.assignee_email;

-- Task for Incident 102 (Client B), assigned to paralegal_b
INSERT INTO task (id, incident_id, type, status, assignee_email, created_at) VALUES
(1002, 102, 'Task Type B1', 'pending', 'paralegal_b@example.com', now())
ON CONFLICT (id) DO UPDATE SET incident_id = EXCLUDED.incident_id, assignee_email = EXCLUDED.assignee_email;

-- Task for Incident 102 (Client B), assigned to the lawyer (to test lawyer access)
INSERT INTO task (id, incident_id, type, status, assignee_email, created_at) VALUES
(1003, 102, 'Task Type L1', 'pending', 'lawyer@example.com', now())
ON CONFLICT (id) DO UPDATE SET incident_id = EXCLUDED.incident_id, assignee_email = EXCLUDED.assignee_email;

-- Insurance for Incident 101 (Client A)
INSERT INTO insurance (id, incident_id, carrier_name, is_client_side, created_at) VALUES
(2001, 101, 'Carrier A', true, now())
ON CONFLICT (id) DO UPDATE SET incident_id = EXCLUDED.incident_id;

-- Provider for Incident 102 (Client B)
INSERT INTO provider (id, incident_id, name, created_at) VALUES
(3001, 102, 'Provider B', now())
ON CONFLICT (id) DO UPDATE SET incident_id = EXCLUDED.incident_id;

-- Doc for Incident 101 (Client A)
INSERT INTO doc (id, incident_id, type, url, status, created_at) VALUES
(4001, 101, 'Doc Type A', 'http://example.com/doc_a', 'pending', now())
ON CONFLICT (id) DO UPDATE SET incident_id = EXCLUDED.incident_id;

-- Sequence updates (optional, good practice if using fixed IDs)
-- SELECT setval('client_id_seq', (SELECT MAX(id) FROM client));
-- SELECT setval('incident_id_seq', (SELECT MAX(id) FROM incident));
-- SELECT setval('task_id_seq', (SELECT MAX(id) FROM task));
-- SELECT setval('insurance_id_seq', (SELECT MAX(id) FROM insurance));
-- SELECT setval('provider_id_seq', (SELECT MAX(id) FROM provider));
-- SELECT setval('doc_id_seq', (SELECT MAX(id) FROM doc));
