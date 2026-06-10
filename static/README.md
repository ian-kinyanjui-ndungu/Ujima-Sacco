# Ujima SACCO Frontend

A modern, responsive web interface for the Ujima SACCO microfinance platform, built with HTML, CSS, and JavaScript.

## 🎨 Design Features

- **Color Scheme**: White and Brown theme
  - Primary Brown: #8B6F47
  - Dark Brown: #6B5434
  - Light Brown: #D4A574
  - Cream White: #FFF8F0

- **Responsive Design**: Mobile-friendly layout that works on all screen sizes
- **Accessibility**: WCAG compliant with keyboard navigation support
- **Modern UI**: Clean, professional interface with smooth animations

## 📁 File Structure

```
frontend/
├── index.html              # Landing page with system info and features
├── app.html                # Loan application form
├── dashboard.html          # Member dashboard and chat interface
├── admin-dashboard.html    # Loan officer review dashboard
├── styles.css              # Global styles with white/brown theme
├── app.js                  # JavaScript utilities and API integration
└── README.md               # This file
```

## 🚀 Features

### Public Pages

1. **Landing Page (index.html)**
   - Overview of Ujima SACCO services
   - Real-time system metrics
   - Feature highlights
   - Call-to-action for loan application

2. **Loan Application (app.html)**
   - Comprehensive application form
   - Personal and financial information collection
   - Household details
   - Loan amount and repayment terms
   - Form validation and error handling

### Member Pages

3. **Member Dashboard (dashboard.html)**
   - Member profile lookup
   - Application status tracking
   - Conversation history
   - Financial summary
   - SMS chat interface with AI agents

### Admin Pages

4. **Admin Dashboard (admin-dashboard.html)**
   - System telemetry and metrics
   - Anomaly alerts
   - Loan review queue
   - Human decision interface
   - Compliance configuration display

## 🔗 API Integration

The frontend integrates with the FastAPI backend at `http://127.0.0.1:8000`

### Available Endpoints

- `GET /` - System status
- `POST /sms/inbound` - SMS/USSD message processing
- `GET /human/queue` - Review queue for loan officers
- `POST /human/takeover` - Submit human decision
- `GET /telemetry/status` - System telemetry and metrics

## 📱 Pages Overview

### Navigation Bar
- Fixed navigation with links to all pages
- Active page indicator
- Brown color scheme for branding

### Landing Page Components
- Hero section with CTA button
- 6 feature cards showcasing benefits
- Real-time metrics dashboard
- 4-step process explanation
- Footer with compliance notice

### Application Form
- 5 fieldsets: Personal, Financial, Household, Loan Details, Terms
- Input validation
- Dynamic form handling
- SMS backend integration

### Member Dashboard
- Member ID lookup
- Profile information display
- Loan status cards
- Conversation history
- Live SMS chat interface

### Admin Dashboard
- System metrics (4 KPIs)
- Anomaly alerts with severity levels
- Application review queue
- Modal review interface
- Decision submission with reasons

## 🎯 Color Usage

| Element | Color | Hex |
|---------|-------|-----|
| Primary Actions | Dark Brown | #6B5434 |
| Secondary Actions | Light Brown | #D4A574 |
| Backgrounds | Cream White | #FFF8F0 |
| Text | Dark Gray | #333333 |
| Borders | Light Tan | #E8D4C0 |

## ⚙️ JavaScript Features

### Global Functions (window.ujimaSacco)
- `loadTelemetryData()` - Fetch system metrics
- `formatCurrency(value)` - Format as KES currency
- `formatDate(dateString)` - Format dates
- `validateLoanAmount(amount)` - Validate loan range
- `validateRepaymentDate(dateString)` - Validate future date
- `calculateFinancialScore(profile)` - Score member profile
- `sendSmsToBackend(memberId, message)` - Send SMS to backend
- `getHumanQueue()` - Fetch applications pending review
- `submitHumanDecision(memberId, decision, reason)` - Submit review decision

### Features
- CORS error handling
- Real-time data updates
- Form validation
- Modal dialogs
- Chat interface
- Auto-refresh telemetry

## 🔒 Security & Compliance

- Kenya Data Protection Act 2022 compliant
- No sensitive data stored locally
- HTTPS recommended for production
- CORS properly configured
- Input validation on all forms

## 📋 Form Validation

### Loan Application
- Member ID: Required
- Name: Required
- Loan Amount: 1,000 - 500,000 KES
- Repayment Date: Must be in future
- Terms acceptance: Required checkbox

### Member Dashboard
- Member ID: Used for lookup
- Chat messages: Auto-sends to SMS API

### Admin Dashboard
- Decision: Radio select (approve/deny)
- Reason: Text area required
- All submissions sent to backend

## 🖥️ Responsive Breakpoints

- **Desktop**: Full multi-column layouts
- **Tablet**: 1-2 column grids
- **Mobile**: Single column, optimized touch targets

## 🚀 Getting Started

1. Ensure the FastAPI backend is running on `http://127.0.0.1:8000`
2. Open `index.html` in a web browser
3. Navigate between pages using the top navigation bar
4. Access forms and dashboards as needed

## 📊 Telemetry

The system automatically loads telemetry data:
- On page load
- Every 30 seconds (auto-refresh)
- When manually triggered

Metrics displayed:
- Total applications
- Approved loans
- Denied loans
- Escalated cases
- System status

## 🎨 Customization

To modify the color scheme, edit the CSS variables in `styles.css`:

```css
:root {
    --primary-brown: #8B6F47;
    --dark-brown: #6B5434;
    --light-brown: #D4A574;
    --cream-white: #FFF8F0;
    /* ... more colors ... */
}
```

## ⚡ Performance

- Lightweight CSS (~35KB)
- Minimal JavaScript (~15KB)
- No external dependencies
- Fast page load times
- Smooth animations with CSS transitions

## 🐛 Known Limitations

- Member endpoint (`/member/{id}`) not yet implemented in backend
- Briefing packets are placeholder text
- Chat interface stores messages in memory (lost on refresh)
- No authentication/authorization UI

## 📞 Support

For issues or questions about the frontend, check:
1. Browser console for errors
2. Network tab for API calls
3. Backend server logs

## 📄 License

Ujima SACCO © 2026. All rights reserved.
Kenya Data Protection Act 2022 Compliant.
