from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from datetime import datetime

import config

app = Flask(__name__)
app.secret_key = config.DOCTOR_SECRET_KEY  # 从环境变量 / .env 读取，不写死在源码里

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
db = SQLAlchemy(app)


# 医生模型
class Doctor(db.Model):
    __tablename__ = 'doctor'
    D_no = db.Column(db.String(10), primary_key=True)
    D_name = db.Column(db.String(20), nullable=False)
    D_password = db.Column(db.String(50), nullable=False)


# 药品模型
class Medicine(db.Model):
    __tablename__ = 'medicine'
    med_id = db.Column(db.Integer, primary_key=True)
    med_name = db.Column(db.String(50), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)


# 挂号模型
class Registration(db.Model):
    __tablename__ = 'registration'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(10))
    D_name = db.Column(db.String(20), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    medical_record = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))

class Patient(db.Model):
    __tablename__ = 'patient'
    P_no = db.Column(db.String(10), primary_key=True)
    P_name = db.Column(db.String(20), nullable=False)
    P_sex = db.Column(db.String(10), nullable=False)  # '男' 或 '女'
    P_age = db.Column(db.Integer)
    P_phonenumber = db.Column(db.String(20))
    P_password = db.Column(db.String(200))

class Schedule(db.Model):
    __tablename__ = 'schedule'
    id = db.Column(db.Integer,primary_key=True)
    De_name = db.Column(db.String(20),nullable=False)
    D_name = db.Column(db.String(20),nullable=False)
    visit_date = db.Column(db.Date, nullable=False)

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

# 主路由 - 重定向到登录页面
@app.route('/')
def index():
    return redirect(url_for('doctor_login'))


