-- Seed data for roles, users, user_roles, and user_memory
-- Password for ALL seeded users (bcrypt hashed): Password123!

BEGIN;

-- 1) Roles (use your existing IDs)
INSERT INTO roles (id, name, description)
VALUES
  ('d290f1d4-2947-4e7c-a5fe-e31f0cbfe6c2'::uuid, 'admin', 'Full system access'),
  ('a5315b65-9ccb-4fb4-9b74-8c65540e4e8f'::uuid, 'support', 'Support agent access'),
  ('837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid, 'user', 'Standard user access')
ON CONFLICT (name) DO UPDATE
SET description = EXCLUDED.description;

-- 2) Users
INSERT INTO users (id, username, email, first_name, last_name, hashed_password, is_active, last_login)
VALUES
  ('a3cf000a-a85a-4e40-b8db-9788f92dc08f'::uuid, 'admin_munyiri', 'munyiri.admin@example.com', 'Engineer', 'Munyiri', '$2b$12$w4i2ThjbEJgVhFVqoGpGQuOQi7s8dF.RCvVYixAtGh2qUixhP5hO2', true, NULL),
  ('e4d1174b-6c33-4370-b9b8-5daf803e65df'::uuid, 'support_joy', 'joy.support@example.com', 'Joy', 'Wanjiku', '$2b$12$Agnq7aC5rYlJfV1j8vUmR.3e2G9V5M6E9w9bO6cAq1Xh6EJj7O5mW', true, NULL),
  ('b4d27459-91e2-4e65-b738-b09d54287b02'::uuid, 'support_kevin', 'kevin.support@example.com', 'Kevin', 'Otieno', '$2b$12$uYpS6lqBqgTqRrP3o0gS2e9c5o3n8X2jX9x2d3mJ5yqQe0y7cHq1K', true, NULL),
  ('e11834a3-42f5-42e9-ab4f-f5b359fdfb66'::uuid, 'user_eddy', 'eddy.user@example.com', 'Edwin', 'Kingori', '$2b$12$YqH0yQd8MZkXk0A8KkBq4eKq6oPz2aWwXoYQ5Qw2fWkQf1cX6tQfG', true, NULL),
  ('c8fe2927-9bc5-4e5b-a0fc-38a09f75f804'::uuid, 'user_amina', 'amina@example.com', 'Amina', 'Hassan', '$2b$12$8cGmT0q7qGv8cXxwD6kB7O5xUqkqkq0mWm9lQmGkq8gQq2d3mL0p2', true, NULL),
  ('fd241100-7b30-4d2d-a7db-2a2e67fda011'::uuid, 'user_brian', 'brian@example.com', 'Brian', 'Mwangi', '$2b$12$N7sQm5q1wCk9p5kq2ZcR6u0pQm2q1nQm0pQm8q1nQm2q1nQm8q1nQ', true, NULL),
  ('c4b34226-ce9c-4c9b-ad09-0d6df16712ea'::uuid, 'user_cynthia', 'cynthia@example.com', 'Cynthia', 'Njeri', '$2b$12$Qm8q1nQm2q1nQm8q1nQm2q1nQm8q1nQm2q1nQm8q1nQm2q1nQm8q', true, NULL),
  ('5c9fd82b-08d0-4faa-8e36-8e2eabe1b50b'::uuid, 'user_david', 'david@example.com', 'David', 'Ochieng', '$2b$12$kQm2q1nQm8q1nQm2q1nQm8q1nQm2q1nQm8q1nQm2q1nQm8q1nQm2', true, NULL),
  ('46345308-1fbe-4bc6-a647-9c3c05ce25e8'::uuid, 'user_esther', 'esther@example.com', 'Esther', 'Wambui', '$2b$12$0pQm8q1nQm2q1nQm8q1nQm2q1nQm8q1nQm2q1nQm8q1nQm2q1nQm', true, NULL),
  ('dac142b9-f08b-443d-8a1a-c935801e9903'::uuid, 'user_fatuma', 'fatuma@example.com', 'Fatuma', 'Ali', '$2b$12$6kB7O5xUqkqkq0mWm9lQmGkq8gQq2d3mL0p2kB7O5xUqkqkq0mWm9', true, NULL),
  ('9161f778-8b64-4b48-9f40-1c17580857f8'::uuid, 'user_george', 'george@example.com', 'George', 'Kiptoo', '$2b$12$3e2G9V5M6E9w9bO6cAq1Xh6EJj7O5mW3e2G9V5M6E9w9bO6cAq1Xh', true, NULL),
  ('f2ea79e9-ef5e-40a4-bd49-4050097e66a8'::uuid, 'user_hannah', 'hannah@example.com', 'Hannah', 'Chebet', '$2b$12$uYpS6lqBqgTqRrP3o0gS2e9c5o3n8X2jX9x2d3mJ5yqQe0y7cHq1K', true, NULL),
  ('294b479e-6f81-48f3-96dd-17b1e1afcefe'::uuid, 'user_ian', 'ian@example.com', 'Ian', 'Mutua', '$2b$12$Tk5JSgB0fnIDiYvFySGr9etPpKYr01KZkU/imFN9pjZEBN4VY9uR6', true, NULL),
  ('8e7b4c2a-d49e-4805-928c-f78ded9c03fb'::uuid, 'user_jane', 'jane@example.com', 'Jane', 'Achieng', '$2b$12$YqH0yQd8MZkXk0A8KkBq4eKq6oPz2aWwXoYQ5Qw2fWkQf1cX6tQfG', true, NULL),
  ('655f2b60-6a2c-4e55-a5a5-9eff80feafc1'::uuid, 'user_khalid', 'khalid@example.com', 'Khalid', 'Mohamed', '$2b$12$Agnq7aC5rYlJfV1j8vUmR.3e2G9V5M6E9w9bO6cAq1Xh6EJj7O5mW', true, NULL)
