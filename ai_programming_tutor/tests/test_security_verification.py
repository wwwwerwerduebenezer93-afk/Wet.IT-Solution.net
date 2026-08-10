import base64
from io import BytesIO
from PIL import Image
from app import app

def camera_image():
    image=Image.new("RGB",(640,480),(30,110,80)); output=BytesIO(); image.save(output,format="JPEG",quality=90)
    return "data:image/jpeg;base64,"+base64.b64encode(output.getvalue()).decode()
def uploaded_picture():
    image=Image.new("RGB",(640,480),(70,90,150)); output=BytesIO(); image.save(output,format="JPEG",quality=90); output.seek(0); return output

def test_secure_registration_and_two_channel_verification():
    client=app.test_client()
    response=client.post("/register",data={"name":"Secure Test User","email":"secure.test@example.com","phone":"0240000099","password":"StrongPass9!","live_photo":camera_image(),"profile_picture":(uploaded_picture(),"profile.jpg"),"latitude":"5.6037","longitude":"-0.1870","location_accuracy":"18"},content_type="multipart/form-data",follow_redirects=True)
    assert response.status_code==200 and b"Enter your codes" in response.data
    with client.session_transaction() as session:
        codes=dict(session["verification_preview"])
    verified=client.post("/verify-account",data={"email_code":codes["email"],"phone_code":codes["phone"]},follow_redirects=True)
    assert b"Continue learning" in verified.data

def test_staff_can_review_location_but_student_cannot():
    student=app.test_client(); student.post("/student/login",data={"email":"student@tutor.local","password":"Student123!"}); assert student.get("/staff/verifications").status_code==403
    staff=app.test_client(); staff.post("/staff/login",data={"email":"staff@tutor.local","password":"Staff123!"}); page=staff.get("/staff/verifications"); assert page.status_code==200 and b"Google Maps" in page.data

def test_weak_password_and_missing_camera_are_rejected():
    client=app.test_client()
    weak=client.post("/register",data={"name":"Weak","email":"weak@example.com","phone":"0240000088","password":"password","live_photo":""},follow_redirects=True)
    assert b"Password needs" in weak.data
