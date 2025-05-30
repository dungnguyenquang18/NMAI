document.addEventListener('DOMContentLoaded', function() {
    const numProfilesInput = document.getElementById('num-profiles');
    const generateBtn = document.getElementById('generate-profiles');
    const profileForm = document.getElementById('profile-form');
    const profilesContainer = document.getElementById('profiles-container');

    generateBtn.addEventListener('click', function() {
        const numProfiles = parseInt(numProfilesInput.value);
        if (numProfiles > 0) {
            generateProfileForms(numProfiles);
        } else {
            alert('Vui lòng nhập số hồ sơ lớn hơn 0');
        }
    });
});

function generateProfileForms(count) {
    const container = document.getElementById('profiles-container');
    container.innerHTML = ''; // Clear existing profiles

    for (let i = 0; i < count; i++) {
        const profileDiv = document.createElement('div');
        profileDiv.className = 'profile-section';
        profileDiv.id = `profile-${i + 1}`;

        profileDiv.innerHTML = `
            <h3>Hồ sơ #${i + 1}</h3>
            <div class="form-group">
                <label>Chức Danh Chuyên Môn</label>
                <input type="text" name="title_${i}" class="form-input" required>
            </div>
            <div class="form-group">
                <label>Kinh Nghiệm, Kỹ Năng</label>
                <textarea name="experience_${i}" class="form-input"></textarea>
            </div>
            <div class="form-group">
                <label>Điểm Mạnh</label>
                <textarea name="strengths_${i}" class="form-input"></textarea>
            </div>
            <div class="form-group">
                <label>Thành Tựu</label>
                <textarea name="achievements_${i}" class="form-input"></textarea>
            </div>
        `;

        container.appendChild(profileDiv);
    }

    // Add submit button if not exists
    if (!document.getElementById('submit-profiles')) {
        const submitBtn = document.createElement('button');
        submitBtn.id = 'submit-profiles';
        submitBtn.className = 'form-submit';
        submitBtn.textContent = 'Lưu Tất Cả Hồ Sơ';
        container.appendChild(submitBtn);

        submitBtn.addEventListener('click', submitProfiles);
    }
}

function submitProfiles(e) {
    e.preventDefault();
    const profiles = [];
    const profileSections = document.querySelectorAll('.profile-section');

    // Validate that we have sections to submit
    if (profileSections.length === 0) {
        alert('Vui lòng tạo ít nhất một hồ sơ trước khi lưu');
        return;
    }

    // Collect and validate all profile data
    let hasErrors = false;
    profileSections.forEach((section, index) => {
        const titleInput = section.querySelector(`[name="title_${index}"]`);
        if (!titleInput.value.trim()) {
            titleInput.classList.add('error');
            hasErrors = true;
        } else {
            titleInput.classList.remove('error');
        }

        const profile = {
            title: titleInput.value,
            experience: section.querySelector(`[name="experience_${index}"]`).value.trim(),
            strengths: section.querySelector(`[name="strengths_${index}"]`).value.trim(),
            achievements: section.querySelector(`[name="achievements_${index}"]`).value.trim()
        };
        profiles.push(profile);
    });

    if (hasErrors) {
        alert('Vui lòng điền đầy đủ thông tin chức danh cho tất cả hồ sơ');
        return;
    }

    const formData = new FormData();
    formData.append('profiles', JSON.stringify(profiles));

    // Get CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]');
    if (!csrfToken) {
        console.error('CSRF token not found');
        alert('Lỗi bảo mật: Không tìm thấy token CSRF');
        return;
    }

    fetch('/profile', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken.value,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Thông tin hồ sơ đã được lưu thành công!');
            window.location.reload();
        } else {
            alert(data.message || 'Có lỗi xảy ra khi lưu thông tin!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Có lỗi xảy ra khi lưu thông tin. Vui lòng thử lại sau!');
    });
}