# 医生登录路由
@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if 'doctor_id' in session:
        return redirect(url_for('doctor_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        doctor = Doctor.query.filter_by(D_name=name, D_password=password).first()

        if doctor:
            session['doctor_id'] = doctor.D_no
            session['doctor_name'] = doctor.D_name
            return redirect(url_for('doctor_dashboard'))
        else:
            return render_template('doctor_login.html', error="姓名或密码错误")

    return render_template('doctor_login.html')


# 医生仪表盘 - 添加登录验证装饰器
def login_required(f):
    @wraps(f)  # 使用wraps保留原始函数信息
    def decorated_function(*args, **kwargs):
        if 'doctor_id' not in session:
            return redirect(url_for('doctor_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    return render_template('doctor_dashboard.html', doctor_name=session['doctor_name'])


# 获取医生就诊安排
@app.route('/api/patient_schedules/<date>')
@login_required
def get_patient_schedules(date):
    try:
        # 将前端传来的日期转换为数据库格式
        visit_date = datetime.strptime(date, '%Y-%m-%d').date()

        # 联表查询获取患者详细信息
        schedules = db.session.query(
            Registration.patient_id,
            Patient.P_name.label('patient_name'),
            Patient.P_sex.label('patient_gender'),
            Registration.visit_date
        ).join(
            Patient, Registration.patient_id == Patient.P_no
        ).filter(
            Registration.D_name == session['doctor_name'],
            Registration.visit_date == visit_date
        ).all()

        result = [{
            'patient_id': s.patient_id,
            'patient_name': s.patient_name,
            'patient_gender': s.patient_gender,
            'visit_date': s.visit_date.strftime('%Y-%m-%d')
        } for s in schedules]

        return jsonify(result)
    except ValueError:
        return jsonify({'error': '日期格式不正确'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 获取药品信息
@app.route('/api/medicines')
@login_required
def get_medicines():
    medicines = Medicine.query.all()

    result = [{
        'med_id': m.med_id,
        'med_name': m.med_name,
        'stock_quantity': m.stock_quantity,
        'unit_price': float(m.unit_price)
    } for m in medicines]

    return jsonify(result)

#排班表
@app.route('/api/doctor_schedules_self')
@login_required
def get_doctor_schedules_self():
    try:
        schedules = db.session.query(
            Schedule.De_name.label('department'),
            Schedule.D_name.label('doctor_name'),
            Schedule.visit_date
        ).filter(
            Schedule.D_name == session['doctor_name']
        ).all()

        result = [{
            'department': s.department,
            'doctor_name': s.doctor_name,
            'visit_date': s.visit_date.strftime('%Y-%m-%d')
        } for s in schedules]

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"获取排班表失败: {str(e)}")
        return jsonify({'error': '获取排班信息失败'}), 500

# 获取医生的所有患者
@app.route('/api/all_patients')
@login_required
def get_all_patients():
    try:
        # 联表查询获取该医生的所有患者
        patients = db.session.query(
            Registration.patient_id,
            Patient.P_name.label('patient_name'),
            Patient.P_sex.label('patient_gender'),
            Registration.visit_date
        ).join(
            Patient, Registration.patient_id == Patient.P_no
        ).filter(
            Registration.D_name == session['doctor_name']
        ).order_by(
            Registration.visit_date.desc()
        ).all()

        result = [{
            'patient_id': p.patient_id,
            'patient_name': p.patient_name,
            'patient_gender': p.patient_gender,
            'visit_date': p.visit_date.strftime('%Y-%m-%d')
        } for p in patients]

        return jsonify(result)
    except Exception as e:
        app.logger.error(f"获取患者列表失败: {str(e)}")
        return jsonify({'error': '获取患者信息失败'}), 500


# 病历查看和编辑页面
@app.route('/patient_record/<patient_id>')
@login_required
def patient_record(patient_id):
    visit_date = request.args.get('date')

    # 获取患者信息和病历
    record = db.session.query(
        Registration,
        Patient.P_name.label('patient_name')
    ).join(
        Patient, Registration.patient_id == Patient.P_no
    ).filter(
        Registration.patient_id == patient_id,
        Registration.D_name == session['doctor_name'],
        Registration.visit_date == visit_date
    ).first()

    if not record:
        return render_template('error.html', message="未找到患者记录")

    return render_template('patient_record.html',
                           patient_id=patient_id,
                           patient_name=record.patient_name,
                           visit_date=visit_date,
                           medical_record=record.Registration.medical_record if hasattr(record.Registration,
                                                                                        'medical_record') else None)


# 保存病历
@app.route('/api/save_medical_record', methods=['POST'])
@login_required
def save_medical_record():
    try:
        data = request.get_json()  # 使用get_json()替代json
        patient_id = data.get('patient_id')
        visit_date_str = data.get('visit_date')
        medical_record = data.get('medical_record')

        if not all([patient_id, visit_date_str, medical_record is not None]):
            return jsonify({'error': '缺少必要参数'}), 400

        visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d').date()

        # 打印调试信息
        app.logger.info(f"尝试更新病历 - 患者ID: {patient_id}, 日期: {visit_date}, 医生: {session['doctor_name']}")

        # 查找并更新病历
        registration = Registration.query.filter_by(
            patient_id=patient_id,
            D_name=session['doctor_name'],
            visit_date=visit_date
        ).first()

        if not registration:
            app.logger.error("未找到匹配的挂号记录")
            return jsonify({'error': '未找到挂号记录'}), 404

        # 检查medical_record属性是否存在
        if not hasattr(registration, 'medical_record'):
            app.logger.error("registration表没有medical_record列")
            return jsonify({'error': '数据库结构不匹配'}), 500

        # 更新病历
        registration.medical_record = medical_record
        db.session.commit()

        app.logger.info("病历更新成功")
        return jsonify({'success': True})
    except ValueError as e:
        db.session.rollback()
        app.logger.error(f"日期格式错误: {str(e)}")
        return jsonify({'error': '日期格式不正确'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"保存病历失败: {str(e)}")
        return jsonify({'error': str(e)}), 500


# 添加开药页面路由
@app.route('/prescribe_medicine')
@login_required
def prescribe_medicine():
    registration_id = request.args.get('registration_id')
    if not registration_id:
        abort(400, description="缺少挂号记录ID")

    # 验证挂号记录属于当前医生
    registration = Registration.query.filter_by(
        id=registration_id,
        D_name=session['doctor_name']
    ).first()

    if not registration:
        abort(404, description="未找到挂号记录")

    return render_template('prescribe_medicine.html',
                           doctor_name=session['doctor_name'],
                           registration_id=registration_id)

# 获取可开药的患者列表
@app.route('/api/prescribe/patients')
@login_required
def get_prescribe_patients():
    patients = db.session.query(
        Registration.id,
        Registration.patient_id,
        Patient.P_name.label('patient_name'),
        Patient.P_sex.label('patient_gender'),
        Registration.visit_date
    ).join(
        Patient, Registration.patient_id == Patient.P_no
    ).filter(
        Registration.D_name == session['doctor_name']
    ).order_by(
        Registration.visit_date.desc()
    ).all()

    return jsonify([{
        'registration_id': p.id,
        'patient_id': p.patient_id,
        'patient_name': p.patient_name,
        'patient_gender': p.patient_gender,
        'visit_date': p.visit_date.strftime('%Y-%m-%d')
    } for p in patients])


# 获取单个挂号信息
@app.route('/api/registration/<int:registration_id>')
@login_required
def get_registration(registration_id):
    registration = db.session.query(
        Registration.id,
        Registration.patient_id,
        Patient.P_name.label('patient_name'),
        Patient.P_sex.label('patient_gender'),
        Registration.visit_date
    ).join(
        Patient, Registration.patient_id == Patient.P_no
    ).filter(
        Registration.id == registration_id,
        Registration.D_name == session['doctor_name']
    ).first()

    if not registration:
        return jsonify({'error': '未找到挂号记录'}), 404

    return jsonify({
        'registration_id': registration.id,
        'patient_id': registration.patient_id,
        'patient_name': registration.patient_name,
        'patient_gender': registration.patient_gender,
        'visit_date': registration.visit_date.strftime('%Y-%m-%d')
    })


# 提交处方
@app.route('/api/prescriptions', methods=['POST'])
@login_required
def create_prescription():
    try:
        data = request.json
        registration_id = data['registration_id']
        medicines = data['medicines']
        total_price = data['total_price']

        # 验证挂号记录
        registration = Registration.query.filter_by(
            id=registration_id,
            D_name=session['doctor_name']
        ).first()

        if not registration:
            return jsonify({'error': '无效的挂号记录'}), 400

        # 创建处方并显式设置创建时间
        prescription = Prescription(
            registration_id=registration_id,
            create_time=datetime.now()  # 添加这一行
        )
        db.session.add(prescription)
        db.session.flush()

        # 添加处方明细并更新库存
        for item in medicines:
            medicine = Medicine.query.get(item['med_id'])
            if not medicine:
                return jsonify({'error': f"药品ID {item['med_id']} 不存在"}), 400

            if medicine.stock_quantity < item['quantity']:
                return jsonify({'error': f"药品 {medicine.med_name} 库存不足"}), 400

            # 添加明细
            detail = PrescriptionDetail(
                prescription_id=prescription.id,
                med_id=medicine.med_id,
                med_name=medicine.med_name,
                unit_price=medicine.unit_price,
                quantity=item['quantity']
            )
            db.session.add(detail)

            # 更新库存
            medicine.stock_quantity -= item['quantity']

        # 更新挂号记录的总费用
        registration.price = total_price
        db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# 获取历史处方
@app.route('/api/prescriptions')
@login_required
def get_prescriptions():
    registration_id = request.args.get('registration_id')

    prescriptions = db.session.query(
        Prescription.id,
        Prescription.create_time,
        PrescriptionDetail.med_name,
        PrescriptionDetail.unit_price,
        PrescriptionDetail.quantity
    ).join(
        PrescriptionDetail, Prescription.id == PrescriptionDetail.prescription_id
    ).filter(
        Prescription.registration_id == registration_id
    ).order_by(
        Prescription.create_time.desc()
    ).all()

    # 按处方分组
    result = {}
    for p in prescriptions:
        if p.id not in result:
            result[p.id] = {
                'id': p.id,
                'create_time': p.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                'details': []
            }
        result[p.id]['details'].append({
            'med_name': p.med_name,
            'unit_price': float(p.unit_price),
            'quantity': p.quantity
        })

    return jsonify(list(result.values()))

# 医生登出
@app.route('/doctor_logout')
def doctor_logout():
    session.pop('doctor_id', None)
    session.pop('doctor_name', None)
    return redirect(url_for('doctor_login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