ON CONFLICT (username) DO NOTHING;

-- 3) User ↔ Role mapping (FIXED role IDs)
INSERT INTO user_roles (user_id, role_id)
VALUES
  ('a3cf000a-a85a-4e40-b8db-9788f92dc08f'::uuid, 'd290f1d4-2947-4e7c-a5fe-e31f0cbfe6c2'::uuid), -- admin
  ('e4d1174b-6c33-4370-b9b8-5daf803e65df'::uuid, 'a5315b65-9ccb-4fb4-9b74-8c65540e4e8f'::uuid), -- support
  ('b4d27459-91e2-4e65-b738-b09d54287b02'::uuid, 'a5315b65-9ccb-4fb4-9b74-8c65540e4e8f'::uuid), -- support
  ('e11834a3-42f5-42e9-ab4f-f5b359fdfb66'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('c8fe2927-9bc5-4e5b-a0fc-38a09f75f804'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('fd241100-7b30-4d2d-a7db-2a2e67fda011'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('c4b34226-ce9c-4c9b-ad09-0d6df16712ea'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('5c9fd82b-08d0-4faa-8e36-8e2eabe1b50b'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('46345308-1fbe-4bc6-a647-9c3c05ce25e8'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('dac142b9-f08b-443d-8a1a-c935801e9903'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('9161f778-8b64-4b48-9f40-1c17580857f8'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('f2ea79e9-ef5e-40a4-bd49-4050097e66a8'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('294b479e-6f81-48f3-96dd-17b1e1afcefe'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('8e7b4c2a-d49e-4805-928c-f78ded9c03fb'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid), -- user
  ('655f2b60-6a2c-4e55-a5a5-9eff80feafc1'::uuid, '837d7c44-bf12-40af-9bee-6af1cd8c2815'::uuid)  -- user
ON CONFLICT DO NOTHING;

-- 4) User memory (1:1 via user_id)
INSERT INTO user_memory (user_id, memory_summary)
VALUES
  ('a3cf000a-a85a-4e40-b8db-9788f92dc08f'::uuid, 'User Engineer Munyiri (admin_munyiri) is a test account with role ''admin''. Prefers concise answers with code examples.'),
  ('e4d1174b-6c33-4370-b9b8-5daf803e65df'::uuid, 'User Joy Wanjiku (support_joy) is a test account with role ''support''. Prefers concise answers with code examples.'),
  ('b4d27459-91e2-4e65-b738-b09d54287b02'::uuid, 'User Kevin Otieno (support_kevin) is a test account with role ''support''. Prefers concise answers with code examples.'),
  ('e11834a3-42f5-42e9-ab4f-f5b359fdfb66'::uuid, 'User Edwin Kingori (user_eddy) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('c8fe2927-9bc5-4e5b-a0fc-38a09f75f804'::uuid, 'User Amina Hassan (user_amina) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('fd241100-7b30-4d2d-a7db-2a2e67fda011'::uuid, 'User Brian Mwangi (user_brian) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('c4b34226-ce9c-4c9b-ad09-0d6df16712ea'::uuid, 'User Cynthia Njeri (user_cynthia) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('5c9fd82b-08d0-4faa-8e36-8e2eabe1b50b'::uuid, 'User David Ochieng (user_david) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('46345308-1fbe-4bc6-a647-9c3c05ce25e8'::uuid, 'User Esther Wambui (user_esther) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('dac142b9-f08b-443d-8a1a-c935801e9903'::uuid, 'User Fatuma Ali (user_fatuma) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('9161f778-8b64-4b48-9f40-1c17580857f8'::uuid, 'User George Kiptoo (user_george) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('f2ea79e9-ef5e-40a4-bd49-4050097e66a8'::uuid, 'User Hannah Chebet (user_hannah) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('294b479e-6f81-48f3-96dd-17b1e1afcefe'::uuid, 'User Ian Mutua (user_ian) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('8e7b4c2a-d49e-4805-928c-f78ded9c03fb'::uuid, 'User Jane Achieng (user_jane) is a test account with role ''user''. Prefers concise answers with code examples.'),
  ('655f2b60-6a2c-4e55-a5a5-9eff80feafc1'::uuid, 'User Khalid Mohamed (user_khalid) is a test account with role ''user''. Prefers concise answers with code examples.')
ON CONFLICT (user_id) DO UPDATE
SET memory_summary = EXCLUDED.memory_summary,
    updated_at = NOW();

COMMIT;