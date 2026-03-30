document.addEventListener('DOMContentLoaded', () => {
    const produceForm = document.getElementById('produceForm');
    const submitBtn = document.getElementById('submitBtn');
    const statusPanel = document.getElementById('statusPanel');
    const progressBar = document.getElementById('progressBar');
    const statusMsg = document.getElementById('statusMsg');
    const statusTitle = document.getElementById('statusTitle');
    const resultInfo = document.getElementById('resultInfo');
    const outputPath = document.getElementById('outputPath');
    const fileList = document.getElementById('fileList');

    const editorSection = document.getElementById('editorSection');
    const subtitleList = document.getElementById('subtitleList');
    const previewVideo = document.getElementById('previewVideo');
    const goEditorBtn = document.getElementById('goEditorBtn');
    const saveSubtitlesBtn = document.getElementById('saveSubtitlesBtn');

    let currentJobData = null; // Store current production info

    // Range display updates
    const vSpeed = document.getElementById('video_speed');
    const tSpeed = document.getElementById('title_speed');
    const bSpeed = document.getElementById('body_speed');
    const eSpeed = document.getElementById('ending_speed');
    const vVal = document.getElementById('vSpeedVal');
    const tVal = document.getElementById('tSpeedVal');
    const bVal = document.getElementById('bSpeedVal');
    const eVal = document.getElementById('eSpeedVal');

    vSpeed.addEventListener('input', () => vVal.textContent = `${vSpeed.value}x`);
    tSpeed.addEventListener('input', () => tVal.textContent = `${tSpeed.value}x`);
    bSpeed.addEventListener('input', () => bVal.textContent = `${bSpeed.value}x`);
    eSpeed.addEventListener('input', () => eVal.textContent = `${eSpeed.value}x`);

    // Photo selection message
    const photosInput = document.getElementById('photos');
    const photoMsg = photosInput.parentElement.querySelector('.file-msg');
    
    photosInput.addEventListener('change', () => {
        const count = photosInput.files.length;
        photoMsg.textContent = count > 0 ? `${count}개의 사진이 선택되었습니다.` : '사진을 여기로 드래그하거나 클릭하여 선택하세요.';
    });

    // Form submission
    produceForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 1. Show Status Panel
        statusPanel.classList.remove('hidden');
        resultInfo.classList.add('hidden');
        statusTitle.textContent = "영상 제작 중...";
        statusMsg.textContent = "고인에 대한 소중한 기억을 영상으로 엮고 있습니다. 잠시만 기다려 주세요.";
        progressBar.style.width = "0%";
        submitBtn.disabled = true;
        submitBtn.style.opacity = "0.5";

        // Scroll to status
        statusPanel.scrollIntoView({ behavior: 'smooth' });

        // Pseudo progress animation
        let progress = 0;
        const interval = setInterval(() => {
            if (progress < 90) {
                progress += Math.random() * 5;
                progressBar.style.width = `${Math.min(progress, 90)}%`;
            }
        }, 1000);

        // 2. Prepare Data
        const formData = new FormData(produceForm);

        try {
            // 3. Send Request
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            clearInterval(interval);

            if (data.status === 'success') {
                // 4. Update UI Success
                progressBar.style.width = "100%";
                statusTitle.textContent = "제작 완료";
                statusMsg.textContent = data.message;
                
                currentJobData = data; // Store for editor

                resultInfo.classList.remove('hidden');
                outputPath.innerHTML = `<i class="fas fa-folder-open"></i> 저장 경로: <code>${data.output_dir}</code>`;
                
                fileList.innerHTML = '<h4>생성된 파일 목록:</h4>';
                const ul = document.createElement('ul');
                data.files.forEach(file => {
                    const li = document.createElement('li');
                    li.innerHTML = `<i class="far fa-file"></i> ${file}`;
                    ul.appendChild(li);
                });
                fileList.appendChild(ul);

            } else {
                throw new Error(data.message);
            }

        } catch (error) {
            clearInterval(interval);
            statusTitle.textContent = "오류 발생";
            statusMsg.textContent = `제작 중 오류가 발생했습니다: ${error.message}`;
            progressBar.style.backgroundColor = "#ff4444";
        } finally {
            submitBtn.disabled = false;
            submitBtn.style.opacity = "1";
        }
    });

    // --- Subtitle Editor Logic ---

    goEditorBtn.addEventListener('click', () => {
        setupEditor();
        editorSection.classList.remove('hidden');
        editorSection.scrollIntoView({ behavior: 'smooth' });
    });

    async function setupEditor() {
        if (!currentJobData) return;

        const srtFile = currentJobData.files.find(f => f.endsWith('.srt'));
        if (!srtFile) return;

        const videoFile = currentJobData.files.find(f => f.endsWith('.mp4'));
        
        // Show video
        const folderName = currentJobData.output_dir.split('\\').pop() || currentJobData.output_dir.split('/').pop();
        previewVideo.src = `/outputs/${folderName}/${videoFile}`;
        
        // Load SRT
        const response = await fetch(`/outputs/${folderName}/${srtFile}`);
        const srtText = await response.text();
        
        renderSubtitles(srtText);
    }

    function renderSubtitles(srtText) {
        subtitleList.innerHTML = '';
        const blocks = srtText.trim().split('\n\n');

        blocks.forEach((block, idx) => {
            const lines = block.split('\n');
            if (lines.length < 3) return;

            const timeRange = lines[1];
            const [start, end] = timeRange.split(' --> ');
            const text = lines.slice(2).join('\n');

            const item = document.createElement('div');
            item.className = 'sub-item';
            item.innerHTML = `
                <div class="sub-time-row">
                    <input type="text" class="sub-time-input start-time" value="${start}">
                    <span>→</span>
                    <input type="text" class="sub-time-input end-time" value="${end}">
                </div>
                <textarea class="sub-text-area" rows="2">${text}</textarea>
            `;

            // Click to seek video
            item.addEventListener('click', (e) => {
                if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                    const seconds = srtTimeToSeconds(start);
                    previewVideo.currentTime = seconds;
                    previewVideo.play();
                }
            });

            subtitleList.appendChild(item);
        });
    }

    function srtTimeToSeconds(timeStr) {
        const [hms, ms] = timeStr.split(',');
        const [h, m, s] = hms.split(':').map(parseFloat);
        return h * 3600 + m * 60 + s + (parseFloat(ms) / 1000);
    }

    // --- Quick Mode Functions ---
    window.applyPreset = (style) => {
        const presets = {
            solemn: { v: 0.8, t: 0.8, b: 0.9, e: 0.7 },
            standard: { v: 1.0, t: 1.0, b: 1.0, e: 1.0 },
            fast: { v: 1.2, t: 1.2, b: 1.4, e: 1.1 }
        };
        const p = presets[style];
        if (!p) return;

        vSpeed.value = p.v;
        tSpeed.value = p.t;
        bSpeed.value = p.b;
        eSpeed.value = p.e;

        // Force update labels
        vSpeed.dispatchEvent(new Event('input'));
        tSpeed.dispatchEvent(new Event('input'));
        bSpeed.dispatchEvent(new Event('input'));
        eSpeed.dispatchEvent(new Event('input'));
    };

    window.insertText = (id, text) => {
        const el = document.getElementById(id);
        if (!el) return;
        const current = el.value.trim();
        el.value = current ? `${current}\n${text}` : text;
        el.focus();
    };

    saveSubtitlesBtn.addEventListener('click', async () => {
        if (!currentJobData) return;

        const items = document.querySelectorAll('.sub-item');
        let newSrt = '';

        items.forEach((item, idx) => {
            const start = item.querySelector('.start-time').value;
            const end = item.querySelector('.end-time').value;
            const text = item.querySelector('.sub-text-area').value;

            newSrt += `${idx + 1}\n${start} --> ${end}\n${text}\n\n`;
        });

        const srtFile = currentJobData.files.find(f => f.endsWith('.srt'));
        const fullSrtPath = `${currentJobData.output_dir}\\${srtFile}`;

        saveSubtitlesBtn.disabled = true;
        saveSubtitlesBtn.querySelector('.btn-text').textContent = "저장 중...";

        try {
            const response = await fetch('/update_subtitles', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    srt_path: fullSrtPath,
                    srt_content: newSrt
                })
            });

            const result = await response.json();
            if (result.status === 'success') {
                alert(result.message);
            } else {
                alert("저장 실패: " + result.message);
            }
        } catch (err) {
            alert("통신 오류: " + err.message);
        } finally {
            saveSubtitlesBtn.disabled = false;
            saveSubtitlesBtn.querySelector('.btn-text').textContent = "자막 업데이트";
        }
    });
});
