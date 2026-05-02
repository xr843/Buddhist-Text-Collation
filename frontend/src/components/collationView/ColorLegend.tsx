/**
 * 颜色图例说明组件
 * 从 CollationView.tsx 中提取
 */

export default function ColorLegend() {
  return (
    <div style={{
      marginBottom: 12,
      padding: '8px 16px',
      background: '#fafafa',
      borderRadius: 4,
      display: 'flex',
      alignItems: 'center',
      gap: 24,
      fontSize: 13,
      flexWrap: 'wrap'
    }}>
      <span style={{ color: '#666', fontWeight: 'bold' }}>颜色说明：</span>
      <span>
        <span style={{
          background: '#b7eb8f',
          color: '#135200',
          padding: '2px 6px',
          borderRadius: 3,
          fontWeight: 500,
          marginRight: 4
        }}>异体字</span>
        同字异形
      </span>
      <span>
        <span style={{
          background: '#ffa39e',
          color: '#a8071a',
          padding: '2px 6px',
          borderRadius: 3,
          fontWeight: 500,
          marginRight: 4
        }}>讹误</span>
        文字差异
      </span>
      <span>
        <span style={{
          background: '#ffd591',
          color: '#ad4e00',
          padding: '2px 6px',
          borderRadius: 3,
          fontWeight: 500,
          marginRight: 4
        }}>衍文</span>
        校本有底本无
      </span>
      <span>
        <span style={{
          background: '#d3adf7',
          color: '#391085',
          padding: '2px 6px',
          borderRadius: 3,
          fontWeight: 500,
          marginRight: 4
        }}>脱文</span>
        底本有校本无
      </span>
    </div>
  )
}
