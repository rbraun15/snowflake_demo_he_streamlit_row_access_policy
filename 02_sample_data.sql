

-- =============================================================================
-- Higher Education Row Access Policy Demo - Sample Data Population
-- =============================================================================

USE DATABASE DEMO_HIGHER_ED_ROW_ACCESS;
USE SCHEMA FINANCE;

-- =============================================================================
-- 1. POPULATE DEPARTMENTS
-- =============================================================================

INSERT INTO DEPARTMENTS (DEPARTMENT_NAME, DEPARTMENT_CODE) VALUES
('Marketing', 'MKT'),
('Information Technology', 'IT'),
('Human Resources', 'HR'),
('Academic Affairs', 'AA'),
('Athletics', 'ATH'),
('Student Services', 'SS');




-- =============================================================================
-- 2. POPULATE DEPARTMENT DIRECTORS
-- =============================================================================

-- Get department IDs for reference
SET dept_marketing = (SELECT DEPARTMENT_ID FROM DEPARTMENTS WHERE DEPARTMENT_CODE = 'MKT');
SET dept_it = (SELECT DEPARTMENT_ID FROM DEPARTMENTS WHERE DEPARTMENT_CODE = 'IT');
SET dept_hr = (SELECT DEPARTMENT_ID FROM DEPARTMENTS WHERE DEPARTMENT_CODE = 'HR');
SET dept_aa = (SELECT DEPARTMENT_ID FROM DEPARTMENTS WHERE DEPARTMENT_CODE = 'AA');
SET dept_ath = (SELECT DEPARTMENT_ID FROM DEPARTMENTS WHERE DEPARTMENT_CODE = 'ATH');
SET dept_ss = (SELECT DEPARTMENT_ID FROM DEPARTMENTS WHERE DEPARTMENT_CODE = 'SS');

INSERT INTO DEPARTMENT_DIRECTORS (DEPARTMENT_ID, DIRECTOR_NAME, START_DATE, END_DATE, IS_CURRENT) VALUES
-- Marketing Directors
($dept_marketing, 'Sarah Thompson', '2019-01-01', '2022-12-31', FALSE),
($dept_marketing, 'Jennifer Martinez', '2023-01-01', NULL, TRUE),

-- IT Directors
($dept_it, 'Michael Chen', '2018-07-01', NULL, TRUE),

-- HR Directors  
($dept_hr, 'Lisa Rodriguez', '2017-03-01', NULL, TRUE),

-- Academic Affairs Directors
($dept_aa, 'Dr. Robert Wilson', '2016-08-01', NULL, TRUE),

-- Athletics Directors
($dept_ath, 'Coach David Anderson', '2020-01-01', NULL, TRUE),

-- Student Services Directors
($dept_ss, 'Amanda Foster', '2019-09-01', NULL, TRUE);

-- =============================================================================
-- 3. POPULATE USER ENTITLEMENTS
-- =============================================================================

INSERT INTO USER_ENTITLEMENTS (USERNAME, DEPARTMENT_ID, ACCESS_LEVEL, IS_ACTIVE) VALUES
-- Admin user has full access to all departments
 
('ADMIN', $dept_marketing, 'DEPARTMENT_ONLY', TRUE),
('ADMIN', $dept_hr, 'DEPARTMENT_ONLY', TRUE),
('ADMIN', $dept_it, 'DEPARTMENT_ONLY', TRUE),
('ADMIN', $dept_aa, 'DEPARTMENT_ONLY', TRUE),
('ADMIN', $dept_ath, 'DEPARTMENT_ONLY', TRUE),
('ADMIN', $dept_ss, 'DEPARTMENT_ONLY', TRUE),


-- Marketing director only has access to marketing department
('MARKETING_DIRECTOR', $dept_marketing, 'DEPARTMENT_ONLY', TRUE);


/* 
-- some statements to add/remove the ROW access policy so you can tweak it as needed
delete from USER_ENTITLEMENTS where username='ADMIN';
delete from USER_ENTITLEMENTS;
select * from USER_ENTITLEMENTS;
ALTER TABLE USER_ENTITLEMENTS ADD ROW ACCESS POLICY DEPARTMENT_ACCESS_POLICY ON (USERNAME);
ALTER TABLE USER_ENTITLEMENTS DROP ROW ACCESS POLICY DEPARTMENT_ACCESS_POLICY;
*/




-- =============================================================================
-- 4. POPULATE FINANCE TRANSACTIONS (2019-2024)
-- =============================================================================

-- Note: This creates realistic monthly financial data for each department
-- The data shows the marketing department's increased software spending after 2023

-- Create a JavaScript UDF to generate realistic amounts
CREATE OR REPLACE FUNCTION GENERATE_FINANCE_AMOUNT(
    dept_code STRING, 
    category STRING, 
    year FLOAT, 
    month FLOAT,
    base_amount FLOAT
)
RETURNS FLOAT
LANGUAGE JAVASCRIPT
AS
$$
    // Access input parameters
    var deptCode = arguments[0];
    var categoryName = arguments[1];
    var yearValue = arguments[2];
    var monthValue = arguments[3];
    var baseAmount = arguments[4];
    
    // Base multipliers by department for realistic budget differences
    var deptMultipliers = {
        'AA': 2.5,   // Academic Affairs - largest budget
        'ATH': 1.8,  // Athletics - significant budget
        'IT': 1.5,   // IT - substantial tech budget
        'SS': 1.2,   // Student Services - moderate budget
        'HR': 1.0,   // HR - baseline budget
        'MKT': 0.8   // Marketing - smaller budget
    };
    
    // Category multipliers for realistic expense distribution
    var categoryMultipliers = {
        'salaries & wages': 8.0,
        'software subscriptions': 0.3,
        'travel': 0.2,
        'supplies & materials': 0.4,
        'equipment': 0.6,
        'printing': 0.1,
        'other expenses': 0.3
    };
    
    // Special case: Marketing software subscriptions spike after 2023
    if (deptCode === 'MKT' && categoryName === 'software subscriptions' && yearValue >= 2023) {
        categoryMultipliers['software subscriptions'] = 1.2; // 4x increase
    }
    
    // Seasonal variations (some months are higher)
    var seasonalMultiplier = 1.0;
    if (monthValue === 1 || monthValue === 9) seasonalMultiplier = 1.3; // Start of year and academic year
    if (monthValue === 12) seasonalMultiplier = 1.2; // End of year spending
    if (monthValue === 7 || monthValue === 8) seasonalMultiplier = 0.7; // Summer reduction
    
    // Random variation ±20%
    var randomMultiplier = 0.8 + (Math.random() * 0.4);
    
    var amount = baseAmount * 
                deptMultipliers[deptCode] * 
                categoryMultipliers[categoryName] * 
                seasonalMultiplier * 
                randomMultiplier;
    
    return Math.round(amount * 100) / 100; // Round to 2 decimal places
