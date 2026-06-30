-- Fail the pipeline if core analytics assumptions are violated.
CREATE TEMP TRIGGER validate_assignment_variant
BEFORE INSERT ON assignments
WHEN NEW.variant NOT IN ('control', 'treatment')
BEGIN SELECT RAISE(ABORT, 'invalid experiment variant'); END;

CREATE INDEX idx_events_user_name ON events(user_id, event_name);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_assignments_experiment ON assignments(experiment_id, variant);

