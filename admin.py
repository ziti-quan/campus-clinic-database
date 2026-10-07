from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
db = SQLAlchemy(app)


# 数据库模型
class Department(db.Model):
    __tablename__ = 'department'
    DE_no = db.Column(db.String(10), primary_key=True)
    DE_name = db.Column(db.String(20))


class Doctor(db.Model):
    __tablename__ = 'doctor'
    D_no = db.Column(db.String(10), primary_key=True)
    D_name = db.Column(db.String(20))
    D_sex = db.Column(db.Enum('男', '女'))
    D_age = db.Column(db.Integer)
    D_Title = db.Column(db.String(20))
    D_Department = db.Column(db.String(20))
    D_password = db.Column(db.String(200))


class Medicine(db.Model):
    __tablename__ = 'medicine'
    med_id = db.Column(db.Integer, primary_key=True)
    med_name = db.Column(db.String(50))
    stock_quantity = db.Column(db.Integer)
    unit_price = db.Column(db.Float)


class Schedule(db.Model):
    __tablename__ = 'schedule'

    id = db.Column(db.Integer, primary_key=True)
    D_name = db.Column(db.String(20), nullable=False)
    D_title = db.Column(db.String(50))
    DE_name = db.Column(db.String(20), nullable=False)
    visit_date = db.Column(db.Date, nullable=False)
    remaining = db.Column(db.Integer, default=0)


@app.route('/')
def admin():
    return render_template('admin.html')


# 部门操作
@app.route('/api/departments', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_departments():
    if request.method == 'GET':
        departments = Department.query.all()
        return jsonify([{'DE_no': de.DE_no, 'DE_name': de.DE_name} for de in departments])

    data = request.get_json()

    if request.method == 'POST':
        department = Department(DE_no=data['DE_no'], DE_name=data['DE_name'])
        db.session.add(department)
        db.session.commit()
        return jsonify({'success': True, 'message': '部门添加成功'})

    elif request.method == 'PUT':
        department = Department.query.get(data['DE_no'])
        if department:
            department.DE_name = data['DE_name']
            db.session.commit()
            return jsonify({'success': True, 'message': '部门更新成功'})
        return jsonify({'success': False, 'message': '部门不存在'})

    elif request.method == 'DELETE':
        department = Department.query.get(data['DE_no'])
        if department:
            db.session.delete(department)
            db.session.commit()
            return jsonify({'success': True, 'message': '部门删除成功'})
        return jsonify({'success': False, 'message': '部门不存在'})


# 医生操作
@app.route('/api/doctors', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_doctors():
    if request.method == 'GET':
        doctors = Doctor.query.all()
        return jsonify([{
            'D_no': doc.D_no,
            'D_name': doc.D_name,
            'D_sex': doc.D_sex,
            'D_age': doc.D_age,
            'D_Title': doc.D_Title,
            'D_Department': doc.D_Department
        } for doc in doctors])

    data = request.get_json()

    if request.method == 'POST':
        doctor = Doctor(
            D_no=data['D_no'],
            D_name=data['D_name'],
            D_sex=data['D_sex'],
            D_age=data['D_age'],
            D_Title=data['D_Title'],
            D_Department=data['D_Department'],
            D_password=data['D_password']
        )
        db.session.add(doctor)
        db.session.commit()
        return jsonify({'success': True, 'message': '医生添加成功'})

    elif request.method == 'PUT':
        doctor = Doctor.query.get(data['D_no'])
        if doctor:
            doctor.D_name = data['D_name']
            doctor.D_sex = data['D_sex']
            doctor.D_age = data['D_age']
            doctor.D_Title = data['D_Title']
            doctor.D_Department = data['D_Department']
            if 'D_password' in data:
                doctor.D_password = data['D_password']
            db.session.commit()
            return jsonify({'success': True, 'message': '医生更新成功'})
        return jsonify({'success': False, 'message': '医生不存在'})

    elif request.method == 'DELETE':
        doctor = Doctor.query.get(data['D_no'])
        if doctor:
            db.session.delete(doctor)
            db.session.commit()
            return jsonify({'success': True, 'message': '医生删除成功'})
        return jsonify({'success': False, 'message': '医生不存在'})


# 药品操作
@app.route('/api/medicines', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_medicines():
    if request.method == 'GET':
        medicines = Medicine.query.all()
        return jsonify([{
            'med_id': med.med_id,
            'med_name': med.med_name,
            'stock_quantity': med.stock_quantity,
            'unit_price': med.unit_price
        } for med in medicines])

    data = request.get_json()

    if request.method == 'POST':
        medicine = Medicine(
            med_name=data['med_name'],
            stock_quantity=data['stock_quantity'],
            unit_price=data['unit_price']
        )
        db.session.add(medicine)
        db.session.commit()
        return jsonify({'success': True, 'message': '药品添加成功'})

    elif request.method == 'PUT':
        medicine = Medicine.query.get(data['med_id'])
        if medicine:
            medicine.med_name = data['med_name']
            medicine.stock_quantity = data['stock_quantity']
            medicine.unit_price = data['unit_price']
            db.session.commit()
            return jsonify({'success': True, 'message': '药品更新成功'})
        return jsonify({'success': False, 'message': '药品不存在'})

    elif request.method == 'DELETE':
        medicine = Medicine.query.get(data['med_id'])
        if medicine:
            db.session.delete(medicine)
            db.session.commit()
            return jsonify({'success': True, 'message': '药品删除成功'})
        return jsonify({'success': False, 'message': '药品不存在'})


# 排班操作
@app.route('/api/schedules', methods=['GET', 'POST', 'PUT', 'DELETE'])
def handle_schedules():
    if request.method == 'GET':
        schedules = Schedule.query.all()
        return jsonify([{
            'id': sch.id,
            'D_name': sch.D_name,  # 使用模型属性名，不是列名
            'D_title': sch.D_title,
            'DE_name': sch.DE_name,
            'visit_date': sch.visit_date.strftime('%Y-%m-%d') if sch.visit_date else None,
            'remaining': sch.remaining  # 使用模型属性名
        } for sch in schedules])

    data = request.get_json()

    if request.method == 'POST':
        schedule = Schedule(
            D_name=data.get('D_name'),
            D_title=data.get('D_title'),
            DE_name=data.get('DE_name'),
            visit_date=datetime.strptime(data['visit_date'], '%Y-%m-%d').date(),
            remaining=int(data.get('remaining') or 0)
        )
        db.session.add(schedule)
        db.session.commit()
        return jsonify({'success': True, 'message': '排班添加成功'})

    elif request.method == 'PUT':
        schedule = Schedule.query.get(data['id'])
        if schedule:
            schedule.D_name = data['D_name']
            schedule.D_title = data['D_title']
            schedule.DE_name = data['DE_name']
            schedule.visit_date = datetime.strptime(data['visit_date'], '%Y-%m-%d').date()
            schedule.remaining = int(data['remaining'])
            db.session.commit()
            return jsonify({'success': True, 'message': '排班更新成功'})
        return jsonify({'success': False, 'message': '排班不存在'})

    elif request.method == 'DELETE':
        schedule = Schedule.query.get(data['id'])
        if schedule:
            db.session.delete(schedule)
            db.session.commit()
            return jsonify({'success': True, 'message': '排班删除成功'})
        return jsonify({'success': False, 'message': '排班不存在'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # 创建表（如果不存在）
    app.run(debug=True)
