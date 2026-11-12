import { useLayoutEffect, useRef, useState } from 'react'

// Below this width a table is always shown as cards (phones, narrow panels).
const MIN_TABLE_WIDTH = 700

/**
 * A table that turns into a list of cards when it does not fit, so nobody
 * ever has to scroll a table (or the page) sideways.
 *
 * It measures the space it really has: the cards appear on a phone, but also
 * on a laptop if a table with many columns would otherwise overflow.
 *
 * columns: [{ key, header, render(row), align?, primary? }]
 *   `primary` marks the column used as the card heading.
 */
export default function DataTable({ columns, rows, rowKey = 'id', onRowClick, caption }) {
  const wrapRef = useRef(null)
  const neededWidth = useRef(MIN_TABLE_WIDTH)
  const [stacked, setStacked] = useState(false)

  useLayoutEffect(() => {
    const wrap = wrapRef.current
    const measure = () => {
      const available = wrap.clientWidth
      if (!stacked) {
        // In table form: does it stick out of its box, or is the box tiny?
        const overflowing = wrap.scrollWidth > available + 1
        if (overflowing) neededWidth.current = wrap.scrollWidth
        if (overflowing || available < MIN_TABLE_WIDTH) setStacked(true)
      } else if (available >= Math.max(neededWidth.current, MIN_TABLE_WIDTH)) {
        setStacked(false) // enough room again: try the table form
      }
    }
    measure()
    const observer = new ResizeObserver(measure)
    observer.observe(wrap)
    return () => observer.disconnect()
  }, [stacked, rows.length, columns.length])

  return (
    <div className={`table-wrap ${stacked ? 'is-stacked' : ''}`} ref={wrapRef}>
      <table className="table">
        {caption && <caption className="sr-only">{caption}</caption>}
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} scope="col" className={column.align ? `align-${column.align}` : undefined}>
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row[rowKey]}
              className={onRowClick ? 'table__row--clickable' : undefined}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  data-label={column.header}
                  className={[
                    column.align && `align-${column.align}`,
                    column.primary && 'table__primary',
                    column.key === 'actions' && 'table__actions',
                  ].filter(Boolean).join(' ') || undefined}
                >
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
