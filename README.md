# 🛡️ DisasterShield AI

### AI-Driven Disaster Management & Emergency Response Platform

DisasterShield AI is a web-based disaster management platform designed to help citizens report disasters, receive emergency alerts, access risk information, and quickly find emergency assistance.

The platform provides separate Citizen and Administrator portals with real-time disaster information, GIS-based visualization, emergency SOS support, disaster reporting, verification and risk management.

---

## 🚀 Key Features

### 👤 Citizen Portal

- Citizen Registration
- Secure Citizen Login
- Citizen Dashboard
- Personal Profile
- Disaster Reporting
- My Reports Tracking
- Report Status Monitoring
- Emergency SOS
- Emergency Services Information
- Emergency Preparedness Guides
- Emergency Checklist
- GIS Disaster Map
- Disaster Risk Information
- Active Disaster Alerts
- Live Emergency Broadcast
- Location-based emergency assistance
- Mobile-friendly interface
- Logout and session management

---

### 🛠️ Administrator Portal

- Secure Administrator Login
- Admin Dashboard
- View Disaster Reports
- Verify Disaster Reports
- Reject Invalid Reports
- Monitor Disaster Activities
- Manage Emergency Alerts
- Risk Data Management
- Disaster Data Sources
- Report Verification Workflow
- Administrative Access Control

---

## 🚨 Emergency Management

The Emergency module provides citizens with quick access to important emergency information.

### Emergency Services

- 🚑 Ambulance
- 🚓 Police
- 🚒 Fire & Rescue
- 🆘 National Emergency Assistance

### Emergency Preparedness

- Emergency safety guides
- Disaster preparedness checklist
- Important emergency instructions
- Location-based emergency links

---

## 🗺️ GIS Disaster Map

DisasterShield AI includes a GIS-based map interface for visualizing disaster-related information.

The map can be used to display:

- Disaster reports
- Disaster locations
- Emergency alerts
- Risk information
- Geographic disaster data

This helps users understand the geographical distribution of disaster events.

---

## 🚨 Disaster Reporting System

Citizens can report disasters through the Citizen Portal.

Supported disaster scenarios can include:

- Flood
- Fire
- Earthquake
- Landslide
- Cyclone
- Other emergency situations

### Report Workflow

Citizen submits report  
↓  
Report stored in database  
↓  
Administrator reviews report  
↓  
Administrator verifies/rejects report  
↓  
Verified information becomes available to the system

---

## 🔔 Disaster Alert System

The platform provides active disaster alerts to citizens.

Alerts can contain:

- Disaster type
- Severity level
- Location
- Alert message
- Timestamp
- Active/inactive status

Severity levels include:

- 🟢 Low
- 🟡 Moderate
- 🟠 High
- 🔴 Critical

---

## 🆘 Emergency SOS

The Emergency SOS module allows citizens to quickly access emergency assistance.

It provides:

- Emergency assistance options
- Current-location based support
- Emergency service information
- Safety instructions
- Emergency preparedness resources

---

## 👥 User Roles

### Citizen

Citizens can:

1. Register an account
2. Login securely
3. Report disasters
4. View their reports
5. Monitor report status
6. View active alerts
7. Access GIS maps
8. Use Emergency SOS
9. Access emergency guides

### Administrator

Administrators can:

1. Login securely
2. View submitted reports
3. Verify reports
4. Reject reports
5. Manage disaster-related information
6. Monitor alerts
7. Manage risk information
8. Monitor system activities

---

## 🔐 Security

The application implements role-based access control.

### Security mechanisms

- Citizen/Admin role separation
- Session-based authentication
- Protected administrator routes
- Protected citizen routes
- Unauthorized access prevention
- Authentication API
- Logout functionality
- Password-based authentication

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │      User           │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Flask Web Server   │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
   Citizen Portal       Admin Portal        Emergency Module
          │                    │                    │
          ▼                    ▼                    ▼
    Disaster Reports     Verification          SOS / Guides
    GIS Map              Alerts                Services
    Alerts               Risk Data             Checklist
          │                    │                    │
          └────────────────────┼────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │     PostgreSQL      │
                    │      Database       │
                    └─────────────────────┘
---

## 🏗️ Technology Stack

### Backend
- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate

### Database
- PostgreSQL

### Frontend
- HTML5
- CSS3
- JavaScript

### Mapping / GIS
- GIS-based disaster visualization
- Location-based disaster information

### Development Environment
- Termux
- Python Virtual Environment
- Git & GitHub

---

## 📂 Project Structure

```text
DisasterShield_AI/
│
├── app.py
├── config.py
├── models.py
├── create_admin.py
├── requirements.txt
│
├── routes/
│   ├── auth.py
│   ├── admin.py
│   ├── alerts.py
│   ├── reports.py
│   ├── risk.py
│   ├── gis.py
│   ├── emergency.py
│   └── data.py
│
├── services/
│   └── auth_service.py
│
├── templates/
│   ├── admin.html
│   ├── admin_dashboard.html
│   ├── admin_login.html
│   ├── citizen_dashboard.html
│   ├── citizen_login.html
│   ├── citizen_register.html
│   ├── emergency.html
│   ├── map.html
│   └── report_disaster.html
│
├── static/
│   ├── css/
│   └── js/
│
└── migrations/


##🔌 API Structure
The application provides REST-style API endpoints for different modules.
Authentication
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me

##Reports
POST /api/reports
GET  /api/reports/my

##Alerts
GET  /api/alerts
POST /api/alerts

##Risk
GET  /api/risk
POST /api/risk
