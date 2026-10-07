-- ============================================================================
--  校园医务室信息管理系统 · 演示数据 (DML)
--  ---------------------------------------------------------------------------
--  前置条件：先执行 schema.sql 建好 8 张表。
--  导入方法：mysql -h 127.0.0.1 -P 3308 -u root -p hospital < seed_data.sql
--
--  设计说明：
--    * 排班日期用 CURDATE() + N 天动态生成，因此无论哪天导入，
--      患者端"预约挂号"页面总能查到未来 5 天的号源。
--    * 医生密码是明文 '123456'：app_D.py 的登录逻辑是
--          Doctor.query.filter_by(D_name=name, D_password=password)
--      直接拿表单值当明文比对，所以这里必须存明文，否则医生端登不进去。
--      （患者端相反，app.py 用 check_password_hash 校验哈希，见下方患者数据）
--    * 不预置 registration / prescription / prescription_detail 数据，
--      挂号、写病历、开处方请在演示时真实走一遍流程，这三个表会自动产生数据。
-- ============================================================================

USE `hospital`;

SET NAMES utf8mb4;

DELETE FROM `prescription_detail`;
DELETE FROM `prescription`;
DELETE FROM `registration`;
DELETE FROM `schedule`;
DELETE FROM `medicine`;
DELETE FROM `patient`;
DELETE FROM `doctor`;
DELETE FROM `department`;
ALTER TABLE `medicine` AUTO_INCREMENT = 1;


-- ---------------------------------------------------------------------------
-- 1. 科室（与 static/js/script.js 中硬编码的三个科室保持一致）
-- ---------------------------------------------------------------------------
INSERT INTO `department` (`DE_no`, `DE_name`) VALUES
    ('DE01', '内科'),
    ('DE02', '外科'),
    ('DE03', '普通门诊');


-- ---------------------------------------------------------------------------
-- 2. 医生（D_password 为明文，医生端登录账号 = 姓名 + 密码）
-- ---------------------------------------------------------------------------
INSERT INTO `doctor` (`D_no`, `D_name`, `D_sex`, `D_age`, `D_Title`, `D_Department`, `D_password`) VALUES
    ('D001', '张伟', '男', 46, '主任医师',   '内科',     '123456'),
    ('D002', '李娜', '女', 38, '副主任医师', '内科',     '123456'),
    ('D003', '王强', '男', 41, '主治医师',   '外科',     '123456'),
    ('D004', '刘敏', '女', 29, '医师',       '普通门诊', '123456');


-- ---------------------------------------------------------------------------
-- 3. 患者（演示账号：手机号 13800138000 / 密码 123456）
--    P_password 必须是 werkzeug 的 pbkdf2 哈希串，明文无法登录。
--    若需要更多患者，直接用前端 /register 页面注册即可，
--    P_no 会由 Patient.get_next_pno() 自动生成。
-- ---------------------------------------------------------------------------
INSERT INTO `patient` (`P_no`, `P_name`, `P_sex`, `P_age`, `P_phonenumber`, `P_password`) VALUES
    ('1', '陈晨', '男', 20, '13800138000',
     'pbkdf2:sha256:260000$bOW7ctiBXgSE2a8p$7edf149ef607e31d8c94a9cb9814c2b16059a45c92ce09a83c209b7a9a85851b'),
    ('2', '赵雪', '女', 22, '13900139000',
     'pbkdf2:sha256:260000$bOW7ctiBXgSE2a8p$7edf149ef607e31d8c94a9cb9814c2b16059a45c92ce09a83c209b7a9a85851b');


-- ---------------------------------------------------------------------------
-- 4. 药品
-- ---------------------------------------------------------------------------
INSERT INTO `medicine` (`med_name`, `stock_quantity`, `unit_price`) VALUES
    ('阿莫西林胶囊',     500, 12.50),
    ('布洛芬缓释胶囊',   400, 18.00),
    ('感冒灵颗粒',       600,  9.80),
    ('蒙脱石散',         300, 15.60),
    ('头孢克肟片',       200, 22.40),
    ('维生素C片',       1000,  6.50),
    ('藿香正气水',       350,  8.90),
    ('创可贴',           800,  3.20),
    ('碘伏消毒液',       250, 11.00),
    ('生理盐水(500ml)',  180,  4.50);


-- ---------------------------------------------------------------------------
-- 5. 排班（未来 5 天号源；一位医生一天只有一条记录，受
--    uk_schedule_doctor_date 唯一键约束）
-- ---------------------------------------------------------------------------
INSERT INTO `schedule` (`DE_name`, `D_name`, `D_title`, `visit_date`, `remaining`) VALUES
    ('内科',     '张伟', '主任医师',   DATE_ADD(CURDATE(), INTERVAL 1 DAY), 20),
    ('内科',     '张伟', '主任医师',   DATE_ADD(CURDATE(), INTERVAL 2 DAY), 20),
    ('内科',     '张伟', '主任医师',   DATE_ADD(CURDATE(), INTERVAL 4 DAY), 15),
    ('内科',     '李娜', '副主任医师', DATE_ADD(CURDATE(), INTERVAL 1 DAY), 25),
    ('内科',     '李娜', '副主任医师', DATE_ADD(CURDATE(), INTERVAL 3 DAY), 25),
    ('内科',     '李娜', '副主任医师', DATE_ADD(CURDATE(), INTERVAL 5 DAY), 20),
    ('外科',     '王强', '主治医师',   DATE_ADD(CURDATE(), INTERVAL 2 DAY), 18),
    ('外科',     '王强', '主治医师',   DATE_ADD(CURDATE(), INTERVAL 3 DAY), 18),
    ('外科',     '王强', '主治医师',   DATE_ADD(CURDATE(), INTERVAL 5 DAY), 12),
    ('普通门诊', '刘敏', '医师',       DATE_ADD(CURDATE(), INTERVAL 1 DAY), 30),
    ('普通门诊', '刘敏', '医师',       DATE_ADD(CURDATE(), INTERVAL 2 DAY), 30),
    ('普通门诊', '刘敏', '医师',       DATE_ADD(CURDATE(), INTERVAL 3 DAY), 30),
    ('普通门诊', '刘敏', '医师',       DATE_ADD(CURDATE(), INTERVAL 4 DAY), 30),
    ('普通门诊', '刘敏', '医师',       DATE_ADD(CURDATE(), INTERVAL 5 DAY), 30);


-- ---------------------------------------------------------------------------
-- 6. 导入结果核对
-- ---------------------------------------------------------------------------
SELECT 'department' AS `表名`, COUNT(*) AS `行数` FROM `department`
UNION ALL SELECT 'doctor',              COUNT(*) FROM `doctor`
UNION ALL SELECT 'patient',             COUNT(*) FROM `patient`
UNION ALL SELECT 'medicine',            COUNT(*) FROM `medicine`
UNION ALL SELECT 'schedule',            COUNT(*) FROM `schedule`
UNION ALL SELECT 'registration',        COUNT(*) FROM `registration`
UNION ALL SELECT 'prescription',        COUNT(*) FROM `prescription`
UNION ALL SELECT 'prescription_detail', COUNT(*) FROM `prescription_detail`;
