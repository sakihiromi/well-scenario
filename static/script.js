// Well-Scenario Frontend Script

// DOM Elements
const meetingPurpose = document.getElementById('meeting-purpose');
const meetingFormat = document.getElementById('meeting-format');
const profileSelect = document.getElementById('profile-select');
const numUtterances = document.getElementById('num-utterances');
const generateBtn = document.getElementById('generate-btn');
const profileSection = document.getElementById('profile-section');
const profileDisplay = document.getElementById('profile-display');
const loading = document.getElementById('loading');
const scenarioSection = document.getElementById('scenario-section');
const scenarioDisplay = document.getElementById('scenario-display');
const scenarioMetadata = document.getElementById('scenario-metadata');

// State
let currentProfile = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProfiles();
    setupEventListeners();
});

function setupEventListeners() {
    generateBtn.addEventListener('click', handleGenerate);
    profileSelect.addEventListener('change', handleProfileChange);
}

// Load available profiles
async function loadProfiles() {
    try {
        const response = await fetch('/api/profiles');
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        profileSelect.innerHTML = '<option value="">選択してください</option>';
        data.profiles.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile.name;
            option.textContent = profile.name;
            profileSelect.appendChild(option);
        });
    } catch (error) {
        showError('プロフィールの読み込みに失敗しました: ' + error.message);
    }
}

// Handle profile selection change
async function handleProfileChange() {
    const filename = profileSelect.value;
    if (!filename) {
        profileSection.style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/api/profile/${encodeURIComponent(filename)}`);
        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        currentProfile = data.profile;
        displayProfile(currentProfile);
    } catch (error) {
        showError('プロフィールの読み込みに失敗しました: ' + error.message);
    }
}

// Display profile
function displayProfile(profile) {
    profileDisplay.innerHTML = '';

    profile.forEach(participant => {
        const card = document.createElement('div');
        card.className = 'profile-card';

        let profileHtml = `
            <h3>${participant.id}</h3>
            <div class="profile-info">
        `;

        if (participant.profile) {
            const prof = participant.profile;
            profileHtml += `
                <div class="profile-info-item">
                    <span class="profile-info-label">役職</span>
                    <span class="profile-info-value">${prof.role || '不明'}</span>
                </div>
                <div class="profile-info-item">
                    <span class="profile-info-label">方針</span>
                    <span class="profile-info-value">${prof.stance || '不明'}</span>
                </div>
                <div class="profile-info-item">
                    <span class="profile-info-label">やる気</span>
                    <span class="profile-info-value">${(prof.motivation * 10).toFixed(1)}/10</span>
                </div>
                <div class="profile-info-item">
                    <span class="profile-info-label">話好き度</span>
                    <span class="profile-info-value">${(prof.talkativeness * 10).toFixed(1)}/10</span>
                </div>
            `;
        }

        profileHtml += '</div>';

        if (participant.instructions) {
            profileHtml += `
                <div class="profile-instructions">
                    ${participant.instructions}
                </div>
            `;
        }

        card.innerHTML = profileHtml;
        profileDisplay.appendChild(card);
    });

    profileSection.style.display = 'block';
    profileSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Handle scenario generation
async function handleGenerate() {
    const purpose = meetingPurpose.value.trim();
    const format = meetingFormat.value;
    const filename = profileSelect.value;
    const numUtts = parseInt(numUtterances.value);

    // Validation
    if (!purpose) {
        showError('会議の目的を入力してください');
        return;
    }

    if (!format) {
        showError('会議の形式を選択してください');
        return;
    }

    if (!filename) {
        showError('参加者プロフィールを選択してください');
        return;
    }

    // Show loading
    loading.style.display = 'block';
    scenarioSection.style.display = 'none';
    generateBtn.disabled = true;

    try {
        const response = await fetch('/api/generate-scenario', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                meeting_purpose: purpose,
                meeting_format: format,
                profile_filename: filename,
                num_utterances: numUtts
            })
        });

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        displayScenario(data.scenario, data.metadata);
    } catch (error) {
        showError('シナリオの生成に失敗しました: ' + error.message);
    } finally {
        loading.style.display = 'none';
        generateBtn.disabled = false;
    }
}

// Display scenario with annotations
function displayScenario(scenario, metadata) {
    // Display metadata
    scenarioMetadata.innerHTML = `
        <strong>会議の目的:</strong> ${metadata.meeting_purpose} &nbsp;|&nbsp;
        <strong>形式:</strong> ${metadata.meeting_format} &nbsp;|&nbsp;
        <strong>発言数:</strong> ${metadata.num_utterances}
    `;

    // Clear previous scenario
    scenarioDisplay.innerHTML = '';

    // Display each utterance
    scenario.forEach((utterance, index) => {
        const uttDiv = document.createElement('div');
        uttDiv.className = 'utterance';

        let metricsHtml = '';
        if (utterance.metrics) {
            metricsHtml = '<div class="metrics">';

            for (const [metricName, metricData] of Object.entries(utterance.metrics)) {
                const score = metricData.score;
                const reason = metricData.reason || '';
                const scoreClass = getScoreClass(score);

                metricsHtml += `
                    <div class="metric">
                        <div class="metric-name">${metricName}</div>
                        <div class="metric-score">
                            <span class="score-badge ${scoreClass}">${score}</span>
                        </div>
                        <div class="metric-reason">${reason}</div>
                    </div>
                `;
            }

            metricsHtml += '</div>';
        }

        uttDiv.innerHTML = `
            <div class="utterance-header">
                <span class="speaker">${utterance.speaker}</span>
                <span class="utterance-number">#${index + 1}</span>
            </div>
            <div class="utterance-text">${utterance.text}</div>
            ${metricsHtml}
        `;

        scenarioDisplay.appendChild(uttDiv);
    });

    // Show scenario section
    scenarioSection.style.display = 'block';
    scenarioSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Initialize charts with the scenario data
    if (typeof chartEditor !== 'undefined') {
        // ファイル名を取得（保存された場合）
        const filename = metadata.saved_to ? metadata.saved_to.split('/').pop() : null;
        chartEditor.initializeCharts(scenario, filename);
    }
}

// Get score class based on value
function getScoreClass(score) {
    if (score <= 3) return 'score-low';
    if (score <= 6) return 'score-medium';
    return 'score-high';
}

// Show error message
function showError(message) {
    alert('エラー: ' + message);
    console.error(message);
}
