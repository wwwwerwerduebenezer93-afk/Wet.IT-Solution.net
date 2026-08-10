import base64,json,os,re,secrets
from pathlib import Path
from datetime import datetime,timedelta
from functools import wraps
from flask import Flask,abort,flash,redirect,render_template,request,session,url_for,jsonify,send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
from dotenv import load_dotenv
from tutor_engine import test_submission,ai_hint,SafetyError
import qrcode
from verification import send_email_code,send_sms_code
load_dotenv(); app=Flask(__name__)
app.config.update(SECRET_KEY=os.getenv("SECRET_KEY","development-only-key"),SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL","sqlite:///tutor.db"),SQLALCHEMY_TRACK_MODIFICATIONS=False)
db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),nullable=False); email=db.Column(db.String(160),unique=True,nullable=False); phone=db.Column(db.String(30),unique=True,nullable=True); password_hash=db.Column(db.String(255),nullable=False); role=db.Column(db.String(20),default="student"); email_verified=db.Column(db.Boolean,default=False,nullable=False); phone_verified=db.Column(db.Boolean,default=False,nullable=False); live_photo_path=db.Column(db.String(255),nullable=True); profile_picture_path=db.Column(db.String(255),nullable=True); live_photo_challenge=db.Column(db.String(120),nullable=True); latitude=db.Column(db.Float,nullable=True); longitude=db.Column(db.Float,nullable=True); location_accuracy=db.Column(db.Float,nullable=True); location_captured_at=db.Column(db.DateTime,nullable=True)
class Concept(db.Model):
    id=db.Column(db.Integer,primary_key=True); title=db.Column(db.String(120),nullable=False); summary=db.Column(db.Text,nullable=False); position=db.Column(db.Integer,default=1)
    exercises=db.relationship("Exercise",backref="concept",lazy=True)
class Exercise(db.Model):
    id=db.Column(db.Integer,primary_key=True); concept_id=db.Column(db.Integer,db.ForeignKey("concept.id"),nullable=False); title=db.Column(db.String(150),nullable=False); objective=db.Column(db.Text,nullable=False); prompt=db.Column(db.Text,nullable=False); starter_code=db.Column(db.Text,default=""); tests_json=db.Column(db.Text,nullable=False); hint1=db.Column(db.Text); hint2=db.Column(db.Text); hint3=db.Column(db.Text); difficulty=db.Column(db.Integer,default=1)
class Submission(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False); exercise_id=db.Column(db.Integer,db.ForeignKey("exercise.id"),nullable=False); code=db.Column(db.Text,nullable=False); status=db.Column(db.String(30)); passed=db.Column(db.Integer,default=0); total=db.Column(db.Integer,default=0); hint_level=db.Column(db.Integer,default=0); created_at=db.Column(db.DateTime,default=datetime.utcnow)
    student=db.relationship("User"); exercise=db.relationship("Exercise")
class Enrollment(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False); course_code=db.Column(db.String(30),nullable=False,default="CSC101"); course_title=db.Column(db.String(160),nullable=False,default="Introductory Computer Science"); registered_at=db.Column(db.DateTime,default=datetime.utcnow)
    student=db.relationship("User"); __table_args__=(db.UniqueConstraint("user_id","course_code",name="uq_student_course"),)
class VerificationCode(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("user.id"),nullable=False); channel=db.Column(db.String(10),nullable=False); code_hash=db.Column(db.String(255),nullable=False); expires_at=db.Column(db.DateTime,nullable=False); used=db.Column(db.Boolean,default=False); created_at=db.Column(db.DateTime,default=datetime.utcnow)
    user=db.relationship("User")

def login_required(fn):
    @wraps(fn)
    def inner(*a,**kw): return fn(*a,**kw) if session.get("user_id") else redirect(url_for("login"))
    return inner
def lecturer_required(fn):
    @wraps(fn)
    def inner(*a,**kw):
        if session.get("role")!="lecturer": flash("Lecturer access is required.","error"); return redirect(url_for("dashboard"))
        return fn(*a,**kw)
    return inner

def strong_password(value):
    return len(value)>=10 and re.search(r"[A-Z]",value) and re.search(r"[a-z]",value) and re.search(r"\d",value) and re.search(r"[^A-Za-z0-9]",value)
