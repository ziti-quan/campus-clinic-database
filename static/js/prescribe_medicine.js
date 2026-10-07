document.addEventListener('DOMContentLoaded', function() {
    const registrationId = new URLSearchParams(window.location.search).get('registration_id');
    let selectedMedicines = [];
    let medicinesData = [];
    
    // 加载患者信息
    function loadPatientInfo() {
        fetch(`/api/registration/${registrationId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('patientName').textContent = data.patient_name;
                document.getElementById('patientId').textContent = data.patient_id;
                document.getElementById('patientGender').textContent = data.patient_gender;
                document.getElementById('visitDate').textContent = data.visit_date;
            });
    }
    
    // 加载药品数据
    function loadMedicines() {
        fetch('/api/medicines')
            .then(response => response.json())
            .then(data => {
                medicinesData = data;
                const select = document.getElementById('medicineSelect');
                select.innerHTML = '<option value="">选择药品</option>';
                
                data.forEach(medicine => {
                    const option = document.createElement('option');
                    option.value = medicine.med_id;
                    option.textContent = `${medicine.med_name} (库存: ${medicine.stock_quantity})`;
                    select.appendChild(option);
                });
            });
    }
    
    // 添加药品
    document.getElementById('addMedicineBtn').addEventListener('click', function() {
        const medId = parseInt(document.getElementById('medicineSelect').value);
        const quantity = parseInt(document.getElementById('medicineQuantity').value);
        
        if (!medId || !quantity || quantity <= 0) {
            alert('请选择药品并输入有效数量');
            return;
        }
        
        const medicine = medicinesData.find(m => m.med_id === medId);
        if (!medicine) return;
        
        if (quantity > medicine.stock_quantity) {
            alert(`库存不足，当前库存: ${medicine.stock_quantity}`);
            return;
        }
        
        // 检查是否已添加
        const existingIndex = selectedMedicines.findIndex(item => item.med_id === medId);
        if (existingIndex >= 0) {
            selectedMedicines[existingIndex].quantity += quantity;
        } else {
            selectedMedicines.push({
                med_id: medId,
                med_name: medicine.med_name,
                unit_price: medicine.unit_price,
                quantity: quantity
            });
        }
        
        updateSelectedMedicinesDisplay();
    });
    
    // 更新已选药品显示
    function updateSelectedMedicinesDisplay() {
        const tbody = document.querySelector('#selectedMedicines tbody');
        tbody.innerHTML = '';
        
        let total = 0;
        
        selectedMedicines.forEach((item, index) => {
            const subtotal = item.unit_price * item.quantity;
            total += subtotal;
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.med_name}</td>
                <td>${item.unit_price.toFixed(2)}</td>
                <td>${item.quantity}</td>
                <td>${subtotal.toFixed(2)}</td>
                <td><span class="remove-medicine" data-index="${index}">删除</span></td>
            `;
            tbody.appendChild(row);
        });
        
        document.getElementById('totalPrice').textContent = total.toFixed(2);
    }
    
    // 删除药品
    document.querySelector('#selectedMedicines').addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-medicine')) {
            const index = parseInt(e.target.dataset.index);
            selectedMedicines.splice(index, 1);
            updateSelectedMedicinesDisplay();
        }
    });
    
    // 提交处方
    document.getElementById('submitPrescriptionBtn').addEventListener('click', function() {
        if (selectedMedicines.length === 0) {
            alert('请至少添加一种药品');
            return;
        }
        
        if (!confirm('确认提交处方？')) return;
        
        const totalPrice = selectedMedicines.reduce((sum, item) => {
            return sum + (item.unit_price * item.quantity);
        }, 0);
        
        fetch('/api/prescriptions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                registration_id: registrationId,
                medicines: selectedMedicines,
                total_price: totalPrice
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('处方提交成功！');
                selectedMedicines = [];
                updateSelectedMedicinesDisplay();
                loadPrescriptionHistory();
            } else {
                throw new Error(data.error || '提交失败');
            }
        })
        .catch(error => {
            console.error('提交处方失败:', error);
            alert('提交处方失败: ' + error.message);
        });
    });
    
    // 加载历史处方
    function loadPrescriptionHistory() {
        fetch(`/api/prescriptions?registration_id=${registrationId}`)
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('prescriptionList');
                container.innerHTML = '';
                
                if (data.length === 0) {
                    container.innerHTML = '<p>暂无历史处方记录</p>';
                    return;
                }
                
                data.forEach(prescription => {
                    const item = document.createElement('div');
                    item.className = 'prescription-item';
                    
                    let html = `<h4>处方日期: ${new Date(prescription.create_time).toLocaleString()}</h4>
                                <div class="prescription-details">
                                    <table>
                                        <thead>
                                            <tr>
                                                <th>药品名称</th>
                                                <th>单价</th>
                                                <th>数量</th>
                                                <th>小计</th>
                                            </tr>
                                        </thead>
                                        <tbody>`;
                    
                    let total = 0;
                    prescription.details.forEach(detail => {
                        const subtotal = detail.unit_price * detail.quantity;
                        total += subtotal;
                        html += `
                            <tr>
                                <td>${detail.med_name}</td>
                                <td>${detail.unit_price.toFixed(2)}</td>
                                <td>${detail.quantity}</td>
                                <td>${subtotal.toFixed(2)}</td>
                            </tr>
                        `;
                    });
                    
                    html += `</tbody></table>
                            <div class="prescription-total">
                                总费用: ${total.toFixed(2)}元
                            </div>
                        </div>`;
                    
                    item.innerHTML = html;
                    container.appendChild(item);
                });
            });
    }
    
    // 初始化
    loadPatientInfo();
    loadMedicines();
    loadPrescriptionHistory();
});