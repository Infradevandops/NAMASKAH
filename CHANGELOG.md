# Changelog

## [2.0.0] - 2025-01-15

### Added
- **Security**: HTTPS enforcement, security headers (HSTS, X-Frame-Options, CSP)
- **Security**: Request ID tracking (X-Request-ID)
- **Security**: Redis rate limiting (100 req/min)
- **Security**: Sentry error tracking integration
- **Auth**: Email verification on registration
- **Auth**: Password reset flow (1-hour token expiry)
- **Auth**: Google OAuth Sign-In
- **Rentals**: Number rental service (1hr-30days)
- **Rentals**: Rental pricing tiers (₵2-₵150)
- **Rentals**: Extend/release with 50% refund
- **Verification**: Voice call support (50% premium)
- **Verification**: Voice call transcription endpoint
- **Payment**: Paystack webhook integration
- **Payment**: Payment verification endpoint
- **Payment**: Auto-credit on successful payment
- **API**: Enhanced OpenAPI documentation
- **API**: 11 new endpoints (rentals, voice, payments)
- **Testing**: 70%+ test coverage with pytest
- **Testing**: 5 test modules, 20+ test cases
- **Frontend**: Forgot password modal
- **Frontend**: Google Sign-In button persistence fix
- **Frontend**: Payment verification on callback

### Changed
- Database schema: Added rental, voice, email verification fields
- Verification model: Added capability, call_duration, transcription, audio_url
- User model: Added email_verified, verification_token, reset_token fields
- Pricing: Voice verification 50% premium
- CORS: Environment-based origins (restricted)

### Fixed
- Google Sign-In buttons disappearing on tab switch
- Rate limiting now persistent with Redis
- Duplicate payment prevention

### Security
- All secrets in environment variables
- HTTPS enforced in production
- Webhook signature verification
- Password reset token expiration
- Email verification required

## [1.0.0] - Initial Release

### Added
- Basic SMS verification
- JWT authentication
- SQLite database
- Web interface
- TextVerified integration
