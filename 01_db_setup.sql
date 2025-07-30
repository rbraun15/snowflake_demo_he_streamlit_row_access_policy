-- =============================================================================
-- Higher Education Row Access Policy Demo
-- =============================================================================

/*
This demo showcases how to implement row-level security in a higher education context, 
demonstrating how different users see different data based on their entitlements while 
maintaining a single application codebase.

Business Context
- Organization: Medium-sized university with annual budget in single-digit millions
- Time Period: 2019-2024 financial data
- Departments: Marketing, IT, HR, Academic Affairs, Athletics, Student Services
- Users: 
  ADMIN - Full access to all departments
  MARKETING_DIRECTOR - Access only to Marketing department data
  to deploy this demo either create two users ADMIN and MARKETING_DIRECTOR or modify
    the demo to incorporate your users.

*/

-- =============================================================================
--  Database Setup
-- =============================================================================

  

-- Create the database and schema
CREATE DATABASE IF NOT EXISTS DEMO_HIGHER_ED_ROW_ACCESS;
USE DATABASE DEMO_HIGHER_ED_ROW_ACCESS;

CREATE SCHEMA IF NOT EXISTS FINANCE;
USE SCHEMA FINANCE;

-- =============================================================================
-- 1. DEPARTMENTS TABLE
-- =============================================================================
CREATE OR REPLACE TABLE DEPARTMENTS (
    DEPARTMENT_ID INT AUTOINCREMENT,
    DEPARTMENT_NAME VARCHAR(100) NOT NULL,
    DEPARTMENT_CODE VARCHAR(10) NOT NULL,
    CREATED_DATE TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (DEPARTMENT_ID)
);

-- =============================================================================
-- 2. DEPARTMENT DIRECTORS TABLE
-- =============================================================================
CREATE OR REPLACE TABLE DEPARTMENT_DIRECTORS (
    DIRECTOR_ID INT AUTOINCREMENT,
    DEPARTMENT_ID INT NOT NULL,
    DIRECTOR_NAME VARCHAR(100) NOT NULL,
    START_DATE DATE NOT NULL,
    END_DATE DATE,
    IS_CURRENT BOOLEAN DEFAULT TRUE,
    CREATED_DATE TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (DIRECTOR_ID),
    FOREIGN KEY (DEPARTMENT_ID) REFERENCES DEPARTMENTS(DEPARTMENT_ID)
);

-- =============================================================================
-- 3. FINANCE TRANSACTIONS TABLE
-- =============================================================================
CREATE OR REPLACE TABLE FINANCE_TRANSACTIONS (
    TRANSACTION_ID INT AUTOINCREMENT,
    DEPARTMENT_ID INT NOT NULL,
    TRANSACTION_DATE DATE NOT NULL,
    EXPENDITURE_CATEGORY VARCHAR(50) NOT NULL,
    AMOUNT DECIMAL(12,2) NOT NULL,
    DESCRIPTION VARCHAR(500),
    FISCAL_YEAR INT NOT NULL,
    FISCAL_MONTH INT NOT NULL,
    CREATED_DATE TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (TRANSACTION_ID),
    FOREIGN KEY (DEPARTMENT_ID) REFERENCES DEPARTMENTS(DEPARTMENT_ID)
);

-- =============================================================================
-- 4. USER ENTITLEMENTS TABLE
-- =============================================================================
CREATE OR REPLACE TABLE USER_ENTITLEMENTS (
    ENTITLEMENT_ID INT AUTOINCREMENT,
    USERNAME VARCHAR(100) NOT NULL,
    DEPARTMENT_ID INT,
    ACCESS_LEVEL VARCHAR(20) NOT NULL, -- 'FULL', 'DEPARTMENT_ONLY'
    IS_ACTIVE BOOLEAN DEFAULT TRUE,
    CREATED_DATE TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_DATE TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (ENTITLEMENT_ID),
    FOREIGN KEY (DEPARTMENT_ID) REFERENCES DEPARTMENTS(DEPARTMENT_ID)
);



-- =============================================================================
-- 5. ROW ACCESS POLICY (Updated to avoid subquery issues)
-- =============================================================================

/*
CREATE OR REPLACE ROW ACCESS POLICY DEPARTMENT_ACCESS_POLICY AS (DEPARTMENT_ID INT) RETURNS BOOLEAN ->
  CURRENT_USER() = 'ADMIN' 
  OR 
  DEPARTMENT_ID = (
    SELECT DEPARTMENT_ID 
    FROM USER_ENTITLEMENTS 
    WHERE USERNAME = CURRENT_USER() 
      AND IS_ACTIVE = TRUE
  );
*/


CREATE OR REPLACE ROW ACCESS POLICY DEPARTMENT_ACCESS_POLICY AS (USERNAME VARCHAR) 
RETURNS BOOLEAN -> UPPER(USERNAME) = UPPER(CURRENT_USER());



SELECT * FROM USER_ENTITLEMENTS;
  

-- =============================================================================
-- 6. APPLY ROW ACCESS POLICY TO FINANCE TRANSACTIONS
-- =============================================================================

   ALTER TABLE USER_ENTITLEMENTS 
ADD ROW ACCESS POLICY DEPARTMENT_ACCESS_POLICY ON (USERNAME);



 
-- Use statements below if you need to remove the row access policy for troubleshooting
--   be sure to re-add the policy (see command 8 lines up)
-- ALTER TABLE FINANCE_TRANSACTIONS DROP ROW ACCESS POLICY DEPARTMENT_ACCESS_POLICY;
-- SELECT COUNT(*) FROM FINANCE_TRANSACTIONS;
-- SELECT DEPARTMENT_ID, COUNT(*) FROM FINANCE_TRANSACTIONS GROUP BY DEPARTMENT_ID;

 



