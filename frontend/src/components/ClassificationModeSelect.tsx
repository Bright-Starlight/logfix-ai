import { useState } from 'react'
import type { ClassificationMode } from '../types'

interface ClassificationModeSelectProps {
  onModeSelected: (mode: ClassificationMode) => void
  isProcessing?: boolean
}

export default function ClassificationModeSelect({
  onModeSelected,
  isProcessing = false,
}: ClassificationModeSelectProps) {
  const [selectedMode, setSelectedMode] = useState<ClassificationMode | null>(null)

  const handleConfirm = () => {
    if (selectedMode && !isProcessing) {
      onModeSelected(selectedMode)
    }
  }

  const handleModeChange = (mode: ClassificationMode) => {
    if (!isProcessing) {
      setSelectedMode(mode)
    }
  }

  return (
    <div className="classification-mode-select">
      <h3>选择分类模式</h3>
      <p className="mode-description">请选择日志分类的处理方式：</p>

      <div className="mode-options">
        <label
          className={`mode-option ${selectedMode === 'rule_engine' ? 'selected' : ''} ${isProcessing ? 'disabled' : ''}`}
        >
          <input
            type="radio"
            name="classificationMode"
            value="rule_engine"
            checked={selectedMode === 'rule_engine'}
            onChange={() => handleModeChange('rule_engine')}
            disabled={isProcessing}
          />
          <div className="mode-content">
            <span className="mode-name">规则引擎模式</span>
            <span className="mode-detail">基于预定义规则进行快速分类</span>
            <span className="mode-advantages">
              <span className="advantage">高速处理</span>
              <span className="advantage">确定性强</span>
              <span className="advantage">无需API调用</span>
            </span>
          </div>
        </label>

        <label
          className={`mode-option ${selectedMode === 'ai' ? 'selected' : ''} ${isProcessing ? 'disabled' : ''}`}
        >
          <input
            type="radio"
            name="classificationMode"
            value="ai"
            checked={selectedMode === 'ai'}
            onChange={() => handleModeChange('ai')}
            disabled={isProcessing}
          />
          <div className="mode-content">
            <span className="mode-name">AI 模式</span>
            <span className="mode-detail">使用人工智能分析日志内容</span>
            <span className="mode-advantages">
              <span className="advantage">智能分类</span>
              <span className="advantage">上下文理解</span>
              <span className="advantage">自动学习</span>
            </span>
          </div>
        </label>
      </div>

      <button
        className="confirm-button"
        onClick={handleConfirm}
        disabled={!selectedMode || isProcessing}
      >
        {isProcessing ? '处理中...' : '确认并开始分类'}
      </button>
    </div>
  )
}
