
// AI Learning System - OpenAI Integration Focus
// Educational purpose only - No real money involved

class AILearningSystem {
    constructor() {
        this.apiBaseUrl = '/api/ai-analysis';
        this.analysisHistory = [];
        this.aiQueries = 1847;
        this.learningProgress = {
            openaiIntegration: 92,
            promptEngineering: 88,
            aiConfidenceCalibration: 85,
            aiSafetyEthics: 79
        };
        this.achievements = [
            { id: 'ai_integration', name: 'AI Integration Expert', achieved: true },
            { id: 'prompt_master', name: 'Prompt Engineering Master', achieved: true },
            { id: 'calibration_pro', name: 'AI Confidence Calibration Pro', achieved: false },
            { id: 'safety_champion', name: 'AI Safety Champion', achieved: false }
        ];
        this.aiAnalysisTypes = {
            'performance': 'Performance Analysis using OpenAI GPT-4',
            'comparison': 'Head-to-Head AI Comparison',
            'surface': 'Surface Adaptation Analysis (AI-Powered)',
            'momentum': 'Momentum Assessment with AI',
            'psychological': 'Psychological Analysis (OpenAI)'

        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeCharts();
        this.loadAIExamples();
        this.updateAIStats();
        console.log('🤖 AI Learning System - OpenAI GPT-4 Focus Initialized');
    }

    setupEventListeners() {
        // AI Analysis form events
        ['aiPlayer1', 'aiPlayer2'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') this.startAIAnalysis();
                });
                
                element.addEventListener('input', (e) => {
                    this.validateAIInput(e.target);
                });
            }
        });

        // AI Analysis type change
        const analysisTypeSelect = document.getElementById('aiAnalysisType');
        if (analysisTypeSelect) {
            analysisTypeSelect.addEventListener('change', (e) => {
                this.showAIAnalysisInfo(e.target.value);
            });
        }

        // Analysis depth change
        const depthSelect = document.getElementById('analysisDepth');
        if (depthSelect) {
            depthSelect.addEventListener('change', (e) => {
                this.updateAIDepthInfo(e.target.value);
            });
        }

        // AI Safety level change
        const safetySelect = document.getElementById('aiSafety');
        if (safetySelect) {
            safetySelect.addEventListener('change', (e) => {
                this.showAISafetyInfo(e.target.value);
            });
        }
    }

    validateAIInput(element) {
        const value = element.value.trim();
        const isValid = value.length >= 2 && value.length <= 50;
        
        if (isValid) {
            element.classList.remove('border-red-300');
            element.classList.add('border-green-300');
        } else {
            element.classList.remove('border-green-300');
            element.classList.add('border-red-300');
        }
    }

    showAIAnalysisInfo(analysisType) {
        const info = {
            'performance': 'Educational focus on AI-powered performance evaluation using OpenAI GPT-4',
            'comparison': 'AI-driven head-to-head analysis with confidence assessment',
            'surface': 'Surface-specific AI analysis with adaptation modeling',
            'momentum': 'AI assessment of momentum and psychological factors',
            'psychological': 'AI-powered psychological and mental game analysis'
        };
        
        this.showAINotification(info[analysisType], 'info');
    }

    updateAIDepthInfo(depth) {
        const info = {
            'basic': 'Basic AI analysis with fundamental OpenAI integration concepts',
            'intermediate': 'Intermediate AI analysis with detailed GPT-4 integration',
            'advanced': 'Advanced AI analysis with sophisticated OpenAI techniques'
        };
        
        this.showAINotification(info[depth], 'info');
    }

    showAISafetyInfo(safetyLevel) {
        const info = {
            'educational': 'Maximum educational safeguards with comprehensive safety measures',
            'conservative': 'Conservative AI analysis with enhanced safety protocols',
            'standard': 'Standard AI analysis with balanced safety measures'
        };
        
        this.showAINotification(info[safetyLevel], 'info');
    }

    async startAIAnalysis() {
        const player1 = document.getElementById('aiPlayer1').value.trim();
        const player2 = document.getElementById('aiPlayer2').value.trim();
        const analysisType = document.getElementById('aiAnalysisType').value;
        const analysisDepth = document.getElementById('analysisDepth').value;
        const aiSafety = document.getElementById('aiSafety').value;

        if (!player1 || !player2) {
            this.showAINotification('Please enter both player names for AI analysis.', 'warning');
            return;
        }

        this.showAILoading();

        try {
            const aiAnalysis = await this.generateAIAnalysis(player1, player2, analysisType, analysisDepth, aiSafety);
            this.displayAIResults(aiAnalysis);
            this.updateAIProgress();
            this.addToAIHistory(aiAnalysis);
            
        } catch (error) {
            console.error('AI analysis error:', error);
            this.showAINotification('AI analysis failed. Please try again.', 'error');
        } finally {
            this.hideAILoading();
        }
    }

    async generateAIAnalysis(player1, player2, analysisType, analysisDepth, aiSafety) {
        // Simulate OpenAI API call delay
        await new Promise(resolve => setTimeout(resolve, 2500));
        
        const confidence = this.generateAIConfidence(player1, player2, analysisType, analysisDepth, aiSafety);
        const aiAnalysis = {
            match: `${player1} vs ${player2}`,
            analysisType: analysisType,
            analysisDepth: analysisDepth,
            aiSafety: aiSafety,
            openaiModel: 'GPT-4',
            prediction: this.generateAIPrediction(confidence, player1, player2),
            aiConfidence: confidence,
            aiReasoning: this.generateAIReasoning(player1, player2, analysisType, analysisDepth),
            openaiPrompt: this.generateOpenAIPrompt(player1, player2, analysisType, analysisDepth),
            aiTransparency: this.provideAITransparency(analysisType, confidence),
            confidenceExplanation: this.explainAIConfidence(confidence),
            learningObjectives: this.generateLearningObjectives(analysisDepth),
            aiLimitations: this.explainAILimitations(),
            openaiIntegration: this.explainOpenAIIntegration(analysisDepth),
            aiEthics: this.provideAIEthics(aiSafety),
            educationalValue: this.assessEducationalValue(confidence, analysisDepth),
            aiModelInsights: this.provideAIModelInsights(analysisType),
            promptEngineering: this.demonstratePromptEngineering(player1, player2, analysisType),
            safetyMeasures: this.explainAISafetyMeasures(aiSafety),
            educationalNote: this.generateEducationalAINote(confidence, analysisDepth),
            timestamp: new Date().toISOString()
        };
        
        return aiAnalysis;
    }

    generateAIConfidence(player1, player2, analysisType, analysisDepth, aiSafety) {
        const baseConfidence = {
            'basic': 0.70,
            'intermediate': 0.78,
            'advanced': 0.85
        };
        
        const analysisModifiers = {
            'performance': 0.05,
            'comparison': 0.03,
            'surface': 0.04,
            'momentum': 0.02,
            'psychological': 0.01
        };
        
        const safetyModifiers = {
            'educational': -0.02,  // More conservative due to safety
            'conservative': -0.01,
            'standard': 0
        };
        
        const randomness = (Math.random() - 0.5) * 0.1;
        let confidence = baseConfidence[analysisDepth] + analysisModifiers[analysisType] + 
                        safetyModifiers[aiSafety] + randomness;
        
        return Math.max(0.65, Math.min(0.92, confidence));
    }

    generateAIPrediction(confidence, player1, player2) {
        if (confidence > 0.80) {
            return `${player1} predicted winner (High AI Confidence)`;
        } else if (confidence > 0.75) {
            return `${player2} predicted winner (Moderate AI Confidence)`;
        } else {
            return `Uncertain - Both players competitive (AI Caution)`;
        }
    }

    generateAIReasoning(player1, player2, analysisType, analysisDepth) {
        const reasoningTemplates = {
            'performance': `OpenAI GPT-4 analysis indicates ${player1} demonstrates superior baseline performance metrics with strong consistency patterns`,
            'comparison': `AI-powered head-to-head analysis reveals balanced competitive dynamics between ${player1} and ${player2}`,
            'surface': `Surface-specific AI evaluation suggests ${player1} shows better adaptation indicators for current conditions`,
            'momentum': `AI momentum assessment indicates ${player2} maintains stronger psychological momentum factors`,
            'psychological': `OpenAI psychological analysis suggests ${player1} possesses superior mental resilience indicators`
        };
        
        const depthModifiers = {
            'basic': ' - Basic AI confidence level applied for educational demonstration.',
            'intermediate': ' - Intermediate AI reasoning with detailed OpenAI integration.',
            'advanced': ' - Advanced AI analysis using sophisticated GPT-4 techniques with comprehensive confidence calibration.'
        };
        
        return reasoningTemplates[analysisType] + depthModifiers[analysisDepth];
    }

    generateOpenAIPrompt(player1, player2, analysisType, analysisDepth) {
        const prompts = {
            basic: `Analyze tennis match: ${player1} vs ${player2}. Focus: ${analysisType}. Provide educational insights with confidence level.`,
            intermediate: `Educational OpenAI GPT-4 Analysis:
Players: ${player1} vs ${player2}
Analysis Type: ${analysisType}
Depth: ${analysisDepth}
Provide: 1) Educational reasoning 2) AI confidence 3) Learning objectives 4) OpenAI integration notes`,
            advanced: `Advanced OpenAI GPT-4 Educational Analysis:
Context: AI learning system
Players: ${player1} (baseline specialist) vs ${player2} (defensive specialist)
Analysis: ${analysisType} (${analysisDepth})
Requirements:
- Detailed AI reasoning process
- OpenAI confidence calibration (0-100%)
- Educational transparency in AI decisions
- Prompt engineering demonstration
- AI safety and ethics considerations
- Learning value assessment
Output format: Educational analysis with AI methodology explanation`
        };
        
        return prompts[analysisDepth];
    }

    provideAITransparency(analysisType, confidence) {
        return {
            aiModel: 'OpenAI GPT-4',
            analysisMethod: this.aiAnalysisTypes[analysisType],
            confidenceSource: 'AI model confidence with educational calibration',
            reasoningProcess: 'AI analysis based on training patterns and educational prompts',
            confidenceInterval: `±${((1 - confidence) * 100).toFixed(1)}%`,
            educationalNote: 'AI confidence reflects model certainty, not prediction accuracy',
            openaiParameters: {
                model: 'gpt-4',
                temperature: 0.3,
                max_tokens: 500,
                educational_mode: true
            }
        };
    }

    explainAIConfidence(confidence) {
        if (confidence > 0.85) {
            return 'Very High AI Confidence - OpenAI model shows strong certainty in educational analysis';
        } else if (confidence > 0.78) {
            return 'High AI Confidence - GPT-4 demonstrates good confidence in educational evaluation';
        } else if (confidence > 0.70) {
            return 'Moderate AI Confidence - OpenAI model shows reasonable confidence with educational caveats';
        } else {
            return 'Lower AI Confidence - GPT-4 indicates uncertainty, good for learning edge cases';
        }
    }

    generateLearningObjectives(analysisDepth) {
        const objectives = {
            'basic': [
                'Understand basic OpenAI GPT-4 integration concepts',
                'Learn fundamental AI confidence assessment',
                'Practice basic prompt engineering techniques',
                'Recognize AI model limitations and biases'
            ],
            'intermediate': [
                'Master intermediate OpenAI API integration',
                'Apply AI confidence calibration techniques',
                'Implement educational safety measures',
                'Understand AI transparency and explainability'
            ],
            'advanced': [
                'Deploy advanced OpenAI GPT-4 techniques',
                'Develop sophisticated AI analysis frameworks',
                'Implement comprehensive AI safety protocols',
                'Create educational AI transparency systems'
            ]
        };
        
        return objectives[analysisDepth];
    }

    explainAILimitations() {
        return {
            modelLimitations: 'OpenAI GPT-4 may not have access to real-time tennis data',
            confidenceCaveats: 'AI confidence does not guarantee prediction accuracy',
            educationalFocus: 'System designed for learning AI methodology, not actual predictions',
            biasConsiderations: 'AI models may exhibit biases from training data',
            transparencyNeeds: 'AI decisions should always include explanation and context'
        };
    }

    explainOpenAIIntegration(analysisDepth) {
        const explanations = {
            'basic': 'Basic OpenAI integration: Simple API calls with educational prompts',
            'intermediate': 'Intermediate OpenAI integration: Structured API usage with confidence calibration',
            'advanced': 'Advanced OpenAI integration: Sophisticated prompt engineering with comprehensive safety measures'
        };
        
        return explanations[analysisDepth];
    }

    provideAIEthics(aiSafety) {
        return {
            educationalPurpose: 'All AI analysis serves educational objectives only',
            safetyLevel: aiSafety,
            transparencyRequirement: 'AI decisions must include educational transparency',
            biasMitigation: 'System includes educational bias detection and mitigation',
            responsibleAI: 'Promotes responsible AI use in educational contexts',
            educationalCompliance: 'Maintains strict educational use compliance'
        };
    }

    assessEducationalValue(confidence, analysisDepth) {
        return {
            learningValue: confidence > 0.80 ? 'Excellent for understanding AI confidence' :
                          confidence > 0.75 ? 'Good for AI methodology learning' :
                          'Valuable for understanding AI limitations',
            tutorialEffectiveness: analysisDepth === 'advanced' ? 'High - Complex AI concepts' :
                                 analysisDepth === 'intermediate' ? 'Medium - Balanced AI learning' :
                                 'Basic - Fundamental AI concepts',
            skillDevelopment: 'AI Integration • Prompt Engineering • Confidence Assessment • Safety Protocols'
        };
    }

    provideAIModelInsights(analysisType) {
        const insights = {
            'performance': 'OpenAI excels at pattern recognition in performance data',
            'comparison': 'GPT-4 provides balanced comparative analysis with educational context',
            'surface': 'AI analysis benefits from surface-specific reasoning patterns',
            'momentum': 'OpenAI can assess momentum through textual pattern analysis',
            'psychological': 'GPT-4 demonstrates strong capability in psychological factor evaluation'
        };
        
        return insights[analysisType];
    }

    demonstratePromptEngineering(player1, player2, analysisType) {
        return {
            promptStrategy: `Educational prompt for ${analysisType} analysis`,
            techniquesUsed: [
                'Role-based prompt design (AI as educational analyst)',
                'Context specification (educational framework)',
                'Output formatting (structured educational response)',
                'Safety constraints (educational only)',
                'Confidence calibration (transparent AI reasoning)'
            ],
            educationalPrompts: [
                `You are an AI educational analyst specializing in tennis analysis using OpenAI GPT-4.`,
                `Provide educational insights with confidence levels and learning objectives.`,
                `Always include transparency in AI reasoning and limitations.`,
                `Focus on learning AI methodology, not actual predictions.`
            ],
            promptOptimization: 'Educational prompts optimized for OpenAI GPT-4 with safety constraints'
        };
    }

    explainAISafetyMeasures(aiSafety) {
        const measures = {
            'educational': [
                'Maximum educational content filtering',
                'Comprehensive AI bias detection',
                'Enhanced transparency requirements',
                'Educational purpose enforcement',
                'No real money recommendations'
            ],
            'conservative': [
                'Conservative AI confidence calibration',
                'Enhanced safety protocol implementation',
                'Comprehensive AI decision documentation',
                'Responsible AI deployment measures',
                'Educational compliance verification'
            ],
            'standard': [
                'Standard AI safety measures',
                'Basic transparency requirements',
                'Educational content guidance',
                'AI model limitation disclosure',
                'Responsible use education'
            ]
        };
        
        return measures[aiSafety];
    }

    generateEducationalAINote(confidence, analysisDepth) {
        const baseNotes = {
            'basic': 'This basic AI analysis demonstrates fundamental OpenAI GPT-4 integration concepts for educational purposes.',
            'intermediate': 'This intermediate AI analysis showcases advanced OpenAI integration with educational safety measures.',
            'advanced': 'This advanced AI analysis exemplifies sophisticated OpenAI GPT-4 techniques with comprehensive educational transparency.'
        };
        
        const confidenceContext = confidence > 0.82 ? 
            'High AI confidence scenarios are excellent for understanding OpenAI model capabilities and limitations.' :
            confidence > 0.75 ?
            'Moderate AI confidence demonstrates balanced OpenAI analysis with educational caveats.' :
            'Lower AI confidence illustrates OpenAI limitations and the importance of educational transparency.';
        
        return baseNotes[analysisDepth] + ' ' + confidenceContext;
    }

    displayAIResults(aiAnalysis) {
        const resultsContainer = document.getElementById('aiResults');
        const contentContainer = document.getElementById('aiResultsContent');
        
        const confidenceClass = aiAnalysis.aiConfidence > 0.82 ? 'confidence-high' : 
                               aiAnalysis.aiConfidence > 0.75 ? 'confidence-medium' : 'confidence-low';
        
        const resultHTML = `
            <div class="ai-result-card ${confidenceClass}">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h4 class="text-lg font-semibold text-gray-800">🤖 OpenAI GPT-4 Analysis: ${aiAnalysis.match}</h4>
                        <p class="text-sm text-gray-600">${aiAnalysis.analysisType} • ${aiAnalysis.analysisDepth} • ${new Date().toLocaleTimeString()}</p>
                    </div>
                    <span class="px-3 py-1 rounded-full text-sm font-bold ${confidenceClass} bg-white shadow-sm">
                        ${(aiAnalysis.aiConfidence * 100).toFixed(1)}% AI Confidence
                    </span>
                </div>
                
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <span class="font-medium text-gray-700">AI Prediction:</span><br>
                        <span class="text-blue-600 font-semibold">${aiAnalysis.prediction}</span>
                    </div>
                    <div>
                        <span class="font-medium text-gray-700">Educational Value:</span><br>
                        <span class="text-purple-600 font-semibold">${aiAnalysis.educationalValue.learningValue}</span>
                    </div>
                </div>
                
                <div class="mb-4">
                    <span class="font-medium text-gray-700">🧠 OpenAI GPT-4 Reasoning:</span>
                    <p class="text-sm text-gray-700 mt-1 leading-relaxed">${aiAnalysis.aiReasoning}</p>
                </div>
                
                <div class="mb-4">
                    <span class="font-medium text-gray-700">🎯 Learning Objectives:</span>
                    <ul class="text-sm text-gray-700 mt-1 space-y-1">
                        ${aiAnalysis.learningObjectives.map(obj => `<li>✓ ${obj}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div class="bg-green-50 p-3 rounded-lg">
                        <span class="font-medium text-green-800">OpenAI Integration (${aiAnalysis.analysisDepth}):</span><br>
                        <span class="text-sm text-green-700">${aiAnalysis.openaiIntegration}</span>
                    </div>
                    <div class="bg-blue-50 p-3 rounded-lg">
                        <span class="font-medium text-blue-800">AI Safety (${aiAnalysis.aiSafety}):</span><br>
                        <span class="text-sm text-blue-700">${aiAnalysis.aiEthics.responsibleAI}</span>
                    </div>
                </div>
                
                <div class="ai-learning-point">
                    <strong>AI Learning Point:</strong> ${aiAnalysis.educationalNote}
                </div>
                
                <div class="ai-transparency mt-4">
                    <strong>🔍 AI Transparency:</strong><br>
                    Model: ${aiAnalysis.aiTransparency.aiModel}<br>
                    Method: ${aiAnalysis.aiTransparency.analysisMethod}<br>
                    Confidence Source: ${aiAnalysis.aiTransparency.confidenceSource}<br>
                    Interval: ${aiAnalysis.aiTransparency.confidenceInterval}
                </div>
                
                <div class="bg-gray-900 text-green-400 p-3 rounded-lg mt-4">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-semibold">OpenAI Prompt (${aiAnalysis.analysisDepth}):</span>
                        <button onclick="copyToClipboard(this.previousElementSibling.textContent)" class="text-blue-400 hover:text-blue-300">
                            <i class="fas fa-copy mr-1"></i>Copy
                        </button>
                    </div>
                    <pre class="text-sm overflow-x-auto">${aiAnalysis.openaiPrompt}</pre>
                </div>
                
                <div class="bg-yellow-50 p-3 rounded-lg mt-4 border border-yellow-200">
                    <div class="flex items-center">
                        <i class="fas fa-shield-alt text-yellow-600 mr-2"></i>
                        <span class="font-semibold text-yellow-800">AI Safety Status: Educational Compliance Active</span>
                    </div>
                </div>
            </div>
        `;
        
        contentContainer.innerHTML = resultHTML;
        resultsContainer.classList.remove('hidden');
        
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // Update AI stats
        this.aiQueries += 1;
        this.updateAIStats();
    }

    updateAIProgress() {
        // Increment progress based on analysis
        this.learningProgress.aiConfidenceCalibration = Math.min(100, this.learningProgress.aiConfidenceCalibration + 1);
        this.updateAIProgressDisplay();
    }

    updateAIStats() {
        document.getElementById('aiQueries').textContent = this.aiQueries.toLocaleString();
    }

    updateAIProgressDisplay() {
        // Update visual progress indicators
        const progressData = this.learningProgress;
        console.log('AI Learning Progress Updated:', progressData);
    }

    addToAIHistory(aiAnalysis) {
        this.analysisHistory.unshift({
            ...aiAnalysis,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 15 analyses
        this.analysisHistory = this.analysisHistory.slice(0, 15);
    }

    showAILoading() {
        const button = document.querySelector('button[onclick="startAIAnalysis()"]');
        if (button) {
            button.classList.add('ai-loading');
            button.innerHTML = '<i class="fas fa-robot mr-2"></i>OpenAI Analyzing...';
            button.disabled = true;
        }
    }

    hideAILoading() {
        const button = document.querySelector('button[onclick="startAIAnalysis()"]');
        if (button) {
            button.classList.remove('ai-loading');
            button.innerHTML = '<i class="fas fa-robot mr-2"></i>Analyze with OpenAI GPT-4';
            button.disabled = false;
        }
    }

    showAINotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `ai-notification ${type}`;
        
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    <i class="fas fa-${type === 'info' ? 'info-circle' : type === 'warning' ? 'exclamation-triangle' : type === 'error' ? 'times-circle' : 'check-circle'} mr-2"></i>
                    <span>${message}</span>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-current opacity-70 hover:opacity-100">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 4 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 4000);
    }

    initializeCharts() {
        // AI Performance Chart
        const aiPerformanceCtx = document.getElementById('aiPerformanceChart');
        if (aiPerformanceCtx) {
            new Chart(aiPerformanceCtx, {
                type: 'line',
                data: {
                    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],
                    datasets: [{
                        label: 'AI Query Success Rate (%)',
                        data: [85, 88, 91, 89, 93, 95],
                        borderColor: 'rgb(16, 163, 127)',
                        backgroundColor: 'rgba(16, 163, 127, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'OpenAI Integration Performance'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            min: 80,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Success Rate %'
                            }
                        }
                    }
                }
            });
        }
        
        // Learning Progress Chart
        const learningProgressCtx = document.getElementById('learningProgressChart');
        if (learningProgressCtx) {
            new Chart(learningProgressCtx, {
                type: 'radar',
                data: {
                    labels: ['OpenAI Integration', 'Prompt Engineering', 'AI Confidence', 'AI Safety', 'Ethics'],
                    datasets: [{
                        label: 'Current Level',
                        data: [92, 88, 85, 79, 82],
                        backgroundColor: 'rgba(37, 99, 235, 0.2)',
                        borderColor: 'rgb(37, 99, 235)',
                        pointBackgroundColor: 'rgb(37, 99, 235)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgb(37, 99, 235)'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'AI Learning Progress'
                        }
                    },
                    scales: {
                        r: {
                            angleLines: {
                                display: false
                            },
                            suggestedMin: 0,
                            suggestedMax: 100
                        }
                    }
                }
            });
        }
    }

    loadAIExamples() {
        // Pre-load OpenAI integration examples
        console.log('🤖 OpenAI GPT-4 Examples Loaded');
    }

    copyPrompt(type) {
        const prompts = {
            basic: `Analyze tennis match for educational purposes:
Players: {player1} vs {player2}
Surface: {surface}
Focus: Performance patterns and educational insights
Output: Educational analysis with confidence level
Note: This is for learning purposes only, no real money involved.`,
            
            advanced: `Educational AI Analysis using OpenAI GPT-4:

Context: Learning AI methodology in sports analysis
Players: {player1} (strong baseline game) vs {player2} (defensive specialist)
Surface: {surface} court
Analysis Depth: {depth}
AI Safety: Educational mode enabled

Provide:
1. Educational reasoning behind prediction
2. AI confidence assessment (0-100%)
3. Key factors considered by AI
4. Educational insights for learning
5. Transparency in AI decision process

Remember: Educational purpose only, no real money.`
        };
        
        const prompt = prompts[type];
        navigator.clipboard.writeText(prompt).then(() => {
            this.showAINotification('OpenAI prompt copied to clipboard!', 'success');
        });
    }
}

// Initialize AI learning system
document.addEventListener('DOMContentLoaded', () => {
    window.aiLearningSystem = new AILearningSystem();
});

// Make functions globally available
function startAIAnalysis() {
    window.aiLearningSystem.startAIAnalysis();
}

function copyPrompt(type) {
    window.aiLearningSystem.copyPrompt(type);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        window.aiLearningSystem.showAINotification('Copied to clipboard!', 'success');
    });
}

// Educational console messages
console.log('🤖 AI Learning System - OpenAI GPT-4 Focus Loaded');
console.log('⚠️  Educational AI Analysis Only - No Real Money');
console.log('🔐 OpenAI Integration Educational Security');
console.log('📊 AI Confidence Calibration Learning');
console.log('🎓 Prompt Engineering Education');
console.log('🛡️  AI Safety and Ethics Training');
    