document.addEventListener('DOMContentLoaded', function() {
    // 标签页切换
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            // 更新按钮状态
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // 更新内容区
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            
            // 加载对应数据
            loadTableData(tabId);
        });
    });
    
    // 模态框
    const modal = document.getElementById('modal');
    const closeBtn = document.querySelector('.close');
    const submitBtn = document.getElementById('submit-btn');
    
    // 打开模态框的按钮
    document.getElementById('add-de-btn').addEventListener('click', () => showModal('department', 'add'));
    document.getElementById('add-doctor-btn').addEventListener('click', () => showModal('doctor', 'add'));
    document.getElementById('add-medicine-btn').addEventListener('click', () => showModal('medicine', 'add'));
    document.getElementById('add-schedule-btn').addEventListener('click', () => showModal('schedule', 'add'));
    
    // 关闭模态框
    closeBtn.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // 初始化加载第一个标签页的数据
    loadTableData('department');
});

let currentAction = ''; // 'add' or 'edit'
let currentTable = '';
let currentId = ''; // 用于编辑时记录ID

function showModal(table, action, data = null) {
    currentAction = action;
    currentTable = table;
    currentId = data ? (table === 'department' ? data.DE_no : 
                       table === 'doctor' ? data.D_no : 
                       table === 'medicine' ? data.med_id : data.id) : '';
    
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modal-title');
    const modalForm = document.getElementById('modal-form');
    modalForm.innerHTML = '';
    
    // 设置标题
    modalTitle.textContent = action === 'add' ? `添加${getTableName(table)}` : `编辑${getTableName(table)}`;
    
    // 根据表类型生成表单
    switch(table) {
        case 'department':
            createDepartmentForm(modalForm, data);
            break;
        case 'doctor':
            createDoctorForm(modalForm, data);
            break;
        case 'medicine':
            createMedicineForm(modalForm, data);
            break;
        case 'schedule':
            createScheduleForm(modalForm, data);
            break;
    }
    
    modal.style.display = 'block';
}

function getTableName(table) {
    const names = {
        'department': '科室',
        'doctor': '医生',
        'medicine': '药品',
        'schedule': '排班'
    };
    return names[table] || '';
}

function createDepartmentForm(form, data) {
    form.innerHTML = `
        <div class="form-group">
            <label for="DE_no">科室编号</label>
            <input type="text" id="DE_no" name="DE_no" value="${data ? data.DE_no : ''}" ${currentAction === 'edit' ? 'readonly' : ''}>
        </div>
        <div class="form-group">
            <label for="DE_name">科室名称</label>
            <input type="text" id="DE_name" name="DE_name" value="${data ? data.DE_name : ''}">
        </div>
    `;
}

function createDoctorForm(form, data) {
    form.innerHTML = `
        <div class="form-group">
            <label for="D_no">工号</label>
            <input type="text" id="D_no" name="D_no" value="${data ? data.D_no : ''}" ${currentAction === 'edit' ? 'readonly' : ''}>
        </div>
        <div class="form-group">
            <label for="D_name">姓名</label>
            <input type="text" id="D_name" name="D_name" value="${data ? data.D_name : ''}">
        </div>
        <div class="form-group">
            <label for="D_sex">性别</label>
            <select id="D_sex" name="D_sex">
                <option value="男" ${data && data.D_sex === '男' ? 'selected' : ''}>男</option>
                <option value="女" ${data && data.D_sex === '女' ? 'selected' : ''}>女</option>
            </select>
        </div>
        <div class="form-group">
            <label for="D_age">年龄</label>
            <input type="number" id="D_age" name="D_age" value="${data ? data.D_age : ''}">
        </div>
        <div class="form-group">
            <label for="D_Title">职称</label>
            <input type="text" id="D_Title" name="D_Title" value="${data ? data.D_Title : ''}">
        </div>
        <div class="form-group">
            <label for="D_Department">科室</label>
            <input type="text" id="D_Department" name="D_Department" value="${data ? data.D_Department : ''}">
        </div>
        ${currentAction === 'add' ? `
        <div class="form-group">
            <label for="D_password">密码</label>
            <input type="password" id="D_password" name="D_password">
        </div>
        ` : ''}
    `;
}

function createMedicineForm(form, data) {
    form.innerHTML = `
        ${currentAction === 'edit' ? `
        <div class="form-group">
            <label for="med_id">药品ID</label>
            <input type="text" id="med_id" name="med_id" value="${data ? data.med_id : ''}" readonly>
        </div>
        ` : ''}
        <div class="form-group">
            <label for="med_name">药品名称</label>
            <input type="text" id="med_name" name="med_name" value="${data ? data.med_name : ''}">
        </div>
        <div class="form-group">
            <label for="stock_quantity">库存数量</label>
            <input type="number" id="stock_quantity" name="stock_quantity" value="${data ? data.stock_quantity : ''}">
        </div>
        <div class="form-group">
            <label for="unit_price">单价</label>
            <input type="number" step="0.01" id="unit_price" name="unit_price" value="${data ? data.unit_price : ''}">
        </div>
    `;
}

