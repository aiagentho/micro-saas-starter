-- Users table example
CREATE TABLE users (
  id uuid PRIMARY KEY,
  email text UNIQUE NOT NULL,
  credits int DEFAULT 0
);

-- Usage logs for tracking
CREATE TABLE usage_logs (
  id serial PRIMARY KEY,
  user_id uuid REFERENCES users(id),
  action text NOT NULL,
  details text,
  created_at timestamptz DEFAULT now()
);
