from __future__ import annotations

import re


class MockSQLGenerator:
    """Deterministic local provider for demos, tests, and offline development."""

    def generate_sql(self, prompt: str) -> str:
        question_match = re.search(r"USER QUESTION:\n(.+?)\n\n", prompt, re.DOTALL)
        question = (question_match.group(1) if question_match else prompt).lower()

        if "top" in question and "customer" in question:
            return """
                SELECT c.name, SUM(oi.quantity * oi.unit_price) AS total_spend
                FROM customers AS c
                JOIN orders AS o ON o.customer_id = c.id
                JOIN order_items AS oi ON oi.order_id = o.id
                WHERE o.status <> 'cancelled'
                GROUP BY c.id, c.name
                ORDER BY total_spend DESC
                LIMIT 5
            """.strip()

        if "revenue" in question and "product" in question:
            return """
                SELECT p.name, SUM(oi.quantity * oi.unit_price) AS revenue
                FROM products AS p
                JOIN order_items AS oi ON oi.product_id = p.id
                JOIN orders AS o ON o.id = oi.order_id
                WHERE o.status <> 'cancelled'
                GROUP BY p.id, p.name
                ORDER BY revenue DESC
                LIMIT 10
            """.strip()

        if "stock" in question:
            return """
                SELECT name, category, stock_quantity
                FROM products
                ORDER BY stock_quantity ASC
                LIMIT 10
            """.strip()

        return "SELECT id, name, category, unit_price, stock_quantity FROM products ORDER BY id LIMIT 20"