def normalize_phone(value):
    value=re.sub(r"[\s()-]","",value or "")
    if value.startswith("0"): value="+233"+value[1:]
    return value if re.fullmatch(r"\+?[1-9]\d{8,14}",value) else None
def save_live_photo(data,user_token):
    match=re.fullmatch(r"data:image/(jpeg|png);base64,([A-Za-z0-9+/=]+)",data or "")
    if not match: raise ValueError("Capture a live camera picture before registration.")
    raw=base64.b64decode(match.group(2),validate=True)
    if len(raw)>2_000_000 or len(raw)<2_000: raise ValueError("The live picture must be a valid image below 2 MB.")
    if not (raw.startswith(b"\xff\xd8\xff") or raw.startswith(b"\x89PNG\r\n\x1a\n")): raise ValueError("Unsupported live-picture format.")
    folder=Path(app.instance_path)/"verification_photos"; folder.mkdir(parents=True,exist_ok=True); path=folder/f"{user_token}.jpg"; path.write_bytes(raw); return str(path.relative_to(Path(app.instance_path)))
def save_uploaded_picture(upload,user_token):
    if not upload or not upload.filename: raise ValueError("Upload a clear profile or ID picture.")
    raw=upload.read(2_000_001)
    if len(raw)>2_000_000 or len(raw)<2_000: raise ValueError("Uploaded picture must be a valid JPEG or PNG below 2 MB.")
    extension="jpg" if raw.startswith(b"\xff\xd8\xff") else "png" if raw.startswith(b"\x89PNG\r\n\x1a\n") else None
    if not extension: raise ValueError("Only genuine JPEG and PNG pictures are accepted.")
    folder=Path(app.instance_path)/"verification_photos"; folder.mkdir(parents=True,exist_ok=True); path=folder/f"{user_token}-profile.{extension}"; path.write_bytes(raw); return str(path.relative_to(Path(app.instance_path)))
def parse_location(form):
    try: lat=float(form.get("latitude","")); lng=float(form.get("longitude","")); accuracy=float(form.get("location_accuracy",""))
    except (TypeError,ValueError): raise ValueError("Allow automatic location access before registration.")
    if not (-90<=lat<=90 and -180<=lng<=180 and 0<=accuracy<=100000): raise ValueError("The captured location is invalid.")
    return lat,lng,accuracy
def issue_verification_codes(user):
    VerificationCode.query.filter_by(user_id=user.id,used=False).update({"used":True})
    email_code=f"{secrets.randbelow(1_000_000):06d}"; phone_code=f"{secrets.randbelow(1_000_000):06d}"; expiry=datetime.utcnow()+timedelta(minutes=10)
    db.session.add_all([VerificationCode(user_id=user.id,channel="email",code_hash=generate_password_hash(email_code),expires_at=expiry),VerificationCode(user_id=user.id,channel="phone",code_hash=generate_password_hash(phone_code),expires_at=expiry)]); db.session.commit()
    email_sent=phone_sent=False
    try: email_sent=send_email_code(user.email,email_code)
    except Exception: pass
    try: phone_sent=send_sms_code(user.phone,phone_code)
    except Exception: pass
    session["verification_preview"]={"email":email_code,"phone":phone_code} if os.getenv("VERIFICATION_MODE","development")=="development" else {}
    return email_sent,phone_sent
def verified_login(user,password):
    return user and check_password_hash(user.password_hash,password)

@app.route("/")
def index(): return redirect(url_for("dashboard")) if session.get("user_id") else render_template("index.html")
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        user=User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if verified_login(user,request.form["password"]):
            if not (user.email_verified and user.phone_verified and user.live_photo_path): session["pending_user_id"]=user.id; issue_verification_codes(user); flash("Complete email and phone verification.","error"); return redirect(url_for("verify_account"))
            session.clear(); session.update(user_id=user.id,name=user.name,role=user.role); target="lecturer" if user.role=="lecturer" else "staff_dashboard" if user.role=="staff" else "dashboard"; return redirect(url_for(target))
        flash("Invalid email or password.","error")
    return render_template("login.html")
