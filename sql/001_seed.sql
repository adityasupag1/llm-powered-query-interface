CREATE TABLE customers (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE products (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    stock_quantity INTEGER NOT NULL CHECK (stock_quantity >= 0)
);

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL REFERENCES customers(id),
    status TEXT NOT NULL CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')),
    ordered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0)
);

INSERT INTO customers (name, email, state, created_at) VALUES
('Aarav Sharma', 'aarav@example.com', 'Bihar', NOW() - INTERVAL '150 days'),
('Meera Verma', 'meera@example.com', 'Delhi', NOW() - INTERVAL '120 days'),
('Kabir Singh', 'kabir@example.com', 'Bihar', NOW() - INTERVAL '90 days'),
('Ananya Gupta', 'ananya@example.com', 'Maharashtra', NOW() - INTERVAL '60 days'),
('Rohan Das', 'rohan@example.com', 'West Bengal', NOW() - INTERVAL '30 days');

INSERT INTO products (name, category, unit_price, stock_quantity) VALUES
('Mechanical Keyboard', 'Electronics', 4499.00, 45),
('Wireless Mouse', 'Electronics', 1799.00, 80),
('USB-C Dock', 'Electronics', 5999.00, 20),
('Notebook Pack', 'Stationery', 499.00, 150),
('Desk Lamp', 'Home Office', 2299.00, 35);

INSERT INTO orders (customer_id, status, ordered_at) VALUES
(1, 'delivered', NOW() - INTERVAL '80 days'),
(1, 'delivered', NOW() - INTERVAL '20 days'),
(2, 'delivered', NOW() - INTERVAL '15 days'),
(3, 'shipped', NOW() - INTERVAL '10 days'),
(4, 'paid', NOW() - INTERVAL '5 days'),
(5, 'cancelled', NOW() - INTERVAL '3 days');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 4499.00),
(1, 2, 2, 1799.00),
(2, 3, 1, 5999.00),
(2, 4, 3, 499.00),
(3, 1, 2, 4499.00),
(4, 5, 2, 2299.00),
(5, 2, 1, 1799.00),
(5, 4, 5, 499.00),
(6, 3, 1, 5999.00);
