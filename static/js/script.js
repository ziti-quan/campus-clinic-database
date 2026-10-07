// 全局状态变量
let currentView = null;
const viewStates = {
    DOCTORS: 'doctors',
    SCHEDULE: 'schedule',
    REGISTRATIONS: 'registrations',
    MEDICAL_RECORDS: 'medicalRecords',
    PRESCRIPTIONS: 'prescriptions'
};

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    // 绑定按钮事件
    document.getElementById('showDoctorsBtn').addEventListener('click', showDoctorsView);
    document.getElementById('showDeptBtn').addEventListener('click', showDeptSelection);
    document.getElementById('showMyRegBtn').addEventListener('click', showMyRegistrations);
    document.getElementById('showMedicalRecordsBtn').addEventListener('click', showMedicalRecords);
    document.getElementById('showPrescriptionsBtn').addEventListener('click', showPrescriptions);
});

// 显示医生信息视图
function showDoctorsView() {
    if (currentView === viewStates.DOCTORS) {
        hideCurrentView();
        return;
    }
    
    setActiveButton('showDoctorsBtn');
    showLoading('doctorsTableContainer');
    
    fetch('/get_doctors')
        .then(handleResponse)
        .then(data => {
            if (data.error) throw new Error(data.details || data.error);
            if (data.warning) {
                renderMessage('doctorsTableContainer', data.warning);
            } else {
                renderDoctorsTable(data);
            }
            showView('doctorsTableContainer', viewStates.DOCTORS);
        })
        .catch(error => {
            console.error('Error:', error);
            renderError('doctorsTableContainer', `获取医生信息失败: ${error.message}`);
            showView('doctorsTableContainer', viewStates.DOCTORS);
        });
}

