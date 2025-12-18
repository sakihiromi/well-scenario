/**
 * chart_editor.js
 * Well-Scenario グラフエディター
 * Chart.jsを使用してメトリクススコアのグラフ表示と編集機能を提供
 */

class ChartEditor {
    constructor() {
        this.charts = {};
        this.currentScenario = null;
        this.currentFilename = null;
        this.humanAnnotations = {}; // { utteranceIdx: { metricName: { score, note } } }
        this.hasUnsavedChanges = false;

        // メトリクス定義
        this.metrics = ['威圧度', '逸脱度', '発言無効度', '偏り度'];
        this.metricIds = {
            '威圧度': 'intimidation',
            '逸脱度': 'deviation',
            '発言無効度': 'ineffectiveness',
            '偏り度': 'bias'
        };

        this.setupEventListeners();
    }

    setupEventListeners() {
        const saveBtn = document.getElementById('save-annotations-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveAnnotations());
        }
    }

    /**
     * シナリオデータからグラフを初期化
     */
    initializeCharts(scenario, filename = null) {
        this.currentScenario = scenario;
        this.currentFilename = filename;
        this.humanAnnotations = {};
        this.hasUnsavedChanges = false;

        // グラフセクションを表示
        const graphSection = document.getElementById('graph-section');
        if (graphSection) {
            graphSection.style.display = 'block';
        }

        // 各メトリクスのグラフを作成
        this.metrics.forEach(metricName => {
            this.createChart(metricName);
        });

        this.updateSaveButton();
    }

