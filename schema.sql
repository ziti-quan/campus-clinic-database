-- ============================================================================
--  校园医务室信息管理系统 · 数据库结构定义脚本 (DDL)
--  ---------------------------------------------------------------------------
--  数据库名 : hospital
--  存储引擎 : InnoDB
--  字符集   : utf8mb4 / utf8mb4_general_ci
--  适用版本 : MySQL 8.0（在 MySQL 5.7 上同样可执行，5.7 会解析但忽略 CHECK 约束）
--
--  导入方法（务必先建表，再启动三个 Flask 应用）：
--      mysql -h 127.0.0.1 -P 3308 -u root -p < schema.sql
--  或在已连接 hospital 的 MySQL 客户端中：
--      source schema.sql
--
--  本脚本与三个应用的对应关系：
--      app.py    患者端 -> patient, doctor, schedule, registration,
--                         prescription, prescription_detail
--      app_D.py  医生端 -> doctor, patient, medicine, schedule, registration,
--                         prescription, prescription_detail
--      admin.py  管理端 -> department, doctor, medicine, schedule
--
--  !! 警告：本脚本会先 DROP 下列 8 张表再重建，原有数据会被清空 !!
--
--  另请注意：不要依赖 Flask-SQLAlchemy 的 db.create_all() 建表。
--  它只会创建"当前文件里定义过的模型"，并且不会修改已存在的表结构；
--  三个应用各自的模型定义互相冲突，谁先执行谁就把表结构定死，
--  另外两个应用随即报错。详见《数据库设计说明.md》第 7 节。
-- ============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `hospital`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_general_ci;

USE `hospital`;

-- 按依赖倒序删除（外部有外键引用的表后删），保证可重复执行
DROP TABLE IF EXISTS `prescription_detail`;
DROP TABLE IF EXISTS `prescription`;
DROP TABLE IF EXISTS `registration`;
DROP TABLE IF EXISTS `schedule`;
DROP TABLE IF EXISTS `medicine`;
DROP TABLE IF EXISTS `patient`;
DROP TABLE IF EXISTS `doctor`;
DROP TABLE IF EXISTS `department`;

SET FOREIGN_KEY_CHECKS = 1;


