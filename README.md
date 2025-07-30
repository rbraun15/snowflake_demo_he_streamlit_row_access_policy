# Higher Education Finance Dashboard - Row Access Policy Demo

🎓 **A comprehensive Snowflake Row Access Policy demonstration with Streamlit in Snowflake**

This demo showcases an example of row-level security in a higher education context, demonstrating how different users see different data based on their entitlements while maintaining a single application codebase.

## 📋 Demo Overview

### Business Context
- **Organization**: Medium-sized university with annual budget in single-digit millions
- **Time Period**: 2019-2024 financial data
- **Departments**: Marketing, IT, HR, Academic Affairs, Athletics, Student Services
- **Users**: 
  - `ADMIN` - Full access to all departments
  - `MARKETING_DIRECTOR` - Access only to Marketing department data

### Key Story
The demo highlights how the **new Marketing Director (Jennifer Martinez, started 2023)** has dramatically increased software subscription spending, suggesting an opportunity to leverage central IT services for cost optimization.

## 🏗️ Architecture

The demo consists of:

1. **Database Layer**: `DEMO_HIGHER_ED_ROW_ACCESS`
2. **Row Access Policy**: `DEPARTMENT_ACCESS_POLICY` 
3. **Entitlements Table**: `USER_ENTITLEMENTS`
4. **Secure Views**: `VW_FINANCE_DATA` and `VW_FINANCE_SUMMARY`
5. **Streamlit Application**: Interactive dashboard

## 🚀 Quick Start

### Prerequisites
- Snowflake account with Streamlit in Snowflake (SiS) enabled
- SYSADMIN or ACCOUNTADMIN privileges for initial setup
- Users `ADMIN` and `MARKETING_DIRECTOR` already exist in your Snowflake account

### Installation Steps

1. **Clone or Download the Demo Files**
   ```bash
   # Download all files to your local machine
   # Files needed:
   # - 01_database_setup.sql
   # - 02_sample_data.sql  
   # - streamlit_app.py
   # - README.md
   ```

2. **Database Setup**
   ```sql
   -- Connect to Snowflake as SYSADMIN or ACCOUNTADMIN
   -- Run the database setup script
   -- This creates tables, indexes, row access policy, and views
   !source 01_database_setup.sql
   ```

3. **Data Population**
   ```sql
   -- Run the sample data script
   -- This populates ~2,500 realistic financial transactions
   !source 02_sample_data.sql
   ```

4. **Grant Permissions** (Automatically handled by setup script)
   ```sql
   -- The setup script automatically:
   -- 1. Creates role DEMO_HIGHER_ED_ROW_ACCESS
   -- 2. Grants necessary permissions to the role
   -- 3. Grants the role to ADMIN and MARKETING_DIRECTOR users
   
   -- If you need to grant the role to additional users later:
   GRANT ROLE DEMO_HIGHER_ED_ROW_ACCESS TO USER <username>;
   ```

5. **Deploy Streamlit App**
   - Navigate to Snowflake Web UI
   - Go to **Data > Streamlit**
   - Create new Streamlit app
   - Copy the contents of `streamlit_app.py`
   - add package - plotly
   - Set database/schema context to `DEMO_HIGHER_ED_ROW_ACCESS.FINANCE`
   - Deploy the application
   - **Important**: Ensure the Streamlit app runs with the `DEMO_HIGHER_ED_ROW_ACCESS` role, once app is deployed click Share > add the role `DEMO_HIGHER_ED_ROW_ACCESS` , copy the link for the application if you like.
  



## 📊 Data Structure

### Tables

| Table | Purpose | Records |
|-------|---------|---------|
| `DEPARTMENTS` | Department master data | 6 departments |
| `DEPARTMENT_DIRECTORS` | Director history with dates | ~7 directors |
| `FINANCE_TRANSACTIONS` | Monthly financial data | ~2,500 transactions |
| `USER_ENTITLEMENTS` | User access permissions | 2 users |

### Expenditure Categories
- Salaries & wages (largest expense)
- Software subscriptions 
- Travel
- Supplies & materials
- Equipment
- Printing
- Other expenses

## 🔐 Security Architecture

### Role Structure
The demo uses a dedicated role for application access:

- **`DEMO_HIGHER_ED_ROW_ACCESS`** - Application role with permissions to:
  - `USAGE` on database and schema
  - `SELECT` on all tables and views
  - `SELECT` on future tables and views (for maintenance)

