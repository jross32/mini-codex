# Inventory Management App

A web application for managing inventory with a React frontend and Flask backend.

## Features

- View inventory in a professional table format with pagination
- Add, edit, and delete inventory items
- Search and filter by brand, model, type, details, and status
- Sort by any column (click headers)
- Bulk operations: select multiple items for update/delete
- Export data to CSV
- Import data from CSV
- Dashboard with stats (total, available, in use, low stock)
- Low-stock alerts (rows highlighted in red for qty < 2)
- RESTful API for inventory data
- Styled with Tailwind CSS

## Setup

1. **Install Python dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Install Node.js dependencies:**
   ```
   npm install
   ```

3. **Import CSV data:**
   ```
   python import_csv.py
   ```

## Running the Application

1. **Start the Flask backend:**
   ```
   python app.py
   ```
   The backend will run on http://127.0.0.1:5000

2. **Start the React frontend:**
   ```
   npm start
   ```
   The frontend will run on http://localhost:3000

## About WhatAPC (V1)

Strategic Analysis of the WhatAPC Custom Computing Ecosystem: Operational Architecture, Hardware Life-Cycles, and the Proliferation of Sustainable High-Performance Engineering.

- “Forever PC” philosophy: modular, upgradeable builds treated as long-lived assets.
- Flagship: i7-8700K (often 4.9 GHz OC) + dual GTX 1080 Ti SLI, 32GB DDR4, 250GB SSD; high-performance tuning.
- Fulfillment: just-in-time ordering; scheduled deliveries into late 2025; transparent client communication.
- Longevity: ATX towers with clearance for future GPUs, strong VRMs, ≥4 DIMMs, multiple M.2; efficient CPUs (e.g., Ryzen 7 5800X / i5-12600K) over hot 240W chips.
- Market insights: Xeon E5-2670 v2 for multi-thread value; i7-8700K for single-thread balance; RTX 2080 Ti used-market sweet spot (~$270–$400).
- Services: data recovery tiers (logical $100–$600; physical $400–$2,000+; RAID $1.5k–$10k), billable labor $75–$200/hr, shift 45–65% of clients to monitoring subscriptions.
- Legal/ops: LLC with ≥$1M general liability; 50% non-refundable deposits defined as liquidated damages before ordering parts.
- Digital roadmap: compatibility checker, AR/3D views, AI assistant, client portal, GPU stock alerts, content marketing.
- Community: youth PC-build workshops, donation program (NIST 800-88 data purge, R2 recycling, 501(c)3 recipients, IRS Form 8283 for >$500 donations).

This summarizes the strategic, technical, and social pillars guiding WhatAPC’s sustainable, high-performance custom PC practice.

## API Endpoints

- `GET /api/inventory` - Retrieve inventory items (with optional search, filter, pagination params)
- `POST /api/inventory` - Add a new item
- `PUT /api/inventory/<id>` - Update an item
- `DELETE /api/inventory/<id>` - Delete an item

## Database

Uses SQLite database (`yourdatabase.db`) with the following schema:
- inventory_id (unique)
- item_type, brand, model, component
- qty, details, socket_or_interface
- status, used_in, ownership, test_status
- cooler_required, notes, photo_refs
- price_paid, source, seller
- location_bin, location_shelf, location_notes