// 渲染医生表格
function renderDoctorsTable(doctors) {
    const container = document.querySelector('#doctorsTableContainer .data-content');
    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th><i class="fas fa-id-card"></i> 医生编号</th>
                    <th><i class="fas fa-user"></i> 姓名</th>
                    <th><i class="fas fa-venus-mars"></i> 性别</th>
                    <th><i class="fas fa-birthday-cake"></i> 年龄</th>
                    <th><i class="fas fa-award"></i> 职称</th>
                    <th><i class="fas fa-clinic-medical"></i> 科室</th>
                </tr>
            </thead>
            <tbody>
                ${doctors.map(doctor => `
                    <tr>
                        <td>${doctor.D_no}</td>
                        <td>${doctor.D_name}</td>
                        <td>${doctor.D_sex}</td>
                        <td>${doctor.D_age}</td>
                        <td>${doctor.D_Title}</td>
                        <td>${doctor.D_Department}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// 显示科室选择界面
function showDeptSelection() {
    if (currentView === viewStates.SCHEDULE) return;
    
    setActiveButton('showDeptBtn');
    const container = document.getElementById('scheduleContainer');
    container.innerHTML = `
        <div class="data-header">
            <h2><i class="fas fa-calendar-plus"></i> 挂号预约</h2>
        </div>
        <div class="data-content">
            <h3><i class="fas fa-clinic-medical"></i> 请选择科室</h3>
            <div class="dept-btn-container">
                ${['内科', '外科', '普通门诊'].map(dept => `
                    <button class="dept-btn" data-dept="${dept}">
                        <i class="fas fa-stethoscope"></i> ${dept}
                    </button>
                `).join('')}
            </div>
        </div>
    `;
    
    // 绑定科室按钮事件
    document.querySelectorAll('.dept-btn').forEach(btn => {
        btn.addEventListener('click', () => showDateSelection(btn.dataset.dept));
    });
    
    showView('scheduleContainer', viewStates.SCHEDULE);
}

// 显示日期选择界面
function showDateSelection(dept) {
    const container = document.getElementById('scheduleContainer');
    container.innerHTML = `
        <div class="data-header">
            <h2><i class="fas fa-calendar-plus"></i> 挂号预约</h2>
        </div>
        <div class="data-content">
            <button class="back-btn" id="backToDeptBtn">
                <i class="fas fa-arrow-left"></i> 返回科室选择
            </button>
            <h3><i class="fas fa-clinic-medical"></i> ${dept} - 请选择日期</h3>
            <div class="date-btn-container">
                ${['2025-06-10', '2025-06-11', '2025-06-12'].map(date => `
                    <button class="date-btn" data-date="${date}">
                        <i class="fas fa-calendar-day"></i> ${date}
                    </button>
                `).join('')}
            </div>
        </div>
    `;
    
    // 绑定日期按钮事件
    document.querySelectorAll('.date-btn').forEach(btn => {
        btn.addEventListener('click', () => loadSchedules(dept, btn.dataset.date));
    });
    
    // 明确绑定返回按钮事件 - 使用ID选择器确保准确
    document.getElementById('backToDeptBtn').addEventListener('click', function(e) {
        e.preventDefault();
        showDeptSelection();
    });
}


// 加载排班信息
function loadSchedules(dept, date) {
    const formattedDate = formatDateToYYYYMMDD(date);
    const container = document.getElementById('scheduleContainer');
    container.querySelector('.data-content').innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i> 正在加载排班信息...
        </div>
    `;
    
    fetch(`/api/schedules/${encodeURIComponent(dept)}?date=${formattedDate}`)
        .then(handleResponse)
        .then(data => {
            let content = `
                <button class="back-btn" id="backToDateBtn" data-dept="${dept}">
                    <i class="fas fa-arrow-left"></i> 返回日期选择
                </button>
                <h3><i class="fas fa-clinic-medical"></i> ${dept} - ${formattedDate}</h3>
            `;
            
            if (data.length > 0) {
                content += data.map(s => `
                    <div class="schedule-item">
                        <h4><i class="fas fa-user-md"></i> ${s.D_name} ${s.D_title}</h4>
                        <p><i class="fas fa-calendar-day"></i> 日期: ${s.visit_date} | <i class="fas fa-ticket-alt"></i> 余量: ${s.挂号余量}</p>
                        <button class="book-btn" 
                                data-dname="${s.D_name}"
                                data-dtitle="${s.D_title}"
                                data-dept="${dept}"
                                data-date="${s.visit_date}">
                            <i class="fas fa-bookmark"></i> 预约
                        </button>
                    </div>
                `).join('');
            } else {
                content += `<p class="no-data"><i class="fas fa-info-circle"></i> ${formattedDate} ${dept}暂无可用号源</p>`;
            }
            
            container.querySelector('.data-content').innerHTML = content;
            
            // 绑定预约按钮事件
            document.querySelectorAll('.book-btn').forEach(btn => {
                btn.addEventListener('click', () => bookSchedule({
                    D_name: btn.dataset.dname,
                    D_title: btn.dataset.dtitle,
                    De_name: btn.dataset.dept,
                    visit_date: btn.dataset.date
                }));
            });
            
            // 明确绑定返回按钮事件 - 使用ID选择器确保准确
            document.getElementById('backToDateBtn').addEventListener('click', function(e) {
                e.preventDefault();
                showDateSelection(dept);
            });
        })
        .catch(error => {
            console.error("加载失败:", error);
            container.querySelector('.data-content').innerHTML = `
                <p class="error"><i class="fas fa-exclamation-circle"></i> 加载失败: ${error.message}</p>
                <button class="back-btn" id="errorBackToDateBtn" data-dept="${dept}">
                    <i class="fas fa-arrow-left"></i> 返回日期选择
                </button>
            `;
            
            // 明确绑定错误页面的返回按钮事件
            document.getElementById('errorBackToDateBtn').addEventListener('click', function(e) {
                e.preventDefault();
                showDateSelection(dept);
            });
        });
}

// 显示我的挂号记录
function showMyRegistrations() {
    if (currentView === viewStates.REGISTRATIONS) {
        hideCurrentView();
        return;
    }
    
    setActiveButton('showMyRegBtn');
    const container = document.getElementById('scheduleContainer');
    container.innerHTML = `
        <div class="data-header">
            <h2><i class="fas fa-calendar-check"></i> 我的挂号</h2>
        </div>
        <div class="data-content">
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i> 正在加载挂号记录...
            </div>
        </div>
    `;
    
    fetch('/api/my_registrations')
        .then(handleResponse)
        .then(regs => {
            let content = '<h3><i class="fas fa-history"></i> 历史挂号记录</h3>';
            
            if (regs.length > 0) {
                content += regs.map(r => `
                    <div class="reg-item">
                        <h3><i class="fas fa-user-md"></i> ${r.D_name} ${r.D_title}</h3>
                        <p><i class="fas fa-clinic-medical"></i> 科室: ${r.De_name} | <i class="fas fa-calendar-day"></i> 日期: ${r.visit_date}</p>
                    </div>
                `).join('');
            } else {
                content += '<p class="no-data"><i class="fas fa-info-circle"></i> 暂无挂号记录</p>';
            }
            
            container.querySelector('.data-content').innerHTML = content;
            showView('scheduleContainer', viewStates.REGISTRATIONS);
        })
        .catch(error => {
            console.error('获取挂号记录失败:', error);
            container.querySelector('.data-content').innerHTML = `
                <p class="error"><i class="fas fa-exclamation-circle"></i> 获取挂号记录失败: ${error.message}</p>
            `;
            showView('scheduleContainer', viewStates.REGISTRATIONS);
        });
}

// 显示病历记录
function showMedicalRecords() {
    if (currentView === viewStates.MEDICAL_RECORDS) {
        hideCurrentView();
        return;
    }
    
    setActiveButton('showMedicalRecordsBtn');
    const container = document.getElementById('medicalRecordsContainer');
    showLoading('medicalRecordsContainer');
    
    fetch('/api/my_medical_records')
        .then(handleResponse)
        .then(data => {
            let content = '<h3><i class="fas fa-file-medical"></i> 病历记录</h3>';
            
            if (data.length > 0) {
                content += data.map(record => `
                    <div class="medical-record-item">
                        <h3><i class="fas fa-user-md"></i> ${record.D_name} ${record.D_title} - ${formatDate(record.visit_date)}</h3>
                        <div class="record-content">
                            ${record.medical_record ? `
                                <pre><i class="fas fa-file-alt"></i> ${record.medical_record}</pre>
                            ` : '<p class="no-data"><i class="fas fa-info-circle"></i> 暂无病历记录</p>'}
                        </div>
                    </div>
                `).join('');
            } else {
                content += '<p class="no-data"><i class="fas fa-info-circle"></i> 暂无病历记录</p>';
            }
            
            container.querySelector('.data-content').innerHTML = content;
            showView('medicalRecordsContainer', viewStates.MEDICAL_RECORDS);
        })
        .catch(error => {
            console.error('获取病历失败:', error);
            renderError('medicalRecordsContainer', `获取病历失败: ${error.message}`);
            showView('medicalRecordsContainer', viewStates.MEDICAL_RECORDS);
        });
}

// 显示药单记录
function showPrescriptions() {
    if (currentView === viewStates.PRESCRIPTIONS) {
        hideCurrentView();
        return;
    }
    
    setActiveButton('showPrescriptionsBtn');
    const container = document.getElementById('prescriptionsContainer');
    showLoading('prescriptionsContainer');
    
    fetch('/api/my_prescriptions')
        .then(handleResponse)
        .then(data => {
            let content = '<h3><i class="fas fa-prescription-bottle-alt"></i> 药单记录</h3>';
            
            if (data.length > 0) {
                content += data.map(prescription => `
                    <div class="prescription-item">
                        <h3><i class="fas fa-user-md"></i> ${prescription.D_name} ${prescription.D_title} - ${formatDate(prescription.visit_date)}</h3>
                        <p><i class="fas fa-clock"></i> 开方时间: ${prescription.create_time} | <i class="fas fa-money-bill-wave"></i> 总费用: ${prescription.total_price.toFixed(2)}元</p>
                        <div class="medicine-list">
                            <table>
                                <thead>
                                    <tr>
                                        <th><i class="fas fa-pills"></i> 药品名称</th>
                                        <th><i class="fas fa-tag"></i> 单价</th>
                                        <th><i class="fas fa-sort-amount-up"></i> 数量</th>
                                        <th><i class="fas fa-calculator"></i> 小计</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${prescription.medicines.map(med => `
                                        <tr>
                                            <td>${med.med_name}</td>
                                            <td>${med.unit_price.toFixed(2)}</td>
                                            <td>${med.quantity}</td>
                                            <td>${(med.unit_price * med.quantity).toFixed(2)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `).join('');
            } else {
                content += '<p class="no-data"><i class="fas fa-info-circle"></i> 暂无药单记录</p>';
            }
            
            container.querySelector('.data-content').innerHTML = content;
            showView('prescriptionsContainer', viewStates.PRESCRIPTIONS);
        })
        .catch(error => {
            console.error('获取药单失败:', error);
            renderError('prescriptionsContainer', `获取药单失败: ${error.message}`);
            showView('prescriptionsContainer', viewStates.PRESCRIPTIONS);
        });
}

// 预约功能
let isSubmitting = false;

function bookSchedule(schedule) {
    if (isSubmitting) return;
    
    if (!confirm(`确认预约 ${schedule.D_name} 医生的 ${schedule.visit_date} 号源?`)) {
        return;
    }
    
    isSubmitting = true;
    const originalBtnText = document.querySelector(`.book-btn[data-dname="${schedule.D_name}"]`)?.textContent;
    
    // 显示加载状态
    document.querySelectorAll('.book-btn').forEach(btn => {
        btn.disabled = true;
        if (btn.dataset.dname === schedule.D_name) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 预约中...';
        }
    });
    
    fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(schedule)
    })
    .then(handleResponse)
    .then(data => {
        alert('预约成功!');
        loadSchedules(schedule.De_name, schedule.visit_date);
    })
    .catch(error => {
        console.error('预约错误:', error);
        alert(`预约失败: ${error.message}`);
    })
    .finally(() => {
        isSubmitting = false;
        // 恢复按钮状态
        document.querySelectorAll('.book-btn').forEach(btn => {
            btn.disabled = false;
            if (btn.dataset.dname === schedule.D_name && originalBtnText) {
                btn.innerHTML = '<i class="fas fa-bookmark"></i> 预约';
            }
        });
    });
}

// 辅助函数：确保日期格式为YYYY-MM-DD
function formatDateToYYYYMMDD(dateStr) {
    if (!dateStr) return '';
    
    if (dateStr.includes('T')) {
        return dateStr.split('T')[0];
    }
    
    const parts = dateStr.split('-');
    if (parts.length === 3) {
        const year = parts[0];
        const month = parts[1].padStart(2, '0');
        const day = parts[2].padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    return dateStr;
}

// 日期格式化函数
window.formatDate = function(dateStr) {
    if (!dateStr) return '未知日期';
    if (dateStr.includes('T')) {
        return dateStr.split('T')[0];
    }
    return dateStr;
};

// 通用响应处理
function handleResponse(res) {
    if (!res.ok) {
        return res.json().then(err => { throw new Error(err.error || err.message || '请求失败'); });
    }
    return res.json();
}

// 显示加载状态
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    container.querySelector('.data-content').innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i> 正在加载数据...
        </div>
    `;
}

// 渲染错误信息
function renderError(containerId, message) {
    const container = document.getElementById(containerId);
    container.querySelector('.data-content').innerHTML = `
        <p class="error">
            <i class="fas fa-exclamation-circle"></i> ${message}
        </p>
    `;
}

// 渲染信息
function renderMessage(containerId, message) {
    const container = document.getElementById(containerId);
    container.querySelector('.data-content').innerHTML = `
        <p class="no-data">
            <i class="fas fa-info-circle"></i> ${message}
        </p>
    `;
}

// 设置活动按钮
function setActiveButton(buttonId) {
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(buttonId).classList.add('active');
}

// 显示视图
function showView(containerId, viewType) {
    document.querySelectorAll('.data-container').forEach(container => {
        container.classList.remove('active');
    });
    
    const container = document.getElementById(containerId);
    container.classList.add('active');
    currentView = viewType;
}

// 隐藏当前视图
function hideCurrentView() {
    document.querySelectorAll('.data-container').forEach(container => {
        container.classList.remove('active');
    });
    
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    currentView = null;
}