-- ============================================================================
-- 1. department 科室表
--    管理员维护；医生归属科室、排班所属科室均以此为参照。
--    DE_name 建唯一索引，作为 doctor.D_Department / schedule.DE_name 的外键目标。
-- ============================================================================
CREATE TABLE `department` (
    `DE_no`   VARCHAR(10) NOT NULL COMMENT '科室编号，业务主键，如 DE01',
    `DE_name` VARCHAR(20) NOT NULL COMMENT '科室名称，如 内科 / 外科 / 普通门诊',
    PRIMARY KEY (`DE_no`),
    UNIQUE KEY `uk_department_name` (`DE_name`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci COMMENT = '科室表';


-- ============================================================================
-- 2. doctor 医生表
--    患者端读取医生基本信息；医生端用 (D_name, D_password) 登录；
--    管理端对医生做增删改。
--    * D_name 唯一：医生端整个模块以"医生姓名"为业务标识
--      （session 里存 D_name，挂号、排班、病历全靠姓名串联），
--      若不唯一会导致查询串号，因此必须加唯一约束。
--    * D_password：医生端目前是明文比对，字段类型沿用 String(200) 以便
--      后续平滑切换到 werkzeug 哈希（见设计说明第 9 节）。
-- ============================================================================
CREATE TABLE `doctor` (
    `D_no`         VARCHAR(10)  NOT NULL COMMENT '医生工号，主键',
    `D_name`       VARCHAR(20)  NOT NULL COMMENT '医生姓名，业务唯一标识',
    `D_sex`        ENUM('男','女') NOT NULL COMMENT '性别',
    `D_age`        INT          NOT NULL COMMENT '年龄',
    `D_Title`      VARCHAR(20)  NOT NULL COMMENT '职称，如 主任医师',
    `D_Department` VARCHAR(20)  NOT NULL COMMENT '所属科室，参照 department.DE_name',
    `D_password`   VARCHAR(200) NOT NULL COMMENT '登录密码',
    PRIMARY KEY (`D_no`),
    UNIQUE KEY `uk_doctor_name` (`D_name`),
    KEY `idx_doctor_department` (`D_Department`),
    CONSTRAINT `fk_doctor_department`
        FOREIGN KEY (`D_Department`) REFERENCES `department` (`DE_name`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `chk_doctor_age` CHECK (`D_age` BETWEEN 18 AND 100)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci COMMENT = '医生表';


-- ============================================================================
-- 3. patient 患者表
--    患者端注册/登录使用；P_password 存 werkzeug 哈希（pbkdf2/scrypt 串，最长 200）。
--    P_no 在代码中被当作数字串自增（Patient.get_next_pno 用 int(P_no)+1），
--    但模型声明为 String(10)，此处保持 String(10) 以兼容代码。
-- ============================================================================
CREATE TABLE `patient` (
    `P_no`          VARCHAR(10)  NOT NULL COMMENT '患者编号，主键（数字串）',
    `P_name`        VARCHAR(20)  NOT NULL COMMENT '姓名',
    `P_sex`         ENUM('男','女') NOT NULL COMMENT '性别',
    `P_age`         INT          NOT NULL COMMENT '年龄',
    `P_phonenumber` VARCHAR(11)  NOT NULL COMMENT '手机号（11 位），同时作为登录账号',
    `P_password`    VARCHAR(200) NOT NULL COMMENT '登录密码（werkzeug 哈希）',
    PRIMARY KEY (`P_no`),
    UNIQUE KEY `uk_patient_phone` (`P_phonenumber`),
    CONSTRAINT `chk_patient_age` CHECK (`P_age` BETWEEN 0 AND 120),
    CONSTRAINT `chk_patient_phone` CHECK (CHAR_LENGTH(`P_phonenumber`) = 11)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci COMMENT = '患者表';


-- ============================================================================
-- 4. medicine 药品表
--    管理员维护药品目录与库存；医生开处方时按 med_id 取值并扣减 stock_quantity。
--    * med_id 必须自增：管理端新增药品时前端不提交 med_id，由数据库生成。
--    * unit_price 用 DECIMAL 而非 FLOAT，避免浮点误差（代码里的 db.Float
--      只是 Python 侧声明，MySQL 侧存 DECIMAL 读取时同样正常）。
-- ============================================================================
CREATE TABLE `medicine` (
    `med_id`         INT           NOT NULL AUTO_INCREMENT COMMENT '药品编号，自增主键',
    `med_name`       VARCHAR(50)   NOT NULL COMMENT '药品名称',
    `stock_quantity` INT           NOT NULL DEFAULT 0 COMMENT '库存数量',
    `unit_price`     DECIMAL(10,2) NOT NULL DEFAULT 0.00 COMMENT '单价（元）',
    PRIMARY KEY (`med_id`),
    UNIQUE KEY `uk_medicine_name` (`med_name`),
    CONSTRAINT `chk_medicine_stock` CHECK (`stock_quantity` >= 0),
    CONSTRAINT `chk_medicine_price` CHECK (`unit_price` >= 0)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci COMMENT = '药品表';


-- ============================================================================
-- 5. schedule 排班表（号源表）
--    管理员发布排班，患者端按"科室 + 日期"查余量并挂号，医生端查看自己的排班。
--    * (D_name, visit_date) 唯一：患者挂号成功后执行
--          UPDATE schedule SET remaining = remaining - 1
--          WHERE D_name = :name AND visit_date = :date
--      若同一医生同一天存在多条记录，这条 UPDATE 会把余量重复扣减，
--      因此唯一约束是保证"扣减幂等"的必要条件。
--      当前数据模型不含"上午/下午"时段，故一位医生一天只有一条排班；
--      若要支持多时段，需新增 time_slot 字段并把唯一键改为
--      (D_name, visit_date, time_slot)。
--    * D_title / DE_name 是发布排班时从 doctor / department 冗余下来的快照，
--      患者端查询排班时不联表即可直接展示（见设计说明第 6 节反范式说明）。
-- ============================================================================
CREATE TABLE `schedule` (
    `id`         INT          NOT NULL AUTO_INCREMENT COMMENT '排班编号，自增主键',
    `DE_name`    VARCHAR(20)  NOT NULL COMMENT '科室名称，参照 department.DE_name',
    `D_name`     VARCHAR(20)  NOT NULL COMMENT '医生姓名，参照 doctor.D_name',
    `D_title`    VARCHAR(50)  NOT NULL COMMENT '医生职称（发布排班时的快照）',
    `visit_date` DATE         NOT NULL COMMENT '出诊日期',
    `remaining`  INT          NOT NULL DEFAULT 0 COMMENT '挂号余量（号源剩余数）',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_schedule_doctor_date` (`D_name`, `visit_date`),
    KEY `idx_schedule_dept_date` (`DE_name`, `visit_date`),
    CONSTRAINT `fk_schedule_doctor`
        FOREIGN KEY (`D_name`) REFERENCES `doctor` (`D_name`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_schedule_department`
        FOREIGN KEY (`DE_name`) REFERENCES `department` (`DE_name`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `chk_schedule_remaining` CHECK (`remaining` >= 0)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci COMMENT = '排班（号源）表';


-- ============================================================================
-- 6. registration 挂号表
--    患者每次挂号生成一条记录，同时是"就诊记录"的载体
--    （medical_record 保存医生书写的病历，price 保存本次就诊的处方总金额）。
--    * D_title / DE_name 为挂号当时的快照，保证历史挂号单在科室改名、
--      医生职称变动后仍能如实还原（因此这两列不建外键）。
--    * (D_name, visit_date) 复合外键指向 schedule，保证"只能对真实存在的
--      号源挂号"，同时让排班表无法被随意删除（RESTRICT）。
--    * D_name 外键带 ON UPDATE CASCADE：管理员在后台改医生姓名时，
--      历史挂号记录会自动跟随，否则医生端将按新姓名查不到旧记录。
-- ============================================================================
CREATE TABLE `registration` (
    `id`             INT           NOT NULL AUTO_INCREMENT COMMENT '挂号编号，自增主键',
    `patient_id`     VARCHAR(10)   NOT NULL COMMENT '患者编号，参照 patient.P_no',
    `D_name`         VARCHAR(20)   NOT NULL COMMENT '医生姓名，参照 doctor.D_name',
    `D_title`        VARCHAR(50)   NOT NULL COMMENT '医生职称（挂号时的快照）',
    `DE_name`        VARCHAR(20)   NOT NULL COMMENT '科室名称（挂号时的快照）',
    `visit_date`     DATE          NOT NULL COMMENT '就诊日期',
    `medical_record` TEXT          NULL     COMMENT '病历（医生填写，未就诊为 NULL）',
    `price`          DECIMAL(10,2) NULL DEFAULT 0.00 COMMENT '本次就诊处方总金额（元）',
    PRIMARY KEY (`id`),
    KEY `idx_registration_patient` (`patient_id`),
    KEY `idx_registration_doctor_date` (`D_name`, `visit_date`),
    CONSTRAINT `fk_registration_patient`
        FOREIGN KEY (`patient_id`) REFERENCES `patient` (`P_no`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_registration_doctor`
        FOREIGN KEY (`D_name`) REFERENCES `doctor` (`D_name`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_registration_schedule`
        FOREIGN KEY (`D_name`, `visit_date`) REFERENCES `schedule` (`D_name`, `visit_date`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `chk_registration_price` CHECK (`price` IS NULL OR `price` >= 0)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci COMMENT = '挂号（就诊）表';


-- ============================================================================
-- 7. prescription 处方表（处方主表）
--    一次挂号可开多张处方（代码每提交一次就新增一条），故与挂号表是 1:N。
--    create_time 用 DATETIME：代码写入 datetime.now() 并按 '%Y-%m-%d %H:%M:%S'
--    输出，若建成 DATE 会丢掉时分秒。
-- ============================================================================
CREATE TABLE `prescription` (
    `id`              INT      NOT NULL AUTO_INCREMENT COMMENT '处方编号，自增主键',
    `registration_id` INT      NOT NULL COMMENT '挂号编号，参照 registration.id',
    `create_time`     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开方时间',
    PRIMARY KEY (`id`),
    KEY `idx_prescription_registration` (`registration_id`),
    CONSTRAINT `fk_prescription_registration`
        FOREIGN KEY (`registration_id`) REFERENCES `registration` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci COMMENT = '处方主表';


-- ============================================================================
-- 8. prescription_detail 处方明细表（弱实体）
--    一行 = 一张处方中的一种药。
--    * med_name / unit_price 是开方当时的快照：药品调价或被删除后，
--      历史处方仍要能正确显示"当时按多少钱开的"。这是有意保留的冗余，
--      因此不把 med_name 建为外键、允许其与 medicine 表取值不一致。
--    * prescription_id 外键带 ON DELETE CASCADE：删处方时明细一并清除，
--      明细脱离主表没有独立意义（典型弱实体/存在依赖）。
-- ============================================================================
CREATE TABLE `prescription_detail` (
    `id`              INT           NOT NULL AUTO_INCREMENT COMMENT '明细编号，自增主键',
    `prescription_id` INT           NOT NULL COMMENT '处方编号，参照 prescription.id',
    `med_id`          INT           NOT NULL COMMENT '药品编号，参照 medicine.med_id',
    `med_name`        VARCHAR(50)   NOT NULL COMMENT '药品名称（开方时的快照）',
    `unit_price`      DECIMAL(10,2) NOT NULL COMMENT '单价（开方时的快照，元）',
    `quantity`        INT           NOT NULL COMMENT '开药数量',
    PRIMARY KEY (`id`),
    KEY `idx_detail_prescription` (`prescription_id`),
    KEY `idx_detail_medicine` (`med_id`),
    CONSTRAINT `fk_detail_prescription`
        FOREIGN KEY (`prescription_id`) REFERENCES `prescription` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_detail_medicine`
        FOREIGN KEY (`med_id`) REFERENCES `medicine` (`med_id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `chk_detail_quantity` CHECK (`quantity` > 0),
    CONSTRAINT `chk_detail_price` CHECK (`unit_price` >= 0)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_general_ci COMMENT = '处方明细表';


-- ============================================================================
-- 建表结果自检（可选，导入后手工执行确认 8 张表齐全）
-- ============================================================================
-- SHOW TABLES;
-- SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES
--   WHERE TABLE_SCHEMA = 'hospital';
-- SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_COMMENT
--   FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'hospital'
--   ORDER BY TABLE_NAME, ORDINAL_POSITION;
