# Portal links and QR codes

Default demonstration address: `http://127.0.0.1:5000`

| Part of the system | Default link | QR image |
|---|---|---|
| Homepage | http://127.0.0.1:5000/ | static/qr/home.png |
| Student login | http://127.0.0.1:5000/student/login | static/qr/student-login.png |
| Teacher login | http://127.0.0.1:5000/teacher/login | static/qr/teacher-login.png |
| Staff login | http://127.0.0.1:5000/staff/login | static/qr/staff-login.png |
| Course registration | http://127.0.0.1:5000/course-registration | static/qr/course-registration.png |
| Complete link directory | http://127.0.0.1:5000/links | static/qr/system-links.png |

For deployment, set `PUBLIC_BASE_URL=https://your-real-domain.example` in `.env` and restart the application. The QR images will be regenerated automatically with the new address.
