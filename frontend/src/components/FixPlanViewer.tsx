import type { FixPlanData } from '../types'

interface FixPlanViewerProps {
  fixPlan: FixPlanData
  onClose?: () => void
}

export default function FixPlanViewer({ fixPlan, onClose }: FixPlanViewerProps) {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10B981' // green
    if (confidence >= 0.6) return '#F59E0B' // yellow
    return '#EF4444' // red
  }

  return (
    <div className="fix-plan-viewer">
      <div className="fix-plan-header">
        <h3>修复计划</h3>
        {onClose && (
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        )}
      </div>

      <div className="fix-plan-content">
        {/* 置信度 */}
        <div className="confidence-section">
          <span className="section-label">置信度</span>
          <div className="confidence-bar">
            <div
              className="confidence-fill"
              style={{
                width: `${fixPlan.confidence * 100}%`,
                backgroundColor: getConfidenceColor(fixPlan.confidence),
              }}
            />
          </div>
          <span
            className="confidence-value"
            style={{ color: getConfidenceColor(fixPlan.confidence) }}
          >
            {Math.round(fixPlan.confidence * 100)}%
          </span>
        </div>

        {/* 根因分析 */}
        <div className="section">
          <h4>问题根因</h4>
          <p className="root-cause">{fixPlan.root_cause}</p>
        </div>

        {/* 修复步骤 */}
        <div className="section">
          <h4>修复步骤</h4>
          <ol className="fix-steps">
            {fixPlan.fix_steps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ol>
        </div>

        {/* 代码位置 */}
        {fixPlan.code_locations.length > 0 && (
          <div className="section">
            <h4>相关代码位置</h4>
            <ul className="code-locations">
              {fixPlan.code_locations.map((location, index) => (
                <li key={index} className="code-location-item">
                  <span className="file-path">{location.file_path}</span>
                  {location.line_range && (
                    <span className="line-range">{location.line_range}</span>
                  )}
                  {location.description && (
                    <p className="location-description">{location.description}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 影响范围评估 */}
        <div className="section">
          <h4>影响范围评估</h4>
          <p className="impact-assessment">{fixPlan.impact_assessment}</p>
        </div>
      </div>
    </div>
  )
}
