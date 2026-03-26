# GraphQL/Direct API Testing Feature

## Overview
Added a new capture mode (Mode 11) to the APA API Sniffer v2 for direct GraphQL endpoint testing with authenticated sessions.

## New Capture Mode: GraphQL/Direct API Testing (Mode 11)

### What It Does
- **Tests GraphQL endpoints directly** with cookies/tokens from your authenticated browser session
- **Discovers GraphQL schema** through introspection queries
- **Validates API accessibility** and responses
- **Tests multiple endpoints** automatically
- **Saves detailed results** to JSON files for analysis

### Endpoints Tested
The feature automatically tests these APA GraphQL endpoints:
- `https://gql.poolplayers.com/graphql/`
- `https://api.poolplayers.com/graphql`
- `https://league.poolplayers.com/graphql`

### GraphQL Queries Executed
1. **Schema Introspection (`__typename`)** - Simple query to test basic endpoint connectivity
2. **Full Schema Discovery** - Retrieves complete schema with all types
3. **Query Root Fields** - Discovers available query operations and their types

### How It Works
1. You log in normally through the browser (Mode 11 uses your authenticated session)
2. The sniffer extracts cookies and authentication tokens from your session
3. It makes direct HTTP POST requests to GraphQL endpoints with those credentials
4. Responses are analyzed and saved to `graphql_tests/` directory
5. Results include endpoint accessibility, query success/failure, and error details

### Output Files
Results are saved in the run directory under `graphql_tests/`:
```
graphql_tests/
  └── 0000_graphql_results.json
```

Each result file contains:
- Endpoint URL
- Test results for each query (name, status code, success flag)
- Response data or error messages
- Whether endpoint is accessible (200 response without errors)

### Integration with "Everything" Mode
Mode 12 ("Everything") now includes GraphQL testing along with all other capture modes.

## Command Line Usage

### Option 1: Interactive Menu
```bash
python apa_api_sniffer_v2.py
# Select mode 11 when prompted
```

### Option 2: Non-Interactive (Environment Variable)
```bash
set CAPTURE_MODE=11 && python apa_api_sniffer_v2.py
```

### Option 3: Combined with Other Features
Select Mode 12 ("Everything") to capture:
- APIs, Network, Client-side Intelligence, Auth/Session, Page Behavior, Content, Tracking, Screenshots, DOM, AND GraphQL Testing

## Output Summary
The script displays:
```
ℹ️  Testing GraphQL endpoints with authenticated session...
✅ GraphQL testing complete: 2/3 endpoints accessible
```

And includes a summary in the main results:
```json
{
  "graphql_summary": {
    "endpoints_tested": 3,
    "accessible_endpoints": 2,
    "tests_file": "graphql_tests/0000_graphql_results.json"
  }
}
```

## Next Steps for Testing
Once you have the GraphQL results:
1. Check which endpoints are accessible (200 status)
2. Review the schema introspection results to understand available operations
3. Report findings to APA security team
4. Use this info to craft custom GraphQL queries for deeper API exploration

## Example GraphQL Query to Add
You can modify the `test_graphql_endpoints()` function to add custom queries:
```python
{
    "name": "Get Current User Info",
    "query": """
    query {
      currentUser {
        id
        name
        email
      }
    }
    """
}
```

## Files Modified
- `apa_api_sniffer_v2.py`:
  - Added `test_graphql_endpoints()` function
  - Added Mode 11: GraphQL/Direct API Testing
  - Updated Mode 12 description to include GraphQL
  - Added GraphQL testing in page processing pipeline
  - Added `collect_graphql_direct` flag to all modes
  - Added CLI help text for Mode 11
  - Added import for `requests` library

## Dependencies
The feature uses:
- `requests` - For direct HTTP POST requests to GraphQL endpoints
- Cookies extracted from Playwright browser context for authentication
