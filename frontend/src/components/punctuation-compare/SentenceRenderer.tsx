/**
 * 句子渲染器 - 渲染带高亮标点差异的文本
 */

import type { PunctuationDifference, PositionMaps } from './types'
import { PUNCT_MARKS_RENDER_REGEX, getPunctuationColor } from './constants'

interface SentenceRendererProps {
  sentence: string
  cleanStartPos: number
  version: 'version1' | 'version2'
  positionMaps: PositionMaps
  scrollToDiffId?: number | null
  onDiffClick?: (diff: PunctuationDifference) => void
}

export default function SentenceRenderer({
  sentence,
  cleanStartPos,
  version,
  positionMaps,
  scrollToDiffId,
  onDiffClick,
}: SentenceRendererProps) {
  const elements: JSX.Element[] = []
  let sentenceCleanCharIndex = 0
  let i = 0
  let elementKey = 0
  const punct_marks = PUNCT_MARKS_RENDER_REGEX

  const positionToDiffMap = version === 'version1'
    ? positionMaps.positionToDiffMapV1
    : positionMaps.positionToDiffMapV2

  let normalCharsBuffer = ''
  const matchedDiffIds = new Set<number>()

  const flushNormalChars = () => {
    if (normalCharsBuffer) {
      elements.push(
        <span key={`normal-${elementKey++}`} style={{ color: '#000' }}>
          {normalCharsBuffer}
        </span>
      )
      normalCharsBuffer = ''
    }
  }

  // 处理句首标点
  let sentenceStartPuncts = ''
  while (i < sentence.length && punct_marks.test(sentence[i])) {
    sentenceStartPuncts += sentence[i]
    i++
  }

  if (sentenceStartPuncts) {
    const prevDiff = positionToDiffMap.get(cleanStartPos - 1)

    if (prevDiff) {
      const punct1 = prevDiff.version1_punct === '无' ? '' : prevDiff.version1_punct
      const punct2 = prevDiff.version2_punct === '无' ? '' : prevDiff.version2_punct
      const currentVersionPunct = version === 'version1' ? punct1 : punct2
      const otherVersionPunct = version === 'version1' ? punct2 : punct1

      const isPartOfDiff = currentVersionPunct.endsWith(sentenceStartPuncts) ||
                          currentVersionPunct.includes(sentenceStartPuncts)

      if (isPartOfDiff) {
        let commonPrefixLen = 0
        const minLen = Math.min(currentVersionPunct.length, otherVersionPunct.length)
        for (let k = 0; k < minLen; k++) {
          if (currentVersionPunct[k] === otherVersionPunct[k]) {
            commonPrefixLen++
          } else {
            break
          }
        }

        const diffPartInFullPunct = currentVersionPunct.substring(commonPrefixLen)
        const otherDiffPart = otherVersionPunct.substring(commonPrefixLen)

        if (diffPartInFullPunct === sentenceStartPuncts || diffPartInFullPunct.endsWith(sentenceStartPuncts)) {
          const isSelected = scrollToDiffId === prevDiff.id
          const punctForColor = sentenceStartPuncts || otherDiffPart
          const bgColor = getPunctuationColor(punctForColor)

          elements.push(
            <span
              key={`start-punct-diff-${elementKey++}`}
              data-diff-id={prevDiff.id}
              onClick={() => onDiffClick?.(prevDiff)}
              style={{
                backgroundColor: bgColor,
                color: '#fff',
                padding: '2px 4px',
                borderRadius: 3,
                cursor: 'pointer',
                fontWeight: 600,
                transition: 'all 0.2s',
                fontSize: '16px',
                animation: isSelected ? 'highlight-flash 1s ease-in-out 3' : 'none',
                boxShadow: isSelected ? '0 0 0 3px rgba(24, 144, 255, 0.6)' : 'none',
                transform: isSelected ? 'scale(1.2)' : 'scale(1)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.8')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
              title={`${prevDiff.diff_type}: ${prevDiff.version1_punct} → ${prevDiff.version2_punct}`}
            >
              {sentenceStartPuncts}
            </span>
          )
        } else {
          elements.push(
            <span key={`start-punct-${elementKey++}`} style={{ color: '#666' }}>
              {sentenceStartPuncts}
            </span>
          )
        }
      } else {
        elements.push(
          <span key={`start-punct-${elementKey++}`} style={{ color: '#666' }}>
            {sentenceStartPuncts}
          </span>
        )
      }
    } else {
      elements.push(
        <span key={`start-punct-${elementKey++}`} style={{ color: '#666' }}>
          {sentenceStartPuncts}
        </span>
      )
    }
  }

  // 处理主体文本
  while (i < sentence.length) {
    const char = sentence[i]

    if (punct_marks.test(char)) {
      normalCharsBuffer += char
      i++
      continue
    }

    if (/\s/.test(char)) {
      normalCharsBuffer += char
      i++
      continue
    }

    const globalCleanPos = cleanStartPos + sentenceCleanCharIndex

    let j = i + 1
    let puncts = ''
    while (j < sentence.length && punct_marks.test(sentence[j])) {
      puncts += sentence[j]
      j++
    }

    let diff = positionToDiffMap.get(globalCleanPos)

    if (diff) {
      const diffChar = version === 'version1' ? diff.character : (diff.character_v2 || diff.character)
      const cleanDiffChar = diffChar?.replace(/^\[句首\]/, '') || ''
      if (cleanDiffChar && cleanDiffChar !== char) {
        diff = undefined
      } else {
        matchedDiffIds.add(diff.id)
      }
    }

    if (!diff) {
      const diffPrev = positionToDiffMap.get(globalCleanPos - 1)
      if (diffPrev && !matchedDiffIds.has(diffPrev.id)) {
        const diffChar = version === 'version1' ? diffPrev.character : (diffPrev.character_v2 || diffPrev.character)
        const cleanDiffChar = diffChar?.replace(/^\[句首\]/, '') || ''
        if (cleanDiffChar === char) {
          diff = diffPrev
        }
      }

      if (!diff) {
        const diffNext = positionToDiffMap.get(globalCleanPos + 1)
        if (diffNext && !matchedDiffIds.has(diffNext.id)) {
          const diffChar = version === 'version1' ? diffNext.character : (diffNext.character_v2 || diffNext.character)
          const cleanDiffChar = diffChar?.replace(/^\[句首\]/, '') || ''
          if (cleanDiffChar === char) {
            diff = diffNext
          }
        }
      }
    }

    const hasDiff = diff !== undefined
    const isCurrentlySelected = scrollToDiffId && diff?.id === scrollToDiffId

    if (hasDiff || isCurrentlySelected) {
      flushNormalChars()

      const actualPunctInText = puncts
      const expectedPunct = diff ? (version === 'version1' ? diff.version1_punct : diff.version2_punct) : ''

      const punct1 = diff?.version1_punct === '无' ? '' : (diff?.version1_punct || '')
      const punct2 = diff?.version2_punct === '无' ? '' : (diff?.version2_punct || '')
      const hasTrueDiff = punct1 !== punct2

      const actualEmpty = !actualPunctInText
      const expectedEmpty = !expectedPunct || expectedPunct === '无'
      const isConsistent = (actualEmpty === expectedEmpty) || (actualPunctInText === expectedPunct)

      if ((!isConsistent || !hasTrueDiff) && hasDiff) {
        elements.push(
          <span key={`char-${elementKey++}`} style={{ color: '#000' }}>
            {char}
          </span>
        )
        if (puncts) {
          elements.push(
            <span key={`punct-${elementKey++}`} style={{ color: '#666' }}>
              {puncts}
            </span>
          )
        }
      } else {
        elements.push(
          <span
            key={`char-${elementKey++}`}
            style={{
              color: '#000',
              borderBottom: isCurrentlySelected ? '3px solid #13c2c2' : 'none',
              paddingBottom: isCurrentlySelected ? '2px' : '0',
            }}
          >
            {char}
          </span>
        )

        if (hasDiff && diff) {
          const currentVersionPunct = version === 'version1' ? punct1 : punct2
          const otherVersionPunct = version === 'version1' ? punct2 : punct1
          const displayBasePunct = actualPunctInText || currentVersionPunct || ''

          let commonPrefixLen = 0
          const minLen = Math.min(currentVersionPunct.length, otherVersionPunct.length)
          for (let k = 0; k < minLen; k++) {
            if (currentVersionPunct[k] === otherVersionPunct[k]) {
              commonPrefixLen++
            } else {
              break
            }
          }

          const commonPrefix = displayBasePunct.substring(0, commonPrefixLen)
          const diffPart = displayBasePunct.substring(commonPrefixLen)
          const otherDiffPart = otherVersionPunct.substring(commonPrefixLen)
          const isSelected = scrollToDiffId === diff.id
          const punctForColor = diffPart || otherDiffPart || displayBasePunct || otherVersionPunct
          const bgColor = getPunctuationColor(punctForColor)

          if (commonPrefix) {
            elements.push(
              <span key={`punct-common-${elementKey++}`} style={{ color: '#666' }}>
                {commonPrefix}
              </span>
            )
          }

          const displayDiffPunct = diffPart || '∅'
          elements.push(
            <span
              key={`punct-diff-${elementKey++}`}
              data-diff-id={diff.id}
              onClick={() => onDiffClick?.(diff)}
              style={{
                backgroundColor: bgColor,
                color: '#fff',
                padding: '2px 4px',
                borderRadius: 3,
                cursor: 'pointer',
                fontWeight: 600,
                transition: 'all 0.2s',
                fontSize: diffPart ? '16px' : '12px',
                animation: isSelected ? 'highlight-flash 1s ease-in-out 3' : 'none',
                boxShadow: isSelected ? '0 0 0 3px rgba(24, 144, 255, 0.6)' : 'none',
                transform: isSelected ? 'scale(1.2)' : 'scale(1)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.8')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
              title={`${diff.diff_type}: ${diff.version1_punct} → ${diff.version2_punct}`}
            >
              {displayDiffPunct}
            </span>
          )
        } else if (puncts) {
          elements.push(
            <span key={`punct-${elementKey++}`} style={{ color: '#666' }}>
              {puncts}
            </span>
          )
        }
      }
    } else {
      normalCharsBuffer += char
      if (puncts) {
        normalCharsBuffer += puncts
      }
    }

    i = j
    sentenceCleanCharIndex++
  }

  flushNormalChars()

  return <>{elements}</>
}
