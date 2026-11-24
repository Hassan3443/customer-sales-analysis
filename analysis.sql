-- MySQL queries for Amazon.csv, loaded into a table named `amazon`.
-- The pandas script (analysis.py) answers the same questions without a database.

-- 1. Total order value, all statuses
SELECT ROUND(SUM(TotalAmount), 2) AS total_order_value
FROM amazon;

-- 2. Order value lost to cancelled and returned orders
SELECT ROUND(SUM(TotalAmount), 2) AS cancelled_or_returned_value
FROM amazon
WHERE OrderStatus IN ('Cancelled', 'Returned');

-- 3. Order value by category
SELECT Category, ROUND(SUM(TotalAmount), 2) AS revenue
FROM amazon
GROUP BY Category
ORDER BY revenue DESC;

-- 4. Monthly trend
SELECT DATE_FORMAT(OrderDate, '%Y-%m') AS month,
       ROUND(SUM(TotalAmount), 2) AS revenue
FROM amazon
GROUP BY month
ORDER BY month;

-- 5. Top 10 states
SELECT State, ROUND(SUM(TotalAmount), 2) AS revenue
FROM amazon
GROUP BY State
ORDER BY revenue DESC
LIMIT 10;

-- 6. Orders by status
SELECT OrderStatus, COUNT(*) AS orders
FROM amazon
GROUP BY OrderStatus
ORDER BY orders DESC;

-- 7. Payment method share of orders
SELECT PaymentMethod,
       COUNT(*) AS orders,
       ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM amazon), 1) AS pct_of_orders
FROM amazon
GROUP BY PaymentMethod
ORDER BY orders DESC;
