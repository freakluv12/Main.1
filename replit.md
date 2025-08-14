# Overview

This is a comprehensive auto business management system built with Flask, designed to track and manage various aspects of an automotive business including car inventory, rental operations, parts management, and financial analytics. The application provides a centralized dashboard for monitoring expenses, rental income, parts sales, and overall business profitability.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask web framework with Python
- **Database**: SQLite database using SQLAlchemy ORM with DeclarativeBase
- **Models**: Six main entities - Car, Expense, Client, Rental, Payment, DisassemblyRecord, Supplier, Part, and Sale
- **Routing**: Centralized route handling in routes.py with comprehensive CRUD operations
- **Session Management**: Flask sessions with configurable secret key

## Frontend Architecture
- **Template Engine**: Jinja2 templating with Bootstrap dark theme
- **UI Framework**: Bootstrap with Replit's dark theme integration
- **Icons**: Font Awesome icon library
- **Charts**: Chart.js for data visualization and analytics
- **Responsive Design**: Mobile-first approach with Bootstrap grid system

## Data Model Design
- **Car Management**: Tracks vehicle inventory with status (active, rented, disassembled)
- **Financial Tracking**: Separate models for expenses, rental payments, and parts sales
- **Rental System**: Client management with rental contracts and payment tracking
- **Parts Inventory**: Parts catalog with supplier relationships and quantity tracking
- **Audit Trail**: Timestamp tracking for all major operations

## Report Generation
- **PDF Export**: ReportLab integration for generating business reports
- **Analytics Dashboard**: Monthly profit/loss calculations and trend analysis
- **Real-time Statistics**: Live dashboard with key performance indicators

## Database Configuration
- **Connection Pooling**: Configured with pool_recycle and pool_pre_ping for reliability
- **Auto-initialization**: Database tables created automatically on application startup
- **Environment Variables**: Database URL configurable via environment variables

# External Dependencies

## Core Dependencies
- **Flask**: Web framework and application server
- **SQLAlchemy**: Database ORM and connection management
- **Werkzeug**: WSGI utilities and proxy handling

## Frontend Libraries
- **Bootstrap**: CSS framework (Replit dark theme variant)
- **Font Awesome**: Icon library for UI elements
- **Chart.js**: JavaScript charting library for analytics

## Report Generation
- **ReportLab**: PDF generation library for business reports
- **TTFont**: Font handling for PDF documents

## Development Tools
- **Logging**: Built-in Python logging for debugging
- **ProxyFix**: Werkzeug middleware for proper URL generation behind proxies

## Database
- **SQLite**: Default database (configurable to other databases via DATABASE_URL)
- **Connection pooling**: Automatic connection management and health checks