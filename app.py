from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, text
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY  # 从环境变量 / .env 读取，不写死在源码里
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
db = SQLAlchemy(app)


class Patient(db.Model):
    __tablename__ = 'patient'
    P_no = db.Column(db.String(10), primary_key=True)  # 仍保留字符串类型以便扩展
    P_name = db.Column(db.String(20), nullable=False)
    P_sex = db.Column(Enum('男', '女', name='patient_gender'), nullable=False)
    P_age = db.Column(db.Integer, nullable=False)
    P_phonenumber = db.Column(db.String(11), nullable=False, unique=True)
    P_password = db.Column(db.String(200), nullable=False)

    @classmethod
    def get_next_pno(cls):
        last_patient = cls.query.order_by(cls.P_no.desc()).first()
        return str(int(last_patient.P_no) + 1) if last_patient else '1'



class Doctor(db.Model):
    __tablename__ = 'doctor'
    D_no = db.Column(db.String(10), primary_key=True)
    D_name = db.Column(db.String(20), nullable=False)
    D_sex = db.Column(Enum('男', '女', name='gender_enum'), nullable=False)
    D_age = db.Column(db.Integer, nullable=False)
    D_Title = db.Column(db.String(20), nullable=False)
    D_Department = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# 添加 Registration 模型
class Registration(db.Model):
    __tablename__ = 'registration'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(10), db.ForeignKey('patient.P_no'))
    D_name = db.Column(db.String(20), nullable=False)
    D_title = db.Column(db.String(50), nullable=False)
    De_name = db.Column(db.String(20), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    medical_record = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))

class Prescription(db.Model):
    __tablename__ = 'prescription'
    id = db.Column(db.Integer,primary_key=True)
    registration_id = db.Column(db.Integer,nullable=False)
    create_time = db.Column(db.Date, nullable=False)

class PrescriptionDetail(db.Model):
    __tablename__ = 'prescription_detail'
    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, nullable=False)
    med_id = db.Column(db.Integer, nullable=False)
    med_name = db.Column(db.String(50),nullable=False)
    unit_price = db.Column(db.Numeric(10, 2),nullable=False)
    quantity = db.Column(db.Integer,nullable=False)

#主页面路由
@app.route('/')
def index():
    if 'patient_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/test_db')
def test_db():
    try:
        db.session.execute(text("SELECT 1"))  # 使用 text()
        return "数据库连接成功！"
    except Exception as e:
        return f"数据库连接失败: {str(e)}"


@app.route('/get_doctors')
def get_doctors():
    try:
        doctors = Doctor.query.all()
        return jsonify([doctor.to_dict() for doctor in doctors])
    except Exception as e:
        return jsonify({'error': f"数据库错误: {str(e)}"}), 500

#登陆路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')

        patient = Patient.query.filter_by(P_phonenumber=phone).first()

        if patient and check_password_hash(patient.P_password, password):
            session['patient_id'] = patient.P_no
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="手机号或密码错误")

    return render_template('login.html')

#注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            print("接收到的表单数据:", request.form)  # 调试点1

            p_no = Patient.get_next_pno()
            print("生成的患者编号:", p_no)  # 调试点2

            new_patient = Patient(
                P_no=p_no,
                P_name=request.form['name'],
                P_sex=request.form['gender'],
                P_age=int(request.form['age']),
                P_phonenumber=request.form['phone'],
                P_password=generate_password_hash(request.form['password'])
            )

            db.session.add(new_patient)
            print("准备提交的数据对象:", new_patient)  # 调试点3

            db.session.commit()
            print("提交成功!")  # 调试点4
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            print("发生错误:", str(e))  # 调试点5
            return render_template('register.html', error=str(e))

    return render_template('register.html')


# 获取科室列表
@app.route('/api/departments')
def get_departments():
    return jsonify(['内科', '外科', '普通门诊'])


# 获取可预约排班
@app.route('/api/schedules/<dept>')
def get_schedules(dept):
    try:
        date_str = request.args.get('date')
        if not date_str:
            return jsonify(error="缺少日期参数"), 400

        try:
            # 解析日期并格式化为YYYY-MM-DD
            visit_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError as e:
            return jsonify(error=f"日期格式不正确，请使用YYYY-MM-DD格式"), 400

        # 修改后的查询（移除了visit_time字段）
        query = text("""
            SELECT D_name, D_title, De_name, 
                   visit_date,
                   remaining
            FROM schedule 
            WHERE De_name = :dept 
              AND visit_date = :visit_date
              AND remaining > 0
        """)

        schedules = db.session.execute(query, {
            'dept': dept,
            'visit_date': visit_date  # 使用格式化后的字符串
        }).fetchall()

        # 确保返回的日期格式统一
        result = [{
            'D_name': row[0],
            'D_title': row[1],
            'De_name': row[2],
            'visit_date': row[3].strftime('%Y-%m-%d') if hasattr(row[3], 'strftime') else row[3],
            '挂号余量': row[4]
        } for row in schedules]

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"排班查询错误: {str(e)}", exc_info=True)
        return jsonify(error="服务器内部错误"), 500


