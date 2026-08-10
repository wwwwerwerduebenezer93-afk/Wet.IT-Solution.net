# Security verification module

## Registration evidence

Every new student account requires:

1. A unique email address.
2. A unique phone number, normalized to international form.
3. A password of at least 10 characters containing uppercase, lowercase, number and symbol.
4. A current camera picture captured in the browser while following a displayed pose prompt.
5. A separately uploaded profile or ID picture in genuine JPEG or PNG format.
6. Automatic browser geolocation, including latitude, longitude, accuracy and capture time.
7. Consent to store the pictures and precise location according to the institution's retention policy.

## Verification codes

Separate six-digit codes are created for email and phone. Only password hashes of the codes are stored. Codes expire after 10 minutes and become unusable after successful verification or code reissue.

`VERIFICATION_MODE=development` displays codes on the verification page for demonstrations. In production, configure SMTP and the SMS webhook variables, then set `VERIFICATION_MODE=production`.

## Picture handling

The backend accepts JPEG or PNG camera data only, checks the file signature and enforces a 2 MB limit. Pictures are stored under the private Flask instance directory, excluded from source control and the distribution ZIP.

This feature provides a live camera capture for identity review. It does not perform automated biometric face matching or certified liveness detection. Use an approved identity-verification provider if those capabilities are required.

Authorized staff can compare the uploaded and live pictures through `/staff/verifications`. The same protected page creates a Google Maps link from the stored coordinates. The application does not expose the private image directory publicly.

## Production requirements

- HTTPS is required for browser camera access outside localhost.
- Encrypt verification pictures and sensitive data at rest.
- Restrict precise location and picture access to specifically authorized staff.
- Establish explicit access, retention and deletion policies.
- Add rate limits for registration, login, resend and code attempts.
- Add CSRF protection, secure cookies and an audit trail.
- Obtain institutional and ethics approval before collecting real student identity data.