    /**
     * 特定のメトリクスのグラフを作成
     */
    createChart(metricName) {
        const metricId = this.metricIds[metricName];
        const canvasId = `chart-${metricId}`;
        const canvas = document.getElementById(canvasId);

        if (!canvas) {
            console.error(`Canvas not found: ${canvasId}`);
            return;
        }

        // 既存のチャートを破棄
        if (this.charts[metricName]) {
            this.charts[metricName].destroy();
        }

        const ctx = canvas.getContext('2d');

        // データを準備
        const { labels, machineScores, humanScores } = this.prepareChartData(metricName);

        // Chart.js設定
        const config = {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    // 人手アノテーションを先に定義して前面に表示
                    {
                        label: '人手アノテーション',
                        data: humanScores,
                        borderColor: 'rgb(239, 68, 68)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 3,
                        borderDash: [5, 5],
                        pointRadius: 8,
                        pointHoverRadius: 10,
                        pointStyle: 'circle',
                        pointBorderWidth: 2,
                        pointBackgroundColor: 'rgb(239, 68, 68)',
                        pointBorderColor: '#ffffff',
                        tension: 0.1,
                        order: 1  // 前面に表示
                    },
                    {
                        label: '機械アノテーション',
                        data: machineScores,
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        tension: 0.1,
                        order: 2  // 背面に表示
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    y: {
                        min: 0,
                        max: 9,
                        ticks: {
                            stepSize: 1
                        },
                        title: {
                            display: true,
                            text: 'スコア'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '発言番号'
                        }
                    }
                },
                plugins: {
                    dragData: {
                        round: 0,
                        showTooltip: true,
                        onDragStart: (e, datasetIndex, index, value) => {
                            // 人手アノテーション（dataset 0）のみドラッグ可能
                            return datasetIndex === 0;
                        },
                        onDrag: (e, datasetIndex, index, value) => {
                            // 0-9の範囲に制限
                            return Math.max(0, Math.min(9, Math.round(value)));
                        },
                        onDragEnd: (e, datasetIndex, index, value) => {
                            if (datasetIndex === 0) {
                                const finalValue = Math.max(0, Math.min(9, Math.round(value)));
                                this.updateHumanAnnotation(index, metricName, finalValue);
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            title: (context) => {
                                // タイトルに発言番号を表示
                                if (context.length > 0) {
                                    return `発言 ${context[0].label}`;
                                }
                                return '';
                            },
                            label: (context) => {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y;
                                return `${label}: ${value}`;
                            },
                            afterLabel: (context) => {
                                // 発言内容を追加表示
                                const utteranceIdx = context.dataIndex;
                                if (this.currentScenario && this.currentScenario[utteranceIdx]) {
                                    const utterance = this.currentScenario[utteranceIdx];
                                    const text = utterance.text || '';
                                    // 長い場合は省略
                                    if (text.length > 100) {
                                        return `「${text.substring(0, 100)}...」`;
                                    }
                                    return `「${text}」`;
                                }
                                return '';
                            }
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        };

        // チャートを作成
        this.charts[metricName] = new Chart(ctx, config);
    }

    /**
     * グラフ用のデータを準備
     */
    prepareChartData(metricName) {
        const labels = [];
        const machineScores = [];
        const humanScores = [];

        this.currentScenario.forEach((utterance, idx) => {
            labels.push(`#${idx + 1}`);

            // 機械アノテーション（既存のmetricsまたはmachine_annotations）
            const machineAnnotations = utterance.machine_annotations || utterance.metrics || {};
            const machineScore = machineAnnotations[metricName]?.score ?? null;
            machineScores.push(machineScore);

            // 人手アノテーション（存在する場合）
            const humanAnnotations = utterance.human_annotations || {};
            const humanScore = humanAnnotations[metricName]?.score ?? machineScore;
            humanScores.push(humanScore);

            // 既存の人手アノテーションをメモリにロード
            if (humanAnnotations[metricName]) {
                if (!this.humanAnnotations[idx]) {
                    this.humanAnnotations[idx] = {};
                }
                this.humanAnnotations[idx][metricName] = {
                    score: humanAnnotations[metricName].score,
                    note: humanAnnotations[metricName].note || ''
                };
            }
        });

        return { labels, machineScores, humanScores };
    }

    /**
     * 人手アノテーションを更新
     */
    updateHumanAnnotation(utteranceIdx, metricName, score) {
        if (!this.humanAnnotations[utteranceIdx]) {
            this.humanAnnotations[utteranceIdx] = {};
        }

        this.humanAnnotations[utteranceIdx][metricName] = {
            score: score,
            note: ''
        };

        this.hasUnsavedChanges = true;
        this.updateSaveButton();

        console.log(`Updated: Utterance #${utteranceIdx + 1}, ${metricName} = ${score}`);
    }

    /**
     * 保存ボタンの状態を更新
     */
    updateSaveButton() {
        const saveBtn = document.getElementById('save-annotations-btn');
        if (saveBtn) {
            saveBtn.disabled = !this.hasUnsavedChanges;
            if (this.hasUnsavedChanges) {
                saveBtn.textContent = '💾 人手アノテーションを保存 *';
            } else {
                saveBtn.textContent = '💾 人手アノテーションを保存';
            }
        }
    }

    /**
     * アノテーションを保存
     */
    async saveAnnotations() {
        if (!this.currentFilename) {
            alert('エラー: ファイル名が不明です');
            return;
        }

        if (Object.keys(this.humanAnnotations).length === 0) {
            alert('変更がありません');
            return;
        }

        try {
            const response = await fetch(`/api/output/${encodeURIComponent(this.currentFilename)}/annotations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    annotations: this.humanAnnotations
                })
            });

            const data = await response.json();

            if (data.error) {
                alert('エラー: ' + data.error);
                return;
            }

            alert('✅ 人手アノテーションを保存しました');
            this.hasUnsavedChanges = false;
            this.updateSaveButton();

        } catch (error) {
            alert('保存に失敗しました: ' + error.message);
            console.error(error);
        }
    }

    /**
     * すべてのチャートを破棄
     */
    destroyAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};

        const graphSection = document.getElementById('graph-section');
        if (graphSection) {
            graphSection.style.display = 'none';
        }
    }
}

// グローバルインスタンスを作成
const chartEditor = new ChartEditor();