# 提交挂号
@app.route('/api/register', methods=['POST'])
def create_registration():
    try:
        data = request.get_json()
        patient_id = session.get('patient_id')

        # 增强型验证
        patient = db.session.execute(
            text("SELECT 1 FROM patient WHERE P_no = :pid"),
            {'pid': patient_id}
        ).fetchone()

        if not patient:
            return jsonify(error="患者信息异常，请重新登录"), 404

        # 使用原生SQL确保类型匹配
        db.session.execute(
            text("""
                INSERT INTO registration 
                (patient_id, D_name, D_title, De_name, visit_date)
                VALUES (:pid, :name, :title, :dept, :date)
            """),
            {
                'pid': patient_id,
                'name': data['D_name'],
                'title': data['D_title'],
                'dept': data['De_name'],
                'date': data['visit_date']
            }
        )

        # 更新余量
        db.session.execute(
            text("""
                                UPDATE schedule 
                SET remaining = remaining - 1 
                WHERE D_name = :name AND visit_date = :date
            """),
            {'name': data['D_name'], 'date': data['visit_date']}
        )

        db.session.commit()
        return jsonify(success=True)

    except Exception as e:
        db.session.rollback()
        return jsonify(error=f"数据库操作失败: {str(e)}"), 500


# 获取我的挂号记录
@app.route('/api/my_registrations')
def get_my_registrations():
    regs = Registration.query.filter_by(patient_id=session['patient_id']).all()
    return jsonify([{
        'D_name': r.D_name,
        'D_title': r.D_title,
        'De_name': r.De_name,
        'visit_date': r.visit_date.strftime('%Y-%m-%d')
    } for r in regs])


# 获取病人的病历记录
@app.route('/api/my_medical_records')
def get_my_medical_records():
    if 'patient_id' not in session:
        return jsonify(error="未登录"), 401

    try:
        # 联表查询获取病历记录
        records = db.session.query(
            Registration.D_name,
            Registration.D_title,
            Registration.visit_date,
            Registration.medical_record
        ).filter(
            Registration.patient_id == session['patient_id'],
            Registration.medical_record.isnot(None)  # 只返回有病历的记录
        ).order_by(
            Registration.visit_date.desc()
        ).all()

        result = [{
            'D_name': r.D_name,
            'D_title': r.D_title,
            'visit_date': r.visit_date.strftime('%Y-%m-%d'),
            'medical_record': r.medical_record
        } for r in records]

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"获取病历失败: {str(e)}")
        return jsonify(error="获取病历失败"), 500

# 获取病人的药单记录
@app.route('/api/my_prescriptions')
def get_my_prescriptions():
    if 'patient_id' not in session:
        return jsonify(error="未登录"), 401

    try:
        # 联表查询获取药单记录
        prescriptions = db.session.query(
            Registration.id,
            Registration.D_name,
            Registration.D_title,
            Registration.visit_date,
            Registration.price,
            Prescription.create_time,
            PrescriptionDetail.med_name,
            PrescriptionDetail.unit_price,
            PrescriptionDetail.quantity
        ).join(
            Prescription, Registration.id == Prescription.registration_id
        ).join(
            PrescriptionDetail, Prescription.id == PrescriptionDetail.prescription_id
        ).filter(
            Registration.patient_id == session['patient_id']
        ).order_by(
            Prescription.create_time.desc()
        ).all()

        # 按处方分组
        result = {}
        for p in prescriptions:
            if p.id not in result:
                result[p.id] = {
                    'registration_id': p.id,
                    'D_name': p.D_name,
                    'D_title': p.D_title,
                    'visit_date': p.visit_date.strftime('%Y-%m-%d'),
                    'total_price': float(p.price) if p.price else 0,
                    'create_time': p.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'medicines': []
                }
            result[p.id]['medicines'].append({
                'med_name': p.med_name,
                'unit_price': float(p.unit_price),
                'quantity': p.quantity
            })

        return jsonify(list(result.values()))
    except Exception as e:
        app.logger.error(f"获取药单失败: {str(e)}")
        return jsonify(error="获取药单失败"), 500

#注销
@app.route('/logout')
def logout():
    session.pop('patient_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
