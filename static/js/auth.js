// 登录表单提交
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const response = await fetch('/login', {
        method: 'POST',
        body: formData
    });
    
    if (response.redirected) {
        window.location.href = response.url;
    } else {
        const error = await response.text();
        document.getElementById('errorMsg').textContent = error;
    }
});

// 注册表单提交
document.getElementById('registerForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // 客户端验证
    const age = parseInt(e.target.age.value);
    if (age < 0 || age > 120) {
        showError("请输入有效的年龄(0-120)");
        return;
    }
    
    if (!/^\d{11}$/.test(e.target.phone.value)) {
        showError("手机号必须是11位数字");
        return;
    }
    
    // 提交数据
    const response = await fetch('/register', {
        method: 'POST',
        body: new FormData(e.target)
    });
    
    handleAuthResponse(response);
});

function showError(message) {
    document.getElementById('errorMsg').textContent = message;
}

async function handleAuthResponse(response) {
    if (response.redirected) {
        window.location.href = response.url;
    } else {
        const error = await response.text();
        showError(error);
    }
}