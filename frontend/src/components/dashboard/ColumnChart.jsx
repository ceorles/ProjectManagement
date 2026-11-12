import { useState } from 'react'
import { ChartColumn, Table } from 'lucide-react'

/** Round the axis up to a clean number and return its tick values. */
function niceScale(maxValue) {
  if (maxValue <= 4) return { max: 4, ticks: [0, 2, 4] }
  const magnitude = 10 ** Math.floor(Math.log10(maxValue))
  // Whole-number steps only (1, 2, 5, 10, 20, 50, ...), at most four above zero.
  const step = [0.5, 1, 2, 5, 10]
    .map((factor) => factor * magnitude)
    .find((candidate) => Number.isInteger(candidate) && maxValue / candidate <= 4)
  const max = Math.ceil(maxValue / step) * step
  const ticks = []
  for (let tick = 0; tick <= max; tick += step) ticks.push(tick)
  return { max, ticks }
}

/**
 * Column chart, stacked when there is more than one series.
 *
 *   data:   [{ label, title, values: { seat: 4, room: 1 } }]
 *   series: [{ key, label, color }]
 *
 * - One y-axis, starting at zero.
 * - Hovering or focusing a column shows its exact numbers.
 * - "Table" switches to the same data as a table, so nothing depends on
 *   being able to tell the colours apart.
 */
export default function ColumnChart({ data, series, height = 220, unit = 'reservations', caption }) {
  const [active, setActive] = useState(null)
  const [asTable, setAsTable] = useState(false)

  const totals = data.map((item) => series.reduce((sum, s) => sum + (item.values[s.key] || 0), 0))
  const { max, ticks } = niceScale(Math.max(...totals, 0))
  const labelEvery = Math.ceil(data.length / 8)
  const stacked = series.length > 1
  const focused = active !== null ? data[active] : null

  return (
    <figure className="chart">
      <div className="chart__top">
        {stacked ? (
          <ul className="chart__legend">
            {series.map((s) => (
              <li key={s.key}><span className="chart__swatch" style={{ background: s.color }} />{s.label}</li>
            ))}
          </ul>
        ) : <span />}
        <button type="button" className="chart__toggle" onClick={() => setAsTable((value) => !value)}
          aria-pressed={asTable}>
          {asTable ? <ChartColumn size={14} aria-hidden="true" /> : <Table size={14} aria-hidden="true" />}
          {asTable ? 'Chart' : 'Table'}
        </button>
      </div>

      {asTable ? (
        <div className="chart__table">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">{caption || 'Period'}</th>
                {series.map((s) => <th key={s.key} scope="col" className="align-right">{s.label}</th>)}
                {stacked && <th scope="col" className="align-right">Total</th>}
              </tr>
            </thead>
            <tbody>
              {data.map((item, index) => (
                <tr key={item.title}>
                  <td className="table__primary">{item.title}</td>
                  {series.map((s) => (
                    <td key={s.key} data-label={s.label} className="align-right">{item.values[s.key] || 0}</td>
                  ))}
                  {stacked && <td data-label="Total" className="align-right strong">{totals[index]}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <>
          <div className="chart__plot" style={{ height }} onMouseLeave={() => setActive(null)}>
            <div className="chart__grid" aria-hidden="true">
              {ticks.map((tick) => (
                <span key={tick} style={{ bottom: `${tick / max * 100}%` }}><i>{tick}</i></span>
              ))}
            </div>
            <div className="chart__columns">
              {data.map((item, index) => {
                const visible = series.filter((s) => item.values[s.key] > 0)
                return (
                  <div
                    key={item.title} className={`chart__slot ${active === index ? 'is-active' : ''}`}
                    tabIndex={0} role="img"
                    aria-label={`${item.title}: ${series.map((s) => `${item.values[s.key] || 0} ${s.label.toLowerCase()}`).join(', ')}`}
                    onMouseEnter={() => setActive(index)} onFocus={() => setActive(index)}
                    onBlur={() => setActive(null)}
                  >
                    <div className="chart__column">
                      {visible.map((s, position) => (
                        <span
                          key={s.key}
                          className={`chart__segment ${position === visible.length - 1 ? 'is-top' : ''}`}
                          style={{ height: `${item.values[s.key] / max * 100}%`, background: s.color }}
                        />
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
            {focused && (
              <div
                className="chart__tooltip" role="status"
                style={{ left: `${(active + 0.5) / data.length * 100}%` }}
                data-edge={active < data.length * 0.2 ? 'start' : active > data.length * 0.8 ? 'end' : undefined}
              >
                <p className="chart__tooltip-title">{focused.title}</p>
                {series.map((s) => (
                  <p key={s.key} className="chart__tooltip-row">
                    <span className="chart__swatch" style={{ background: s.color }} />
                    <span className="grow">{s.label}</span>
                    <strong>{focused.values[s.key] || 0}</strong>
                  </p>
                ))}
                {stacked && (
                  <p className="chart__tooltip-row chart__tooltip-total">
                    <span className="grow">Total {unit}</span><strong>{totals[active]}</strong>
                  </p>
                )}
              </div>
            )}
          </div>
          <div className="chart__axis" aria-hidden="true">
            {data.map((item, index) => (
              <span key={item.title}>{index % labelEvery === 0 ? item.label : ''}</span>
            ))}
          </div>
        </>
      )}
    </figure>
  )
}
