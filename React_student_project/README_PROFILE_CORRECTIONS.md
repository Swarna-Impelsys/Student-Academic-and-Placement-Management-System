# SAMS Profile Correction Frontend Update

This archive contains the existing React project plus the Profile Correction frontend additions.

## New pages
- `src/pages/ProfileCorrectionRequests.jsx` — Student/Teacher correction request form, request history, evidence upload, OCR status display.
- `src/pages/RegistrationOfficerDashboard.jsx` — Registration Officer request queue, evidence/OCR review, and approve/reject/request-more-evidence actions.
- `src/pages/ProfileCorrections.css` — styles for the new pages.

## Existing files updated
- `src/App.jsx` — routes for the Registration Officer dashboard and Student/Teacher profile corrections.
- `src/components/ProtectedRoute.jsx` — Registration Officer dashboard redirect.
- `src/components/Layout.jsx` — role-aware dashboard link and correction navigation.
- `src/pages/Login.jsx` — accepts common Registration Officer role-name formats.

## API endpoints used
- `GET/POST /api/profile-corrections/`
- `POST /api/profile-corrections/<id>/documents/`
- `PATCH /api/profile-corrections/<id>/review/`

The frontend assumes Django runs at `http://127.0.0.1:8001/api/`, matching the existing `src/services/api.js`.

## Run locally
From the project folder in PowerShell:
1. `npm install` (only if dependencies are not installed)
2. `npm run dev`
3. Open the Vite URL shown in the terminal.

The frontend build could not be verified in the packaging environment because the uploaded dependency folder did not contain a runnable Vite binary. Run `npm run build` locally after applying the update.

## Notes
- The feature supports Student fields `name`, `date_of_birth`, `address`, `phone`, `email`, and Teacher fields `first_name`, `last_name`, `email`.
- Profile changes are not applied by the frontend; the backend applies them after officer approval.
- OCR is shown as a review aid and is not presented as proof of document authenticity.
- The archive excludes `node_modules` and `.git` to keep the source package smaller. Existing unrelated source modules are preserved.