@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        email=request.form["email"].strip().lower()
        phone=normalize_phone(request.form.get("phone")); password=request.form["password"]
        if User.query.filter_by(email=email).first(): flash("That email is already registered.","error")
        elif not phone: flash("Enter a valid Ghana or international phone number.","error")
        elif User.query.filter_by(phone=phone).first(): flash("That phone number is already registered.","error")
        elif not strong_password(password): flash("Password needs 10+ characters with uppercase, lowercase, number and symbol.","error")
        else:
            token=secrets.token_hex(16)
            try:
                photo=save_live_photo(request.form.get("live_photo"),token); profile_picture=save_uploaded_picture(request.files.get("profile_picture"),token); lat,lng,accuracy=parse_location(request.form)
            except ValueError as err: flash(str(err),"error"); return render_template("register.html",challenge=session.get("live_challenge"))
            user=User(name=request.form["name"].strip(),email=email,phone=phone,password_hash=generate_password_hash(password),role="student",live_photo_path=photo,profile_picture_path=profile_picture,live_photo_challenge=session.get("live_challenge"),latitude=lat,longitude=lng,location_accuracy=accuracy,location_captured_at=datetime.utcnow()); db.session.add(user); db.session.commit(); session["pending_user_id"]=user.id; issue_verification_codes(user); return redirect(url_for("verify_account"))
    if not session.get("live_challenge"): session["live_challenge"]=secrets.choice(["Turn your face slightly left","Turn your face slightly right","Look directly at the camera"])
    return render_template("register.html",challenge=session["live_challenge"])
@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("index"))

@app.route("/verify-account",methods=["GET","POST"])
def verify_account():
    user=User.query.get(session.get("pending_user_id")) if session.get("pending_user_id") else None
    if not user: flash("Start registration or sign in first.","error"); return redirect(url_for("register"))
    if request.method=="POST":
        now=datetime.utcnow(); valid=True
        for channel,field in [("email","email_code"),("phone","phone_code")]:
            record=VerificationCode.query.filter_by(user_id=user.id,channel=channel,used=False).order_by(VerificationCode.id.desc()).first(); value=request.form.get(field,"").strip()
            if not record or record.expires_at<now or not check_password_hash(record.code_hash,value): valid=False
            else: record.used=True
        if valid:
            user.email_verified=True; user.phone_verified=True; db.session.commit(); session.clear(); session.update(user_id=user.id,name=user.name,role=user.role); flash("Account verified successfully.","success"); return redirect(url_for("dashboard"))
        db.session.rollback(); flash("One or both codes are invalid or expired.","error")
    return render_template("verify_account.html",user=user,preview=session.get("verification_preview",{}))
@app.post("/resend-verification")
def resend_verification():
    user=User.query.get(session.get("pending_user_id")) if session.get("pending_user_id") else None
    if not user: return redirect(url_for("register"))
    issue_verification_codes(user); flash("New verification codes were issued.","success"); return redirect(url_for("verify_account"))

def role_login(expected_role,label):
    if request.method=="POST":
        user=User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if user and user.role==expected_role and verified_login(user,request.form["password"]):
            if not (user.email_verified and user.phone_verified and user.live_photo_path): session["pending_user_id"]=user.id; issue_verification_codes(user); return redirect(url_for("verify_account"))
            session.clear(); session.update(user_id=user.id,name=user.name,role=user.role)
            return redirect(url_for("staff_dashboard" if expected_role=="staff" else "lecturer" if expected_role=="lecturer" else "dashboard"))
        flash(f"Invalid {label.lower()} credentials.","error")
    return render_template("portal_login.html",portal=label,role=expected_role)
@app.route("/student/login",methods=["GET","POST"])
def student_login(): return role_login("student","Student Portal")
@app.route("/teacher/login",methods=["GET","POST"])
def teacher_login(): return role_login("lecturer","Teacher Portal")
@app.route("/staff/login",methods=["GET","POST"])
def staff_login(): return role_login("staff","Staff Portal")

