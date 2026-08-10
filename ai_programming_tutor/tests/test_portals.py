from app import app

def test_public_portal_links():
    client=app.test_client()
    for path in ["/student/login","/teacher/login","/staff/login","/links"]:
        assert client.get(path).status_code==200

def test_teacher_and_staff_logins():
    client=app.test_client()
    teacher=client.post("/teacher/login",data={"email":"teacher@tutor.local","password":"Teacher123!"},follow_redirects=True)
    assert b"Course learning signals" in teacher.data
    client.get("/logout")
    staff=client.post("/staff/login",data={"email":"staff@tutor.local","password":"Staff123!"},follow_redirects=True)
    assert b"System overview" in staff.data

def test_student_course_registration():
    client=app.test_client()
    client.post("/student/login",data={"email":"student@tutor.local","password":"Student123!"})
    page=client.get("/course-registration")
    assert page.status_code==200 and b"CSC101" in page.data
    result=client.post("/course-registration",follow_redirects=True)
    assert result.status_code==200 and (b"Registered" in result.data or b"registered" in result.data)
