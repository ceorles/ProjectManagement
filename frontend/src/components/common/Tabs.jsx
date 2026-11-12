/** Segmented control. tabs: [{ value, label, count? }] */
export default function Tabs({ tabs, value, onChange, label = 'Views', className = '' }) {
  return (
    <div className={`tabs ${className}`} role="tablist" aria-label={label}>
      {tabs.map((tab) => (
        <button
          key={tab.value} type="button" role="tab" aria-selected={tab.value === value}
          className={`tabs__tab ${tab.value === value ? 'is-active' : ''}`}
          onClick={() => onChange(tab.value)}
        >
          {tab.icon && <tab.icon size={15} aria-hidden="true" />}
          {tab.label}
          {tab.count !== undefined && <span className="tabs__count">{tab.count}</span>}
        </button>
      ))}
    </div>
  )
}