@app.route("/course-registration",methods=["GET","POST"])
@login_required
def course_registration():
    if session.get("role")!="student": flash("Course registration is for student accounts.","error"); return redirect(url_for("system_links"))
    current=Enrollment.query.filter_by(user_id=session["user_id"],course_code="CSC101").first()
    if request.method=="POST" and not current:
        current=Enrollment(user_id=session["user_id"]); db.session.add(current); db.session.commit(); flash("CSC101 registered successfully.","success")
    return render_template("course_registration.html",current=current)

@app.route("/staff")
@login_required
def staff_dashboard():
    if session.get("role")!="staff": flash("Staff access is required.","error"); return redirect(url_for("system_links"))
    return render_template("staff.html",users=User.query.count(),verified=User.query.filter_by(email_verified=True,phone_verified=True).count(),enrollments=Enrollment.query.count(),attempts=Submission.query.count())
@app.route("/staff/verifications")
@login_required
def staff_verifications():
    if session.get("role")!="staff": abort(403)
    users=User.query.filter(User.role=="student").order_by(User.id.desc()).all(); return render_template("staff_verifications.html",users=users)
@app.route("/staff/verification-image/<int:user_id>/<kind>")
@login_required
def verification_image(user_id,kind):
    if session.get("role")!="staff": abort(403)
    user=User.query.get_or_404(user_id); relative=user.profile_picture_path if kind=="profile" else user.live_photo_path if kind=="live" else None
    if not relative or relative=="demo-account": abort(404)
    base=Path(app.instance_path).resolve(); path=(base/relative).resolve()
    if base not in path.parents or not path.is_file(): abort(404)
    return send_file(path)

PORTAL_LINKS=[("Homepage","/","home"),("Student login","/student/login","student-login"),("Teacher login","/teacher/login","teacher-login"),("Staff login","/staff/login","staff-login"),("Course registration","/course-registration","course-registration"),("System link directory","/links","system-links")]
def generate_qr_codes():
    base=os.getenv("PUBLIC_BASE_URL","http://127.0.0.1:5000").rstrip('/'); folder=Path(app.static_folder)/"qr"; folder.mkdir(parents=True,exist_ok=True)
    for _,path,name in PORTAL_LINKS: qrcode.make(base+path).save(folder/f"{name}.png")
@app.route("/links")
def system_links():
    base=os.getenv("PUBLIC_BASE_URL","http://127.0.0.1:5000").rstrip('/'); return render_template("links.html",links=[{"title":t,"url":base+p,"name":n} for t,p,n in PORTAL_LINKS],base=base)

@app.route("/dashboard")
@login_required
def dashboard():
    if session.get("role")=="lecturer": return redirect(url_for("lecturer"))
    concepts=Concept.query.order_by(Concept.position).all(); done={s.exercise_id for s in Submission.query.filter_by(user_id=session["user_id"],status="passed").all()}
    return render_template("dashboard.html",concepts=concepts,done=done,total=Exercise.query.count())
@app.route("/exercise/<int:eid>")
@login_required
def exercise(eid):
    ex=Exercise.query.get_or_404(eid); last=Submission.query.filter_by(user_id=session["user_id"],exercise_id=eid).order_by(Submission.id.desc()).first()
    return render_template("exercise.html",ex=ex,last=last)
@app.post("/api/exercise/<int:eid>/submit")
@login_required
def submit(eid):
    ex=Exercise.query.get_or_404(eid); code=(request.get_json() or {}).get("code",""); tests=json.loads(ex.tests_json)
    try: result=test_submission(code,tests,int(os.getenv("CODE_TIMEOUT_SECONDS","3")))
    except SafetyError as err: result={"status":"blocked","stdout":"","stderr":str(err),"passed":0,"total":len(tests),"details":[]}
    complete=result["total"]>0 and result["passed"]==result["total"]
    sub=Submission(user_id=session["user_id"],exercise_id=eid,code=code,status="passed" if complete else result["status"],passed=result["passed"],total=result["total"]); db.session.add(sub); db.session.commit()
    return jsonify({**result,"submission_id":sub.id,"complete":complete})
