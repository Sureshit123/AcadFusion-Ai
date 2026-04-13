function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    if (tabName === 'range') {
        document.querySelectorAll('.tab')[0].classList.add('active');
        document.getElementById('range-tab').classList.add('active');
    } else {
        document.querySelectorAll('.tab')[1].classList.add('active');
        document.getElementById('bulk-tab').classList.add('active');
    }
}

let progressInterval;

async function startJob(formData, submitBtnId) {
    const submitBtn = document.getElementById(submitBtnId);
    submitBtn.disabled = true;
    submitBtn.innerHTML = 'Starting...';
    
    document.getElementById('progressArea').style.display = 'block';
    document.getElementById('downloadBtn').style.display = 'none';
    document.getElementById('progressBar').style.width = '0%';
    document.getElementById('currentStatus').innerText = 'Initializing scraper...';
    document.getElementById('currentStatus').style.color = 'var(--text-secondary)';

    try {
        const response = await fetch('/api/start_analysis', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to start job');
        }
        
        const data = await response.json();
        pollProgress(data.job_id, submitBtn, submitBtnId);
    } catch (error) {
        alert("Error: " + error.message);
        submitBtn.disabled = false;
        submitBtn.innerHTML = submitBtnId.includes('Range') ? 'Start Analysis' : 'Process File';
        document.getElementById('progressArea').style.display = 'none';
    }
}

document.getElementById('rangeForm').addEventListener('submit', function(e) {
    e.preventDefault();
    startJob(new FormData(this), 'startBtnRange');
});

document.getElementById('bulkForm').addEventListener('submit', function(e) {
    e.preventDefault();
    startJob(new FormData(this), 'startBtnBulk');
});

let isWaitingForCaptcha = false;
let currentJobId = null;
let lastAttemptFailed = false;

function pollProgress(jobId, btnRef, btnOriginalId) {
    currentJobId = jobId;
    const texts = {
        'startBtnRange': 'Start Analysis',
        'startBtnBulk': 'Process File'
    };

    progressInterval = setInterval(async () => {
        if (isWaitingForCaptcha) return; // Pause polling while modal is open

        try {
            const res = await fetch(`/api/progress/${jobId}`);
            if (!res.ok) throw new Error('Failed to fetch progress');
            
            const data = await res.json();
            
            const percent = data.total > 0 ? (data.completed / data.total) * 100 : 0;
            document.getElementById('progressBar').style.width = `${percent}%`;
            document.getElementById('progressText').innerText = `${data.completed} / ${data.total}`;
            
            if (data.status === 'Waiting for Captcha') {
                document.getElementById('currentStatus').innerText = "Action Required: Solve CAPTCHA";
                document.getElementById('currentStatus').style.color = 'var(--text-primary)';
                
                // Show Modal
                isWaitingForCaptcha = true;
                document.getElementById('captchaUsn').innerText = data.current_usn;
                document.getElementById('captchaImage').src = "data:image/png;base64," + data.captcha_base64;
                document.getElementById('captchaInput').value = '';
                document.getElementById('submitCaptchaBtn').disabled = false;
                
                // Show Error if retry
                const errorEl = document.getElementById('captchaError');
                if (lastAttemptFailed) {
                    errorEl.style.display = 'block';
                    errorEl.innerText = 'Invalid CAPTCHA code. Please try again.';
                    // Shake effect
                    const modal = document.querySelector('.modal-content');
                    modal.style.animation = 'none';
                    setTimeout(() => modal.style.animation = 'shake 0.4s ease-in-out', 10);
                } else {
                    errorEl.style.display = 'none';
                }
                
                document.getElementById('captchaModal').style.display = 'flex';
                document.getElementById('captchaInput').focus();
                return;
            }

            if (data.status && data.status.includes('Invalid Captcha')) {
                lastAttemptFailed = true;
            } else if (data.status && data.status.includes('Scraping')) {
                lastAttemptFailed = false; // Reset on progress
            }
            
            if (data.status === 'Completed') {
                clearInterval(progressInterval);
                document.getElementById('currentStatus').innerText = 'Analysis Complete!';
                document.getElementById('currentStatus').style.color = 'var(--success)';
                btnRef.disabled = false;
                btnRef.innerHTML = texts[btnOriginalId];
                
                const downloadBtn = document.getElementById('downloadBtn');
                downloadBtn.href = `/download/${jobId}`;
                downloadBtn.style.display = 'flex';
                
            } else if (data.status && data.status.includes('Error')) {
                clearInterval(progressInterval);
                document.getElementById('currentStatus').innerText = data.status;
                document.getElementById('currentStatus').style.color = 'var(--error)';
                btnRef.disabled = false;
                btnRef.innerHTML = texts[btnOriginalId];
            } else {
                document.getElementById('currentStatus').innerText = 
                    data.status === 'Running' ? `Scraping: ${data.current_usn}` : data.status;
            }
            
        } catch (error) {
            console.error(error);
            clearInterval(progressInterval);
            document.getElementById('currentStatus').innerText = "Connection lost during polling.";
            document.getElementById('currentStatus').style.color = 'var(--error)';
            btnRef.disabled = false;
            btnRef.innerHTML = texts[btnOriginalId];
        }
    }, 1000);
}

async function submitCaptcha() {
    const val = document.getElementById('captchaInput').value.trim();
    if (!val) return;
    
    document.getElementById('submitCaptchaBtn').disabled = true;
    try {
        const res = await fetch(`/api/submit_captcha/${currentJobId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({captcha: val})
        });
        
        if (res.ok) {
            document.getElementById('captchaModal').style.display = 'none';
            isWaitingForCaptcha = false;
        } else {
            alert('Failed to submit captcha. Please try again.');
            document.getElementById('submitCaptchaBtn').disabled = false;
        }
    } catch(e) {
        alert('Data Error');
        document.getElementById('submitCaptchaBtn').disabled = false;
    }
}

// Allow Enter key
document.getElementById('captchaInput').addEventListener('keypress', function(e) {
    if(e.key === 'Enter') submitCaptcha();
});