$$;

-- Generate the transaction data
INSERT INTO FINANCE_TRANSACTIONS 
(DEPARTMENT_ID, TRANSACTION_DATE, EXPENDITURE_CATEGORY, AMOUNT, DESCRIPTION, FISCAL_YEAR, FISCAL_MONTH)

-- Use a CTE to generate all combinations and then calculate amounts
WITH date_range AS (
    SELECT 
        DATE_FROM_PARTS(year_val, month_val, 1) as transaction_date,
        year_val as fiscal_year,
        month_val as fiscal_month
    FROM (
        SELECT DISTINCT seq4() + 2019 as year_val 
        FROM TABLE(GENERATOR(rowcount => 6))
    ) years
    CROSS JOIN (
        SELECT DISTINCT seq4() + 1 as month_val
        FROM TABLE(GENERATOR(rowcount => 12))
    ) months
    WHERE year_val <= 2024
),
dept_category_combinations AS (
    SELECT 
        d.DEPARTMENT_ID,
        d.DEPARTMENT_CODE,
        cat.expenditure_category,
        dr.transaction_date,
        dr.fiscal_year,
        dr.fiscal_month
    FROM DEPARTMENTS d
    CROSS JOIN (
        SELECT 'salaries & wages' as expenditure_category
        UNION ALL SELECT 'software subscriptions'
        UNION ALL SELECT 'travel'
        UNION ALL SELECT 'supplies & materials'
        UNION ALL SELECT 'equipment'
        UNION ALL SELECT 'printing'
        UNION ALL SELECT 'other expenses'
    ) cat
    CROSS JOIN date_range dr
)

SELECT 
    DEPARTMENT_ID,
    transaction_date,
    expenditure_category,
    GENERATE_FINANCE_AMOUNT(DEPARTMENT_CODE, expenditure_category, CAST(fiscal_year AS FLOAT), CAST(fiscal_month AS FLOAT), 5000.0) as amount,
    DEPARTMENT_CODE || ' - ' || expenditure_category || ' for ' || 
    TO_CHAR(transaction_date, 'MMMM YYYY') as description,
    fiscal_year,
    fiscal_month
FROM dept_category_combinations
WHERE transaction_date <= CURRENT_DATE();

-- =============================================================================
-- 5. VERIFICATION QUERIES (Removed statistics and index sections)
-- =============================================================================

-- Verify data counts
SELECT 'DEPARTMENTS' as table_name, COUNT(*) as record_count FROM DEPARTMENTS
UNION ALL
SELECT 'DEPARTMENT_DIRECTORS', COUNT(*) FROM DEPARTMENT_DIRECTORS
UNION ALL
SELECT 'FINANCE_TRANSACTIONS', COUNT(*) FROM FINANCE_TRANSACTIONS
UNION ALL
SELECT 'USER_ENTITLEMENTS', COUNT(*) FROM USER_ENTITLEMENTS;

-- Verify date ranges
SELECT 
    'FINANCE_TRANSACTIONS' as table_name,
    MIN(TRANSACTION_DATE) as min_date,
    MAX(TRANSACTION_DATE) as max_date,
    COUNT(DISTINCT FISCAL_YEAR) as year_count,
    COUNT(DISTINCT EXPENDITURE_CATEGORY) as category_count
FROM FINANCE_TRANSACTIONS;

-- Verify department totals by year
SELECT 
    d.DEPARTMENT_NAME,
    ft.FISCAL_YEAR,
    SUM(ft.AMOUNT) as total_amount,
    COUNT(*) as transaction_count
FROM FINANCE_TRANSACTIONS ft
JOIN DEPARTMENTS d ON ft.DEPARTMENT_ID = d.DEPARTMENT_ID
GROUP BY d.DEPARTMENT_NAME, ft.FISCAL_YEAR
ORDER BY d.DEPARTMENT_NAME, ft.FISCAL_YEAR;

-- Verify marketing software subscriptions trend (should show increase in 2023-2024)
SELECT 
    fiscal_year,
    SUM(amount) as total_software_spending
FROM FINANCE_TRANSACTIONS ft
JOIN DEPARTMENTS d ON ft.DEPARTMENT_ID = d.DEPARTMENT_ID
WHERE d.DEPARTMENT_CODE = 'MKT' 
    AND ft.EXPENDITURE_CATEGORY = 'software subscriptions'
GROUP BY fiscal_year
ORDER BY fiscal_year;

-- Clean up the UDF after data generation
DROP FUNCTION IF EXISTS GENERATE_FINANCE_AMOUNT(STRING, STRING, INT, INT, FLOAT);

SELECT 'Sample data population completed successfully!' as status; 