@app.post("/api/exercise/<int:eid>/hint")
@login_required
def hint(eid):
    ex=Exercise.query.get_or_404(eid); data=request.get_json() or {}; sub=Submission.query.filter_by(user_id=session["user_id"],exercise_id=eid).order_by(Submission.id.desc()).first(); level=min((sub.hint_level if sub else 0)+1,3)
    result={"status":sub.status if sub else "not_run","passed":sub.passed if sub else 0,"total":sub.total if sub else len(json.loads(ex.tests_json)),"stderr":data.get("stderr","")}; text=ai_hint(ex,data.get("code",""),result,level)
    if sub: sub.hint_level=level; db.session.commit()
    return jsonify({"level":level,"hint":text})

@app.route("/lecturer")
@login_required
@lecturer_required
def lecturer():
    students=User.query.filter_by(role="student").all(); recent=Submission.query.order_by(Submission.created_at.desc()).limit(100).all(); stats=[]
    for user in students:
        ss=[s for s in recent if s.user_id==user.id]; stats.append({"student":user,"complete":len({s.exercise_id for s in ss if s.status=="passed"}),"attempts":len(ss),"hints":sum(s.hint_level for s in ss)})
    return render_template("lecturer.html",stats=stats,exercise_count=Exercise.query.count(),recent=recent[:12])

def seed():
    demos=[("Demo Student","student@tutor.local","+233200000001","Student123!","student"),("Course Teacher","teacher@tutor.local","+233200000002","Teacher123!","lecturer"),("System Staff","staff@tutor.local","+233200000003","Staff123!","staff")]
    for name,email,phone,password,role in demos:
        if not User.query.filter_by(email=email).first(): db.session.add(User(name=name,email=email,phone=phone,password_hash=generate_password_hash(password),role=role,email_verified=True,phone_verified=True,live_photo_path="demo-account"))
    if Concept.query.count()==0:
        topics=[("Variables and Output","Store values, calculate and display results."),("Selection","Use Boolean expressions and conditions."),("Loops","Repeat operations safely."),("Functions","Create reusable units of logic."),("Lists and Strings","Process collections and text.")]
        for i,(title,summary) in enumerate(topics,1): db.session.add(Concept(title=title,summary=summary,position=i))
        db.session.flush()
        rows=[
        (1,"Cedi Total","Use variables and arithmetic.","Set price to 25 and quantity to 4. Print exactly: Total: GHS 100","price = 25\nquantity = 4\n# Calculate and print the total\n","Total: GHS 100","What operation combines unit price and quantity?","Store the multiplication in total.","Use print('Total: GHS', total)."),
        (2,"Grade Classifier","Apply ordered conditions.","Set score to 72. Print Distinction for 70 or above, Pass for 50–69, otherwise Retry.","score = 72\n# Write your decision below\n","Distinction","Start with the highest boundary.","Use if, elif and else.","The first condition is score >= 70."),
        (3,"Sum 1 to 5","Use a loop accumulator.","Use a loop to calculate 1 + 2 + 3 + 4 + 5 and print 15.","total = 0\n# Add a loop\nprint(total)\n","15","An accumulator changes inside the loop.","range(1, 6) gives the required values.","Update with total += number."),
        (4,"Welcome Function","Define and call a function.","Create greet(name) that returns 'Welcome, ' plus the name. Print greet('Ama').","def greet(name):\n    pass\n\nprint(greet('Ama'))\n","Welcome, Ama","A function can return a string.","Join 'Welcome, ' and name.","Replace pass with a return statement."),
        (5,"Count Vowels","Iterate through a string.","Count vowels in 'education' and print 5.","word = 'education'\ncount = 0\n# Inspect each character\nprint(count)\n","5","Visit each character and test membership.","Use for character in word.","Increase count when character in 'aeiou'.")]
        for c,title,obj,prompt,start,expected,h1,h2,h3 in rows: db.session.add(Exercise(concept_id=c,title=title,objective=obj,prompt=prompt,starter_code=start,tests_json=json.dumps([{"name":"Expected output","expected":expected,"visible":True}]),hint1=h1,hint2=h2,hint3=h3))
    db.session.commit()

@app.cli.command("init-db")
def init_db(): db.create_all(); seed(); print("Database initialized.")
with app.app_context(): db.create_all(); seed(); generate_qr_codes()
if __name__=="__main__": app.run(host="0.0.0.0",port=5000,debug=os.getenv("FLASK_DEBUG")=="1")
