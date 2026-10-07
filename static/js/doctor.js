document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('doctorLoginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // 简单的客户端验证
            const name = this.name.value.trim();
            const password = this.password.value.trim();
            
            if (!name || !password) {
                e.preventDefault();
                alert('请输入医生姓名和密码');
                return false;
            }
            
            // 可以在这里添加更多验证逻辑
            return true;
        });
    }
});