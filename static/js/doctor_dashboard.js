document.addEventListener('DOMContentLoaded', function() {
    // 状态变量定义
    const showSchedulesBtn = document.getElementById('showSchedulesBtn');
    const schedulesContainer = document.getElementById('schedulesContainer');
    let isSchedulesVisible = false;
    
    const showMedicinesBtn = document.getElementById('showMedicinesBtn');
    const medicinesContainer = document.getElementById('medicinesContainer');
    let isMedicinesVisible = false;  // 添加药品信息可见状态变量

    const showMyScheduleBtn = document.getElementById('showMyScheduleBtn');
    const myScheduleContainer = document.getElementById('myScheduleContainer');
    let isMyScheduleVisible = false;

    const showAllPatientsBtn = document.getElementById('showAllPatientsBtn');
    const allPatientsContainer = document.getElementById('allPatientsContainer');
    let isAllPatientsVisible = false;

    // 就诊安排按钮点击事件
    showSchedulesBtn.addEventListener('click', function() {
        if (isSchedulesVisible) {
            schedulesContainer.classList.add('hidden');
            showSchedulesBtn.textContent = '就诊安排';
            isSchedulesVisible = false;
        } else {
            schedulesContainer.classList.remove('hidden');
            showSchedulesBtn.textContent = '隐藏安排';
            isSchedulesVisible = true;
            
            // 初始化日期按钮
            initDateButtons();
        }
    });

    // 初始化日期按钮
    function initDateButtons() {
        const dateButtons = schedulesContainer.querySelectorAll('.date-btn');
        
        dateButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const selectedDate = this.dataset.date;
                loadPatientSchedules(selectedDate);
            });
        });
    }

    // 加载患者信息
    function loadPatientSchedules(date) {
        const tbody = schedulesContainer.querySelector('tbody');
        tbody.innerHTML = '<tr><td colspan="4" class="loading">加载中...</td></tr>';
        
        fetch(`/api/patient_schedules/${date}`)
            .then(response => {
                if (!response.ok) throw new Error('网络响应不正常');
                return response.json();
            })
            .then(data => {
                tbody.innerHTML = '';
                
                if (data.length > 0) {
                    data.forEach(patient => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${patient.patient_id}</td>
                            <td>${patient.patient_name}</td>
                            <td>${patient.patient_gender}</td>
                            <td>${patient.visit_date}</td>
                        `;
                        tbody.appendChild(row);
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="4" class="no-data">该日期无就诊安排</td></tr>';
                }
            })
            .catch(error => {
                tbody.innerHTML = `<tr><td colspan="4" class="error">加载失败: ${error.message}</td></tr>`;
            });
    }

    // 药品信息按钮点击事件
    showMedicinesBtn.addEventListener('click', function() {
        if (isMedicinesVisible) {
            medicinesContainer.classList.add('hidden');
            showMedicinesBtn.innerHTML = '<span class="btn-icon">💊</span><span>药品信息</span>';
            isMedicinesVisible = false;
            return;
        }
        
        showMedicinesBtn.innerHTML = '<span class="btn-icon">⏳</span><span>加载中...</span>';
        
        fetch('/api/medicines')
            .then(response => {
                if (!response.ok) throw new Error('网络响应不正常');
                return response.json();
            })
            .then(data => {
                const tbody = medicinesContainer.querySelector('tbody');
                tbody.innerHTML = '';
                
                if (data.length > 0) {
                    data.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${item.med_id}</td>
                            <td>${item.med_name}</td>
                            <td>${item.stock_quantity}</td>
                            <td>${item.unit_price.toFixed(2)}</td>
                        `;
                        tbody.appendChild(row);
                    });
                } else {
                    const row = document.createElement('tr');
                    row.innerHTML = '<td colspan="4" class="no-data">暂无药品信息</td>';
                    tbody.appendChild(row);
                }
                
                medicinesContainer.classList.remove('hidden');
                showMedicinesBtn.innerHTML = '<span class="btn-icon">💊</span><span>隐藏药品</span>';
                isMedicinesVisible = true;
                
                // 确保就诊安排面板关闭
                schedulesContainer.classList.add('hidden');
                showSchedulesBtn.innerHTML = '<span class="btn-icon">📅</span><span>就诊安排</span>';
                isSchedulesVisible = false;
            })
            .catch(error => {
                console.error('获取药品信息失败:', error);
                alert('获取药品信息失败: ' + error.message);
                showMedicinesBtn.innerHTML = '<span class="btn-icon">💊</span><span>药品信息</span>';
            });
    });

    // 我的排班表按钮点击事件
    showMyScheduleBtn.addEventListener('click', function() {
        if (isMyScheduleVisible) {
            myScheduleContainer.classList.add('hidden');
            showMyScheduleBtn.innerHTML = '<span class="btn-icon">📋</span><span>我的排班表</span>';
            isMyScheduleVisible = false;
            return;
        }
        
        showMyScheduleBtn.innerHTML = '<span class="btn-icon">⏳</span><span>加载中...</span>';
        
        fetch('/api/doctor_schedules_self')
            .then(response => {
                if (!response.ok) throw new Error('网络响应不正常');
                return response.json();
            })
            .then(data => {
                const tbody = myScheduleContainer.querySelector('tbody');
                tbody.innerHTML = '';
                
                if (data.length > 0) {
                    data.forEach(item => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${item.department || '未知'}</td>
                            <td>${item.doctor_name || '未知'}</td>
                            <td>${item.visit_date}</td>
                        `;
                        tbody.appendChild(row);
                    });
                } else {
                    const row = document.createElement('tr');
                    row.innerHTML = '<td colspan="3" class="no-data">暂无排班信息</td>';
                    tbody.appendChild(row);
                }
                
                myScheduleContainer.classList.remove('hidden');
                showMyScheduleBtn.innerHTML = '<span class="btn-icon">📋</span><span>隐藏排班表</span>';
                isMyScheduleVisible = true;
                
                // 隐藏其他面板
                schedulesContainer.classList.add('hidden');
                medicinesContainer.classList.add('hidden');
                isSchedulesVisible = false;
                isMedicinesVisible = false;
                showSchedulesBtn.innerHTML = '<span class="btn-icon">📅</span><span>就诊安排</span>';
                showMedicinesBtn.innerHTML = '<span class="btn-icon">💊</span><span>药品信息</span>';
            })
            .catch(error => {
                console.error('获取排班表失败:', error);
                alert('获取排班信息失败: ' + error.message);
                showMyScheduleBtn.innerHTML = '<span class="btn-icon">📋</span><span>我的排班表</span>';
            });
    });

    // 添加"我的患者"按钮点击事件
    showAllPatientsBtn.addEventListener('click', function() {
        if (isAllPatientsVisible) {
            allPatientsContainer.classList.add('hidden');
            showAllPatientsBtn.innerHTML = '<span class="btn-icon">👥</span><span>我的患者</span>';
            isAllPatientsVisible = false;
            return;
        }
        
        showAllPatientsBtn.innerHTML = '<span class="btn-icon">⏳</span><span>加载中...</span>';
        
        fetch('/api/all_patients')
            .then(response => {
                if (!response.ok) throw new Error('网络响应不正常');
                return response.json();
            })
            .then(data => {
                const tbody = allPatientsContainer.querySelector('tbody');
                tbody.innerHTML = '';
                
                if (data.length > 0) {
                    data.forEach(patient => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${patient.patient_id}</td>
                            <td>${patient.patient_name}</td>
                            <td>${patient.patient_gender}</td>
                            <td>${patient.visit_date}</td>
                        `;
                        // 添加点击事件
                        row.style.cursor = 'pointer';
                        row.addEventListener('click', () => {
                            window.location.href = `/patient_record/${patient.patient_id}?date=${patient.visit_date}`;
                        });
                        tbody.appendChild(row);
                    });
                } else {
                    const row = document.createElement('tr');
                    row.innerHTML = '<td colspan="4" class="no-data">暂无患者信息</td>';
                    tbody.appendChild(row);
                }
                
                allPatientsContainer.classList.remove('hidden');
                showAllPatientsBtn.innerHTML = '<span class="btn-icon">👥</span><span>隐藏患者</span>';
                isAllPatientsVisible = true;
                
                // 隐藏其他面板
                schedulesContainer.classList.add('hidden');
                medicinesContainer.classList.add('hidden');
                myScheduleContainer.classList.add('hidden');
                isSchedulesVisible = false;
                isMedicinesVisible = false;
                isMyScheduleVisible = false;
                showSchedulesBtn.innerHTML = '<span class="btn-icon">📅</span><span>就诊安排</span>';
                showMedicinesBtn.innerHTML = '<span class="btn-icon">💊</span><span>药品信息</span>';
                showMyScheduleBtn.innerHTML = '<span class="btn-icon">📋</span><span>我的排班表</span>';
            })
            .catch(error => {
                console.error('获取患者信息失败:', error);
                alert('获取患者信息失败: ' + error.message);
                showAllPatientsBtn.innerHTML = '<span class="btn-icon">👥</span><span>我的患者</span>';
            });
    });
});

// 添加开药按钮功能
document.getElementById('prescribeMedicineBtn').addEventListener('click', function() {
    if (this.classList.contains('active')) {
        document.getElementById('prescribeMedicineContainer').classList.add('hidden');
        this.classList.remove('active');
        return;
    }
    
    this.classList.add('active');
    fetch('/api/prescribe/patients')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('prescribePatientList');
            container.innerHTML = '';
            
            if (data.length === 0) {
                container.innerHTML = '<tr><td colspan="4">没有可开药的患者</td></tr>';
                return;
            }
            
            data.forEach(patient => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${patient.patient_id}</td>
                    <td>${patient.patient_name}</td>
                    <td>${patient.patient_gender}</td>
                    <td>${patient.visit_date}</td>
                `;
                row.style.cursor = 'pointer';
                row.addEventListener('click', () => {
                    window.location.href = `/prescribe_medicine?registration_id=${patient.registration_id}`;
                });
                container.appendChild(row);
            });
            
            document.getElementById('prescribeMedicineContainer').classList.remove('hidden');
        });
});