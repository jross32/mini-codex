## Mock League Data for Development

This directory contains mock APA league data for local development and testing.

### Purpose

`leagueData.json` is a realistic but fully simulated dataset that allows developers to:

- Test onboarding flows
- Build and verify lineup features
- Develop dashboard views with populated data
- Test admin statistics and reports
- Verify data loading without needing a real scraper or external API

### Data Structure

The mock data includes:

- **1 League**: APA Rio Grande Valley
- **3 Divisions**: Mixed 8-ball and 9-ball formats across Thursday, Monday, and Wednesday play
- **5 Locations**: Realistic bar/pool hall names in South Texas
- **10 Teams**: 6-10 teams across divisions, including "MY TEAM - Breaking Cues" for captain testing
- **51 Players**: Mixed skill levels (APA 2-7 for 8-ball, 1-9 for 9-ball), realistic statistics
- **13 Matches**: Multiple weeks of completed matches with detailed set-by-set results

### Key Features

✓ Consistent ID references across all entities
✓ Realistic skill level distributions
✓ Balanced match scores (competitive play)
✓ Multiple weeks of data for standings/trends
✓ Captain designations on all teams
✓ Clear "MY TEAM" for testing admin/captain features
✓ Both 8-ball and 9-ball formats
✓ Defensive shots, innings, PPM, and win percentages

### Usage

When the app starts in development mode, it automatically loads this mock data if:

1. `DATA_DIR` environment variable points to this directory
2. OR if the default data directory contains this file

To use the mock data:

```bash
export DATA_DIR=backend/data/mock
python app/main.py
```

Or load it into the onboarding flow manually via the frontend UI.

### Notes

- All names, venues, and statistics are simulated and do not represent real league data
- Generated: 2026-01-25
- This is for development only and should not be used in production
