/** The white rounded label used for every section title, as on the library's board. */
export default function SectionPill({ children, dark = false }) {
  return <h2 className={`landing-pill ${dark ? 'landing-pill--dark' : ''}`}>{children}</h2>
}