This role is granted to both demo users (`ADMIN` and `MARKETING_DIRECTOR`), providing a clean separation between application permissions and user entitlements.

### Row Access Policy Details

### Policy Logic
```sql
CREATE OR REPLACE ROW ACCESS POLICY DEPARTMENT_ACCESS_POLICY AS (USERNAME VARCHAR) 
RETURNS BOOLEAN -> UPPER(USERNAME) = UPPER(CURRENT_USER());
```

### User Entitlements

| User | Access Level | Department | Can See |
|------|-------------|------------|---------|
| `ADMIN` | DEPARTMENT_ONLY | Marketing | Marketing |
| `ADMIN` | DEPARTMENT_ONLY | Athletics | Atheltics |
| `ADMIN` | DEPARTMENT_ONLY | Information Technology | Information Technology |
| `ADMIN` | DEPARTMENT_ONLY | Human Resources | Human Resources |
| `ADMIN` | DEPARTMENT_ONLY | Academic Affairs | Academic Affairs |
| `ADMIN` | DEPARTMENT_ONLY | Student Services | Student Services |
| `MARKETING_DIRECTOR` | DEPARTMENT_ONLY | Marketing | Marketing only |

## 🎯 Demo Features

### For ADMIN Users
- **Full Dashboard**: See all 6 departments
- **Department Comparison**: Charts comparing all departments
- **Complete Data**: All ~2,500 transactions
- **Cross-Department Analysis**: Full university view

### For MARKETING_DIRECTOR Users  
- **Restricted View**: Only Marketing department data
- **Focused Analytics**: Marketing-specific insights
- **Limited Data**: Only ~400 Marketing transactions
- **Insight Highlighting**: Software subscription spending increase

### Interactive Features
- 📅 **Date Filters**: Filter by fiscal year
- 📊 **Category Filters**: Filter by expenditure category  
- 🏢 **Department Filters**: Filter by department (based on access)
- 📈 **Trend Analysis**: Multi-year spending trends
- 💻 **Software Analysis**: Specific analysis of software subscriptions
- 📋 **Data Export**: Download filtered data as CSV
- 📊 **Multiple Chart Types**: Line charts, pie charts, bar charts

## 🎭 Testing the Demo

### Test Scenario 1: Admin User
1. **Login as ADMIN**
2. **Expected Result**: 
   - See all 6 departments in filters
   - Dashboard shows "Departments Visible: Academic Affairs, Athletics, Human Resources, Information Technology, Marketing, Student Services"
   - Department comparison chart shows all departments
   - Can see software subscription trends across all departments

### Test Scenario 2: Marketing Director
1. **Login as MARKETING_DIRECTOR**  
2. **Expected Result**:
   - See only "Marketing" in department filter
   - Dashboard shows "Departments Visible: Marketing"
   - No department comparison chart (single department)
   - Software subscription analysis highlights Marketing's 4x increase since 2023
   - Insight message: "Marketing software subscriptions have increased by X% since 2023"

### Test Scenario 3: Verify Data Filtering
```sql
-- Test query as different users
SELECT CURRENT_USER(), COUNT(*), COUNT(DISTINCT DEPARTMENT_NAME) 
FROM VW_FINANCE_DATA;

-- Expected Results:
-- ADMIN: ~2,500 records, 6 departments
-- MARKETING_DIRECTOR: ~400 records, 1 department
```

## 🔧 Customization Guide

### Adding New Users
1. **Create user entitlement**:
   ```sql
   INSERT INTO USER_ENTITLEMENTS (USERNAME, DEPARTMENT_ID, ACCESS_LEVEL, IS_ACTIVE)
   VALUES ('NEW_USER', (SELECT DEPARTMENT_ID FROM DEPARTMENTS WHERE DEPARTMENT_CODE = 'IT'), 'DEPARTMENT_ONLY', TRUE);
   ```

2. **Grant the demo role**:
   ```sql
   GRANT ROLE DEMO_HIGHER_ED_ROW_ACCESS TO USER NEW_USER;
   ```

3. **Verify access**:
   ```sql
   -- Test as the new user
   SELECT CURRENT_USER(), COUNT(*) FROM VW_FINANCE_DATA;
   ```

### Adding New Departments
1. **Add department**:
   ```sql
   INSERT INTO DEPARTMENTS (DEPARTMENT_NAME, DEPARTMENT_CODE) 
   VALUES ('New Department', 'NEW');
   ```

