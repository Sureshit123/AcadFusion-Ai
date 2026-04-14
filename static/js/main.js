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
                btnRef.disabled = false;
                btnRef.innerHTML = texts[btnOriginalId];
                
                const downloadBtn = document.getElementById('downloadBtn');
                const viewBtn = document.getElementById('viewResultsBtn');
                downloadBtn.href = `/download/${jobId}`;
                downloadBtn.style.display = 'flex';
                viewBtn.style.display = 'flex';
                viewBtn.setAttribute('onclick', `openResultsPreview('${jobId}')`);
                
                document.getElementById('currentStatus').innerHTML = '<span style="color: #10b981">Analysis Complete!</span>';
                
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

async function openResultsPreview(job_id) {
    const modal = document.getElementById('resultsModal');
    const body = document.getElementById('previewBody');
    body.innerHTML = '<tr><td colspan="5" style="text-align:center">Loading data...</td></tr>';
    modal.style.display = 'flex';
    
    try {
        const res = await fetch(`/api/job_results/${job_id}`);
        const results = await res.json();
        
        if (!results || results.length === 0) {
            body.innerHTML = '<tr><td colspan="5" style="text-align:center">No data found.</td></tr>';
            return;
        }
        
        body.innerHTML = results.map(r => {
            // Fallback calculation for older records missing percentage field
            let pct = r.percentage;
            if ((!pct || pct == 0) && r.total_marks > 0) {
                // Heuristic: VTU subjects are usually 100 marks. 
                // We'll calculate based on common semester total targets (e.g., 600, 700, 800)
                // or just display total/target if we knew target. 
                // For now, we'll try to keep it as provided or 0.
                pct = r.percentage || 0;
            }

            return `
                <tr>
                    <td style="font-weight:700; color:var(--accent-primary)">${r.usn}</td>
                    <td>${r.name || 'N/A'}</td>
                    <td style="text-align:center">${r.total_marks || 0}</td>
                    <td style="text-align:center">${pct}%</td>
                    <td><span class="badge ${(r.status || 'Fail').toLowerCase() === 'pass' ? 'pass' : 'fail'}">${r.status || 'Fail'}</span></td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        body.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#ef4444">Error: ${e.message}</td></tr>`;
    }
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
async function toggleMockMode(cb) {
    const isLive = cb.checked;
    const labelDemo = document.getElementById('label-demo');
    const labelLive = document.getElementById('label-live');
    
    // Immediate UI feedback
    if (isLive) {
        labelLive.classList.add('active');
        labelDemo.classList.remove('active');
    } else {
        labelDemo.classList.add('active');
        labelLive.classList.remove('active');
    }
    
    try {
        const res = await fetch('/api/toggle_mock', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ use_mock: !isLive })
        });
        
        if (!res.ok) throw new Error("Failed to switch mode");
        
        // Success Toast or console log
        console.log(`Mode switched to: ${isLive ? 'Live VTU' : 'Simulation'}`);
        
    } catch (e) {
        alert("Error switching mode: " + e.message);
        cb.checked = !isLive; // Revert
        // Revert UI labels
        labelLive.classList.toggle('active');
        labelDemo.classList.toggle('active');
    }
}

// Initial state cleanup
window.addEventListener('DOMContentLoaded', () => {
    const cb = document.getElementById('modeToggle');
    if (cb) {
        const labelDemo = document.getElementById('label-demo');
        const labelLive = document.getElementById('label-live');
        // If checked, it means LIVE
        if (cb.checked) {
            labelLive.classList.add('active');
            labelDemo.classList.remove('active');
        } else {
            labelDemo.classList.add('active');
            labelLive.classList.remove('active');
        }
    }
    
    // Auto-refresh history every minute
    setInterval(loadHistory, 60000);
});
