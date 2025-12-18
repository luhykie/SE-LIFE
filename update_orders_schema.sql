-- Update existing orders to Pending status
UPDATE purchase_orders SET status = 'Pending' WHERE status = 'Completed';

-- Alter the table to change the default value
ALTER TABLE purchase_orders MODIFY COLUMN status VARCHAR(50) DEFAULT 'Pending';