2. **Add director**:
   ```sql
   INSERT INTO DEPARTMENT_DIRECTORS (DEPARTMENT_ID, DIRECTOR_NAME, START_DATE, IS_CURRENT)
   VALUES ((SELECT DEPARTMENT_ID FROM DEPARTMENTS WHERE DEPARTMENT_CODE = 'NEW'), 'Director Name', '2024-01-01', TRUE);
   ```

3. **Generate sample data**: Modify the data generation script to include the new department

### Modifying Access Patterns
- **Regional Access**: Modify the row access policy to filter by geographic regions
- **Time-based Access**: Add date-based restrictions to the policy
- **Hierarchical Access**: Implement manager-subordinate access patterns

## 🎓 Educational Value

### Learning Objectives
1. **Row-Level Security**: Understand how RLS works in practice
2. **Context Functions**: Learn to use `CURRENT_USER()` for dynamic filtering
3. **Entitlements Pattern**: See how to implement flexible user permissions
4. **Secure Views**: Understand how views inherit security policies
5. **Application Integration**: Learn how Streamlit apps work with secured data

### Key Concepts Demonstrated
- **Zero Trust Security**: Data is secured at the database level
- **Transparent Security**: Applications don't need security logic
- **Dynamic Filtering**: Same query returns different results per user
- **Governance**: Clear audit trail of who can see what data
- **Scalability**: Easy to add new users and permissions

## 🔍 Verification Queries

### Check Row Access Policy
```sql
-- Verify policy is applied
SHOW ROW ACCESS POLICIES IN SCHEMA FINANCE;

-- Check policy details
DESCRIBE ROW ACCESS POLICY DEPARTMENT_ACCESS_POLICY;
```

### Test Data Access
```sql
-- Test as different users
SELECT 
    CURRENT_USER() as current_user,
    COUNT(*) as total_records,
    COUNT(DISTINCT DEPARTMENT_NAME) as departments_visible,
    MIN(TRANSACTION_DATE) as earliest_date,
    MAX(TRANSACTION_DATE) as latest_date,
    SUM(AMOUNT) as total_amount
FROM VW_FINANCE_DATA;
```

### Verify Marketing Insight
```sql
-- Check marketing software subscriptions trend
SELECT 
    FISCAL_YEAR,
    SUM(AMOUNT) as software_spending,
    COUNT(*) as transactions
FROM VW_FINANCE_DATA 
WHERE EXPENDITURE_CATEGORY = 'software subscriptions'
    AND DEPARTMENT_NAME = 'Marketing'
GROUP BY FISCAL_YEAR
ORDER BY FISCAL_YEAR;
```

## 🚨 Troubleshooting

### Common Issues

1. **"No data available"**
   - Check user entitlements table
   - Verify row access policy is applied
   - Confirm user exists and has proper grants

2. **"Error loading finance data"**
   - Check database and schema context in Streamlit
   - Verify connection permissions
   - Check if tables exist and are populated

3. **"Permission denied"**
   - Ensure user has the `DEMO_HIGHER_ED_ROW_ACCESS` role
   - Check if user has activated the role: `USE ROLE DEMO_HIGHER_ED_ROW_ACCESS;`
   - Verify row access policy logic

### Debug Queries
```sql
-- Check current user and role context
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA();

-- Check if user has the demo role
SHOW GRANTS TO USER CURRENT_USER();

-- Check user entitlements
SELECT * FROM USER_ENTITLEMENTS WHERE USERNAME = CURRENT_USER();

-- Test row access policy manually
SELECT COUNT(*) FROM FINANCE_TRANSACTIONS; -- Should respect RLS

-- Verify role permissions
SHOW GRANTS TO ROLE DEMO_HIGHER_ED_ROW_ACCESS;
```

## 📈 Performance Considerations

- **Caching**: Streamlit uses `@st.cache_data` for performance
- **Views**: Secure views provide optimized access patterns

## 🔗 References

- [Snowflake Row Access Policies Documentation](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [Streamlit in Snowflake Context Functions](https://docs.snowflake.com/en/developer-guide/streamlit/additional-features#context-functions-and-row-access-policies-in-sis)
- [Snowflake Security Best Practices](https://docs.snowflake.com/en/user-guide/security-access-control-overview)

## 📞 Support

For questions about this demo:
1. Check the troubleshooting section above
2. Verify all setup steps were completed
3. Test with the provided verification queries
4. Review Snowflake documentation for advanced configurations

---

**Built with ❤️ for demonstrating Snowflake's powerful security capabilities** 