function createScheduleForm(form, data) {
    form.innerHTML = `
        ${currentAction === 'edit' ? `
        <div class="form-group">
            <label for="id">ID</label>
            <input type="text" id="id" name="id" value="${data ? data.id : ''}" readonly>
        </div>
        ` : ''}
        <div class="form-group">
            <label for="D_name">医生姓名</label>
            <input type="text" id="D_name" name="D_name" value="${data ? data.D_name : ''}">
        </div>
        <div class="form-group">
            <label for="D_title">医生职称</label>
            <input type="text" id="D_title" name="D_title" value="${data ? data.D_title : ''}">
        </div>
        <div class="form-group">
            <label for="DE_name">科室名称</label>
            <input type="text" id="DE_name" name="DE_name" value="${data ? data.DE_name : ''}">
        </div>
        <div class="form-group">
            <label for="visit_date">出诊日期</label>
            <input type="date" id="visit_date" name="visit_date" value="${data ? data.visit_date : ''}">
        </div>
        <div class="form-group">
            <label for="remaining">挂号余量</label>
            <input type="number" id="remaining" name="remaining" value="${data ? data.remaining : ''}">
        </div>
    `;
}

// 提交表单
document.getElementById('submit-btn').addEventListener('click', function() {
    const form = document.getElementById('modal-form');
    const formData = new FormData(form);
    const data = {};
    
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    let url = `/api/${currentTable}s`;
    let method = 'POST';
    
    if (currentAction === 'edit') {
        method = 'PUT';
        if (currentTable === 'department') data['DE_no'] = currentId;
        else if (currentTable === 'doctor') data['D_no'] = currentId;
        else if (currentTable === 'medicine') data['med_id'] = currentId;
        else if (currentTable === 'schedule') data['id'] = currentId;
    }
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert(result.message);
            document.getElementById('modal').style.display = 'none';
            loadTableData(currentTable);
        } else {
            alert('操作失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('操作失败: ' + error);
    });
});

// 加载表格数据
function loadTableData(table) {
    fetch(`/api/${table}s`)
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector(`#${table}-table tbody`);
            tbody.innerHTML = '';
            
            data.forEach(item => {
                const row = document.createElement('tr');
                
                if (table === 'department') {
                    row.innerHTML = `
                        <td>${item.DE_no}</td>
                        <td>${item.DE_name}</td>
                        <td>
                            <button class="edit" onclick="editItem('${table}', ${JSON.stringify(item).replace(/"/g, '&quot;')})">编辑</button>
                            <button class="delete" onclick="deleteItem('${table}', '${item.DE_no}')">删除</button>
                        </td>
                    `;
                } else if (table === 'doctor') {
                    row.innerHTML = `
                        <td>${item.D_no}</td>
                        <td>${item.D_name}</td>
                        <td>${item.D_sex}</td>
                        <td>${item.D_age}</td>
                        <td>${item.D_Title}</td>
                        <td>${item.D_Department}</td>
                        <td>
                            <button class="edit" onclick="editItem('${table}', ${JSON.stringify(item).replace(/"/g, '&quot;')})">编辑</button>
                            <button class="delete" onclick="deleteItem('${table}', '${item.D_no}')">删除</button>
                        </td>
                    `;
                } else if (table === 'medicine') {
                    row.innerHTML = `
                        <td>${item.med_id}</td>
                        <td>${item.med_name}</td>
                        <td>${item.stock_quantity}</td>
                        <td>${item.unit_price}</td>
                        <td>
                            <button class="edit" onclick="editItem('${table}', ${JSON.stringify(item).replace(/"/g, '&quot;')})">编辑</button>
                            <button class="delete" onclick="deleteItem('${table}', '${item.med_id}')">删除</button>
                        </td>
                    `;
                } else if (table === 'schedule') {
                    row.innerHTML = `
                        <td>${item.id}</td>
                        <td>${item.D_name || ''}</td>
                        <td>${item.D_title || ''}</td>
                        <td>${item.DE_name || ''}</td>
                        <td>${item.visit_date || ''}</td>
                        <td>${item.remaining || ''}</td>  <!-- 保持使用remaining -->
                        <td>
                            <button class="edit" onclick="editItem('${table}', ${JSON.stringify(item).replace(/"/g, '&quot;')})">编辑</button>
                            <button class="delete" onclick="deleteItem('${table}', '${item.id}')">删除</button>
                        </td>
                    `;
                }
                
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// 全局函数
window.editItem = function(table, data) {
    showModal(table, 'edit', data);
};

window.deleteItem = function(table, id) {
    if (!confirm('确定要删除这条记录吗？')) return;
    
    let data = {};
    if (table === 'department') data['DE_no'] = id;
    else if (table === 'doctor') data['D_no'] = id;
    else if (table === 'medicine') data['med_id'] = id;
    else if (table === 'schedule') data['id'] = id;
    
    fetch(`/api/${table}s`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert(result.message);
            loadTableData(table);
        } else {
            alert('删除失败: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('删除失败: ' + error);
    });
};