-- =============================================================================
-- 7. CREATE SECURE VIEW FOR APPLICATION ACCESS
-- =============================================================================

CREATE OR REPLACE SECURE VIEW VW_FINANCE_DATA AS
SELECT 
    ft.TRANSACTION_ID,
    d.DEPARTMENT_NAME,
    d.DEPARTMENT_CODE,
    ft.TRANSACTION_DATE,
    ft.EXPENDITURE_CATEGORY,
    ft.AMOUNT,
    ft.DESCRIPTION,
    ft.FISCAL_YEAR,
    ft.FISCAL_MONTH,
    dd.DIRECTOR_NAME,
    dd.START_DATE AS DIRECTOR_START_DATE,
    dd.END_DATE AS DIRECTOR_END_DATE,
    dd.IS_CURRENT AS IS_CURRENT_DIRECTOR
FROM FINANCE_TRANSACTIONS ft
JOIN USER_ENTITLEMENTS ue on ue.DEPARTMENT_ID = ft.DEPARTMENT_ID
JOIN DEPARTMENTS d ON ft.DEPARTMENT_ID = d.DEPARTMENT_ID
LEFT JOIN DEPARTMENT_DIRECTORS dd ON d.DEPARTMENT_ID = dd.DEPARTMENT_ID
    AND ft.TRANSACTION_DATE >= dd.START_DATE
    AND (dd.END_DATE IS NULL OR ft.TRANSACTION_DATE <= dd.END_DATE);

-- =============================================================================
-- 8. CREATE AGGREGATED VIEW FOR DASHBOARD
-- =============================================================================

CREATE OR REPLACE SECURE VIEW VW_FINANCE_SUMMARY AS
SELECT 
    d.DEPARTMENT_NAME,
    d.DEPARTMENT_CODE,
    ft.FISCAL_YEAR,
    ft.FISCAL_MONTH,
    ft.EXPENDITURE_CATEGORY,
    SUM(ft.AMOUNT) AS TOTAL_AMOUNT,
    COUNT(*) AS TRANSACTION_COUNT,
    AVG(ft.AMOUNT) AS AVERAGE_AMOUNT,
    dd.DIRECTOR_NAME,
    dd.START_DATE AS DIRECTOR_START_DATE
FROM FINANCE_TRANSACTIONS ft
JOIN USER_ENTITLEMENTS ue on ue.DEPARTMENT_ID = ft.DEPARTMENT_ID
JOIN DEPARTMENTS d ON ft.DEPARTMENT_ID = d.DEPARTMENT_ID
LEFT JOIN DEPARTMENT_DIRECTORS dd ON d.DEPARTMENT_ID = dd.DEPARTMENT_ID
    AND ft.TRANSACTION_DATE >= dd.START_DATE
    AND (dd.END_DATE IS NULL OR ft.TRANSACTION_DATE <= dd.END_DATE)
GROUP BY 
    d.DEPARTMENT_NAME,
    d.DEPARTMENT_CODE,
    ft.FISCAL_YEAR,
    ft.FISCAL_MONTH,
    ft.EXPENDITURE_CATEGORY,
    dd.DIRECTOR_NAME,
    dd.START_DATE;

-- =============================================================================
-- 9. CREATE ROLE AND GRANT PERMISSIONS FOR STREAMLIT APP
-- =============================================================================

-- Create dedicated role for demo application users
CREATE ROLE IF NOT EXISTS DEMO_HIGHER_ED_ROW_ACCESS;

-- Grant database and schema permissions to the role
GRANT USAGE ON DATABASE DEMO_HIGHER_ED_ROW_ACCESS TO ROLE DEMO_HIGHER_ED_ROW_ACCESS;
GRANT USAGE ON SCHEMA FINANCE TO ROLE DEMO_HIGHER_ED_ROW_ACCESS;

-- Grant table and view permissions
GRANT SELECT ON ALL TABLES IN SCHEMA FINANCE TO ROLE DEMO_HIGHER_ED_ROW_ACCESS;
GRANT SELECT ON ALL VIEWS IN SCHEMA FINANCE TO ROLE DEMO_HIGHER_ED_ROW_ACCESS;

-- Grant permissions on future objects (for ongoing maintenance)
GRANT SELECT ON FUTURE TABLES IN SCHEMA FINANCE TO ROLE DEMO_HIGHER_ED_ROW_ACCESS;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA FINANCE TO ROLE DEMO_HIGHER_ED_ROW_ACCESS;

-- Grant the role to demo users
GRANT ROLE DEMO_HIGHER_ED_ROW_ACCESS TO USER ADMIN;
GRANT ROLE DEMO_HIGHER_ED_ROW_ACCESS TO USER MARKETING_DIRECTOR;

-- Optional: Grant role to other administrative roles for management
-- GRANT ROLE DEMO_HIGHER_ED_ROW_ACCESS TO ROLE SYSADMIN;

COMMENT ON ROLE DEMO_HIGHER_ED_ROW_ACCESS IS 'Role for Higher Education Row Access Policy demo application users';
COMMENT ON DATABASE DEMO_HIGHER_ED_ROW_ACCESS IS 'Demo database for Higher Education Row Access Policy with Streamlit';
COMMENT ON SCHEMA FINANCE IS 'Schema containing financial data and entitlements for row access policy demo'; 

